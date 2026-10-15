"""Build lab/asset-lineup/lineup.blend from scratch (idempotent; overwrites the output file).

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python lab/asset-lineup/scripts/build_lineup.py
  add  -- --refresh-snapshot   to re-copy the selection lab's saved file into snapshots/ first.

Read-only sources (appended, never saved): realistic scene, low-poly scene, snapshot of the selection-lab human.
Assembly only: nothing is redesigned. Deviations from the sources are listed in lab/results/asset-lineup.md."""
import bpy, sys, math, json, shutil, importlib
from pathlib import Path
from mathutils import Vector, Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lineup_lib as L
importlib.reload(L)

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if "--refresh-snapshot" in ARGS or not L.SNAP.exists():
    L.SNAP.parent.mkdir(exist_ok=True)
    shutil.copy2(L.SRC_HUMAN, L.SNAP)
    print("snapshot refreshed from", L.SRC_HUMAN)

# ------------------------------------------------------------------ scene
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.name = "Lineup"
sc.unit_settings.system = "METRIC"
sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.render.fps = 24
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Medium High Contrast"
sc.render.filter_size = 1.5
ev = sc.eevee                     # settings of the realistic scene
ev.use_raytracing = True; ev.ray_tracing_method = "SCREEN"
ev.ray_tracing_options.resolution_scale = "2"; ev.ray_tracing_options.screen_trace_quality = 0.25
ev.ray_tracing_options.screen_trace_thickness = 0.2; ev.ray_tracing_options.trace_max_roughness = 0.5
ev.use_fast_gi = True; ev.fast_gi_method = "GLOBAL_ILLUMINATION"; ev.fast_gi_resolution = "2"
ev.fast_gi_ray_count = 2; ev.fast_gi_step_count = 8; ev.fast_gi_quality = 0.25
ev.shadow_pool_size = "256"; ev.gi_irradiance_pool_size = "16"; ev.gi_cubemap_resolution = "512"
ev.taa_render_samples = 32; ev.taa_samples = 16; ev.light_threshold = 0.005; ev.use_shadows = True
ev.shadow_resolution_scale = 0.5; ev.shadow_ray_count = 1; ev.shadow_step_count = 4; ev.use_gtao = False

root_coll = sc.collection
def mk_coll(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or root_coll).children.link(c)
    return c
C_ASSETS = mk_coll("LU_Assets")
C_STAGE = mk_coll("LU_Staging")
C_LAB = mk_coll("LU_Labels")
C_CAMS = mk_coll("LU_Cameras")
C_LS = mk_coll("LU_LIGHT_Studio")
C_LG = mk_coll("LU_LIGHT_Golden")
C_TMP = mk_coll("LU_TMP")

# ------------------------------------------------------------------ append sources
def load(src, tag, prefixes, exact=()):
    before = set(bpy.data.objects)
    with bpy.data.libraries.load(str(src), link=False) as (df, dt):
        names = [n for n in df.objects if n in exact or n.startswith(tuple(prefixes))]
        dt.objects = list(names)
    wanted = [o for o in dt.objects if o]
    extra = [o for o in bpy.data.objects if o not in before and o not in wanted]   # pulled in as parent / constraint target
    orig = {o: n for n, o in zip(names, dt.objects)}
    for o in wanted + extra:
        C_TMP.objects.link(o)
    for o in wanted:
        o.name = f"LU_{tag}_{orig[o]}"
    for o in wanted:                              # unique datablock names across the two scenes
        if o.data and not o.data.name.startswith(tag + "_"):
            o.data.name = f"{tag}_{o.data.name}"
        for s in getattr(o, "material_slots", []):
            if s.material and not s.material.name.startswith(tag + "_"):
                s.material.name = f"{tag}_{s.material.name}"
    return wanted, extra, orig

new_objs, new_extra, new_orig = load(L.SRC_NEW, "NEW", ("CAR_", "CHAR_Claude", "PROP_Phone", "PROP_UI_"), ("CITY_ParkedCar_00",))
old_objs, old_extra, old_orig = load(L.SRC_OLD, "OLD", ("CAR_", "CHAR_Claude", "PROP_Phone", "CHAR_Human_Street"))
ORIG = {**new_orig, **old_orig}
print("loaded", len(new_objs), "new,", len(old_objs), "old; extras", [o.name for o in new_extra + old_extra])

