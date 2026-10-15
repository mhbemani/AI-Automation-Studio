"""Step 2 weight cleanup after the creator's palm cut: rebind, then make each hand follow only its own side.
- local patch = verts within R of the hands' centre; the piece connected to the left wrist is 'L', to the right wrist 'R'
- in an L vertex every *.R arm weight (shoulder/upper_arm/forearm/hand) is moved to the same bone on .L, and vice versa
- tiny loose islands (<= 6 verts, chopped off by the cut) join the side of the nearest piece vertex
Run: Blender -b --factory-startup character_selection_lab.blend --python scripts/rebind.py --python scripts/fix_hand_weights.py
("Error: Vertex not in group" lines are harmless: weight() raising for vertices without that group.)"""
import bpy, bmesh
R = 0.15
o = bpy.data.objects["HUM_Body"]; rig = bpy.data.objects["RIG_Human"]; me = o.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
B = rig.data.bones
wrist = {s: B[f"hand.{s}"].head_local for s in "LR"}
mid = (wrist["L"] + wrist["R"] + B["hand.L"].tail_local + B["hand.R"].tail_local) / 4
patch = {v.index for v in bm.verts if (v.co - mid).length < R}
def flood(seed, allowed):
    st, seen = [seed], {seed}
    while st:
        a = st.pop()
        for e in bm.verts[a].link_edges:
            b = e.other_vert(bm.verts[a]).index
            if b in allowed and b not in seen: seen.add(b); st.append(b)
    return seen
side = {}
for s in "LR":
    seed = min(patch, key=lambda i: (bm.verts[i].co - wrist[s]).length)
    for i in flood(seed, patch): side[i] = s
assert not ({i for i in side if side[i] == "L"} & {i for i in side if side[i] == "R"})
# tiny loose islands anywhere near the hands
allv = set(range(len(bm.verts))); done = set(); tiny = 0
for i in patch:
    if i in side or i in done: continue
    isl = flood(i, allv); done |= isl
    if len(isl) <= 6:
        near = min(side, key=lambda j: min((bm.verts[j].co - bm.verts[k].co).length for k in isl))
        for k in isl: side[k] = side[near]
        tiny += 1
gi = {g.name: g for g in o.vertex_groups}
moved = 0
for i, s in side.items():
    other = "R" if s == "L" else "L"
    for part in ("shoulder", "upper_arm", "forearm", "hand"):
        src, dst = gi[f"{part}.{other}"], gi[f"{part}.{s}"]
        try: w = src.weight(i)
        except RuntimeError: continue
        src.remove([i]); moved += 1
        try: w += dst.weight(i)
        except RuntimeError: pass
        dst.add([i], min(w, 1.0), 'REPLACE')
print("FIX patch", len(patch), "L", sum(v == "L" for v in side.values()), "R", sum(v == "R" for v in side.values()),
      "unassigned", len(patch - set(side)), "tiny islands", tiny, "weights moved", moved)
bpy.ops.wm.save_mainfile()
