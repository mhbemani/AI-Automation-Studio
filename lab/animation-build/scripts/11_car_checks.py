"""Numeric checks of the car actions (bridge). Writes stills/car_action_checks.json."""
import bpy, json, math, os
ROOT = os.environ.get("ANIM_ROOT") or os.path.dirname(os.path.abspath(__import__("bpy").data.filepath))
R = 0.335
EXPECT = {"CAR_wheel_spin": 12, "CAR_steering_sway": 96, "CAR_steering_turn_left": 24, "CAR_steering_turn_right": 24, "CAR_door_open_L": 24, "CAR_door_open_R": 24, "CAR_door_close_L": 24, "CAR_door_close_R": 24}
LOOPS = ("CAR_wheel_spin", "CAR_steering_sway")
res = {"actions": {}, "problems": []}
for n, length in EXPECT.items():
    a = bpy.data.actions[n]; f0, f1 = a.frame_range; loop = n in LOOPS
    r = {"range": [int(f0), int(f1)], "length_ok": (int(f1 - f0) == length) if loop else (int(f1 - f0 + 1) == length), "fake_user": a.use_fake_user}
    for fc in a.fcurves:
        p = fc.data_path.split('"')[1]; vals = [fc.evaluate(f) for f in range(int(f0), int(f1) + 1)]
        r[p + "_min_max"] = [round(min(vals), 3), round(max(vals), 3)]
        if n == "CAR_wheel_spin":
            deg = [math.degrees(v / R) for v in vals]
            r["deg_per_frame"] = round(deg[1] - deg[0], 3); r["deg_total_one_loop"] = round(deg[-1] - deg[0], 3)
            r["next_cycle_increment_ok"] = abs((fc.evaluate(14) - fc.evaluate(13)) - (fc.evaluate(2) - fc.evaluate(1))) < 1e-6 and abs(fc.evaluate(25) - fc.evaluate(1) - 2 * 2 * math.pi * R) < 1e-4
            r["spoke_alias_ok(<36deg/frame)"] = r["deg_per_frame"] < 36
        if n == "CAR_steering_sway": r["loop_max_diff"] = max(abs(fc.evaluate(f) - fc.evaluate(f + 96)) for f in range(1, 97))
        if p.startswith("door"): r["door_range_ok"] = min(vals) >= -1e-6 and max(vals) <= 1.0 + 1e-6
        if p == "steer" and abs(max(vals, key=abs)) > 1: res["problems"].append(n + " steer>1")
    if not r["length_ok"]: res["problems"].append(n)
    if n.startswith("CAR_door") and not r["door_range_ok"]: res["problems"].append(n + " range")
    res["actions"][n] = r
json.dump(res, open(os.path.join(ROOT, "stills", "car_action_checks.json"), "w"), indent=1)
result = {"problems": res["problems"], "wheel": {k: res["actions"]["CAR_wheel_spin"][k] for k in ("deg_per_frame", "deg_total_one_loop", "next_cycle_increment_ok", "spoke_alias_ok(<36deg/frame)")}, "sway_loop_diff": res["actions"]["CAR_steering_sway"]["loop_max_diff"]}