# Follow Path is not needed in the lineup
for o in new_objs + old_objs:
    for c in list(o.constraints):
        if c.type == "FOLLOW_PATH":
            o.constraints.remove(c)

# bake the old scene's keyed state at frame 200 (phone + bubble visible, Claude neutral); new scene has no animation
sc.frame_set(200)
bpy.context.view_layer.update()
sc.frame_set(200)
bpy.context.view_layer.update()

def by(objs, orig_name):
    return next(o for o in objs if ORIG[o] == orig_name)

ASSETS = []
def asset(key, tag, label, src, root, members, **kw):
    a = dict(key=key, tag=tag, label=label, src=src, root=root, objs=members, **kw)
    ASSETS.append(a)
    return a

# ---- NEW
n_car = by(new_objs, "CAR_Exterior"); n_claude = by(new_objs, "CHAR_Claude"); n_phone = by(new_objs, "PROP_Phone")
n_park = by(new_objs, "CITY_ParkedCar_00")
o_car = by(old_objs, "CAR_Exterior"); o_claude = by(old_objs, "CHAR_Claude"); o_phone = by(old_objs, "PROP_Phone")
o_human = by(old_objs, "CHAR_Human_Street")

# old Claude's arms Track-To the steering-wheel grips: give Claude its own copies of the grips (same relative position)
claude_o_set = set(subtree := L.subtree(o_claude, old_objs))
grip_copies = []
for ob in subtree:
    for c in ob.constraints:
        t = getattr(c, "target", None)
        if t is not None and t not in claude_o_set:
            g = t.copy(); g.name = f"LU_OLD_{ORIG[t][4:] if t in ORIG else t.name}_ClaudeCopy"
            g.parent = None; g.matrix_world = t.matrix_world.copy()
            C_TMP.objects.link(g)
            c.target = g
            grip_copies.append(g)
bpy.context.view_layer.update()

# detach Claude and the phones from their scene parents (car seat / human hand) keeping the world pose
for r in (n_claude, o_claude, n_phone, o_phone):
    L.detach(r)
for g in grip_copies:
    mw = g.matrix_world.copy(); g.parent = o_claude; g.matrix_parent_inverse = o_claude.matrix_world.inverted(); g.matrix_world = mw

# remove the helper objects that were pulled in (human hand armature in the NEW scene, drive path)
for o in list(new_extra) + list(old_extra):
    bpy.data.objects.remove(o)

members_of = {}
def members(root, pool):
    return L.subtree(root, pool)

pools_n = [o for o in new_objs if o.name in bpy.data.objects]
pools_o = [o for o in old_objs if o.name in bpy.data.objects]
# note: after the detach calls the subtree walk follows the new parent links
A = {}
A["NEW_Claude"] = asset("NEW_Claude", "NEW", "Claude", L.SRC_NEW, n_claude, members(n_claude, pools_n), coll="LU_NEW_Claude")
A["NEW_Car"] = asset("NEW_Car", "NEW", "Hero car", L.SRC_NEW, n_car, members(n_car, pools_n), coll="LU_NEW_Car")
A["NEW_Phone"] = asset("NEW_Phone", "NEW", "Phone", L.SRC_NEW, n_phone, members(n_phone, pools_n), coll="LU_NEW_Phone")
A["NEW_ParkedCar"] = asset("NEW_ParkedCar", "NEW", "Parked car", L.SRC_NEW, n_park, [n_park], coll="LU_NEW_ParkedCar")
A["OLD_Claude"] = asset("OLD_Claude", "OLD", "Claude", L.SRC_OLD, o_claude, members(o_claude, pools_o) , coll="LU_OLD_Claude")
A["OLD_Car"] = asset("OLD_Car", "OLD", "Car", L.SRC_OLD, o_car, members(o_car, pools_o), coll="LU_OLD_Car")
A["OLD_Phone"] = asset("OLD_Phone", "OLD", "Phone", L.SRC_OLD, o_phone, members(o_phone, pools_o), coll="LU_OLD_Phone")
A["OLD_Human"] = asset("OLD_Human", "OLD", "Human (low-poly)", L.SRC_OLD, o_human, members(o_human, pools_o), coll="LU_OLD_Human")
for k, a in A.items():                                   # the grip copies live with old Claude
    if k == "OLD_Claude":
        a["objs"] = a["objs"] + [g for g in grip_copies if g not in a["objs"]]
    a["orig_name"] = ORIG[a["root"]]
    print(k, len(a["objs"]), "objects")
