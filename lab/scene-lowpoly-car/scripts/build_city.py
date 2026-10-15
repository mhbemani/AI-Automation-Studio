# City: a closed rounded-rectangle ring road (the car can circle forever) built from 00_LIB linked duplicates.
# Re-runnable: deletes only objects tagged cs_owner in OWNERS that the creator has not marked user_locked.
# Ring centreline: x -176..184, y 0..216 (360 x 216 m), Kenney curve tiles at the corners (centreline radius 12).
# The car drives counter-clockwise in the right lane = the outer lane (2 m outside the centreline, corner
# radius 14). The pickup street is the south straight (y=0), exit building door at x~1.5, y=-8.
# Kenney orientation (found by snapshot): building fronts face +Y, cars face -Y, light-curved arm points +Y,
# road-straight runs along X, road-curve (rot 0) arcs through the NE quadrant of its turning centre
# (tile centre = turning centre + (8, 8)).
import bpy, math, random
from mathutils import Vector

OWNERS = {"city", "stage"}
for o in [o for o in bpy.data.objects if o.get("cs_owner") in OWNERS and not o.get("user_locked")]:
    bpy.data.objects.remove(o)
for o in [o for o in bpy.data.objects if o.name.startswith("TMP_")]: bpy.data.objects.remove(o)
taken = {o.name for o in bpy.data.objects}   # creator-locked survivors keep their names
CITY = "01_CITY"
rng = random.Random(7)   # fixed seed: the same city on every rebuild

def put(src, name, loc, rot=0, owner="city", scale=None, coll=CITY, shadow=True):
    if name in taken: return None
    s = bpy.data.objects[src]; o = s.copy(); o.name = name; o["cs_owner"] = owner
    bpy.data.collections[coll].objects.link(o)
    o.location = loc; o.rotation_mode = "XYZ"; o.rotation_euler = (0, 0, math.radians(rot))  # glTF import uses quaternions
    if scale: o.scale = scale
    o.visible_shadow = shadow
    for c in s.children:   # car wheels / rig mesh
        k = c.copy(); k.parent = o; k["cs_owner"] = owner; k.name = name + c.name[len(src):]
        bpy.data.collections[coll].objects.link(k)
        for m in k.modifiers:
            if m.type == "ARMATURE": m.object = o
    return o

def own_mesh(name, verts, faces, mats, uv=None):   # meshes this script owns (rebuilt each run)
    me = bpy.data.meshes.get(name)
    if me: me.clear_geometry(); me.materials.clear()
    else: me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    for m in mats: me.materials.append(m)
    if uv:
        me.uv_layers.new()
        for d in me.uv_layers.active.data: d.uv = uv
    return me

def flat_mat(name, color):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*color, 1)
    m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
    m.diffuse_color = (*color, 1)
    return m

dims = lambda src: bpy.data.objects[src].dimensions

# --- Ring geometry ---------------------------------------------------------------------------------
X0, X1, Y0, Y1, R = -176, 184, 0, 216, 12          # centreline rectangle, corner radius (curve tile)
CORNERS = [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)]  # CCW driving order: SW, SE, NE, NW
LANE = 2                                            # right lane centre: 2 m outside the centreline
CX, CY = (X0 + X1) / 2, (Y0 + Y1) / 2

def edge(k):   # edge k runs from corner k to corner k+1; n points out of the ring (right of t)
    A, B = Vector(CORNERS[k]), Vector(CORNERS[(k + 1) % 4])
    t = (B - A).normalized(); return A, B, t, Vector((t.y, -t.x)), (B - A).length

def at(A, t, n, s, off, z=0): p = A + t * s + n * off; return (p.x, p.y, z)
yaw = lambda f: math.degrees(math.atan2(-f.x, f.y))   # rot that turns a +Y-facing kit model to face f
heading = lambda t: math.degrees(math.atan2(t.y, t.x))

# Ground: 1.6 km square around the ring, so the horizon never shows the void.
G = 800
me = own_mesh("CITY_Ground", [(CX - G, CY - G, 0), (CX + G, CY - G, 0), (CX + G, CY + G, 0), (CX - G, CY + G, 0)],
              [(0, 1, 2, 3)], [flat_mat("MAT_Ground", (0.18, 0.2, 0.17))])
