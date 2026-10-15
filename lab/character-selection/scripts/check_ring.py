"""Diagnose the creator's selected edge ring on HUM_Body: closed? gaps? already split? islands.
Run: Blender -b --factory-startup character_selection_lab.blend --python scripts/check_ring.py"""
import bpy, bmesh, collections
o = bpy.data.objects["HUM_Body"]; bm = bmesh.new(); bm.from_mesh(o.data)
bm.verts.ensure_lookup_table()
sel = [e for e in bm.edges if e.select]
deg = collections.Counter(v.index for e in sel for v in e.verts)
print("INFO mode", o.mode, "verts", len(bm.verts), "faces", len(bm.faces), "selected edges", len(sel),
      "selected verts", sum(v.select for v in bm.verts), "boundary edges", sum(e.is_boundary for e in bm.edges))
ends = [i for i, d in deg.items() if d == 1]; forks = [i for i, d in deg.items() if d > 2]
print("INFO ring ends (gaps)", len(ends), "forks", len(forks))
for i in ends + forks:
    p = o.matrix_world @ bm.verts[i].co
    print("INFO", "end" if i in ends else "fork", i, "deg", deg[i], "at x %.3f y %.3f z %.3f" % tuple(p))
zs = [(o.matrix_world @ v.co).z for e in sel for v in e.verts]
if zs: print("INFO ring z range %.3f..%.3f" % (min(zs), max(zs)))
# islands
seen, isl = set(), []
for v in bm.verts:
    if v.index in seen: continue
    st = [v]; seen.add(v.index); n = 0
    while st:
        a = st.pop(); n += 1
        for e in a.link_edges:
            b = e.other_vert(a)
            if b.index not in seen: seen.add(b.index); st.append(b)
    isl.append(n)
print("INFO islands", sorted(isl, reverse=True))
# selected-edge components
adj = collections.defaultdict(set)
for e in sel: a, b = (v.index for v in e.verts); adj[a].add(b); adj[b].add(a)
seen, comps = set(), []
for s in adj:
    if s in seen: continue
    st = [s]; seen.add(s); c = 0
    while st:
        a = st.pop(); c += 1
        for b in adj[a]:
            if b not in seen: seen.add(b); st.append(b)
    comps.append(c)
print("INFO selection pieces (vertex counts)", comps)
