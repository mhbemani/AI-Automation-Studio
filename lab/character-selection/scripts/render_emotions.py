"""Render every EMO_* action: a body shot (perspective, 3/4 from his front-left, where Claude would be) and a face
close-up (front, slightly from below because his head hangs). Also a brow-key test (each brow key alone at 1.0).
Run: Blender -b <blend> --python scripts/render_emotions.py -- <out_dir>"""
import bpy, sys, os, math
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1]; os.makedirs(out, exist_ok=True)
sc = bpy.context.scene; o = bpy.data.objects["HUM_Body"]; rig = bpy.data.objects["RIG_Human"]
for ob in sc.objects: ob.hide_render = ob.name != "HUM_Body"
r = sc.render; r.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.72, .7, .67)
sh.show_cavity = True; sh.cavity_type = 'BOTH'; sh.show_shadows = True; sh.show_object_outline = True
sc.world = sc.world or bpy.data.worlds.new("W")
cam_d = bpy.data.cameras.new("C"); cam = bpy.data.objects.new("C", cam_d); sc.collection.objects.link(cam); sc.camera = cam
def shoot(path, loc, target, ortho=None, res=(700, 900), lens=50):
    r.resolution_x, r.resolution_y = res
    cam_d.type = 'ORTHO' if ortho else 'PERSP'
    if ortho: cam_d.ortho_scale = ortho
    else: cam_d.lens = lens
    cam.location = loc; d = (Vector(target) - Vector(loc)); cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = d.to_track_quat('-Z', 'Y')
    r.filepath = path; bpy.ops.render.render(write_still=True)
def head_point():
    bpy.context.view_layer.update(); pb = rig.pose.bones["head"]
    return rig.matrix_world @ ((pb.head + pb.tail) / 2)
def face_dir():
    """where the face points now: the rest-pose face direction carried through the head bone's pose"""
    pb = rig.pose.bones["head"]; b = pb.bone
    u = (b.tail_local - b.head_local).normalized(); f = Vector((0, -1, 0)); f = (f - u * f.dot(u)).normalized()
    R = (rig.matrix_world @ pb.matrix @ b.matrix_local.inverted()).to_3x3()
    return (R @ f).normalized(), (R @ u).normalized()
acts = sorted(a.name for a in bpy.data.actions if a.name.startswith("EMO_"))
for an in acts:
    rig.animation_data.action = bpy.data.actions[an]; sc.frame_set(1); bpy.context.view_layer.update()
    h = head_point(); fd, ud = face_dir()
    shoot(f"{out}/{an}_body.png", (0.55, -2.15, 1.45), (0.05, 0.05, 1.22), lens=50)          # waist-up, from his front-left
    shoot(f"{out}/{an}_face.png", h + fd * 1.5 - ud * 0.08, h, ortho=0.30, res=(600, 600))      # in front of the face, slightly low
rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
hp = rig.pose.bones["head"]
keys = [k for k in ("brow_up_L", "brow_up_R", "brow_down_L", "brow_down_R", "brow_inner_up", "brow_squeeze")]
for k in ["none"] + keys:
    for n in keys: hp[n] = 0.0
    if k != "none": hp[k] = 1.0
    sc.frame_set(1); bpy.context.view_layer.update(); h = head_point()
    shoot(f"{out}/BROW_{k}.png", h + Vector((0.0, -1.5, -0.12)), h + Vector((0, 0, 0.02)), ortho=0.22, res=(500, 500))
print("RENDERED", len(acts), "emotions")