leftover = [o for o in new_objs + old_objs if o.name in bpy.data.objects and not any(o in a["objs"] for a in ASSETS)]
print("not in any asset (dropped):", [o.name for o in leftover])
for o in leftover:
    bpy.data.objects.remove(o)

# unhook actions (values already evaluated at frame 200), put frame back
for a in ASSETS:
    L.clear_anim(a["objs"])
sc.frame_set(1)
bpy.context.view_layer.update()

# ---- NEW human (snapshot of the selection lab)
c_h = bpy.data.collections.new("LU_NEW_Human")
rig, hobjs = L.append_human(L.SNAP, c_h)
for o in hobjs:
    C_TMP.objects.link(o) if o.name not in C_TMP.objects else None
    c_h.objects.unlink(o)
ASSETS.append(dict(key="NEW_Human", tag="NEW", label="Human (scan)", src=L.SNAP, root=rig, objs=hobjs, coll="LU_NEW_Human",
                   orig_name="RIG_Human + HUM_Body"))
A["NEW_Human"] = ASSETS[-1]
bpy.context.view_layer.update()

# move every asset into its own collection under LU_Assets
for a in ASSETS:
    c = bpy.data.collections.get(a["coll"]) or bpy.data.collections.new(a["coll"])
    if c.name not in C_ASSETS.children:
        C_ASSETS.children.link(c)
    for o in a["objs"]:
        for uc in list(o.users_collection):
            uc.objects.unlink(o)
        c.objects.link(o)
    a["collection"] = c
bpy.data.collections.remove(C_TMP)
bpy.context.view_layer.update()

# ------------------------------------------------------------------ orient + place
COL_X = {"Claude": -10.5, "Car": -3.5, "Phone": 2.5, "ParkedCar": 8.8, "Human": 15.5}
def where(a):
    kind = a["key"].split("_", 1)[1]
    col = {"Claude": "Claude", "Car": "Car", "Phone": "Phone", "ParkedCar": "ParkedCar", "Human": "Human"}[kind]
    return (COL_X[col], L.ROW_Y[a["tag"]])

def ob(a, orig):
    return next((o for o in a["objs"] if ORIG.get(o, o.name).endswith(orig)), None)

for key in ("NEW_Claude", "OLD_Claude"):
    a = A[key]
    eyes = [o for o in a["objs"] if "Eye" in o.name and "Glint" not in o.name]
    c0 = L.centre_of(a["root"]); ce = sum((L.centre_of(e) for e in eyes), Vector()) / len(eyes)
    L.yaw_to(a["root"], a["objs"], c0, ce, (0, -1))
    L.put_on_plinth(a["root"], a["objs"], where(a))

for key in ("NEW_Car", "OLD_Car"):
    a = A[key]
    fr = [o for o in a["objs"] if "Wheel_front" in o.name]; bk = [o for o in a["objs"] if "Wheel_back" in o.name]
    cf = sum((L.centre_of(o) for o in fr), Vector()) / len(fr); cb = sum((L.centre_of(o) for o in bk), Vector()) / len(bk)
    L.yaw_to(a["root"], a["objs"], cb, cf, (1, 0))
    L.put_on_plinth(a["root"], a["objs"], where(a))

