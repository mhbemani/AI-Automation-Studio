"""Mirror the front-right wheel-arch edit of the car body onto the front-left (x -> -x).
The edit is found by diffing the body against the untouched source mesh (LIB_Hero_Body in the realistic scene, read-only):
  D = source faces in the right-front zone that no longer exist, A = faces in that zone that are not in the source.
On the left: delete the mirror image of D (and any non-source faces already in the left zone), add the mirror image of A, weld the seam.
Reads IN.blend, writes OUT.blend (never the input):
  Blender -b --factory-startup IN.blend --python lab/asset-lineup/scripts/mirror_arch.py -- OUT.blend
Body-local frame: x across (right negative), y along (front negative)."""
import bpy, bmesh, sys, os, numpy as np
from mathutils import Vector, Matrix, kdtree
out = sys.argv[sys.argv.index("--") + 1]
SRC = os.path.join(os.environ.get("LU_MAIN_REPO", os.getcwd()), "lab/scene-realistic-car/scene.blend")
body = bpy.data.objects["LU_NEW_CAR_Ext_Body"]; me = body.data
if body.mode != "OBJECT":
    bpy.context.view_layer.objects.active = body; bpy.ops.object.mode_set(mode="OBJECT")
LO, HI = Vector((-1.05, -2.6, 0.2)), Vector((-0.4, -1.0, 0.95))          # right-front zone (body-local)
mirror = Matrix.Scale(-1, 4, Vector((1, 0, 0)))
R = lambda c, sx=1: (round(c[0] * sx, 4) + 0.0, round(c[1], 4) + 0.0, round(c[2], 4) + 0.0)
fkey = lambda f, sx=1: tuple(sorted(R(v.co, sx) for v in f.verts))
inzone = lambda p, lo, hi: all(lo[i] <= p[i] <= hi[i] for i in range(3))

with bpy.data.libraries.load(SRC, link=False) as (df, dt):
    dt.meshes = ["LIB_Hero_Body"]
sbm = bmesh.new(); sbm.from_mesh(dt.meshes[0])
S = {fkey(f): f.calc_center_median() for f in sbm.faces}
bm = bmesh.new(); bm.from_mesh(me)
C = {fkey(f) for f in bm.faces}
D = {k for k, c in S.items() if inzone(c, LO, HI) and k not in C}                       # source faces the right side lost
A = [f for f in bm.faces if inzone(f.calc_center_median(), LO, HI) and fkey(f) not in S]  # new faces on the right
LLO, LHI = Vector((-HI.x, LO.y, LO.z)), Vector((-LO.x, HI.y, HI.z))
dels = [f for f in bm.faces if inzone(f.calc_center_median(), LLO, LHI) and (fkey(f, -1) in D or fkey(f) not in S)]
print("right edit: removed", len(D), "source faces, added", len(A), "faces; left: deleting", len(dels))
geom = list(A)
for f in A: geom += list(f.edges) + list(f.verts)
dup = bmesh.ops.duplicate(bm, geom=list(set(geom)))["geom"]
nv = [g for g in dup if isinstance(g, bmesh.types.BMVert)]; nf = [g for g in dup if isinstance(g, bmesh.types.BMFace)]
bmesh.ops.transform(bm, matrix=mirror, verts=nv)
bmesh.ops.reverse_faces(bm, faces=nf)
bmesh.ops.delete(bm, geom=dels, context="FACES")
ns = set(nv); old = [v for v in bm.verts if v not in ns]
kd = kdtree.KDTree(len(old))
for i, v in enumerate(old): kd.insert(v.co, i)
kd.balance()
tm = {}
for v in nv:
    if v.is_valid:
        hit = kd.find_range(v.co, 1e-4)
        if hit: tm[v] = old[min(hit, key=lambda h: h[2])[1]]
bmesh.ops.weld_verts(bm, targetmap=tm)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
# report open edges in both zones
def opened(lo, hi, sx):
    return {tuple(sorted(R(v.co, sx) for v in e.verts)) for e in bm.edges if (e.is_boundary or not e.is_manifold) and inzone((e.verts[0].co + e.verts[1].co) / 2, lo, hi)}
r, l = opened(LO, HI, 1), opened(LLO, LHI, -1)
print("open edges right", len(r), "left", len(l), "differing", len(r ^ l))
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=out, copy=False)
print("saved", out)
