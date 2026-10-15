"""Numeric checks of the locomotion actions (bridge): loop closure, foot sliding during flat stance, reach (leg stretch), frame counts. -> stills/locomotion_checks.json"""
import bpy, json, math, os
ROOT = os.environ.get("ANIM_ROOT") or os.path.dirname(os.path.abspath(__import__("bpy").data.filepath))
rig = bpy.data.objects["RIG_Human"]; V_ = 1.2 / 24
res = {}
def play(name):
    ad = rig.animation_data_create(); ad.action = bpy.data.actions[name]
def ankle(side):
    e = rig.evaluated_get(bpy.context.evaluated_depsgraph_get()); h = e.pose.bones[f"DEF-foot.{side}"].head; return h.y, h.z
def leg_len(side):
    e = rig.evaluated_get(bpy.context.evaluated_depsgraph_get()); return (e.pose.bones[f"DEF-thigh.{side}"].head - e.pose.bones[f"DEF-foot.{side}"].head).length
rest = {}
rig.animation_data_create().action = None
# walk cycle
play("HUM_walk_cycle"); a = bpy.data.actions["HUM_walk_cycle"]
ys = {}; zs = {}; ll = []
for f in range(1, 26):
    bpy.context.scene.frame_set(f)
    for s in "LR": y, z = ankle(s); ys[(s, f)] = y; zs[(s, f)] = z; ll.append(leg_len(s))
stance = {"L": range(3, 12), "R": range(15, 24)}
drift = {s: max(ys[(s, f)] - V_ * (f - 1) * -1 * -1 * 0 + 0 for f in stance[s]) for s in "LR"}   # placeholder, replaced below
drift = {}
for s in "LR":
    w = [ys[(s, f)] - V_ * (f - 1) for f in stance[s]]       # world y of the ankle if the body walks toward -Y at V_ per frame
    drift[s] = round((max(w) - min(w)) * 100, 3)
res["walk_cycle"] = {"foot_drift_cm_in_stance": drift, "min_ankle_z": round(min(zs.values()), 3), "max_ankle_z": round(max(zs.values()), 3), "leg_length_range": [round(min(ll), 3), round(max(ll), 3)]}
loop = max(abs(ys[("L", 25)] - ys[("L", 1)]), abs(ys[("R", 25)] - ys[("R", 1)]))
fcs = {}
for fc in a.fcurves: fcs[(fc.data_path, fc.array_index)] = abs(fc.evaluate(25) - fc.evaluate(1))
res["walk_cycle"]["loop_max_diff_channels"] = round(max(fcs.values()), 6); res["walk_cycle"]["ankle_y_loop_diff_m"] = round(loop, 6)
res["walk_cycle"]["range"] = list(a.frame_range)
# symmetry: ankle lateral offset from the hip centre line, and foot yaw (toe out), during flat stance of each foot
def lat(side):
    e = rig.evaluated_get(bpy.context.evaluated_depsgraph_get()); pb = e.pose.bones
    c = (pb["DEF-thigh.L"].head.x + pb["DEF-thigh.R"].head.x) / 2
    d = pb[f"DEF-toe.{side}"].tail - pb[f"DEF-foot.{side}"].head; sx = 1 if side == "L" else -1
    return round(sx * (pb[f"DEF-foot.{side}"].head.x - c), 3), round(math.degrees(math.atan2(sx * d.x, -d.y)), 1)
sym = {}
for s_, rng in (("L", range(3, 12)), ("R", range(15, 24))):
    vals = []
    for f in rng: bpy.context.scene.frame_set(f); vals.append(lat(s_))
    sym[s_] = {"ankle_out_from_centre_m": round(sum(v[0] for v in vals) / len(vals), 3), "toe_out_deg": round(sum(v[1] for v in vals) / len(vals), 1)}
res["walk_cycle"]["symmetry_in_stance"] = sym
# walk out of the building: root motion on, planted ankles should not drift in world during steady state (frames 40..72 look at flat stance windows)
play("HUM_walk_out_building"); drs = []
w = {"L": [], "R": []}
for f in range(1, 73):
    bpy.context.scene.frame_set(f)
    for s in "LR": w[s].append((f, ankle(s)[0]))
# steady state p = 0.5 + (t-1): phase of L foot = p; flat stance when (p % 1) in [0.08, 0.45]
def phase(f):
    t = (f - 1) / 24.0; return 0.5 * t * t if t < 1 else 0.5 + (t - 1)
for s, off in (("L", 0.0), ("R", 0.5)):
    groups = {}
    for f, y in w[s]:
        if f >= 30:
            ph = (phase(f) + off) % 1.0
            if 0.10 < ph < 0.44: groups.setdefault(int(phase(f) + off), []).append(y)
    drs += [(max(v) - min(v)) * 100 for v in groups.values() if len(v) > 2]
res["walk_out_building"] = {"foot_drift_cm_in_stance": round(max(drs), 3), "range": list(bpy.data.actions["HUM_walk_out_building"].frame_range)}
for n, length in (("HUM_stand_idle", 96), ("HUM_stand_to_walk", 12), ("HUM_walk_to_stand", 12), ("HUM_stop_from_walk", 18)):
    a2 = bpy.data.actions[n]; f0, f1 = a2.frame_range
    r = {"range": [int(f0), int(f1)], "length_ok": (int(f1 - f0) == length) if n == "HUM_stand_idle" else (int(f1 - f0 + 1) == length)}
    if n == "HUM_stand_idle": r["loop_max_diff"] = round(max(abs(fc.evaluate(f0) - fc.evaluate(f1)) for fc in a2.fcurves), 6)
    res[n] = r
# walk_to_stand starts at the walk's first pose, stand_to_walk ends there
def pose_vec(name, frame):
    play(name); bpy.context.scene.frame_set(frame); return [round(x, 4) for s in "LR" for x in ankle(s)]
res["blend_match"] = {"walk f1 vs stand_to_walk f12": max(abs(a - b) for a, b in zip(pose_vec("HUM_walk_cycle", 1), pose_vec("HUM_stand_to_walk", 12))),
                      "walk f1 vs walk_to_stand f1": max(abs(a - b) for a, b in zip(pose_vec("HUM_walk_cycle", 1), pose_vec("HUM_walk_to_stand", 1)))}
rig.animation_data.action = None
json.dump(res, open(os.path.join(ROOT, "stills", "locomotion_checks.json"), "w"), indent=1)
result = res