# parked car (single mesh): nose = centroid of the lamp faces, tail = centroid of the tail-light faces -> +X forward
a = A["NEW_ParkedCar"]
def mat_centroid(o, key):
    me = o.data; acc = Vector(); n = 0
    for p in me.polygons:
        m = me.materials[p.material_index] if p.material_index < len(me.materials) else None
        if m and key in m.name:
            acc += o.matrix_world @ p.center; n += 1
    return acc / max(n, 1)
L.yaw_to(a["root"], a["objs"], mat_centroid(a["root"], "TailLight"), mat_centroid(a["root"], "Lamp"), (1, 0))
L.put_on_plinth(a["root"], a["objs"], where(a))

a = A["NEW_Human"]
L.put_on_plinth(a["root"], a["objs"], where(a))
a = A["OLD_Human"]
lo, hi = L.world_bbox(a["objs"]); c = (lo + hi) / 2
a["root"].matrix_world = Matrix.Translation(c) @ Matrix.Rotation(math.pi, 4, "Z") @ Matrix.Translation(-c) @ a["root"].matrix_world   # source scene's human faces +Y here
L.settle()
L.put_on_plinth(a["root"], a["objs"], where(a))

# phones: stand upright on a plinth, leaning 15 degrees back, screen facing -Y
TILT = math.radians(15)
def orient_phone(a):
    root = a["root"]
    objs = a["objs"]
    body = root
    d = body.dimensions                      # local-axis dims of the body mesh
    axes = [Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))]
    ilong = max(range(3), key=lambda i: d[i]); ithin = min(range(3), key=lambda i: d[i])
    M3 = root.matrix_world.to_3x3().normalized()
    long_w = (M3 @ axes[ilong]).normalized(); thin_w = (M3 @ axes[ithin]).normalized()
    screen = next(o for o in objs if o.name.endswith("Screen"))
    # screen side of the body along the thin axis -> outward normal sign
    sgn_n = 1 if (L.centre_of(screen) - L.centre_of(root)).dot(thin_w) >= 0 else -1
    # up sign: new phone has Title above InputBar, old phone: assume local long axis is up
    title = ob(a, "UI_Title"); inbar = ob(a, "UI_InputBar")
    if title and inbar:
        sgn_u = 1 if (L.centre_of(title) - L.centre_of(inbar)).dot(long_w) >= 0 else -1
    else:
        sgn_u = 1
    A_up = long_w * sgn_u; A_n = thin_w * sgn_n
    # make A_n perpendicular to A_up
    A_n = (A_n - A_up * A_n.dot(A_up)).normalized()
    U = Vector((0, math.sin(TILT), math.cos(TILT)))
    T = Vector((0, -math.cos(TILT), math.sin(TILT)))
    src_f = Matrix([A_up, A_n, A_up.cross(A_n)]).transposed()
    dst_f = Matrix([U, T, U.cross(T)]).transposed()
    D = (dst_f @ src_f.inverted()).to_4x4()
    lo0, hi0 = L.world_bbox(objs); c0 = (lo0 + hi0) / 2
    root.matrix_world = Matrix.Translation(c0) @ D @ Matrix.Translation(-c0) @ root.matrix_world
    L.settle()
    return sgn_u, sgn_n
for key in ("NEW_Phone", "OLD_Phone"):
    a = A[key]
    r = orient_phone(a)
    L.put_on_plinth(a["root"], a["objs"], where(a))
    print(key, "orient flags (up, normal)", r)
bpy.context.view_layer.update()

# ------------------------------------------------------------------ measure each asset
def info(a):
    lo, hi = L.world_bbox(a["objs"])
    a["bbox"] = (lo.copy(), hi.copy())
    a["dims"] = tuple(round(v, 3) for v in (hi - lo))
    a["tris"] = L.tri_count(a["objs"])
    a["nobj"] = len(a["objs"])
    a["tex"] = L.textures_of(a["objs"])
for a in ASSETS:
    info(a)
    r = a["root"]
    r["lineup_source"] = {"file": str(a["src"]), "object": a["orig_name"], "git": L.git_info(a["src"]) if a["key"] != "NEW_Human" else f"snapshot sha1 {L.sha1(L.SNAP)} of {L.SRC_HUMAN}"}
    r["lineup_tris"] = a["tris"]; r["lineup_objects"] = a["nobj"]; r["lineup_dims_m"] = list(a["dims"])
    print(a["key"], a["tris"], "tris", a["nobj"], "objs", a["dims"])

