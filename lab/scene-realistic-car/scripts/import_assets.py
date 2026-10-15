# Import the downloaded assets into a hidden library collection (00_LIB), create the scene collections,
# set the HDRI world and the colour management. Re-runnable: rebuilds only 00_LIB (and the world nodes).
# Scene objects are linked duplicates/instances of LIB objects (shared mesh data -> light on RAM).
import bpy, os, math
from mathutils import Matrix, Vector

A = bpy.path.abspath("//assets/")
PH = A + "polyhaven/models/"
PROPS = {  # LIB name: (glTF file, decimate ratio or None). Diet: every prop ~1K tris (they are never seen close up)
    "LIB_StreetLamp": (PH + "street_lamp_02/street_lamp_02_1k.gltf", 0.05),
    "LIB_Hydrant": (PH + "fire_hydrant/fire_hydrant_1k.gltf", 0.012),   # 86k -> ~1k tris
    "LIB_TrashCan": (PH + "metal_trash_can/metal_trash_can_1k.gltf", 0.3),
    "LIB_Bench": (PH + "modular_street_seating/modular_street_seating_1k.gltf", 0.12),
    "LIB_UtilityBox": (PH + "utility_box_01/utility_box_01_1k.gltf", 0.25),
    "LIB_Manhole": (PH + "water_manhole_cover/water_manhole_cover_1k.gltf", 0.025),   # a flat disc
}
CROP_X = {"LIB_Bench": (-0.1, 1.75), "LIB_TrashCan": (0.0, 2.0)}   # x-range after centring
HDRI = A + "polyhaven/hdri/sunset_jhbcentral_2k.hdr"

def coll(name, parent=None):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    p = parent or bpy.context.scene.collection
    if c.name not in p.children: p.children.link(c)
    return c

for n in ["01_CITY", "02_CAR", "03_CHARACTERS", "04_CAMERAS", "05_LIGHTS", "06_PROPS"]: coll(n)
lib = coll("00_LIB")
for o in list(lib.all_objects):
    if not o.get("user_locked") and not o.name.startswith(("LIB_Hero_", "LIB_JDM")): bpy.data.objects.remove(o)
lc = bpy.context.view_layer.layer_collection.children["00_LIB"]
lc.exclude = False

def to_lib(objs):
    for o in objs:
        for c in list(o.users_collection): c.objects.unlink(o)
        lib.objects.link(o); o["cs_owner"] = "import"

# --- Poly Haven props: glTF is metres, Y-up handled by the importer. One root object per prop.
for name, (path, dec) in PROPS.items():
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    to_lib(new)
    meshes = [o for o in new if o.type == "MESH"]
    for o in meshes:   # bake transforms so instances are simple
        o.data.transform(o.matrix_world); o.parent = None; o.matrix_world = Matrix()
    for o in new:
        if o.type != "MESH": bpy.data.objects.remove(o)
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1: bpy.ops.object.join()
    root = bpy.context.view_layer.objects.active; root.name = root.data.name = name
    def recentre(me):   # origin at the bottom centre of the geometry
        vs = [v.co for v in me.vertices]
        lo = [min(v[i] for v in vs) for i in range(3)]; hi = [max(v[i] for v in vs) for i in range(3)]
        me.transform(Matrix.Translation((-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2])))
    recentre(root.data)
    if name in CROP_X:   # the file is a kit of loose pieces side by side; keep one assembled item
        import bmesh
        bm = bmesh.new(); bm.from_mesh(root.data); lo_, hi_ = CROP_X[name]
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not lo_ <= v.co.x <= hi_], context="VERTS")
        bm.to_mesh(root.data); bm.free(); recentre(root.data)
    if dec:
        m = root.modifiers.new("Decimate", "DECIMATE"); m.ratio = dec
        bpy.ops.object.modifier_apply(modifier=m.name)
    root.select_set(False)

# --- Human, polygon diet: BlenderKit "Lowpoly Male Standing" + our FK rig with Rigify control names, face parts and
# emotion shape keys (scripts/human_lib.py). Replaces Oscar (66K tris); the old file stays in assets/ for reference.
exec(open(bpy.path.abspath("//scripts/human_lib.py")).read())

