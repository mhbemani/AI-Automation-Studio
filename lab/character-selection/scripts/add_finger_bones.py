"""Step 7: finger bones (3 per digit, both hands) + finger weights.
Digits are found from the mesh: each fingertip dome top (6-triangle fan) is walked back ring by ring
(dome ring, tip ring, last joint, middle joint, base) -> the ring centres are the joints.
Bones (Rigify-style names): thumb.01-.03, f_index/f_middle/f_ring/f_pinky.01-.03 .L/.R
  .01 base -> middle joint (parent hand, not connected), .02 middle -> last joint, .03 last joint -> tip.
  Roll: local X = across the hand (the curl axis), so curling a finger = rotating its bones around X.
Weights are per ring, so they stay right if the bones are moved later:
  base ring hand/.01 50/50, middle joint .01/.02 50/50, last joint .02/.03 50/50, tip ring + dome .03 100 %.
Run: Blender -b --factory-startup character_selection_lab.blend --python scripts/add_finger_bones.py  (env OUT=)"""
import bpy, bmesh, os
from mathutils import Vector
o = bpy.data.objects["HUM_Body"]; rig = bpy.data.objects["RIG_Human"]
for ob in (o, rig):
    bpy.context.view_layer.objects.active = ob
    if ob.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
gi = {g.name: g.index for g in o.vertex_groups}; gn = {i: n for n, i in gi.items()}
bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table(); dl = bm.verts.layers.deform.active
dom = lambda v: gn[max(v[dl].keys(), key=lambda k: v[dl][k])] if v[dl] else None
cen = lambda vs: sum((v.co for v in vs), Vector()) / len(vs)

def walk_digit(top):
    """top -> [dome ring, tip ring, last joint, middle joint, base] (6 verts each) or None"""
    rings, prev, cur = [], {top}, {e.other_vert(top) for e in top.link_edges}
    for _ in range(5):
        if len(cur) != 6: return None
        rings.append(cur)
        nxt = {e.other_vert(v) for v in cur for e in v.link_edges} - cur - prev
        prev, cur = cur, nxt
    return rings
digits = {"R": [], "L": []}
for v in bm.verts:
    if len(v.link_faces) == 6 and all(len(f.verts) == 3 for f in v.link_faces) and dom(v) in ("hand.R", "hand.L"):
        r = walk_digit(v)
        if r: digits[dom(v)[-1]].append((v, r))
assert all(len(d) == 5 for d in digits.values()), {k: len(d) for k, d in digits.items()}

bones = {}   # name -> (head, tail, parent)
weights = {}  # vert -> {group: w}
for s, ds in digits.items():
    info = [dict(top=t, base=cen(r[4]), mid=cen(r[3]), last=cen(r[2]), rings=r) for t, r in ds]
    wrist = rig.data.bones[f"hand.{s}"].head_local
    thumb = min(info, key=lambda d: (d["base"] - wrist).length)          # the digit rooted closest to the wrist
    rest = sorted((d for d in info if d is not thumb), key=lambda d: (d["base"] - thumb["base"]).length)
    names = {id(thumb): "thumb"} | {id(d): n for d, n in zip(rest, ("f_index", "f_middle", "f_ring", "f_pinky"))}
    across = (rest[0]["base"] - rest[-1]["base"]).normalized()           # index -> pinky line
    along = (sum((d["base"] for d in rest), Vector()) / 4 - wrist).normalized()
    back = along.cross(across) if s == "R" else across.cross(along)        # back-of-hand side (sign checked below)
    for d in info:
        n = names[id(d)]; tip = d["top"].co.copy()
        J = [d["base"], d["mid"], d["last"], tip]
        for k in range(3):
            bones[f"{n}.0{k+1}.{s}"] = (J[k], J[k + 1], f"hand.{s}" if k == 0 else f"{n}.0{k}.{s}", back, across)
        r = d["rings"]
        for v in r[4]: weights[v] = {f"hand.{s}": .5, f"{n}.01.{s}": .5}
        for v in r[3]: weights[v] = {f"{n}.01.{s}": .5, f"{n}.02.{s}": .5}
        for v in r[2]: weights[v] = {f"{n}.02.{s}": .5, f"{n}.03.{s}": .5}
        for v in r[1] | r[0] | {d["top"]}: weights[v] = {f"{n}.03.{s}": 1.0}

# --- bones
bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
for name in [b for b in bones if b in eb]: eb.remove(eb[name])
for name, (h, t, parent, back, across) in bones.items():
    b = eb.new(name); b.head = h; b.tail = t; b.parent = eb[parent]
    b.use_connect = not parent.startswith("hand.")
    b.align_roll(back)                                  # Z toward the back of the hand -> X across the hand
bpy.ops.object.mode_set(mode='OBJECT')

# --- weights
for name in bones:
    if name not in gi: gi[name] = o.vertex_groups.new(name=name).index
for v, w in weights.items():
    d = v[dl]
    for k in list(d.keys()):
        if gn.get(k, "").startswith("hand.") or k not in gn: del d[k]
    for g, x in w.items(): d[gi[g]] = x
bm.to_mesh(o.data); o.data.update()
print("FINGERS bones", len(bones), "| weighted verts", len(weights), "| bones total", len(rig.data.bones))
bpy.ops.wm.save_as_mainfile(filepath=os.environ.get("OUT", bpy.data.filepath))
