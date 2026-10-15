"""Quick health report of the lab file. Run: Blender -b --factory-startup character_selection_lab.blend --python scripts/state_check.py"""
import bpy, bmesh
rig = bpy.data.objects["RIG_Human"]; b = bpy.data.objects["HUM_Body"]
print("ST objects", [(o.name, o.type, o.mode) for o in bpy.data.objects], "| posed", [p.name for p in rig.pose.bones if not p.matrix_basis.is_identity])
bm = bmesh.new(); bm.from_mesh(b.data); dl = bm.verts.layers.deform.active
gn = {g.index: g.name for g in b.vertex_groups}
def handw(v, s):
    return sum(w for k, w in v[dl].items() if gn[k].endswith("." + s) and (gn[k].startswith(("hand", "f_", "thumb"))))
for s in "RL":
    H = [v for v in bm.verts if handw(v, s) >= 0.5]
    F = [f for f in bm.faces if all(handw(v, s) >= 0.5 for v in f.verts)]
    print("ST hand", s, "verts", len(H), "faces", len(F), "tris", sum(len(f.verts) - 2 for f in F))
print("ST mesh verts", len(bm.verts), "tris", sum(len(f.verts) - 2 for f in bm.faces), "open edges", sum(e.is_boundary for e in bm.edges),
      "nonmanifold", sum(not e.is_manifold for e in bm.edges), "unweighted", sum(1 for v in b.data.vertices if not v.groups), "bones", len(rig.data.bones))
