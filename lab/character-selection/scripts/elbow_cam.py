"""Close-up of an elbow from 4 sides around the arm (camera perpendicular to the arm, centred on the elbow), with the
pose_test.py pose applied first. Run: Blender -b <blend> --python scripts/elbow_cam.py -- <prefix> <pose> [L|R]"""
import bpy, sys, os, math
from mathutils import Vector, Matrix
args = sys.argv[sys.argv.index("--") + 1:]; prefix, pose = args[0], args[1]; s = args[2] if len(args) > 2 else "L"
src = open(os.path.join(os.path.dirname(__file__), "pose_test.py")).read()
exec(src.split("sys.argv = sys.argv[:sys.argv.index")[0].replace("pose = args[1]", f"pose = {pose!r}"))
sc = bpy.context.scene; bpy.context.view_layer.update()
for ob in sc.objects: ob.hide_render = ob.name != "HUM_Body"
r = sc.render; r.engine = 'BLENDER_WORKBENCH'; r.resolution_x = r.resolution_y = 600
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.75, .72, .68); sh.show_cavity = True; sh.show_object_outline = True
pb = rig.pose.bones; M = rig.matrix_world
E = M @ pb[f"forearm.{s}"].head; S = M @ pb[f"upper_arm.{s}"].head; W = M @ pb[f"forearm.{s}"].tail
ax = ((E - S).normalized() + (W - E).normalized()).normalized()
side = (E - S).normalized().cross((W - E).normalized())
if side.length < 1e-3: side = ax.cross(Vector((0, 0, 1)))
side.normalize(); up = ax.cross(side).normalized()
cd = bpy.data.cameras.new("C"); cd.type = 'ORTHO'; cd.ortho_scale = 0.38
cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
for k, n in enumerate(("a", "b", "c", "d")):
    a = math.radians(90 * k); d = side * math.cos(a) + up * math.sin(a)
    cam.location = E + d * 2; cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = (-d).to_track_quat('-Z', 'Y')
    r.filepath = f"{prefix}_{pose}_{n}.png"; bpy.ops.render.render(write_still=True)
