"""Flicker bisect: smooth constant-speed sweep (head yaw -25..25 deg, right arm raise 0..90 deg, torso twist) rendered as PNGs, to see whether
facet specular / clearcoat highlights pop on moving facets.  blender -b facet.blend -P sweep_check.py -- --out DIR [--preset draft] [--frames 90] [--camera-cfg ...] [--eevee k=v ...]"""
import bpy, sys, os, json, argparse, time
from math import radians as rad
from mathutils import Euler
HERE = os.path.dirname(os.path.abspath(bpy.data.filepath)); sys.path.insert(0, HERE)
import stagecfg
ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--preset", default="draft"); ap.add_argument("--frames", type=int, default=90)
ap.add_argument("--camera-cfg"); ap.add_argument("--eevee", nargs="*", default=[]); ap.add_argument("--material", nargs="*", default=[])
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:])
c = json.load(open(a.camera_cfg)); k = c["camera"]; stagecfg.CAMERAS[k["name"]] = (k["targetZ"], k["visHeight"], k["azimuthDeg"], k["elevationDeg"], k["aspect"])
for p, v in c.get("quality", {}).items(): stagecfg.QUALITY[p] = tuple(v)
sc = bpy.context.scene; rig = bpy.data.objects["FacetRig"]; rig.animation_data_clear()
stagecfg.apply(sc, bpy.data.objects["STAGE_camera"], k["name"], a.preset)
for kv in a.eevee: n, v = kv.split("="); setattr(sc.eevee, n, eval(v))
for kv in a.material:   # e.g. crystal:Coat Weight=0
    m, rest = kv.split(":"); n, v = rest.split("="); bpy.data.materials[m].node_tree.nodes["Principled BSDF"].inputs[n].default_value = float(v)
CONV = {pb.name: pb.bone.matrix_local.to_3x3() for pb in rig.pose.bones}
def q(bn, e): m = CONV[bn]; return (m.inverted() @ Euler([rad(x) for x in e]).to_matrix() @ m).to_quaternion()
N = a.frames
for bn in ("head", "arm_R", "torso"): rig.pose.bones[bn].rotation_mode = 'QUATERNION'
for f in range(N):
    u = f / (N - 1)
    rig.pose.bones["head"].rotation_quaternion = q("head", (0, 0, -25 + 50 * u))
    rig.pose.bones["arm_R"].rotation_quaternion = q("arm_R", (0, -90 * u, 0))
    rig.pose.bones["torso"].rotation_quaternion = q("torso", (0, 0, -10 + 20 * u))
    for bn in ("head", "arm_R", "torso"): rig.pose.bones[bn].keyframe_insert("rotation_quaternion", frame=f + 1)
os.makedirs(a.out, exist_ok=True); sc.render.filepath = os.path.join(a.out, "f_"); sc.frame_start, sc.frame_end = 1, N
t = time.time(); bpy.ops.render.render(animation=True); print("RENDER_SECONDS %.1f" % (time.time() - t))