g = bpy.data.objects.get("CITY_Ground") or bpy.data.objects.new("CITY_Ground", me)
if g.name not in bpy.data.collections[CITY].objects: bpy.data.collections[CITY].objects.link(g)
g["cs_owner"] = "ground"; g.location = (0, 0, -0.02)
# Inner block floor (a pale plaza/park colour, under the inner buildings and the park).
park_me = own_mesh("CITY_Park", [(X0 + 8, Y0 + 8, 0), (X1 - 8, Y0 + 8, 0), (X1 - 8, Y1 - 8, 0), (X0 + 8, Y1 - 8, 0)],
                    [(0, 1, 2, 3)], [flat_mat("MAT_Park", (0.22, 0.3, 0.16))])
p = bpy.data.objects.new("CITY_Park", park_me); p["cs_owner"] = "city"; p.location.z = -0.01
bpy.data.collections[CITY].objects.link(p)

# Corner fills: the curve tile leaves its outer corner and inner quarter bare; fill them with sidewalk
# (same texel of the Kenney colormap as tile-low). Built in the NE quadrant of the turning centre.
SIDE_MAT = bpy.data.objects["LIB_tile-low"].data.materials[0]
arc = lambda r, a0, a1, n: [(r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
                             r * math.sin(math.radians(a0 + (a1 - a0) * i / n)), 0.16) for i in range(n + 1)]
outer = [(20, 0, 0.16)] + arc(16, 0, 90, 24) + [(0, 20, 0.16), (20, 20, 0.16)]
inner = [(0, 0, 0.16)] + arc(8, 0, 90, 16)
fill_o = own_mesh("CITY_CornerFill_Outer", outer, [tuple(range(len(outer)))], [SIDE_MAT], uv=(0.40625, 0.375))
fill_i = own_mesh("CITY_CornerFill_Inner", inner, [tuple(range(len(inner)))], [SIDE_MAT], uv=(0.40625, 0.375))

BLDG = ["building-" + c for c in "abcdefgh"]

def row(k, side, s0, s1, tag):
    """Buildings along edge k on one side (+1 outer, -1 inner) between s0..s1, fronts facing the road.
    Random kit buildings (seeded); leftover length is spread over the gaps so rows end flush."""
    A, B, t, n, L = edge(k)
    picks, used = [], 0.0
    while True:
        nm = "LIB_" + rng.choice(BLDG); w = dims(nm).x
        if used + w + 0.6 > s1 - s0: break
        picks.append(nm); used += w + 0.6
    if not picks: return
    gap = (s1 - s0 - sum(dims(nm).x for nm in picks)) / len(picks)
    s = s0
    for i, nm in enumerate(picks):
        w, d = dims(nm).x, dims(nm).y; s += gap / 2 + w / 2
        put(nm, f"CITY_Bldg_{tag}_{i:02d}", at(A, t, n, s, side * (8 + d / 2)), rot=yaw(-n * side))
        s += w / 2 + gap / 2

TREE = None
def tree(name, loc, h=1.0):
    global TREE
    if TREE is None:   # one shared low-poly tree mesh: 6-sided trunk + a 2-tier cone canopy
        v, f = [], []
        def ring_(r, z): b = len(v); v.extend((r * math.cos(a * math.pi / 3), r * math.sin(a * math.pi / 3), z) for a in range(6)); return b
        a0, a1 = ring_(0.15, 0), ring_(0.12, 1.6); f += [(a0 + i, a0 + (i + 1) % 6, a1 + (i + 1) % 6, a1 + i) for i in range(6)]
        for r, z0, z1 in ((1.5, 1.4, 3.6), (1.1, 2.8, 4.8)):
            b = ring_(r, z0); v.append((0, 0, z1)); tip = len(v) - 1
            f += [(b + i, b + (i + 1) % 6, tip) for i in range(6)] + [tuple(b + i for i in range(5, -1, -1))]
        TREE = own_mesh("CITY_Tree", v, f, [flat_mat("MAT_TreeTrunk", (0.25, 0.15, 0.08)), flat_mat("MAT_TreeLeaf", (0.16, 0.42, 0.16))])
        for p_ in TREE.polygons: p_.material_index = 0 if p_.index < 6 else 1
    if name in taken: return
    o = bpy.data.objects.new(name, TREE); o["cs_owner"] = "city"; bpy.data.collections[CITY].objects.link(o)
    o.location = loc; o.rotation_euler.z = rng.uniform(0, 6.28); o.scale = (h, h, h)

