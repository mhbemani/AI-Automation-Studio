# blender -b -P mascot.py -- mp4|alpha [last_frame]
import bpy, math, sys, os
args = sys.argv[sys.argv.index("--") + 1:]
mode = args[0] if args else "mp4"
FPS, N = 30, 150
out = os.path.dirname(os.path.abspath(__file__)) + "/out"
os.makedirs(out, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def mat(name, rgb, rough=0.4, emit=0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*rgb, 1); b.inputs["Emission Strength"].default_value = emit
    return m

def prim(op, name, m, parent=None, **kw):
    op(**kw); o = bpy.context.object; o.name = name; o.data.materials.append(m)
    if op is not bpy.ops.mesh.primitive_plane_add: bpy.ops.object.shade_smooth()
    if parent: o.parent = parent
    return o

blue, white, dark, cyan, orange = (mat("blue", (.1, .35, .9)), mat("white", (.9, .9, .95), .3),
    mat("dark", (.03, .03, .05), .2), mat("cyan", (.2, .9, 1), .2, 1.5), mat("orange", (1, .5, .1)))
floor = prim(bpy.ops.mesh.primitive_plane_add, "floor", mat("floor", (.8, .8, .85), .8), size=14)

root = bpy.data.objects.new("root", None); sc.collection.objects.link(root)
body = prim(bpy.ops.mesh.primitive_uv_sphere_add, "body", blue, root, radius=1, location=(0, 0, 1.2)); body.scale = (.8, .65, 1.05)
belly = prim(bpy.ops.mesh.primitive_uv_sphere_add, "belly", white, root, radius=.6, location=(0, -.5, 1.1)); belly.scale = (.9, .35, .9)
headp = bpy.data.objects.new("headpivot", None); sc.collection.objects.link(headp); headp.parent = root; headp.location = (0, 0, 2.3)
head = prim(bpy.ops.mesh.primitive_uv_sphere_add, "head", white, headp, radius=.7, location=(0, 0, .55)); head.scale = (1.1, .9, .85)
for s in (-1, 1):
    prim(bpy.ops.mesh.primitive_uv_sphere_add, "eye", cyan, headp, radius=.16, location=(s * .38, -.72, .62))
    prim(bpy.ops.mesh.primitive_uv_sphere_add, "ear", orange, headp, radius=.17, location=(s * .78, 0, .55))
prim(bpy.ops.mesh.primitive_cylinder_add, "antenna", dark, headp, radius=.03, depth=.4, location=(0, 0, 1.3))
prim(bpy.ops.mesh.primitive_uv_sphere_add, "tip", orange, headp, radius=.09, location=(0, 0, 1.55))
armL = bpy.data.objects.new("armL", None); armR = bpy.data.objects.new("armR", None)
for a, s in ((armL, -1), (armR, 1)):
    sc.collection.objects.link(a); a.parent = root; a.location = (s * .85, 0, 1.9)
    arm = prim(bpy.ops.mesh.primitive_cylinder_add,
               "arm", blue, a, radius=.14, depth=.9, location=(s * .15, 0, -.45))
    prim(bpy.ops.mesh.primitive_uv_sphere_add, "hand", orange, a, radius=.18, location=(s * .15, 0, -.95))
    a.rotation_euler = (0, math.radians(s * 20), 0)

# lights + camera
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(50), 0, math.radians(30))); bpy.context.object.data.energy = 2.2
bpy.ops.object.light_add(type="AREA", location=(-4, -5, 4)); l = bpy.context.object; l.data.energy = 250; l.data.size = 4
l.rotation_euler = (math.radians(60), 0, math.radians(-35))
bpy.ops.object.camera_add(location=(0, -15, 2.4), rotation=(math.radians(90), 0, 0)); sc.camera = bpy.context.object
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (.6, .75, 1, 1)

# animation: bounce, head turn, right-arm wave
sc.frame_start, sc.frame_end = 1, N
def key(o, prop, idx, f, v):
    setattr(o, prop, [v if i == idx else getattr(o, prop)[i] for i in range(3)]); o.keyframe_insert(prop, index=idx, frame=f)
for f in range(1, N + 1, 3):
    t = (f - 1) / FPS
    key(root, "location", 2, f, abs(math.sin(t * math.pi * 1.5)) * .6)
    key(headp, "rotation_euler", 2, f, math.sin(t * 2) * .6)
    key(armR, "rotation_euler", 1, f, math.radians(-100 - 20 * math.sin(t * 12)) if 1 < t < 4 else math.radians(20))
    key(armR, "rotation_euler", 0, f, 0)
    key(armL, "rotation_euler", 1, f, math.radians(-20 - 8 * math.sin(t * 3)))
for o in bpy.data.objects:  # smooth interpolation
    if o.animation_data:
        for fc in o.animation_data.action.fcurves:
            for k in fc.keyframe_points: k.interpolation = "BEZIER"

# render
sc.view_settings.view_transform = "Standard"
sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.eevee.taa_render_samples = 32
sc.render.resolution_x, sc.render.resolution_y, sc.render.fps = 1920, 1080, FPS
if len(args) > 1: sc.frame_end = int(args[1])
if mode == "alpha":
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_mode = "RGBA"
    sc.render.filepath = out + "/alpha/f_"
else:
    sc.render.image_settings.file_format = "FFMPEG"
    sc.render.ffmpeg.format = "MPEG4"; sc.render.ffmpeg.codec = "H264"; sc.render.ffmpeg.constant_rate_factor = "HIGH"
    sc.render.filepath = out + "/mascot.mp4"
bpy.ops.render.render(animation=True)
