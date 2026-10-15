# Headless frame renderer:  blender -b scene.blend -P scripts/render_sequence.py -- [options]
#   --preset draft|final      960x540 / 1920x1080 with the Eevee settings in PRESETS below
#   --range A B               frames A..B inclusive (default 1..totalFrames)
#   --shots S04,S05           only the frames of these shots (timeline.json ids)
#   --frames 230,620          explicit frame list (tests)
#   --every N                 every Nth frame of the selection
#   --out DIR                 default production/out/frames_<preset>   (f00001.png ...)
#   --set key=value           override one Eevee property, e.g. --set taa_render_samples=24 --set ray_tracing_options.resolution_scale=2
#   --tag NAME                suffix for the timing log (production/out/frame_times_<preset><tag>.csv)
# Resume-friendly: frames whose PNG exists are skipped; each frame is written to a temp name and renamed when complete.
# Every frame sets scene.camera from the shot list and calls frame_set, so the result does not depend on marker evaluation.
import bpy, sys, os, json, time, argparse, resource
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--preset", default="draft", choices=["draft", "final"]); ap.add_argument("--range", nargs=2, type=int)
ap.add_argument("--shots"); ap.add_argument("--frames"); ap.add_argument("--every", type=int, default=1)
ap.add_argument("--out"); ap.add_argument("--set", action="append", default=[]); ap.add_argument("--tag", default="")
a = ap.parse_args(argv)

PRESETS = {   # chosen from the tests in lab/results/car-render.md
    "draft": dict(res=(960, 540), eevee=dict(taa_render_samples=16, shadow_ray_count=1, shadow_step_count=3, light_threshold=0.005,
                  **{"ray_tracing_options.resolution_scale": "1"}, use_fast_gi=False)),
    "final": dict(res=(1920, 1080), eevee=dict(taa_render_samples=32, shadow_ray_count=2, shadow_step_count=6, light_threshold=0.005,
                  **{"ray_tracing_options.resolution_scale": "1"}, use_fast_gi=False)),
}
blend_dir = os.path.dirname(bpy.data.filepath)
TL = json.load(open(os.path.join(blend_dir, "production", "timeline.json")))
sc = bpy.context.scene; r = sc.render; ee = sc.eevee
P = PRESETS[a.preset]
r.resolution_x, r.resolution_y = P["res"]; r.resolution_percentage = 100
def setattr_path(root, path, val):
    *head, last = path.split(".")
    for h in head: root = getattr(root, h)
    cur = getattr(root, last)
    if isinstance(cur, bool): val = val in (True, "1", "true", "True")
    elif isinstance(cur, int): val = int(val)
    elif isinstance(cur, float): val = float(val)
    setattr(root, last, val)
for k, v in P["eevee"].items(): setattr_path(ee, k, v)
for kv in a.set: k, v = kv.split("=", 1); setattr_path(ee, k, v)
r.image_settings.file_format = "PNG"; r.image_settings.color_mode = "RGB"; r.image_settings.color_depth = "8"; r.image_settings.compression = 15
r.use_motion_blur = False; r.fps = TL["meta"]["fps"]

N = TL["meta"]["totalFrames"]; shot_of = {}
for s in TL["shots"]:
    for f in range(s["startFrame"], s["endFrame"]): shot_of[f] = s
frames = list(range(1, N + 1))
if a.range: frames = [f for f in frames if a.range[0] <= f <= a.range[1]]
if a.shots: keep = set(a.shots.split(",")); frames = [f for f in frames if shot_of[f]["id"] in keep]
if a.frames: frames = [int(x) for x in a.frames.split(",")]
frames = frames[::a.every]
out = a.out or os.path.join(blend_dir, "production", "out", "frames_" + a.preset); os.makedirs(out, exist_ok=True)
logp = os.path.join(blend_dir, "production", "out", f"frame_times_{a.preset}{a.tag}.csv")
new = not os.path.exists(logp); log = open(logp, "a")
if new: log.write("frame,shot,camera,seconds,max_rss_mb\n")
print(f"[render_sequence] {a.preset} {r.resolution_x}x{r.resolution_y} samples={ee.taa_render_samples} {len(frames)} frames -> {out}", flush=True)
tmp = os.path.join(out, "_partial.png"); t_all = time.time(); done = 0
for f in frames:
    dst = os.path.join(out, f"f{f:05d}.png")
    if os.path.exists(dst) and os.path.getsize(dst) > 0: continue
    s = shot_of[f]; sc.camera = bpy.data.objects[s["camera"]]; sc.frame_set(f)
    r.filepath = tmp; t0 = time.time()
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t0; os.replace(tmp, dst); done += 1
    log.write(f"{f},{s['id']},{s['camera']},{dt:.3f},{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1048576:.0f}\n"); log.flush()
    if done % 25 == 0 or len(frames) < 30: print(f"[render_sequence] f{f} {s['id']} {dt:.2f}s ({done}/{len(frames)})", flush=True)
print(f"[render_sequence] done: {done} frames in {time.time() - t_all:.1f}s", flush=True)
