"""Pose the fingers (not saved) and render both hands: rest / curl / fist / point / spread, with the bones drawn.
Curling = rotating the finger bones around their local X axis (negative = toward the palm).
Run: Blender -b --factory-startup <blend> --python scripts/finger_pose_test.py -- <prefix>"""
import bpy, sys, math
from mathutils import Vector, Euler
args = sys.argv[sys.argv.index("--")+1:]; prefix = args[0]
sc = bpy.context.scene; rig = bpy.data.objects["RIG_Human"]; body = bpy.data.objects["HUM_Body"]
for o in sc.objects: o.hide_render = o.name != "HUM_Body"
r = sc.render; r.engine = 'BLENDER_WORKBENCH'; r.resolution_x = r.resolution_y = 500
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.78, .7, .64); sh.show_cavity = True
F = ["f_index", "f_middle", "f_ring", "f_pinky"]
POSES = {
    "rest": {},
    "curl": {f"{f}.0{k}": (-35, 0) for f in F for k in (1, 2, 3)} | {"thumb.02": (-20, 0), "thumb.03": (-25, 0)},
    "fist": {f"{f}.0{k}": (-80 if k == 1 else -95, 0) for f in F for k in (1, 2, 3)} | {"thumb.01": (-15, 0), "thumb.02": (-40, 0), "thumb.03": (-50, 0)},
    "point": {f"{f}.0{k}": (-80 if k == 1 else -95, 0) for f in F[1:] for k in (1, 2, 3)} | {"thumb.02": (-35, 0), "thumb.03": (-45, 0)},
    "spread": {"f_index.01": (0, 12), "f_middle.01": (0, 3), "f_ring.01": (0, -6), "f_pinky.01": (0, -15), "thumb.01": (0, 15)},
}
cd = bpy.data.cameras.new("C"); cd.type = 'ORTHO'; cd.ortho_scale = 0.24
cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
for pose, rots in POSES.items():
    for pb in rig.pose.bones: pb.matrix_basis.identity()
    for s in "LR":
        for name, (x, z) in rots.items():
            pb = rig.pose.bones[f"{name}.{s}"]; pb.rotation_mode = 'XYZ'
            pb.rotation_euler = Euler((math.radians(x), 0, math.radians(z if s == "L" else -z)))
    bpy.context.view_layer.update()
    for s in "LR":
        fb = [pb for pb in rig.pose.bones if pb.name.endswith(f".{s}") and (pb.name.startswith("f_") or pb.name.startswith("thumb"))]
        c = rig.matrix_world @ (sum((pb.head + pb.tail for pb in fb), Vector()) / (2 * len(fb)))
        for vn, d in {"front": Vector((0, -1, 0.1)), "side": Vector((-1 if s == "R" else 1, -0.4, 0.1))}.items():
            d.normalize(); cam.location = c + d * 2; cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = (-d).to_track_quat('-Z', 'Y')
            r.filepath = f"{prefix}_{pose}_{s}_{vn}.png"; bpy.ops.render.render(write_still=True)
    if pose == "rest":  # bone sticks over the rest hands (x-ray)
        sh.show_xray = True; sh.xray_alpha = 0.45; sticks = []
        for pb in rig.pose.bones:
            if not (pb.name.startswith("f_") or pb.name.startswith("thumb") or pb.name.startswith("hand.")): continue
            a, b = rig.matrix_world @ pb.head, rig.matrix_world @ pb.tail
            bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.0018, depth=(b - a).length, location=(a + b) / 2)
            st = bpy.context.object; st.rotation_mode = 'QUATERNION'; st.rotation_quaternion = (b - a).to_track_quat('Z', 'Y'); sticks.append(st)
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0035, location=a, segments=8, ring_count=6); sticks.append(bpy.context.object)
        mat = bpy.data.materials.new("bone"); mat.diffuse_color = (1, .3, .05, 1)
        for st in sticks: st.data.materials.append(mat)
        body.data.materials.clear(); m2 = bpy.data.materials.new("skin"); m2.diffuse_color = (.78, .7, .64, 1); body.data.materials.append(m2)
        sh.color_type = 'MATERIAL'
        for s in "LR":
            fb = [pb for pb in rig.pose.bones if pb.name.endswith(f".{s}") and (pb.name.startswith("f_") or pb.name.startswith("thumb"))]
            c = rig.matrix_world @ (sum((pb.head + pb.tail for pb in fb), Vector()) / (2 * len(fb)))
            for vn, d in {"front": Vector((0, -1, 0.1)), "side": Vector((-1 if s == "R" else 1, -0.4, 0.1))}.items():
                d.normalize(); cam.location = c + d * 2; cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = (-d).to_track_quat('-Z', 'Y')
                r.filepath = f"{prefix}_bones_{s}_{vn}.png"; bpy.ops.render.render(write_still=True)
        for st in sticks: bpy.data.objects.remove(st)
        sh.show_xray = False; sh.color_type = 'SINGLE'