# ------------------------------------------------------------------ staging: floor, plinths, labels
mat_floor = L.mat_simple("LU_Floor", (0.30, 0.30, 0.30), 0.85)
mat_plinth = L.mat_simple("LU_Plinth_NEW", (0.40, 0.52, 0.49), 0.7)
mat_plinth_old = L.mat_simple("LU_Plinth_OLD", (0.55, 0.48, 0.38), 0.7)
mat_board = L.mat_simple("LU_Board", (0.92, 0.92, 0.9), 0.9)
mat_txt = L.mat_simple("LU_Text", (0.02, 0.02, 0.02), 0.9)
mat_new = L.mat_simple("LU_TagNEW", (0.05, 0.45, 0.35), 0.8)
mat_old = L.mat_simple("LU_TagOLD", (0.65, 0.35, 0.05), 0.8)
mat_stand = L.mat_simple("LU_Stand", (0.12, 0.12, 0.13), 0.5)

L.box_obj("LU_Floor", 400, 400, 0.2, (0, 0, -0.1), mat_floor, C_STAGE)

PLINTH = {"Claude": ("cyl", 0.9), "Car": ("box", (6.6, 3.6)), "Phone": ("cyl", 0.5), "ParkedCar": ("box", (6.4, 3.2)),
          "Human": ("cyl", 0.9)}
def fmt_tris(n):
    return f"{n:,}"
stage = {}
for a in ASSETS:
    kind = a["key"].split("_", 1)[1]
    kind = "Human" if kind == "Human" else kind
    shape, size = PLINTH[kind]
    x, y = where(a)
    if shape == "cyl":
        p = L.cyl_obj(f"LU_Plinth_{a['key']}", size, L.PLINTH_H, (x, y, L.PLINTH_H / 2), mat_plinth if a["tag"] == "NEW" else mat_plinth_old, C_STAGE)
        halfd = size; w = size * 2
    else:
        p = L.box_obj(f"LU_Plinth_{a['key']}", size[0], size[1], L.PLINTH_H, (x, y, L.PLINTH_H / 2), mat_plinth if a["tag"] == "NEW" else mat_plinth_old, C_STAGE)
        halfd = size[1] / 2; w = size[0]
    # placard (tilted board in front of the plinth, three text lines)
    big = kind in ("Car", "ParkedCar")
    bw = 3.4 if big else (2.6 if kind != "Phone" else 2.2)
    bh = 1.0 if big else 0.8
    ang = math.radians(55)
    cy = y - halfd - 0.45 - (bh / 2) * math.cos(ang)
    cz = 0.03 + (bh / 2) * math.sin(ang)
    board = L.box_obj(f"LU_Placard_{a['key']}", bw, bh, 0.03, (x, cy, cz), mat_board, C_LAB)
    board.rotation_euler = (ang, 0, 0)
    srcname = Path(a['src']).parent.name if a['key'] != 'NEW_Human' else 'character-selection (snapshot)'
    l1 = f"{a['tag']}  {a['label']}"
    l2 = srcname
    l3 = f"{fmt_tris(a['tris'])} tris   {' x '.join(f'{v:.2f}' for v in a['dims'])} m"
    s1, s2 = (0.30, 0.15) if big else (0.24, 0.12)
    L.text_obj(f"LU_Label_{a['key']}_name", l1, s1, (0, bh * 0.25, 0.02), (0, 0, 0), mat_txt, C_LAB, parent=board)
    L.text_obj(f"LU_Label_{a['key']}_src", l2, s2, (0, -bh * 0.02, 0.02), (0, 0, 0), mat_txt, C_LAB, parent=board)
    L.text_obj(f"LU_Label_{a['key']}_info", l3, s2, (0, -bh * 0.26, 0.02), (0, 0, 0), mat_txt, C_LAB, parent=board)
    strip = L.box_obj(f"LU_Tag_{a['key']}", bw, 0.07, 0.034, (0, -bh / 2 + 0.04, 0.0), mat_new if a["tag"] == "NEW" else mat_old, C_LAB)
    strip.parent = board
    stage[a["key"]] = dict(plinth=p, board=board, x=x, y=y)

