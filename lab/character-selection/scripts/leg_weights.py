"""Leg weights by joint rules (replaces the automatic weights on the legs; everything above the hips is untouched).
Rules
- Side lock: a vertex left of the body centre line can only follow left-leg bones, and vice versa (no bleeding
  from one leg into the other, or into the crotch of the other side).
- Hip (ball joint, wide): blend from 3 cm above to 6 cm below the hip-joint plane (plane through the hip joint,
  normal along the thigh). Above it the vertex keeps its existing body weights (pelvis/spine).
  The crotch point keeps 60 % body weight, fading to 0 within 6 cm, so lifting one leg does not tear the crotch.
- Knee (hinge, narrow): thigh -> shin over +-4 cm around the knee plane (normal = mid-direction of thigh and shin).
- Ankle (hinge, narrow): shin -> foot over +-2.5 cm around the ankle height (along the shin), so the whole shoe
  follows the foot and the trouser cuff follows the shin.
- Above the hip zone no vertex may follow a leg bone.
- Weights sum to 1, tiny weights (< 1 %) are dropped.
Run: Blender -b --factory-startup character_selection_lab.blend --python scripts/leg_weights.py  (env OUT=)"""
import bpy, os
from mathutils import Vector
o = bpy.data.objects["HUM_Body"]; rig = bpy.data.objects["RIG_Human"]
for ob in (o, rig):
    bpy.context.view_layer.objects.active = ob
    if ob.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
B = rig.data.bones; G = o.vertex_groups; gi = {g.name: g.index for g in G}; gn = {i: n for n, i in gi.items()}
LEG = {f"{b}.{s}" for b in ("thigh", "shin", "foot") for s in "LR"}
ARMS = ("shoulder", "upper_arm", "forearm", "hand", "f_", "thumb", "neck", "head")
def ss(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)
J = {}
for s in "LR":
    H, K, A, T = B[f"thigh.{s}"].head_local, B[f"thigh.{s}"].tail_local, B[f"shin.{s}"].tail_local, B[f"foot.{s}"].tail_local
    J[s] = dict(H=H, K=K, A=A, dt=(K - H).normalized(), ds=(A - K).normalized())
xc = (J["L"]["H"].x + J["R"]["H"].x) / 2
body_top = max(J[s]["H"].z for s in "LR") + 0.06
# crotch point: walk up the centre line from the knees; the first height where a front-to-back ray hits the mesh
from mathutils.bvhtree import BVHTree
bvh = BVHTree.FromPolygons([v.co for v in o.data.vertices], [list(f.vertices) for f in o.data.polygons])
z = min(J[s]["K"].z for s in "LR")
while z < body_top:
    hit = bvh.ray_cast(Vector((xc, -1.0, z)), Vector((0, 1, 0)), 2.0)
    if hit[0] is not None: break
    z += 0.002
C = hit[0]
changed = 0
for v in o.data.vertices:
    p = v.co
    old = {gn[g.group]: g.weight for g in v.groups}
    if p.z > body_top:   # above the hips: no leg bone may pull the hoodie (left over from the automatic weights)
        if any(k in LEG for k in old):
            keep = {k: w for k, w in old.items() if k not in LEG} or {"pelvis": 1.0}
            t = sum(keep.values())
            for k_ in [g.group for g in v.groups]: G[k_].remove([v.index])   # indices first: removing shifts v.groups
            for k, w in keep.items(): G[k].add([v.index], w / t, 'REPLACE')
            changed += 1
        continue
    if old and gn and max(old, key=old.get).startswith(ARMS): continue
    s = "L" if p.x >= xc else "R"; j = J[s]
    wh = ss(-0.03, 0.06, (p - j["H"]).dot(j["dt"])) * (0.4 + 0.6 * ss(0.0, 0.06, (p - C).length))
    wk = ss(-0.04, 0.04, (p - j["K"]).dot((j["dt"] + j["ds"]).normalized()))
    wa = ss(-0.025, 0.025, (p - j["A"]).dot(j["ds"]))
    new = {f"thigh.{s}": wh * (1 - wk), f"shin.{s}": wh * wk * (1 - wa), f"foot.{s}": wh * wk * wa}
    torso = {k: w for k, w in old.items() if k not in LEG}
    tw = sum(torso.values())
    if 1 - wh > 1e-4:
        if tw < 1e-6: torso, tw = {"pelvis": 1.0}, 1.0
        for k, w in torso.items(): new[k] = new.get(k, 0) + (1 - wh) * w / tw
    new = {k: w for k, w in new.items() if w >= 0.01}
    tot = sum(new.values()); new = {k: w / tot for k, w in new.items()}
    for k_ in [g.group for g in v.groups]: G[k_].remove([v.index])   # indices first: removing shifts v.groups
    for k, w in new.items(): G[k].add([v.index], w, 'REPLACE')
    changed += 1
print("LEGS reweighted", changed, "vertices | crotch point", tuple(round(c, 3) for c in C), "| centre x %.3f" % xc)
bpy.ops.wm.save_as_mainfile(filepath=os.environ.get("OUT", bpy.data.filepath))
