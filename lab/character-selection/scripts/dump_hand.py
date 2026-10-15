"""Dump the right hand (strongest weight hand.R, plus the faces touching it) in hand.R bone-local coordinates to JSON.
Bone-local: +Y along the hand (wrist -> fingertips), X/Z across it. Run: Blender -b ... --python scripts/dump_hand.py -- out.json"""
import bpy, bmesh, json, sys
o = bpy.data.objects["HUM_Body"]; rig = bpy.data.objects["RIG_Human"]
gi = {g.index: g.name for g in o.vertex_groups}
bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table(); dl = bm.verts.layers.deform.active
def dom(v):
    d = v[dl]; return gi[max(d.keys(), key=lambda k: d[k])] if d else None
R = {v.index for v in bm.verts if dom(v) == "hand.R"}
faces = [f for f in bm.faces if any(v.index in R for v in f.verts)]
Minv = rig.data.bones["hand.R"].matrix_local.inverted()
vs = sorted({v.index for f in faces for v in f.verts})
out = {"verts": {i: list(Minv @ bm.verts[i].co) for i in vs}, "hand": sorted(R),
       "faces": [[v.index for v in f.verts] for f in faces],
       "normals": [list(Minv.to_3x3() @ f.normal) for f in faces],
       "boundary": [[e.verts[0].index, e.verts[1].index] for e in bm.edges if e.is_boundary and any(v.index in R for v in e.verts)],
       "bone_len": rig.data.bones["hand.R"].length}
json.dump(out, open(sys.argv[-1], "w"))
print("DUMP", len(vs), "verts", len(faces), "faces", len(out["boundary"]), "open edges at the hand")