# phone stands (small easel behind each phone) + 5x enlarged linked duplicates
def make_stand(name, x, y):
    # foot + back board in the phone's tilted frame; origin = base point of the phone on the plinth
    import bmesh
    bm = bmesh.new()
    def add_box(w, d, h, cx, cy, cz):
        r = bmesh.ops.create_cube(bm, size=1.0)
        for v in r["verts"]:
            v.co.x = v.co.x * w + cx; v.co.y = v.co.y * d + cy; v.co.z = v.co.z * h + cz
    add_box(0.10, 0.06, 0.008, 0, 0.03, 0.004)          # foot plate under/behind
    add_box(0.10, 0.012, 0.012, 0, -0.004, 0.006)        # front lip stopping the phone slipping
    add_box(0.10, 0.006, 0.15, 0, 0.0085, 0.075)         # back rest
    o = L.new_mesh_obj(name, bm, mat_stand, C_STAGE)
    return o
dups = {}
for key in ("NEW_Phone", "OLD_Phone"):
    a = A[key]
    lo, hi = a["bbox"]
    base = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    # base point = lowest phone corner centre; stand origin there, tilted like the phone
    st = make_stand(f"LU_Stand_{key}", 0, 0)
    st.rotation_euler = (-TILT, 0, 0)
    st.location = base
    L.settle()
    # enlarged linked duplicate x5 in front of the row (NEW: between the rows, OLD: in front of the old row)
    dc = bpy.data.collections.new(f"LU_{key}_5x"); C_ASSETS.children.link(dc)
    droot, dobjs = L.dup_hierarchy(a["objs"], a["root"], dc, "_5x")
    dy = 0.0 if a["tag"] == "NEW" else L.ROW_Y["OLD"] - 4.2
    P1 = Vector((a["bbox"][0].x, dy, L.PLINTH_H))
    P0 = Vector((base.x, base.y, base.z))
    M = Matrix.Translation(P1) @ Matrix.Scale(5, 4) @ Matrix.Translation(-P0)
    droot.matrix_world = M @ a["root"].matrix_world
    ds = st.copy(); ds.name = f"LU_Stand_{key}_5x"; ds.data = st.data; C_STAGE.objects.link(ds)
    ds.matrix_world = M @ st.matrix_world
    p5 = L.cyl_obj(f"LU_Plinth_{key}_5x", 0.5, L.PLINTH_H, (P1.x, dy, L.PLINTH_H / 2), mat_plinth if a["tag"] == "NEW" else mat_plinth_old, C_STAGE)
    lb = L.box_obj(f"LU_Placard_{key}_5x", 1.9, 0.5, 0.03, (P1.x, dy - 0.5 - 0.15, 0.03 + 0.25 * math.sin(math.radians(55))), mat_board, C_LAB)
    lb.rotation_euler = (math.radians(55), 0, 0)
    L.text_obj(f"LU_Label_{key}_5x", f"{a['tag']}  Phone x5 (enlarged)", 0.16, (0, 0, 0.02), (0, 0, 0), mat_txt, C_LAB, parent=lb)
    dups[key] = dict(root=droot, objs=dobjs, x=P1.x, y=dy)
    droot["lineup_note"] = "linked duplicate of " + a["root"].name + " scaled x5; not counted in the triangle table"
bpy.context.view_layer.update()

# row banners
for tag in ("NEW", "OLD"):
    y = L.ROW_Y[tag]
    L.text_obj(f"LU_Banner_{tag}", tag, 1.5, (-16.2, y + 0.4, 0.005), (0, 0, 0), mat_new if tag == "NEW" else mat_old, C_LAB)
    L.text_obj(f"LU_Banner_{tag}_sub", "realistic scene (diet)" if tag == "NEW" else "low-poly scene (Kenney/Quaternius)", 0.28, (-16.2, y - 1.0, 0.005), (0, 0, 0), mat_txt, C_LAB)
