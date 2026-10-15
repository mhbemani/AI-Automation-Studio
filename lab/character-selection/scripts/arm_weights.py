"""Arm weights by joint rules (hands and fingers are left exactly as they are).
Rules
- Arm region: grown over the mesh surface from the forearm, staying near that arm's bones and on that side of the
  body: within 14 cm of the upper arm / 10 cm of the forearm (baggy sleeve), but only 7 cm on the side that faces
  the body's centre line, and nothing medial to the shoulder joint (so the chest and upper back stay out). Only arm-region vertices may follow the arm bones: the chest, back and the other side lose any
  arm weight (the arm cannot drag the chest along).
- Shoulder (ball joint, wide): body -> upper arm from 3 cm before to 15 cm past the shoulder joint (along the upper
  arm). Before it the vertex keeps its body weights (chest / shoulder bone).
- Armpit / side fade: body vertices within 12 cm of the arm region, but more than 10 cm from the centre line, follow
  the upper arm by up to 60 %, fading out with distance (no hard seam under a raised arm; the chest stays still).
- Elbow (hinge, narrow): upper arm -> forearm over +-4 cm around the elbow (normal = mid-direction of both bones).
- Weights sum to 1, < 1 % dropped.
Run: Blender -b --factory-startup character_selection_lab.blend --python scripts/arm_weights.py  (env OUT=)"""
import bpy, os, bmesh
from mathutils import Vector
from mathutils.geometry import intersect_point_line
o = bpy.data.objects["HUM_Body"]; rig = bpy.data.objects["RIG_Human"]
for ob in (o, rig):
    bpy.context.view_layer.objects.active = ob
    if ob.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
B = rig.data.bones; G = o.vertex_groups; gi = {g.name: g.index for g in G}; gn = {i: n for n, i in gi.items()}
ARM = {f"{b}.{s}" for b in ("upper_arm", "forearm", "hand") for s in "LR"}
LOCK = ("hand", "f_", "thumb")
R_UA, R_FA, R_MED = 0.14, 0.10, 0.07
SH_A, SH_B = float(os.environ.get('SH_A', '-0.03')), float(os.environ.get('SH_B', '0.15'))   # shoulder blend along the upper arm
def ss(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)
def seg_dist(p, a, b):
    q, t = intersect_point_line(p, a, b); q = a if t < 0 else b if t > 1 else q
    return (p - q).length
xc = B["chest"].head_local.x
me = o.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
W = {v.index: {gn[g.group]: g.weight for g in v.groups} for v in me.vertices}
locked = {i for i, w in W.items() if any(k.startswith(LOCK) and x > 0.01 for k, x in w.items())}
region, info = {}, []
for s in "LR":
    S, E, Wr = B[f"upper_arm.{s}"].head_local, B[f"forearm.{s}"].head_local, B[f"forearm.{s}"].tail_local
    dua = (E - S).normalized()
    def ok(p):
        if (p.x >= xc) != (s == "L") or (p - S).dot(dua) < -0.05: return False
        side_sign = 1 if s == "L" else -1
        for a, b, r in ((S, E, R_UA), (E, Wr, R_FA)):
            q, t = intersect_point_line(p, a, b)
            if a is S and t < 0 and (p.x - S.x) * side_sign < -0.02: continue   # medial to the shoulder joint = chest/back
            q = a if t < 0 else b if t > 1 else q
            rad = p - q; d = rad.length
            medial = d > 1e-6 and rad.normalized().dot(Vector((xc - q.x, 0, 0)).normalized()) > 0.5
            if d < (min(r, R_MED) if medial else r): return True
        return False
    seeds = [i for i, w in W.items() if w and max(w, key=w.get) == f"forearm.{s}" and ok(me.vertices[i].co)]
    seen, st = set(seeds), list(seeds)
    while st:
        a = st.pop()
        for e in bm.verts[a].link_edges:
            b = e.other_vert(bm.verts[a]).index
            if b not in seen and ok(me.vertices[b].co): seen.add(b); st.append(b)
    for i in seen: region[i] = s
    info.append(f"{s}: {len(seen)} arm vertices")
