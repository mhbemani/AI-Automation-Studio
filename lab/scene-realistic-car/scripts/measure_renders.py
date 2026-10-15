# Headless render timings: blender -b scene.blend -P scripts/measure_renders.py -- OUTDIR W H SAMPLES FRAME@CAM ...
# One warm-up render (shader compile) is discarded; then each FRAME@CAM is rendered once and timed.
# Writes OUTDIR/times_<W>x<H>_<SAMPLES>.csv and the stills (PNG). Peak memory: run under /usr/bin/time -l.
import bpy, sys, time, os, csv
a = sys.argv[sys.argv.index("--") + 1:]
out, W, H, S, specs = a[0], int(a[1]), int(a[2]), int(a[3]), a[4:]
os.makedirs(out, exist_ok=True)
sc, r = bpy.context.scene, bpy.context.scene.render
r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100
sc.eevee.taa_render_samples = S
r.image_settings.file_format = "PNG"
for m in sc.timeline_markers: m.camera = None          # each spec names its camera
rows = []
def render(f, cam, path):
    sc.frame_set(f); sc.camera = bpy.data.objects[cam]; r.filepath = path
    t = time.perf_counter(); bpy.ops.render.render(write_still=True); return time.perf_counter() - t
f0, c0 = specs[0].split("@"); render(int(f0), c0, os.path.join(out, "warmup.png"))
for s in specs:
    f, cam = s.split("@")
    dt = render(int(f), cam, os.path.join(out, f"{cam}_f{f}_{W}x{H}.png"))
    rows.append((cam, f, W, H, S, round(dt, 2))); print(f"TIME {cam} f{f} {W}x{H} s{S}: {dt:.2f} s", flush=True)
with open(os.path.join(out, f"times_{W}x{H}_{S}.csv"), "w", newline="") as fh:
    csv.writer(fh).writerows([("camera", "frame", "w", "h", "samples", "seconds")] + rows)