L.text_obj("LU_Banner_Title", "ASSET LINEUP  -  real-world scale, 1 unit = 1 m", 0.5, (0, 8.6, 0.005), (0, 0, 0), mat_txt, C_LAB)

# ------------------------------------------------------------------ lighting presets
def sun(name, toward, energy, angle_deg, color, coll):
    ld = bpy.data.lights.new(name, "SUN")
    ld.energy = energy; ld.angle = math.radians(angle_deg); ld.color = color
    o = bpy.data.objects.new(name, ld)
    coll.objects.link(o)
    t = -Vector(toward).normalized()
    o.rotation_euler = t.to_track_quat("-Z", "Y").to_euler()
    o.location = (0, 0, 30)
    return o

# studio: soft key (sun), big soft-box fill (area), rim from behind, neutral grey backdrop
sun("LU_Studio_Key", (-0.45, -0.75, 0.75), 2.0, 12, (1.0, 0.97, 0.94), C_LS)
sun("LU_Studio_Rim", (0.55, 0.9, 0.45), 1.2, 6, (0.9, 0.95, 1.0), C_LS)
ad = bpy.data.lights.new("LU_Studio_Fill", "AREA")
ad.use_shadow = False; ad.shape = "RECTANGLE"; ad.size = 34; ad.size_y = 16; ad.energy = 3500
af = bpy.data.objects.new("LU_Studio_Fill", ad); C_LS.objects.link(af)
af.location = (1.5, -2.0, 14.0)
w_s = bpy.data.worlds.new("LU_World_Studio"); w_s.use_nodes = True
w_s.node_tree.nodes["Background"].inputs["Color"].default_value = (0.5, 0.5, 0.5, 1)
w_s.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.5

# golden hour: the realistic scene's world (sunset HDRI + painted sky) and sun, azimuth turned toward the camera side
with bpy.data.libraries.load(str(L.SRC_NEW), link=False) as (df, dt):
    dt.worlds = [n for n in df.worlds if n == "World"]
    dt.objects = [n for n in df.objects if n == "LIGHT_Sun"]
w_g = dt.worlds[0]; w_g.name = "LU_World_Golden"
so = dt.objects[0]; so.name = "LU_Golden_Sun"; so.data.name = "LU_Golden_Sun"; C_LG.objects.link(so)
so.rotation_mode = "XYZ"; so.parent = None
so.location = (0, 0, 30)
t = -Vector((0.45, -0.76, 0.47)).normalized()      # same elevation as the scene sun (28 deg), azimuth toward the front-right
so.rotation_euler = t.to_track_quat("-Z", "Y").to_euler()
w_s.use_fake_user = True; w_g.use_fake_user = True
L.apply_light("studio", sc)

# ------------------------------------------------------------------ cameras
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
def asset_cam(a, suffix, az, el, lens):
    cam = L.make_camera(f"LU_CAM_{a['key']}_{suffix}", C_CAMS, lens)
    lo, hi = a["bbox"]
    L.fit_camera(cam, lo, hi, az, el, margin=0.10, lens=lens)
    return cam
SPEC = {"Claude": (-90, -50, 70), "Car": (0, -40, 50), "Phone": (-90, -55, 85), "ParkedCar": (0, -40, 50), "Human": (-90, -50, 70)}
for a in ASSETS:
    kind = a["key"].split("_", 1)[1]
    if a["key"] == "OLD_Human":
        kind = "Human"
    fa, a34, lens = SPEC[kind]
    asset_cam(a, "Front", fa, 8, lens)
    asset_cam(a, "34", a34, 18, lens)
    # LU_CAM_<NEW|OLD>_<Asset>_<Front|34> naming
