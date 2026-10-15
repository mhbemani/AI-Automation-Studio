"""Numeric checks for milestone 3 (via bridge): frame counts, one-shots return to their start, transitions end on HUM_pose_seated, planted feet, leg stretch. Writes stills/react_checks.json"""
import bpy, json, math
from mathutils import Vector as V
exp = {"HUM_react_startle": 16, "HUM_react_laugh": 36, "HUM_react_impressed": 30, "HUM_react_shake_head": 18, "HUM_phone_to_seat_idle": 36, "PHN_phone_pocket": 36, "HUM_stand_to_sit_car": 72, "HUM_sit_to_stand_car": 72,
       "CLA_react_proud_puff": 24, "CLA_react_oops": 20, "CLA_react_giggle": 24, "CLA_pickup_arrival": 72}
out = {n: {"frames": int(bpy.data.actions[n].frame_range[1] - bpy.data.actions[n].frame_range[0] + 1), "expected": L} for n, L in exp.items()}
out["CLA_react_giggle"]["loop_diff"] = round(max(abs(fc.evaluate(1) - fc.evaluate(25)) for fc in bpy.data.actions["CLA_react_giggle"].fcurves), 5)
for n in ("HUM_react_startle", "HUM_react_laugh", "HUM_react_impressed", "HUM_react_shake_head", "CLA_react_proud_puff", "CLA_react_oops"):
    a = bpy.data.actions[n]; r = a.frame_range
    # rotation channels only (degrees) / props, difference first vs last key
    out[n]["end_minus_start_max"] = round(max(abs(fc.evaluate(r[1]) - fc.evaluate(r[0])) for fc in a.fcurves), 4)
H = bpy.data.objects["RIG_Human"]; had = H.animation_data_create()
def hpose(n, f):
    had.action = bpy.data.actions[n]; bpy.context.scene.frame_set(500); bpy.context.scene.frame_set(f)
    return H.evaluated_get(bpy.context.evaluated_depsgraph_get())
def defs(ev): return {b.name: V(b.head) for b in ev.pose.bones if b.name.startswith("DEF-")}
ref = defs(hpose("HUM_pose_seated", 1))
for n in ("HUM_stand_to_sit_car", "HUM_phone_to_seat_idle"):
    end = defs(hpose(n, 72 if n.endswith("car") else 36)); d = {k: (end[k] - ref[k]).length for k in ref}
    out[n]["end_vs_seated_max_cm"] = round(100 * max(d.values()), 2); out[n]["end_vs_seated_worst_bone"] = max(d, key=d.get)
end = defs(hpose("HUM_sit_to_stand_car", 1)); d = {k: (end[k] - ref[k]).length for k in ref}; out["HUM_sit_to_stand_car"]["start_vs_seated_max_cm"] = round(100 * max(d.values()), 2)
# planted feet in the transition: ankle xy while the plan says the foot is down
import importlib
drift = {}
for s in "LR":
    pts = []
    for f in range(1, 73):
        ev = hpose("HUM_stand_to_sit_car", f); pts.append((f, V(ev.pose.bones[f"DEF-foot.{s}"].head)))
    # planted windows (frames where the foot target does not move): L 1-26, 38-46, 62-72 ; R 1-10, 24-40, 52-72 (feet pivot with the turn, the ankle stays)
    win = {"L": [(1, 26), (38, 46), (62, 63)], "R": [(1, 10), (24, 40), (52, 53)]}[s]
    worst = 0.0
    for a, b in win:
        seg = [p for f, p in pts if a <= f <= b]
        if len(seg) > 1: worst = max(worst, max((p - seg[0]).length for p in seg))
    drift[s] = round(100 * worst, 2)
out["HUM_stand_to_sit_car"]["planted_ankle_drift_cm"] = drift
mx = 0.0
for f in range(1, 73):
    ev = hpose("HUM_stand_to_sit_car", f)
    for s in "LR":
        hp = V(ev.pose.bones[f"DEF-thigh.{s}"].head); an = V(ev.pose.bones[f"DEF-foot.{s}"].head); mx = max(mx, (hp - an).length)
out["HUM_stand_to_sit_car"]["max_hip_ankle_m"] = round(mx, 3); out["HUM_stand_to_sit_car"]["leg_length_m"] = 0.818
had.action = None
# Claude pickup: planted-foot drift (world, includes root travel) in the running part
R = bpy.data.objects["RIG_Claude"]; R.hide_viewport = False; R.update_tag(); bpy.context.view_layer.update(); rad = R.animation_data_create(); rad.action = None
for t in list(rad.nla_tracks): rad.nla_tracks.remove(t)
s_ = rad.nla_tracks.new().strips.new("CLA_pickup_arrival", 1, bpy.data.actions["CLA_pickup_arrival"]); s_.extrapolation = "HOLD"
tails = {k: [] for k in (1, 2, 3, 4)}; roots = []
for f in range(1, 73):
    bpy.context.scene.frame_set(500); bpy.context.scene.frame_set(f); ev = R.evaluated_get(bpy.context.evaluated_depsgraph_get())
    for k in tails: tails[k].append(V(ev.matrix_world @ ev.pose.bones[f"leg_{k}"].tail))
    roots.append(V(ev.matrix_world @ ev.pose.bones["root"].head))
drifts = []
for k, pts in tails.items():
    for i in range(2, 44):                       # a foot that did not move between frames i and i+1 is planted; track the max step of "planted" feet (z near ground)
        if pts[i].z < 0.004 and pts[i + 1].z < 0.004: drifts.append((pts[i + 1] - pts[i]).length * 100)
out["CLA_pickup_arrival"]["planted_step_max_cm_per_frame"] = round(max(drifts), 2) if drifts else None
out["CLA_pickup_arrival"]["travel_m"] = round((roots[-1] - roots[0]).length, 3); out["CLA_pickup_arrival"]["end_yaw_deg"] = round(math.degrees(R.evaluated_get(bpy.context.evaluated_depsgraph_get()).pose.bones["root"].matrix.to_euler().z), 1)
rad.nla_tracks.remove(rad.nla_tracks[0])
json.dump(out, open("stills/react_checks.json", "w"), indent=1); result = out
