"""Orthographic workbench stills of the reference/rigged character, with optional bone sticks and a 10 cm grid.
Run: Blender -b --factory-startup <file.blend> --python scripts/views.py -- <out_prefix> [object_name]
Views: front (looking +Y), side (looking -X), back, 3/4. 1000 px = 2.2 m, so 2.2 mm per px; image centre z = 0.97."""
import bpy, sys, math
from mathutils import Vector
args = sys.argv[sys.argv.index("--")+1:]
prefix = args[0]; objname = args[1] if len(args) > 1 and not args[1].startswith("--") else "Lowpoly Male Standing"
sc = bpy.context.scene
for o in sc.objects:  # show only the target (and its armature)
    o.hide_render = not (o.name == objname or (o.type == 'ARMATURE' and any(m.type=='ARMATURE' and m.object==o for m in bpy.data.objects[objname].modifiers)))
r = sc.render; r.engine = 'BLENDER_WORKBENCH'; r.resolution_x = r.resolution_y = 1000; r.film_transparent = False
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.75, 0.72, 0.68)
sh.show_cavity = True; sh.show_object_outline = True; sh.show_xray = '--xray' in args; sh.xray_alpha = 0.5
sc.world = sc.world or bpy.data.worlds.new("W")
# grid lines every 10 cm (thin boxes in the XZ and YZ planes, behind the character)
mat = bpy.data.materials.new("grid"); mat.diffuse_color = (0.2, 0.4, 0.9, 1)
def stick(a, b, rad, col):
    a, b = Vector(a), Vector(b); d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=rad, depth=d.length, location=(a+b)/2)
    c = bpy.context.object; c.rotation_mode='QUATERNION'; c.rotation_quaternion = d.to_track_quat('Z','Y')
    m = bpy.data.materials.new("m"); m.diffuse_color = col; c.data.materials.append(m)
    sh.color_type = 'MATERIAL'; return c
arm = next((o for o in sc.objects if o.type=='ARMATURE'), None)
if arm and '--bones' in args:
    sh.show_xray = True; sh.xray_alpha = 0.35
    for pb in arm.pose.bones:
        h = arm.matrix_world @ pb.head; t = arm.matrix_world @ pb.tail
        col = (1,0.15,0.1,1) if pb.name.endswith('.L') else (0.1,0.8,0.2,1) if pb.name.endswith('.R') else (1,0.85,0,1)
        stick(h, t, 0.008, col)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.016, location=h, segments=8, ring_count=6)
        s = bpy.context.object; s.data.materials.append(bpy.data.materials.get("m") or mat)
    sh.color_type = 'MATERIAL'
    tgt = bpy.data.objects[objname]
    for m in tgt.data.materials:
        if m: m.diffuse_color = (0.75, 0.72, 0.68, 1)
if '--grid' in args:
    for i in range(-10, 11):
        stick((i/10, 0.6, -0.15), (i/10, 0.6, 2.1), 0.0015, (0.3,0.4,0.9,1))
    for k in range(0, 21):
        stick((-1.1, 0.6, k/10), (1.1, 0.6, k/10), 0.0015 if k%5 else 0.003, (0.3,0.4,0.9,1))
    sh.color_type = 'MATERIAL'
    tgt = bpy.data.objects[objname]
    if not tgt.data.materials or tgt.data.materials[0] is None: pass
    for m in tgt.data.materials:
        if m: m.diffuse_color = (0.75, 0.72, 0.68, 1)
cam_d = bpy.data.cameras.new("C"); cam_d.type = 'ORTHO'; cam_d.ortho_scale = 1.3 if '--legs' in args else 2.2
CZ = 0.55 if '--legs' in args else 0.97
cam = bpy.data.objects.new("C", cam_d); sc.collection.objects.link(cam); sc.camera = cam
views = {"front": (0, -5, 0), "side": (5, 0, 0), "back": (0, 5, 0), "q34": (3.5, -3.5, 0), "inner": (-5, 0, 0), "top": (0, -0.01, 5), "below": (0, -0.01, -5)}
FOCUS = next((a.split("=")[1] for a in args if a.startswith("--focus=")), None)  # e.g. --focus=shin.L : close-up on that bone's head
for name, (x, y, _z) in views.items():
    if '--only' in args and name not in args: continue
    cam.location = (x, y, CZ)
    if FOCUS:
        arm_o = next(o for o in sc.objects if o.type == 'ARMATURE'); bpy.context.view_layer.update()
        f = arm_o.matrix_world @ arm_o.pose.bones[FOCUS].head; cam_d.ortho_scale = 0.5
        cam.location = (f.x + x / 5 * 2, f.y + y / 5 * 2, f.z + (_z / 5 * 2 if name in ('top', 'below') else 0))
    cam.rotation_euler = (math.pi/2, 0, math.atan2(x, -y))
    if name in ('top', 'below'): cam.rotation_euler = (0 if name == 'top' else math.pi, 0, 0)
    r.filepath = f"{prefix}_{name}.png"; bpy.ops.render.render(write_still=True)
