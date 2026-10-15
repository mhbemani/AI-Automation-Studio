"""Checks of the seated actions (bridge) -> stills/seated_checks.json: frame counts, loop closure, rotation limits, feet vs floor, head turn."""
import bpy, json, math, os
ROOT = os.environ.get("ANIM_ROOT") or os.path.dirname(os.path.abspath(__import__("bpy").data.filepath))
rig = bpy.data.objects["RIG_Human"]
for o in (rig, bpy.data.objects["HUM_Body"]): o.hide_viewport = False
EXPECT = {"HUM_pass_hands_lap": 96, "HUM_pass_turn_to_claude": 24, "HUM_pass_look_out_window": 120, "HUM_pass_lean_forward": 20, "HUM_talk_hand_gesture_a": 36}
LOOPS = ("HUM_pass_hands_lap", "HUM_pass_look_out_window", "HUM_talk_hand_gesture_a")
LIM = {"head": 75, "neck": 45, "spine": 35, "shoulder": 25}
res = {}
for n, length in EXPECT.items():
    a = bpy.data.actions[n]; f0, f1 = a.frame_range; loop = n in LOOPS
    r = {"range": [int(f0), int(f1)], "length_ok": (int(f1 - f0) == length) if loop else (int(f1 - f0 + 1) == length)}
    if loop: r["loop_max_diff"] = round(max(abs(fc.evaluate(f0) - fc.evaluate(f1)) for fc in a.fcurves), 6)
    over = {}
    for fc in a.fcurves:
        b = fc.data_path.split('"')[1]
        if fc.data_path.endswith("rotation_euler"):
            pk = max(abs(math.degrees(fc.evaluate(f))) for f in range(int(f0), int(f1) + 1))
            for k, l in LIM.items():
                if b.startswith(k) and pk > l: over[b] = round(pk, 1)
    r["over_limit"] = over
    rig.animation_data_create().action = a; bpy.context.scene.frame_set(500); zs = []; yaw = []
    for f in range(int(f0), int(f1) + 1, 2):
        bpy.context.scene.frame_set(f); e = rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
        zs += [e.pose.bones[f"DEF-foot.{s}"].head.z for s in "LR"]
        h = e.pose.bones["head"]; d = h.tail - h.head
        yaw.append(math.degrees(math.atan2(-(e.pose.bones["DEF-spine.006"].matrix.to_3x3().col[1].x), -e.pose.bones["DEF-spine.006"].matrix.to_3x3().col[1].y)))
    r["min_ankle_z"] = round(min(zs), 3); r["max_ankle_z"] = round(max(zs), 3)
    res[n] = r
rig.animation_data.action = None
json.dump(res, open(os.path.join(ROOT, "stills", "seated_checks.json"), "w"), indent=1)
bad = [n for n, r in res.items() if not r["length_ok"] or r["over_limit"] or r.get("loop_max_diff", 0) > 1e-3]
result = {"problems": bad, **{n: {k: v for k, v in r.items() if k in ("loop_max_diff", "min_ankle_z", "max_ankle_z")} for n, r in res.items()}}
