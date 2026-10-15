"""helper: place the work camera. usage via bridge: set CAMSPEC=(loc, target, lens) then exec this."""
import bpy, mathutils
def cam(loc, target, lens=50, name="ANIM_CAM"):
    c = bpy.data.objects.get(name)
    if not c:
        c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); bpy.context.scene.collection.objects.link(c)
    c.location = loc
    d = mathutils.Vector(target) - mathutils.Vector(loc)
    c.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    c.data.lens = lens; c.data.clip_start = 0.01
    bpy.context.scene.camera = c
    return c

def iso(*names):
    """show only the named collections/objects' collections in the viewport/render."""
    def walk(lc):
        for c in lc.children:
            c.exclude = False
            walk(c)
    vl = bpy.context.view_layer
    walk(vl.layer_collection)
    for o in bpy.data.objects:
        if o.type in ('MESH','ARMATURE','EMPTY','CURVE','FONT'):
            o.hide_viewport = o.hide_render = not any(o.name == n or o.name.startswith(n) for n in names)

def bonedbg(arm, name="DBG_bones", radius=0.006, only=None, pose=False):
    """draw bones as thin tubes (the fast snapshot does not draw armatures). Debug only."""
    old = bpy.data.objects.get(name)
    if old: bpy.data.objects.remove(old)
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = radius; cu.bevel_resolution = 1
    mat = bpy.data.materials.get("DBG_red") or bpy.data.materials.new("DBG_red")
    mat.diffuse_color = (1, .1, .05, 1); cu.materials.append(mat)
    for b in arm.pose.bones if pose else arm.data.bones:
        if only and not only(b.name): continue
        h, t = ((arm.matrix_world @ b.head), (arm.matrix_world @ b.tail)) if pose else ((arm.matrix_world @ b.head_local), (arm.matrix_world @ b.tail_local))
        sp = cu.splines.new('POLY'); sp.points.add(1)
        sp.points[0].co = (*h, 1); sp.points[1].co = (*t, 1)
    o = bpy.data.objects.new(name, cu); bpy.context.scene.collection.objects.link(o)
    o.show_in_front = True; o["anim_debug"] = 1
    return o

def studio():
    """neutral preview lighting (collection ANIM_STUDIO, owned by me)."""
    col = bpy.data.collections.get("ANIM_STUDIO") or bpy.data.collections.new("ANIM_STUDIO")
    if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
    def light(name, kind, loc, rot, energy, size=1.0, color=(1, 1, 1)):
        o = bpy.data.objects.get(name)
        if not o:
            o = bpy.data.objects.new(name, bpy.data.lights.new(name, kind)); col.objects.link(o)
        o.location = loc; o.rotation_euler = rot; o.data.energy = energy; o.data.color = color
        if kind == 'AREA': o.data.size = size
        o["anim_debug"] = 1
    light("ANIM_key", 'SUN', (0, 0, 5), (0.9, 0.2, -0.6), 3.2, color=(1, .95, .88))
    light("ANIM_fill", 'AREA', (-3, -3, 2.5), (1.2, 0, -0.6), 150, 3, color=(.85, .92, 1))
    light("ANIM_rim", 'AREA', (2.5, 3, 3), (-1.1, 0, 2.6), 120, 2)
    w = bpy.context.scene.world or bpy.data.worlds.new("World"); bpy.context.scene.world = w
    w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.09, 0.1, 0.11, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    r = bpy.context.scene.render; r.engine = 'BLENDER_EEVEE_NEXT'; bpy.context.scene.eevee.taa_render_samples = 24
