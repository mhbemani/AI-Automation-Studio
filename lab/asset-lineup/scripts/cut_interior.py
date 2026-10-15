"""Cut the parts of the new car's interior (floor, door cards, dashboard) that stick out of the body: at the sides, in the wheel arches and
below. The cut lines are measured from the body itself (rays against LU_NEW_CAR_Ext_Body), so it follows whatever placement you made:
  * sides:  a sloped plane following the body's side surface (fitted at several heights), 8 mm inside it
  * arches: the arch ceiling profile, measured along y, extruded outward from the arch inner wall
  * below:  everything under the body floor
Exact booleans against throw-away cutter objects, then the result is baked into the mesh (no modifiers left).
Reads IN.blend, writes OUT.blend (never the input):
  Blender -b --factory-startup IN.blend --python lab/asset-lineup/scripts/cut_interior.py -- OUT.blend"""
import bpy, bmesh, sys, math, numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
out = sys.argv[sys.argv.index("--") + 1]
MARGIN = 0.008
root = bpy.data.objects["LU_NEW_CAR_Exterior"]; inv = root.matrix_world.inverted()
body = bpy.data.objects["LU_NEW_CAR_Ext_Body"]
bm = bmesh.new(); bm.from_mesh(body.data); bm.transform(inv @ body.matrix_world)
bvh = BVHTree.FromBMesh(bm)
zmin = min(v.co.z for v in bm.verts)
CUT = ["Int_Floor", "Int_DoorCards", "Dashboard"]
ALL = CUT + ["Seat_FL", "Seat_FL_Back", "Seat_FL_Headrest", "Seat_FR", "Seat_FR_Back", "Seat_FR_Headrest", "SteeringWheel", "SteeringColumn"]
objs = {n: bpy.data.objects["LU_NEW_CAR_" + n] for n in ALL}
interior_z0 = min(min((inv @ (o.matrix_world @ v.co)).z for v in o.data.vertices) for o in objs.values())

# --- 1. side surface: x of the body side seen from outside, per height, away from the arches (min over y)
ys = np.arange(-1.0, 1.3, 0.05)
ztop = max(max((inv @ (o.matrix_world @ v.co)).z for v in o.data.vertices) for o in (objs[n] for n in CUT)) + 0.1
zs = np.arange(interior_z0 - 0.02, ztop, 0.05)
side = []                                             # (z, x_limit) polyline of the body side
for z in zs:
    xs = [h.x for y in ys if (h := bvh.ray_cast(Vector((2.0, y, z)), Vector((-1, 0, 0)))[0]) is not None and h.x > 0.75]   # arch walls (~0.62) excluded
    if xs: side.append((float(z), min(xs) - MARGIN))
print("side profile (z, max x):", [(round(z, 2), round(x, 3)) for z, x in side])

# --- 2. arches: ceiling profile along y at x = 0.8 (first body surface above the floor that is not the floor), and the arch inner wall x
def first_above(o, zthr, zlim):
    p = Vector(o)
    for _ in range(6):
        h = bvh.ray_cast(p, Vector((0, 0, 1)))[0]
        if h is None: return None
        if h.z > zthr: return h.z if h.z < zlim else None
        p = Vector((p.x, p.y, h.z + 0.002))
    return None
def arch_profile(sx):
    out_ = []
    for y in np.arange(-3.0, 3.0, 0.03):
        zs_ = [z for xx in (0.8,) if (z := first_above((sx * xx, y, zmin - 0.1), zmin + 0.12, zmin + 0.52)) is not None]
        if zs_: out_.append((float(y), max(zs_)))        # highest ceiling over the arch width, so nothing is left standing inside the arch
    return out_
def runs(prof):
    out_, cur = [], []
    for y, z in prof:
        if cur and y - cur[-1][0] > 0.05: out_.append(cur); cur = []
        cur.append((y, z))
    if cur: out_.append(cur)
    return [r for r in out_ if len(r) > 6]