# --- Per edge: roads, sidewalks, curve + fills, buildings, lights, trees ---------------------------
EXIT_S = 176   # exit building at x=0 on the south edge (s = x - X0)
for k in range(4):
    A, B, t, n, L = edge(k)
    nt = int((L - 2 * R) / 8)
    for i in range(nt):
        s = R + 4 + 8 * i
        put("LIB_road-straight", f"CITY_Road_{k}_{i:02d}", at(A, t, n, s, 0), rot=heading(t))
        for sd, tag in ((1, "O"), (-1, "I")):
            put("LIB_tile-low", f"CITY_Sidewalk_{k}{tag}_{i:02d}", at(A, t, n, s, sd * 6), rot=heading(t), scale=(1, 0.5, 1))
    tc = B - t * R - n * R                                    # turning centre of the corner at the end of edge k
    rot = heading(t) - 90
    put("LIB_road-curve", f"CITY_Road_Curve_{k}", (*(tc + t * 8 + n * 8), 0), rot=rot)
    for me_, tag in ((fill_o, "Outer"), (fill_i, "Inner")):
        o = bpy.data.objects.new(f"CITY_CornerFill_{k}_{tag}", me_); o["cs_owner"] = "city"
        bpy.data.collections[CITY].objects.link(o); o.location = (*tc, 0); o.rotation_euler.z = math.radians(rot)

    # Buildings: outer row runs corner to corner (s -8..L+8), inner row stops 10 m short of the inner corners.
    if k == 0:
        w = dims("LIB_building-a").x
        put("LIB_building-a", "CITY_ExitBuilding", (0, -8 - dims("LIB_building-a").y / 2, 0))
        row(k, 1, -8, EXIT_S - w / 2 - 0.6, f"{k}O"); row(k, 1, EXIT_S + w / 2 + 0.6, L + 8, f"{k}Ob")
    else:
        row(k, 1, -8, L + 8, f"{k}O")
    row(k, -1, 18, L - 18, f"{k}I")
    # Corner buildings: a tower on the outer corner, a block on the inner corner (both face edge k's road).
    put("LIB_building-skyscraper-" + "ab"[k % 2], f"CITY_Bldg_Corner_{k}O", at(A, t, n, L + 8 + 5.6, 8 + 5.6), rot=yaw(-n))
    put("LIB_building-" + "cfhd"[k], f"CITY_Bldg_Corner_{k}I", at(A, t, n, L - 13.5, -13.5), rot=yaw(n))

    # Street lights every 16 m on both sides, staggered (outer s=4 mod 16, inner s=12 mod 16), arms over the road.
    for i, s in enumerate(range(R + 8, int(L - R - 4), 16)):
        put("LIB_light-curved", f"CITY_StreetLight_{k}O_{i:02d}", at(A, t, n, s, 4.6), rot=yaw(-n))
        if s + 8 < L - R - 4:
            put("LIB_light-curved", f"CITY_StreetLight_{k}I_{i:02d}", at(A, t, n, s + 8, -4.6), rot=yaw(n))
    # Trees: sparse, on the inner sidewalk between the lights.
    for i, s in enumerate(range(R + 40, int(L - R - 20), 48)):
        tree(f"CITY_Tree_{k}_{i:02d}", at(A, t, n, s, -6.3), rng.uniform(0.85, 1.15))

    # Background: a ring of towers/blocks 30-45 m outside the centreline (no shadows: cheap), and a far
    # skyline of big low-detail blocks ~120 m out so the horizon is never empty.
    for i, s in enumerate(range(-40, int(L + 40), 14)):
        off = 34 + rng.uniform(0, 10)
        if i % 4 == 0:
            put("LIB_building-skyscraper-" + "ab"[i // 4 % 2], f"CITY_BG_{k}_{i:02d}", at(A, t, n, s, off), rot=yaw(-n), shadow=False)
        else:
            put(f"LIB_low-detail-building-{'abcd'[i % 4]}", f"CITY_BG_{k}_{i:02d}", at(A, t, n, s, off), rot=yaw(-n),
                scale=(2.5, 2.5, rng.uniform(1.0, 1.8)), shadow=False)
    for i, s in enumerate(range(-120, int(L + 120), 30)):
        put(f"LIB_low-detail-building-{'abcd'[i % 4]}", f"CITY_BG_Far_{k}_{i:02d}", at(A, t, n, s, 120 + rng.uniform(0, 40)),
            rot=yaw(-n), scale=(5, 5, rng.uniform(1.5, 3.0)), shadow=False)

# Inner block: low blocks on a 28 m grid around a central park with trees.
for i, x in enumerate(range(X0 + 34, X1 - 30, 28)):
    for j, y in enumerate(range(Y0 + 34, Y1 - 30, 28)):
        if abs(x - CX) < 60 and abs(y - CY) < 40:   # the park
            if (i + j) % 2 == 0: tree(f"CITY_Tree_Park_{i:02d}_{j:02d}", (x + rng.uniform(-6, 6), y + rng.uniform(-6, 6), 0), rng.uniform(1.0, 1.4))
            continue
        put(f"LIB_low-detail-building-{'abcd'[(i + j) % 4]}", f"CITY_BG_In_{i:02d}_{j:02d}", (x, y, 0),
            rot=90 * rng.randrange(4), scale=(2, 2, rng.uniform(0.5, 1.0)), shadow=False)

# Parked cars, sparingly, on the inner (oncoming) lane's curb, far from corners; never in the drive lane.
PARKED = [(0, 154, "van"), (0, 202, "suv"), (1, 70, "taxi"), (2, 120, "sedan"), (2, 260, "suv"), (3, 140, "van")]
for i, (k, s, m) in enumerate(PARKED):
    A, B, t, n, L = edge(k)
    put("LIB_" + m, f"CITY_ParkedCar_{'ABCDEF'[i]}", at(A, t, n, s, -2.3), rot=yaw(t))

# Drive path: closed (cyclic) poly curve along the right lane, starting at the pickup point (x=5) on the
# south straight; corners are 1-degree arcs of radius R+LANE=14 (smooth heading). z=0: the car's origin
# sits on the road. Car forward axis: -Y (see drive_car.py).
PICKUP = Vector((5, Y0 - LANE))
pts = [PICKUP]
for k in range(4):
    A, B, t, n, L = edge(k); tc = B - t * R - n * R
    pts += [tc + (n * math.cos(math.radians(d)) + t * math.sin(math.radians(d))) * (R + LANE) for d in range(91)]
dense = []   # a point every <=8 m on the straights: Blender smooths poly tangents across long segments
for a, b in zip(pts, pts[1:] + pts[:1]):
    m = max(1, math.ceil((b - a).length / 8)); dense += [a.lerp(b, i / m) for i in range(m)]
pts = dense
p = bpy.data.objects.get("CITY_DrivePath")
if p and not p.get("user_locked"):
    cu = p.data; bpy.data.objects.remove(p); bpy.data.curves.remove(cu); p = None
if not p:
    old = bpy.data.curves.get("CITY_DrivePath")
    if old and not old.users: bpy.data.curves.remove(old)
    cu = bpy.data.curves.new("CITY_DrivePath", "CURVE"); cu.dimensions = "3D"; cu.use_path = True
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1); sp.use_cyclic_u = True
    for q, v in zip(sp.points, pts): q.co = (v.x, v.y, 0, 1)
    p = bpy.data.objects.new("CITY_DrivePath", cu); p["cs_owner"] = "city"
    bpy.data.collections[CITY].objects.link(p)
    p["length_m"] = sum((pts[i] - pts[i - 1]).length for i in range(len(pts)))   # includes the closing segment

# Staging: Claude's car at the pickup curb in front of the exit building, facing +X (driving: drive_car.py).
put("LIB_sedan", "CAR_Exterior", (*PICKUP, 0), rot=90, owner="stage", coll="02_CAR")   # interior: build_car.py

# Working cameras (not shots): the old street overview and an orthographic top view of the whole ring.
cam = bpy.data.objects.get("CAM_WORK_Overview")
if not cam:
    cam = bpy.data.objects.new("CAM_WORK_Overview", bpy.data.cameras.new("CAM_WORK_Overview"))
    bpy.data.collections["04_CAMERAS"].objects.link(cam)
    cam.location = (-26, 3, 9); cam.rotation_euler = (math.radians(76), 0, math.radians(-100))
    cam.data.lens = 24
top = bpy.data.objects.get("CAM_WORK_Top")
if not top:
    top = bpy.data.objects.new("CAM_WORK_Top", bpy.data.cameras.new("CAM_WORK_Top"))
    bpy.data.collections["04_CAMERAS"].objects.link(top)
top.location = (CX, CY, 300); top.rotation_euler = (0, 0, 0)
top.data.type = "ORTHO"; top.data.ortho_scale = 440; top.data.clip_end = 1000
bpy.data.orphans_purge(do_recursive=True); bpy.context.view_layer.update()   # later scripts read CAR_Exterior.matrix_world
result = {"objects": len([o for o in bpy.data.objects if o.get("cs_owner") in OWNERS]),
          "path_m": round(p["length_m"], 1) if "length_m" in p else None}