# --- Claude's car, polygon diet (2026-10-09): BlenderKit "Low poly plymouth car" (Rohit Gupta, Royalty Free). Appended
# ONCE as LIB_Hero_* (delete them to re-import). Scaled HS, mirror + "Smooth by Angle" applied; split into the body and four
# wheels (pivot at the wheel centre, axle = X); the wheels and the dense front grille are decimated (the asset is 31K tris
# mirrored, listed as 7.5K faces). Window materials become glass in build_car; the paint is recoloured there.
HERO, HS = A + "blenderkit/plymouth_lowpoly.blend", 1.06
import bmesh
for o in [o for o in bpy.data.objects if o.name.startswith("LIB_Vulcar_")]: bpy.data.objects.remove(o)   # the old heavy car
def apply_all(o):
    with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
        for m in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=m.name)
def split_mesh(src_me, face_sets, names):
    """New meshes, one per face-index set (materials kept)."""
    out = []
    for idx, nm in zip(face_sets, names):
        me = src_me.copy(); me.name = nm; bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
        keep = set(idx); bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context="FACES")
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")   # no loose verts
        bm.to_mesh(me); bm.free(); out.append(me)
    return out
def decimate(o, ratio, vgroup=None):
    d = o.modifiers.new("Dec", "DECIMATE"); d.ratio = ratio
    if vgroup: d.vertex_group = vgroup
    with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
        bpy.ops.object.modifier_apply(modifier="Dec")
if not any(o.name.startswith("LIB_Hero_") for o in bpy.data.objects):
    with bpy.data.libraries.load(HERO, link=False) as (src, dst):
        dst.objects = list(src.objects)
    src_o = next(o for o in dst.objects if o and o.type == "MESH"); to_lib([src_o])
    ROLE = {".041": "paint", ".027": "glass", ".026": "glass", ".031": "glass", ".067": "glass", ".068": "glass", ".069": "glass",
            ".042": "glass", ".059": "roof"}   # source material names (.067-.069 / .042 = side and vent windows)
    for m in src_o.data.materials:
        if m:
            for suf, role in ROLE.items():
                if m.name.endswith(suf) and m.name.count(".") == 1: m["hero_role"] = role
    src_o.data.transform(Matrix.Scale(HS, 4) @ src_o.matrix_world); src_o.matrix_world = Matrix()
    src_o.delta_location = src_o.delta_rotation_euler = (0, 0, 0); src_o.delta_scale = (1, 1, 1)
    apply_all(src_o)
    me = src_o.data
    AX = {"front": -1.56 * HS, "back": 1.205 * HS}; AZ, WR = 0.31 * HS, 0.335 * HS   # axle y/z and tyre radius (measured)
    def base_col(m):
        b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if m and m.use_nodes else None
        return tuple(b.inputs["Base Color"].default_value[:3]) if b else (0, 0, 0)
    paint = {i for i, m in enumerate(me.materials) if base_col(m)[2] > 0.3 and base_col(m)[0] < 0.2}   # the purple paint
    wheel_sets = {}; body = []
    for p_ in me.polygons:   # per face: inside a wheel's circle, on the outer side, not paint -> that wheel
        c = p_.center; w = None
        if abs(c.x) > 0.55 * HS and p_.material_index not in paint:
            for ax, y in AX.items():
                if (Vector((c.y - y, c.z - AZ))).length < WR: w = f"{ax}-{'left' if c.x > 0 else 'right'}"
        (wheel_sets.setdefault(w, []) if w else body).append(p_.index)
    names = ["LIB_Hero_Body"] + [f"LIB_Hero_Wheel_{k}" for k in sorted(wheel_sets)]
    meshes = split_mesh(me, [body] + [wheel_sets[k] for k in sorted(wheel_sets)], names)
    for nm, m2 in zip(names, meshes):
        o = bpy.data.objects.new(nm, m2); to_lib([o])
        if "Wheel" in nm:
            vs = [v.co for v in m2.vertices]; c = Vector([(min(v[k] for v in vs) + max(v[k] for v in vs)) / 2 for k in range(3)])
            m2.transform(Matrix.Translation(-c)); o.location = c; decimate(o, 0.12)
        else:   # body: the dense front grille (most faces of any dark material at the nose) is split off and decimated hard,
                # the rest lightly; then joined back into one body mesh
            gi = max(range(len(m2.materials)), key=lambda i: sum(1 for p_ in m2.polygons if p_.material_index == i and p_.center.y < -2.2 * HS))
            gset = [p_.index for p_ in m2.polygons if p_.material_index == gi]
            rest = [p_.index for p_ in m2.polygons if p_.material_index != gi]
            gm, rm = split_mesh(m2, [gset, rest], ["LIB_Hero_Grille", "LIB_Hero_BodyRest"])
            og = bpy.data.objects.new("LIB_Hero_Grille", gm); to_lib([og]); decimate(og, 0.12)
            o.data = rm; bpy.data.meshes.remove(m2)
            with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o, og], selected_editable_objects=[o, og]):
                bpy.ops.object.join()
            o.data.name = "LIB_Hero_Body"
            d = o.modifiers.new("Planar", "DECIMATE"); d.decimate_type = "DISSOLVE"; d.angle_limit = math.radians(11)   # merges flat faces only
            with bpy.context.temp_override(object=o, active_object=o, selected_objects=[o]):
                bpy.ops.object.modifier_apply(modifier="Planar")
    bpy.data.objects.remove(src_o)
    for o in [o for o in lib.objects if o.name.startswith("LIB_Hero_")]:
        o.data.use_fake_user = False
        for sl in o.material_slots:
            if sl.material: sl.material.use_fake_user = False

