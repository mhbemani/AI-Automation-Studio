# Import the downloaded packs into a hidden library collection (00_LIB) at real-world scale,
# set the golden-hour HDRI, and create the scene collections. Re-runnable: rebuilds only 00_LIB.
# Scene objects are linked duplicates of the LIB objects (they share mesh data -> light on RAM).
import bpy, os
from mathutils import Matrix, Vector

HERE = os.path.dirname(bpy.data.filepath)          # lab/scene-lowpoly-car/
A = os.path.join(HERE, "assets")
ROADS = A + "/kenney_city-kit-roads/Models/GLB format/"
COMM = A + "/kenney_city-kit-commercial_2.1/Models/GLB format/"
CARS = A + "/kenney_car-kit/Models/GLB format/"
HUMAN = A + "/quaternius_animated_human/Animated Human by @Quaternius/FBX/Animated Human.fbx"
CITY_S, CAR_S = 8.0, 1.8   # kit units -> metres: road tile 8 m, sedan 4.6 m long

LIB = {  # lib name: (file, scale)
    **{f"LIB_{n}": (ROADS + n + ".glb", CITY_S) for n in
       ["road-straight", "road-bend", "road-curve", "road-crossroad", "road-intersection", "tile-low",
        "light-curved", "light-square", "traffic-light"]},
    **{f"LIB_{n}": (COMM + n + ".glb", CITY_S) for n in
       ["building-a", "building-b", "building-c", "building-d", "building-e", "building-f", "building-g",
        "building-h", "building-skyscraper-a", "building-skyscraper-b", "low-detail-building-a",
        "low-detail-building-b", "low-detail-building-c", "low-detail-building-d", "detail-awning"]},
    **{f"LIB_{n}": (CARS + n + ".glb", CAR_S) for n in ["sedan", "taxi", "suv", "van"]},
}

def coll(name, parent=None, hide=False):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    p = parent or bpy.context.scene.collection
    if c.name not in p.children: p.children.link(c)
    return c

for n in ["01_CITY", "02_CAR", "03_CHARACTERS", "04_CAMERAS", "05_LIGHTS", "06_PROPS"]: coll(n)
lib = coll("00_LIB")
for o in list(lib.all_objects): bpy.data.objects.remove(o)

def grab(fn, path):
    before = set(bpy.data.objects); fn(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        for c in list(o.users_collection): c.objects.unlink(o)
        lib.objects.link(o)
    return new

for name, (path, s) in LIB.items():
    new = grab(bpy.ops.import_scene.gltf, path)
    S = Matrix.Scale(s, 4)
    for o in new:   # bake scale + import transform into the mesh, keep parts (car wheels) separate
        o.data.transform(S @ o.matrix_world); o.matrix_world = Matrix()
    root = next(o for o in new if o.name.split(".")[0] in ("body", name[4:]))
    root.name = name
    for o in new:
        if o is not root: o.name = f"{name}_{o.name.split('.')[0]}"; o.parent = root
    if len(new) > 1:   # car: wheel pivots at wheel centres so they can spin later
        for o in new:
            if o is root: continue
            vs = [v.co for v in o.data.vertices]   # bound_box is stale until a depsgraph update
            c = Vector([(min(v[i] for v in vs) + max(v[i] for v in vs)) / 2 for i in range(3)])
            o.data.transform(Matrix.Translation(-c)); o.matrix_parent_inverse = Matrix(); o.location = c

# Human: FBX is Y-up with armature rot 90deg X, scale 0.692, 5.26 units tall -> ~1.8 m, applied.
# The FBX's active action poses it; clear it (actions kept with fake user: Walk/Idle/Run for later).
for ac in list(bpy.data.actions):
    if ac.name.startswith("Human Armature|"): bpy.data.actions.remove(ac)
lc = bpy.context.view_layer.layer_collection.children["00_LIB"]
lc.exclude = False; bpy.context.view_layer.update()
new = grab(bpy.ops.import_scene.fbx, HUMAN)
arm = next(o for o in new if o.type == "ARMATURE"); mesh = next(o for o in new if o.type == "MESH")
arm.name, mesh.name = "LIB_Human", "LIB_Human_Mesh"
arm.animation_data.action = None
for ac in bpy.data.actions: ac.use_fake_user = True
arm.scale = (0.692 * 1.75 / 5.26,) * 3
bpy.ops.object.select_all(action="DESELECT")
for o in new: o.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
for o in new: o.select_set(False)
lc.exclude = True   # library stays out of the viewport/render
# The FBX material has no texture; the pack's 32x32 palette textures live in Blend/Textures/.
HUMAN_SKIN = "ClothedLightSkin.png"   # also: ClothedLightSkin1/2, ClothedDarkSkin/1/2
mt = mesh.material_slots[0].material; mt.name = "MAT_Human"; nt = mt.node_tree
tex = nt.nodes.get("Skin") or nt.nodes.new("ShaderNodeTexImage"); tex.name = "Skin"; tex.interpolation = "Closest"
tex.image = bpy.data.images.load(os.path.dirname(HUMAN).replace("/FBX", "/Blend/Textures/") + HUMAN_SKIN, check_existing=True)
nt.links.new(tex.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])

# Remove the default startup objects (only if still untouched defaults).
for n in ["Cube", "Light", "Camera"]:
    o = bpy.data.objects.get(n)
    if o and not o.get("user_locked"): bpy.data.objects.remove(o)

# Golden-hour world.
w = bpy.context.scene.world or bpy.data.worlds.new("World"); bpy.context.scene.world = w
w.use_nodes = True; nt = w.node_tree
env = nt.nodes.get("HDRI") or nt.nodes.new("ShaderNodeTexEnvironment"); env.name = "HDRI"
env.image = bpy.data.images.load(os.path.join(A, "venice_sunset_1k.hdr"), check_existing=True)
nt.links.new(env.outputs["Color"], nt.nodes["Background"].inputs["Color"])

result = {o.name: [round(d, 2) for d in o.dimensions] for o in lib.objects if o.parent is None}

bpy.data.orphans_purge(do_recursive=True)