# armpit / side fade: body vertices next to the arm region (not the central chest or back) follow the upper arm a
# little, fading out over FADE, so a raised arm stretches the side of the hoodie instead of tearing a hard seam.
FADE, FADE_MAX, CORE = float(os.environ.get('FADE', '0.12')), float(os.environ.get('FADE_MAX', '0.6')), 0.10
from mathutils.kdtree import KDTree
fade = {}
for s in "LR":
    pts = [i for i, sd in region.items() if sd == s]
    kd = KDTree(len(pts))
    for k, i in enumerate(pts): kd.insert(me.vertices[i].co, k)
    kd.balance()
    S, E = B[f"upper_arm.{s}"].head_local, B[f"forearm.{s}"].head_local; dua = (E - S).normalized()
    for v in me.vertices:
        i = v.index
        if i in region or i in locked or ((v.co.x >= xc) != (s == "L")) or abs(v.co.x - xc) < CORE: continue
        co, k, d = kd.find(v.co)
        if d < FADE:
            wu_edge = ss(SH_A, SH_B, (co - S).dot(dua))           # how much the nearest arm vertex follows the arm
            fade[i] = (s, FADE_MAX * wu_edge * (1 - d / FADE) ** 2)
stripped = changed = 0
for v in me.vertices:
    i = v.index
    if i in locked: continue
    old = W[i]
    if i in region:
        s = region[i]; p = v.co
        S, E, Wr = B[f"upper_arm.{s}"].head_local, B[f"forearm.{s}"].head_local, B[f"forearm.{s}"].tail_local
        dua, dfa = (E - S).normalized(), (Wr - E).normalized()
        wu = ss(SH_A, SH_B, (p - S).dot(dua))
        wf = ss(-0.04, 0.04, (p - E).dot((dua + dfa).normalized()))
        new = {f"upper_arm.{s}": wu * (1 - wf), f"forearm.{s}": wu * wf}
        torso = {k: x for k, x in old.items() if k not in ARM}
        tw = sum(torso.values())
        if 1 - wu > 1e-4:
            if tw < 1e-6: torso, tw = {f"shoulder.{s}": 1.0}, 1.0
            for k, x in torso.items(): new[k] = new.get(k, 0) + (1 - wu) * x / tw
    else:
        if not any(k in ARM for k in old) and i not in fade: continue
        new = {k: x for k, x in old.items() if k not in ARM}
        if any(k in ARM for k in old): stripped += 1
        if not new: new = {"chest": 1.0}
        if i in fade:
            s, wf_ = fade[i]; t_ = sum(new.values())
            new = {k: x / t_ * (1 - wf_) for k, x in new.items()}; new[f"upper_arm.{s}"] = wf_
    new = {k: x for k, x in new.items() if x >= 0.01}
    tot = sum(new.values()); new = {k: x / tot for k, x in new.items()}
    for k_ in [g.group for g in v.groups]: G[k_].remove([i])   # indices first: removing shifts v.groups
    for k, x in new.items(): G[k].add([i], x, 'REPLACE')
    changed += 1
if os.environ.get("DEBUG_RENDER"):   # colour the arm regions for a visual check
    ca = me.color_attributes.get("arm_region") or me.color_attributes.new("arm_region", 'FLOAT_COLOR', 'POINT')
    for v in me.vertices:
        ca.data[v.index].color = (1, .2, .1, 1) if region.get(v.index) == "L" else (.1, .4, 1, 1) if region.get(v.index) == "R" else (.75, .75, .72, 1) if v.index not in locked else (.3, .8, .3, 1)
print("ARMS", " | ".join(info), "| side/armpit fade vertices", len(fade), "| body vertices that lost arm weight:", stripped, "| locked hand vertices", len(locked), "| changed", changed)
bpy.ops.wm.save_as_mainfile(filepath=os.environ.get("OUT", bpy.data.filepath))