# --- Parked cars, polygon diet: BlenderKit "Low Poly JDM Sports Car (Skyline)" (Sachin H, Royalty Free), joined ONCE into
# one mesh LIB_JDM (linked duplicates in build_car). Smoother look WITHOUT new geometry: smooth shading, sharp edges only above
# 60 deg (35 deg looked MORE faceted than the asset as shipped), weighted normals (face area, keep sharp). Vertex/face counts are logged before and after (must match).
JDM = A + "blenderkit/jdm_skyline_lowpoly.blend"
if not bpy.data.objects.get("LIB_JDM"):
    with bpy.data.libraries.load(JDM, link=False) as (src, dst):
        dst.objects = list(src.objects)
    parts = [o for o in dst.objects if o is not None]
    for o in parts: bpy.context.scene.collection.objects.link(o)
    bpy.context.view_layer.update()
    meshes = [o for o in parts if o.type == "MESH"]
    for o in meshes:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
        if o.data.users > 1: o.data = o.data.copy()
        apply_all(o)                                                   # their weighted-normal / smooth modifiers
        o.data.transform(o.matrix_world); o.delta_location = o.delta_rotation_euler = (0, 0, 0); o.delta_scale = (1, 1, 1)
        o.matrix_world = Matrix()
    for o in parts:
        if o.type != "MESH": bpy.data.objects.remove(o)
    with bpy.context.temp_override(object=meshes[0], active_object=meshes[0], selected_objects=meshes, selected_editable_objects=meshes):
        bpy.ops.object.join()
    o = meshes[0]; o.name = o.data.name = "LIB_JDM"
    o.data.transform(o.matrix_world); o.delta_location = o.delta_rotation_euler = (0, 0, 0); o.delta_scale = (1, 1, 1)
    o.matrix_world = Matrix()
    for c in list(o.users_collection): c.objects.unlink(o)
    to_lib([o])
    me = o.data; before = (len(me.vertices), len(me.polygons))
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons)); me.set_sharp_from_angle(angle=math.radians(60))
    wn = o.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL"); wn.keep_sharp = True; wn.mode = "FACE_AREA"
    apply_all(o)
    after = (len(me.vertices), len(me.polygons))
    o["counts_before"], o["counts_after"] = before, after
    assert before == after, (before, after)
    o.data.use_fake_user = False
    for sl in o.material_slots:
        if sl.material: sl.material.use_fake_user = False
lc.exclude = True

for n in ["Cube", "Light", "Camera"]:
    o = bpy.data.objects.get(n)
    if o and not o.get("user_locked"): bpy.data.objects.remove(o)

# --- World: golden-hour HDRI for light + reflections (rotation tuned in build_lighting).
sc = bpy.context.scene
w = sc.world or bpy.data.worlds.new("World"); sc.world = w; w.use_nodes = True; nt = w.node_tree
env = nt.nodes.get("HDRI") or nt.nodes.new("ShaderNodeTexEnvironment"); env.name = "HDRI"
env.image = bpy.data.images.load(HDRI, check_existing=True)
nt.links.new(env.outputs["Color"], nt.nodes["Background"].inputs["Color"])
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
sc.unit_settings.system = "METRIC"; sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.render.fps = 24

def tris(o): return sum(len(p.vertices) - 2 for p in o.data.polygons)
result = {"human": human_report, **{o.name: ([round(d, 2) for d in o.dimensions], tris(o) if o.type == "MESH" else o.type)
          for o in lib.objects}}
bpy.data.orphans_purge(do_recursive=True)