for key, d in dups.items():
    lo, hi = L.world_bbox(d["objs"])
    cam = L.make_camera(f"LU_CAM_{key}5x_Front", C_CAMS, 85); L.fit_camera(cam, lo, hi, -90, 8, margin=0.10, lens=85)
    cam = L.make_camera(f"LU_CAM_{key}5x_34", C_CAMS, 85); L.fit_camera(cam, lo, hi, -55, 18, margin=0.10, lens=85)
all_lo = Vector((1e9,) * 3); all_hi = Vector((-1e9,) * 3)
for a in ASSETS:
    lo, hi = a["bbox"]
    all_lo = Vector(map(min, all_lo, lo)); all_hi = Vector(map(max, all_hi, hi))
all_lo = Vector((-17.5, -10.8, 0)); all_hi = Vector((17.5, 9.6, 2.3))
ov = L.make_camera("LU_CAM_Overview", C_CAMS, 35)
d_ov = L.fit_camera(ov, all_lo, all_hi, -90, 38, margin=0.03, lens=35)
def row_box(tag):
    los = [A[k]["bbox"][0] for k in A if A[k]["tag"] == tag]; his = [A[k]["bbox"][1] for k in A if A[k]["tag"] == tag]
    lo = Vector((min(v.x for v in los) - 1.2, min(v.y for v in los) - 1.3, 0)); hi = Vector((max(v.x for v in his) + 1.2, max(v.y for v in his) + 1, max(v.z for v in his)))
    return lo, hi
for tag, el in (("NEW", 40), ("OLD", 30)):
    cam = L.make_camera(f"LU_CAM_{tag}_Row", C_CAMS, 40)
    lo, hi = row_box(tag)
    L.fit_camera(cam, lo, hi, -90, el, margin=0.04, lens=40)
for name, kn, lens in (("Claude", "Claude", 70), ("Car", "Car", 50)):
    cam = L.make_camera(f"LU_CAM_Compare_{name}", C_CAMS, lens)
    la, ha = A["NEW_" + kn]["bbox"]; lb, hb = A["OLD_" + kn]["bbox"]
    lo = Vector(map(min, la, lb)); hi = Vector(map(max, ha, hb))
    L.fit_camera(cam, lo, hi, -128, 12, margin=0.06, lens=lens)
sc.camera = bpy.data.objects["LU_CAM_Overview"]

# ------------------------------------------------------------------ helper text blocks (Scripting workspace: Run Script)
for nm, preset in (("LU_light_studio.py", "studio"), ("LU_light_golden.py", "golden")):
    t = bpy.data.texts.new(nm)
    t.write(
        "# Run Script (Alt+P) to switch the lineup lighting.  Render with the camera you want afterwards.\n"
        "import bpy\n"
        "sc = bpy.context.scene\n"
        "def walk(lc):\n"
        "    for c in lc.children:\n"
        "        if c.name == 'LU_LIGHT_Studio': c.exclude = %r != 'studio'\n"
        "        elif c.name == 'LU_LIGHT_Golden': c.exclude = %r != 'golden'\n"
        "        walk(c)\n"
        "walk(sc.view_layers[0].layer_collection)\n"
        "sc.world = bpy.data.worlds['LU_World_Studio' if %r == 'studio' else 'LU_World_Golden']\n"
        "sc['lineup_light'] = %r\n" % (preset, preset, preset, preset))
sc["lineup_help"] = ("Lighting: Text editor -> LU_light_studio.py / LU_light_golden.py -> Run Script. "
                     "Cameras: LU_CAM_* in LU_Cameras. Render from shell: scripts/render_lineup.py. Refresh human: scripts/refresh_human.py.")

# ------------------------------------------------------------------ table + save
rows = []
for a in ASSETS:
    rows.append(dict(key=a["key"], label=a["label"], tris=a["tris"], objects=a["nobj"], dims=a["dims"], tex=a["tex"],
                     source=str(a["src"]), orig=a["orig_name"]))
(L.LAB / "asset_table.json").write_text(json.dumps(rows, indent=1, default=str))
bpy.data.orphans_purge(do_recursive=True)
try:
    bpy.ops.file.pack_all()
except Exception as e:
    print("pack_all failed:", e)
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(L.OUT))
print("saved", L.OUT)
