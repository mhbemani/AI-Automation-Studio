"""Numeric checks of the human actions (bridge). Writes stills/human_action_checks.json."""
import bpy, json, math, os
ROOT = os.environ.get("ANIM_ROOT") or os.path.dirname(os.path.abspath(__import__("bpy").data.filepath))
EMO = ["neutral", "happy", "curious", "excited", "surprised", "thoughtful", "proud", "amused"]
EXPECT = {"HUM_seat_idle": 96, "HUM_talk_small": 48, "HUM_talk_nod": 14}
for e in EMO: EXPECT[f"HUM_emobody_{e}"] = 16
for t in ("phone", "claude", "road", "window", "monitor"): EXPECT[f"HUM_look_at_{t}"] = 10
LOOPS = ("HUM_seat_idle", "HUM_talk_small")
LIM = {"head": 75, "neck": 45, "spine": 35, "shoulder": 25, "f_": 100, "thumb": 100}
res = {"actions": {}, "problems": []}
rig = bpy.data.objects["RIG_Human"]
neutral = {n: [math.degrees(x) for x in __import__("mathutils").Matrix(m).to_euler('XYZ')] for n, m in json.loads(rig["neutral_pose"]).items()}
for name, length in EXPECT.items():
    a = bpy.data.actions.get(name)
    if not a: res["problems"].append("missing " + name); continue
    f0, f1 = a.frame_range; loop = name in LOOPS
    r = {"range": [int(f0), int(f1)], "length_ok": (int(f1 - f0) == length) if loop else (int(f1 - f0 + 1) == length), "fake_user": a.use_fake_user}
    worst_loop = 0.0; peaks = {}
    for fc in a.fcurves:
        bone = fc.data_path.split('"')[1]
        vals = [math.degrees(fc.evaluate(f)) for f in range(int(f0), int(f1) + 1)]
        pk = max(abs(v) for v in vals); peaks[bone] = max(peaks.get(bone, 0), round(pk, 1))
        if loop:
            worst_loop = max(worst_loop, abs(fc.evaluate(f0) - fc.evaluate(f1)))
            for f in range(int(f0), int(f1)): worst_loop = max(worst_loop, abs(fc.evaluate(f) - fc.evaluate(f + length)))
    over = {b: p for b, p in peaks.items() for k, l in LIM.items() if b.startswith(k) and p > l}
    r["peak_deg"] = {b: p for b, p in sorted(peaks.items(), key=lambda kv: -kv[1])[:4]}
    if loop: r["loop_max_diff_rad"] = round(worst_loop, 6)
    r["over_limit"] = over
    if not r["length_ok"] or over or (loop and worst_loop > 1e-3): res["problems"].append(name)
    res["actions"][name] = r
json.dump(res, open(os.path.join(ROOT, "stills", "human_action_checks.json"), "w"), indent=1)
result = {"problems": res["problems"], "n": len(res["actions"]), "loops": {n: res["actions"][n]["loop_max_diff_rad"] for n in LOOPS}}
