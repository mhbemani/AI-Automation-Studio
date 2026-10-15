"""blender -b facet.blend -P render_performance.py -- --perf performance_16x9.json --out DIR --camera-cfg character.json [--preset draft|final]
        [--frames a-b] [--only f1,f2,...] [--every N] [--res 480] [--samples 4] [--verify verify_in.json --verify-out verify.json] [--no-render] [--shadow-blob]
Poses the rig from the solver's per-frame channels (keyframe EVERY frame, no NLA, no action switching), renders an RGBA PNG sequence f_%04d.png
(frame number = video frame + 1, like every clip of this pipeline) and optionally measures where hands / head really are on screen (verify)."""
import bpy, sys, os, json, argparse, time
HERE = os.path.dirname(os.path.abspath(bpy.data.filepath)); sys.path.insert(0, HERE)
import stagecfg, rigpose
from bpy_extras.object_utils import world_to_camera_view
ap = argparse.ArgumentParser(); ap.add_argument("--perf", required=True); ap.add_argument("--out"); ap.add_argument("--camera-cfg", required=True)
ap.add_argument("--preset", default="draft"); ap.add_argument("--frames"); ap.add_argument("--only"); ap.add_argument("--every", type=int, default=1)
ap.add_argument("--res", type=int); ap.add_argument("--samples", type=int); ap.add_argument("--verify"); ap.add_argument("--verify-out"); ap.add_argument("--no-render", action="store_true")
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:])
cfg = json.load(open(a.camera_cfg)); k = cfg["camera"]; stagecfg.CAMERAS[k["name"]] = (k["targetZ"], k["visHeight"], k["azimuthDeg"], k["elevationDeg"], k["aspect"])
for p, v in cfg.get("quality", {}).items(): stagecfg.QUALITY[p] = tuple(v)
perf = json.load(open(a.perf)); ch = perf["channels"]; f0 = perf["f0"]; n = perf["count"]
sc = bpy.context.scene; cam = bpy.data.objects["STAGE_camera"]
if a.res: stagecfg.QUALITY[a.preset] = (a.res, a.samples or stagecfg.QUALITY[a.preset][1])
stagecfg.apply(sc, cam, k["name"], a.preset, k["aspect"])
if a.samples: sc.eevee.taa_render_samples = a.samples
rig = rigpose.Rig()
t0 = time.time()
for i in range(n): rig.pose_frame(ch, i, frame=f0 + i + 1)   # keyframe every frame; Blender frame = video frame + 1
print("POSE_SECONDS %.1f frames %d" % (time.time() - t0, n))
sc.frame_start, sc.frame_end = f0 + 1, f0 + n

if a.verify:   # where do the hands / head really end up on screen? (independent of the solver's own model: evaluated armature + the real camera)
    ver = json.load(open(a.verify)); res = []
    def px(co, rect):
        v = world_to_camera_view(sc, cam, co); return [rect[0] + v.x * rect[2], rect[1] + (1 - v.y) * rect[2]]
    ao = rig.obj.matrix_world
    for item in ver["frames"]:
        f = item["frame"]; sc.frame_set(f + 1); bpy.context.view_layer.update(); rect = item["rect"]; P = rig.obj.pose.bones; r = {"frame": f}
        for side in ("L", "R"):
            r["wrist_" + side] = px(ao @ P["hand_" + side].head, rect); r["tip_" + side] = px(ao @ P["hand_" + side].tail, rect); r["shoulder_" + side] = px(ao @ P["arm_" + side].head, rect)
        em = (P["eye_L"].head + P["eye_R"].head) / 2; hp = P["head"]; hh = hp.head
        Rp = (hp.matrix.to_3x3() @ rig.M["head"].inverted()); g = Rp @ __import__("mathutils").Vector((0, -1, 0))
        r["eye"] = px(ao @ em, rect); r["gaze_pt"] = px(ao @ (em + g * 1.0), rect)
        res.append(r)
    json.dump({"frames": res}, open(a.verify_out, "w")); print("VERIFY frames", len(res))

if not a.no_render:
    os.makedirs(a.out, exist_ok=True)
    for f in os.listdir(a.out):
        if f.startswith("f_") and f.endswith(".png"): os.remove(os.path.join(a.out, f))
    sc.render.filepath = os.path.join(a.out, "f_")
    t0 = time.time()
    if a.only:
        for f in [int(x) for x in a.only.split(",")]:
            sc.frame_set(f + 1); sc.render.filepath = os.path.join(a.out, "f_%04d" % (f + 1)); bpy.ops.render.render(write_still=True)
    else:
        if a.frames: x, y = [int(v) for v in a.frames.split("-")]; sc.frame_start, sc.frame_end = x + 1, y
        sc.frame_step = max(1, a.every); bpy.ops.render.render(animation=True)
    print("RENDER_SECONDS %.1f %dx%d samples %d" % (time.time() - t0, sc.render.resolution_x, sc.render.resolution_y, sc.eevee.taa_render_samples))
