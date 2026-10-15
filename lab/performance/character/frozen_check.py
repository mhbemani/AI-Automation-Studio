"""Flicker bisect step: render a FROZEN pose for N frames (nothing animated) so any frame-to-frame difference is render noise.
blender -b facet.blend -P frozen_check.py -- --out DIR [--preset draft|final] [--frames 60] [--camera-cfg ../pipeline/character.json] [--samples N] [--eevee name=value ...]"""
import bpy, sys, os, json, argparse, time
HERE = os.path.dirname(os.path.abspath(bpy.data.filepath)); sys.path.insert(0, HERE)
import stagecfg
ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--preset", default="draft"); ap.add_argument("--frames", type=int, default=60)
ap.add_argument("--camera-cfg"); ap.add_argument("--samples", type=int); ap.add_argument("--eevee", nargs="*", default=[]); ap.add_argument("--render", nargs="*", default=[])
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:])
if a.camera_cfg:
    c = json.load(open(a.camera_cfg)); k = c["camera"]; stagecfg.CAMERAS[k["name"]] = (k["targetZ"], k["visHeight"], k["azimuthDeg"], k["elevationDeg"], k["aspect"])
    for p, v in c.get("quality", {}).items(): stagecfg.QUALITY[p] = tuple(v)
    cam_name = k["name"]
else: cam_name = "full"
sc = bpy.context.scene; rig = bpy.data.objects["FacetRig"]
rig.animation_data.action = bpy.data.actions["talk"]; sc.frame_set(20)
vals = {pb.name: (pb.rotation_quaternion.copy(), pb.location.copy(), pb.scale.copy()) for pb in rig.pose.bones}
rig.animation_data_clear()
for pb in rig.pose.bones: pb.rotation_quaternion, pb.location, pb.scale = vals[pb.name]
stagecfg.apply(sc, bpy.data.objects["STAGE_camera"], cam_name, a.preset)
if a.samples: sc.eevee.taa_render_samples = a.samples
for kv in a.eevee:
    k, v = kv.split("="); setattr(sc.eevee, k, eval(v))
for kv in a.render:
    k, v = kv.split("="); setattr(sc.render, k, eval(v))
os.makedirs(a.out, exist_ok=True); sc.render.filepath = os.path.join(a.out, "f_"); sc.frame_start, sc.frame_end = 1, a.frames
t = time.time(); bpy.ops.render.render(animation=True)
print("RENDER_SECONDS %.1f samples %d %dx%d" % (time.time() - t, sc.eevee.taa_render_samples, sc.render.resolution_x, sc.render.resolution_y))
