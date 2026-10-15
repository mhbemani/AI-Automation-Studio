"""Are the two hands still connected to each other (ignoring the long path through the arms and torso)?
Geometric, independent of the (old) weights: takes vertices within R of either hand bone, labels each by the nearer
hand bone, and finds connected pieces of that local patch. A piece holding both labels = hands still joined there.
Run: Blender -b --factory-startup character_selection_lab.blend --python scripts/check_hands.py"""
import bpy, bmesh
from mathutils.geometry import intersect_point_line
R = 0.06
o = bpy.data.objects["HUM_Body"]; rig = bpy.data.objects["RIG_Human"]
seg = {s: (rig.matrix_world @ rig.data.bones[f"hand.{s}"].head_local, rig.matrix_world @ rig.data.bones[f"hand.{s}"].tail_local) for s in "LR"}
def dist(p, a, b):
    q, t = intersect_point_line(p, a, b); q = a if t < 0 else b if t > 1 else q
    return (p - q).length
bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
side = {}
for v in bm.verts:
    p = o.matrix_world @ v.co; d = {s: dist(p, *seg[s]) for s in "LR"}
    s = min(d, key=d.get)
    if d[s] < R: side[v.index] = s
seen, comps = set(), []
for s0 in side:
    if s0 in seen: continue
    st = [s0]; seen.add(s0); c = []
    while st:
        a = st.pop(); c.append(a)
        for e in bm.verts[a].link_edges:
            b = e.other_vert(bm.verts[a]).index
            if b in side and b not in seen: seen.add(b); st.append(b)
    comps.append(c)
for c in sorted(comps, key=len, reverse=True):
    print("INFO local hand piece", len(c), "verts; nearest hand:", {s: sum(side[i] == s for i in c) for s in "LR"})
bridge = [e for e in bm.edges if all(v.index in side for v in e.verts) and side[e.verts[0].index] != side[e.verts[1].index]]
print("INFO edges between a left-hand and a right-hand vertex:", len(bridge))
for e in bridge:
    p = [o.matrix_world @ v.co for v in e.verts]
    print("INFO  edge %d mid (%.3f %.3f %.3f) len %.3f selected %s" % (e.index, *((p[0] + p[1]) / 2), (p[0] - p[1]).length, e.select))