ARCH = {sx: runs(arch_profile(sx)) for sx in (1, -1)}
wall = {}
for sx in (1, -1):
    kept = []
    for r in ARCH[sx]:
        h = bvh.ray_cast(Vector((sx * 2.0, r[len(r) // 2][0], zmin + 0.3)), Vector((-sx, 0, 0)))[0]
        w = abs(h.x) if h else 0.62
        if w < 0.8:                      # real wheel arches have their inner wall at ~0.62; other pockets (e.g. the tail) are skipped
            wall[(sx, len(kept))] = w; kept.append(r)
    ARCH[sx] = kept
print("arch runs (y ranges):", {sx: [(round(r[0][0], 2), round(r[-1][0], 2), round(max(z for _, z in r), 2)) for r in ARCH[sx]] for sx in ARCH}, "inner wall x", {k: round(v, 3) for k, v in wall.items()})

# --- 3. cutters (root-local), made as objects in the scene, deleted afterwards
cutters = []
def cutter_from_bm(name, b):
    me = bpy.data.meshes.new(name); b.to_mesh(me); b.free()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    o.matrix_world = root.matrix_world; cutters.append(o); return o
def prism(name, poly_xz_or_yz, axis, lo, hi):
    """closed prism: polygon in the plane perpendicular to `axis` ('y': polygon is (x, z); 'x': polygon is (y, z)), extruded from lo to hi"""
    b = bmesh.new(); rings = []
    for t in (lo, hi):
        rings.append([b.verts.new((px, t, pz) if axis == "y" else (t, px, pz)) for px, pz in poly_xz_or_yz])
    n = len(poly_xz_or_yz)
    b.faces.new(rings[0]); b.faces.new(rings[1][::-1])
    for k in range(n): b.faces.new((rings[0][k], rings[0][(k + 1) % n], rings[1][(k + 1) % n], rings[1][k]))
    bmesh.ops.recalc_face_normals(b, faces=b.faces[:])
    return cutter_from_bm(name, b)
for sx in (1, -1):    # sides: everything beyond the side profile, full cabin length
    poly = [(sx * x, z) for z, x in side] + [(sx * (side[-1][1] + 1.0), side[-1][0]), (sx * (side[0][1] + 1.0), side[0][0])]
    prism(f"cut_side_{sx}", [(sx * x, z) for z, x in side] + [(sx * (max(x for _, x in side) + 1.0), side[-1][0]), (sx * (max(x for _, x in side) + 1.0), side[0][0])], "y", -3.5, 3.5)
b = bmesh.new(); bmesh.ops.create_cube(b, size=1.0)       # below the body floor
for v in b.verts: v.co = Vector((v.co.x * 6, v.co.y * 12, v.co.z * 4 - 2 + zmin + 0.004))
cutter_from_bm("cut_below", b)
for sx in (1, -1):
    for i, r in enumerate(ARCH[sx]):
        w = wall[(sx, i)] - MARGIN
        top = [(y, z - MARGIN) for y, z in r]
        poly = [(top[0][0], zmin - 0.3)] + top + [(top[-1][0], zmin - 0.3)]
        lo, hi = (w, w + 0.8) if sx > 0 else (-w - 0.8, -w)
        prism(f"cut_arch_{sx}_{i}", poly, "x", lo, hi)

# --- 4. count what sticks out before, cut, count again
def outside(o):
    n = 0
    for v in o.data.vertices:
        p = inv @ (o.matrix_world @ v.co); sx = 1 if p.x >= 0 else -1
        lim = np.interp(p.z, [z for z, _ in side], [x for _, x in side])
        if abs(p.x) > lim + 0.001 or p.z < zmin: n += 1
    return n
before = {n: outside(objs[n]) for n in ALL}
dg = bpy.context.evaluated_depsgraph_get()
for n in CUT:
    o = objs[n]
    for c in cutters:
        m = o.modifiers.new(c.name, "BOOLEAN"); m.operation = "DIFFERENCE"; m.solver = "EXACT"; m.object = c
    dg = bpy.context.evaluated_depsgraph_get()
    new = bpy.data.meshes.new_from_object(o.evaluated_get(dg)); new.name = o.data.name
    old = o.data
    for m in list(o.modifiers): o.modifiers.remove(m)
    o.data = new
    if old.users == 0: bpy.data.meshes.remove(old)
    o.data.name = "NEW_CAR_" + n + ".cut"
    print("cut", n, "->", len(new.vertices), "verts")
after = {n: outside(objs[n]) for n in ALL}
print("vertices beyond the side plane / below the floor, before -> after:", {n: (before[n], after[n]) for n in ALL})
for c in cutters: bpy.data.objects.remove(c)
bpy.ops.wm.save_as_mainfile(filepath=out, copy=False)
print("saved", out)
