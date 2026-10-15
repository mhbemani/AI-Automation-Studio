"""Copy the finished back-right wheel + its wheel-arch section on the body to the other three wheels.
Reads a lineup .blend, writes a NEW file (never the input):
  Blender -b --factory-startup IN.blend --python lab/asset-lineup/scripts/copy_wheels.py -- OUT.blend [--front-arches]
Body-local frame: x = across (right wheels negative), y = along (rear +, front -)."""
import bpy, bmesh, sys, numpy as np
from mathutils import kdtree
from mathutils import Vector, Matrix
out = sys.argv[sys.argv.index("--") + 1]
FRONT = "--front-arches" in sys.argv
body = bpy.data.objects["LU_NEW_CAR_Ext_Body"]
W = {n: bpy.data.objects["LU_NEW_CAR_Wheel_" + n] for n in ("back-right", "back-left", "front-right", "front-left")}
BR_LO, BR_HI = Vector((-1.03, 0.78, 0.20)), Vector((-0.50, 1.74, 0.75))      # arch region of the finished wheel
REAR_Y, FRONT_Y = 1.265, -1.657

def faces_in(bm, lo, hi):
    return [f for f in bm.faces if all(lo[i] <= f.calc_center_median()[i] <= hi[i] for i in range(3))]

def asym(me):
    co = np.round(np.array([v.co[:] for v in me.vertices]), 4); k = {tuple(r) for r in co}
    return sum(1 for r in co if (-r[0], r[1], r[2]) not in k)

def paste(bm, src_faces, xform, flip, tgt_lo, tgt_hi):
    """Replace the faces in the target box by a transformed copy of src_faces; weld the seam."""
    tgt = faces_in(bm, tgt_lo, tgt_hi)
    geom = list(src_faces)
    for f in src_faces: geom += list(f.edges) + list(f.verts)
    dup = bmesh.ops.duplicate(bm, geom=list(set(geom)))["geom"]
    nv = [g for g in dup if isinstance(g, bmesh.types.BMVert)]
    nf = [g for g in dup if isinstance(g, bmesh.types.BMFace)]
    bmesh.ops.transform(bm, matrix=xform, verts=nv)
    if flip: bmesh.ops.reverse_faces(bm, faces=nf)
    bmesh.ops.delete(bm, geom=tgt, context="FACES")
    # weld only copy -> existing vertices (never copy-copy or existing-existing, so overlapping shells stay as they were)
    newset = set(nv)
    kd = kdtree.KDTree(len(bm.verts)); old = [v for v in bm.verts if v not in newset]
    for i, v in enumerate(old): kd.insert(v.co, i)
    kd.balance()
    tm = {}
    for v in nv:
        if not v.is_valid: continue
        hit = kd.find_range(v.co, 1e-4)
        if hit: tm[v] = old[min(hit, key=lambda h: h[2])[1]]
    bmesh.ops.weld_verts(bm, targetmap=tm)
    bm.edges.ensure_lookup_table()
    return len(tgt), len(nf)

me = body.data
before = (len(me.vertices), len(me.polygons), asym(me))
bm = bmesh.new(); bm.from_mesh(me)
src = faces_in(bm, BR_LO, BR_HI)
mirror = Matrix.Scale(-1, 4, Vector((1, 0, 0)))
# rear-left arch = mirror of the rear-right arch
bl_lo, bl_hi = Vector((0.50, BR_LO.y, BR_LO.z)), Vector((1.03, BR_HI.y, BR_HI.z))
print("rear-left arch: replaced", paste(bm, src, mirror, True, bl_lo, bl_hi))
if FRONT:
    src = faces_in(bm, BR_LO, BR_HI)
    dy = FRONT_Y - REAR_Y
    sh = Matrix.Translation((0, dy, 0))
    fr_lo, fr_hi = BR_LO + Vector((0, dy, 0)), BR_HI + Vector((0, dy, 0))
    fl_lo, fl_hi = bl_lo + Vector((0, dy, 0)), bl_hi + Vector((0, dy, 0))
    print("front-right arch:", paste(bm, src, sh, False, fr_lo, fr_hi))
    print("front-left arch:", paste(bm, src, sh @ mirror, True, fl_lo, fl_hi))
bm.to_mesh(me); bm.free(); me.update()
print("body verts/faces/asym before", before, "after", (len(me.vertices), len(me.polygons), asym(me)))

# wheels: mesh of the finished back-right wheel -> mirrored for the left, same mesh shifted to sit flush on the front axles
br = W["back-right"]; brm = br.data
half = lambda o: abs(o.matrix_world.translation.y - body.matrix_world.translation.y)   # half-track of this axle
def clone(name, mirrored, dx):
    m = brm.copy(); m.name = name
    for v in m.vertices:
        v.co.x = (-v.co.x if mirrored else v.co.x) + dx
    if mirrored: m.flip_normals()
    m.update(); return m
for n, o in W.items():
    if n == "back-right": continue
    left = "left" in n
    # front axles are 3.7 cm wider than the rear ones: shift the tyre inboard by that much so its outer face stays flush with the arch like the finished rear wheel
    dx = (half(o) - half(br)) * (1 if left is False else -1)
    o.data = clone("NEW_LIB_Hero_Wheel_" + n, left, dx)
    print("wheel", n, "mirrored", left, "mesh shift", round(dx, 3))
bpy.ops.wm.save_as_mainfile(filepath=out, copy=False)
print("saved", out)
