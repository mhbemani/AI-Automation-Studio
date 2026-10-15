"""Step 3: replace the left hand with a mirrored copy of the right hand.
- hand sets = vertices whose strongest weight is hand.R / hand.L (the wrist sits at the 50 % weight line)
- the left hand's vertices are deleted and the opening at the left wrist is closed
- the right hand's faces (plus the one ring of forearm vertices they touch, a stub that tucks into the left cuff)
  are duplicated and moved with  M_L @ mirrorX @ M_R^-1  (bone rest matrices), so the right wrist lands on the
  left wrist and the hand follows the left hand bone's angle; face winding is reversed after the mirror
- the copy's weights are the right hand's weights with every .R group renamed to .L
Run: Blender -b --factory-startup character_selection_lab.blend --python scripts/mirror_hand.py"""
import bpy, bmesh
from mathutils import Matrix
o = bpy.data.objects["HUM_Body"]; rig = bpy.data.objects["RIG_Human"]
for ob in (o, rig):
    bpy.context.view_layer.objects.active = ob
    if ob.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
gi = {g.name: g.index for g in o.vertex_groups}; gn = {i: n for n, i in gi.items()}
swap = {gi[n]: gi[n[:-2] + ".L"] for n in gi if n.endswith(".R")}
bm = bmesh.new(); bm.from_mesh(o.data); dl = bm.verts.layers.deform.active
def dom(v):
    d = v[dl]; return gn[max(d.keys(), key=lambda k: d[k])] if d else None
L = [v for v in bm.verts if dom(v) == "hand.L"]; R = {v for v in bm.verts if dom(v) == "hand.R"}
nL, nR = len(L), len(R)
# 1. delete the left hand and close the wrist opening
before = {e for e in bm.edges if e.is_boundary}
bmesh.ops.delete(bm, geom=L, context='VERTS')
rim = [e for e in bm.edges if e.is_boundary and e not in before]
filled = bmesh.ops.holes_fill(bm, edges=rim, sides=0)["faces"]
# 2. duplicate the right hand (+ the forearm ring it touches)
faces = [f for f in bm.faces if any(v in R for v in f.verts)]
dup = bmesh.ops.duplicate(bm, geom=faces)
nv = [g for g in dup["geom"] if isinstance(g, bmesh.types.BMVert)]
nf = [g for g in dup["geom"] if isinstance(g, bmesh.types.BMFace)]
B = rig.data.bones
M = B["hand.L"].matrix_local @ Matrix.Scale(-1, 4, (1, 0, 0)) @ B["hand.R"].matrix_local.inverted()
bmesh.ops.transform(bm, matrix=M, verts=nv)
bmesh.ops.reverse_faces(bm, faces=nf)
for v in nv:
    d = v[dl]; old = dict(d); d.clear()
    for k, w in old.items(): d[swap.get(k, k)] = w
bm.normal_update(); bm.to_mesh(o.data); o.data.update()
print("MIRROR left hand verts removed", nL, "| wrist faces filled", len(filled), "| right hand verts", nR,
      "| copied verts", len(nv), "faces", len(nf), "| total verts", len(o.data.vertices))
bpy.ops.wm.save_mainfile()
