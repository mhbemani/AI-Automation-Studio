"""Close-up ortho views of the hands at REST, coloured by dominant bone (hand.R red, hand.L blue, forearm.R pink,
forearm.L light blue, rest grey). Not saved. Run: Blender -b --factory-startup <blend> --python scripts/hand_views.py -- <prefix> [--posed]"""
import bpy, sys, math
from mathutils import Vector
args = sys.argv[sys.argv.index("--")+1:]; prefix = args[0]
sc = bpy.context.scene; b = bpy.data.objects["HUM_Body"]; rig = bpy.data.objects["RIG_Human"]
for ob in (b, rig):  # files saved in Edit Mode
    bpy.context.view_layer.objects.active = ob
    if ob.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
if '--posed' not in args:
    for pb in rig.pose.bones: pb.matrix_basis.identity()
for o in sc.objects: o.hide_render = o.name not in ("HUM_Body",)
COL = {"hand.R": (1, .15, .1), "hand.L": (.1, .3, 1), "forearm.R": (1, .6, .6), "forearm.L": (.6, .75, 1)}
names = {g.index: g.name for g in b.vertex_groups}
ca = b.data.color_attributes.new("dom", 'FLOAT_COLOR', 'POINT')
for v in b.data.vertices:
    g = max(v.groups, key=lambda x: x.weight, default=None)
    c = COL.get(names[g.group], (.7, .7, .7)) if g else (0, 0, 0)
    ca.data[v.index].color = (*c, 1)
r = sc.render; r.engine = 'BLENDER_WORKBENCH'; r.resolution_x = r.resolution_y = 800
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'VERTEX'; sh.show_object_outline = True
bpy.context.view_layer.update()
B = rig.data.bones
mid = (B["hand.L"].head_local + B["hand.R"].head_local + B["hand.L"].tail_local + B["hand.R"].tail_local) / 4
cd = bpy.data.cameras.new("C"); cd.type = 'ORTHO'; cd.ortho_scale = 0.42
cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
V = {"front": Vector((0, -1, 0)), "top": Vector((0, 0, 1)), "bottom": Vector((0, 0, -1)), "right": Vector((-1, 0, 0)), "left": Vector((1, 0, 0)), "back": Vector((0, 1, 0))}
for n, d in V.items():
    cam.location = mid + d * 2
    cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = (-d).to_track_quat('-Z', 'Y' if abs(d.z) < .9 else 'Y')
    r.filepath = f"{prefix}_{n}.png"; bpy.ops.render.render(write_still=True)
