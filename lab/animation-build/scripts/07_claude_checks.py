"""Numeric checks of the Claude actions (run in Blender via bridge). result = dict -> also written to stills/claude_action_checks.json."""
import bpy, json, math, sys, os
ROOT = os.environ.get("ANIM_ROOT") or os.path.dirname(os.path.abspath(__import__("bpy").data.filepath))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
rig = bpy.data.objects["RIG_Claude"]; ctrl = rig.pose.bones["ctrl"]
UI = {k: ctrl.id_properties_ui(k).as_dict() for k in ctrl.keys()}
EXPECT = {"CLA_idle": 96, "CLA_blink": 6, "CLA_talk_pulse": 12, "CLA_look_around": 60}
for e in ["neutral", "happy", "curious", "excited", "surprised", "thoughtful", "proud", "amused"]:
    EXPECT[f"CLA_emoeyes_{e}"] = 8; EXPECT[f"CLA_emobody_{e}"] = 16
for d in ("left", "right", "up", "down", "camera"): EXPECT[f"CLA_look_{d}"] = 6
LOOPS = ("CLA_idle", "CLA_talk_pulse")
def prop(fc): return fc.data_path.split('"')[3]
res = {"actions": {}, "problems": []}
for name, length in EXPECT.items():
    a = bpy.data.actions.get(name)
    if not a: res["problems"].append(f"missing {name}"); continue
    f0, f1 = a.frame_range
    r = {"frames": int(f1 - f0 + 1), "range": [int(f0), int(f1)], "fake_user": a.use_fake_user}
    loop = name in LOOPS
    r["expected_length"] = length
    r["length_ok"] = (int(f1 - f0) == length) if loop else (int(f1 - f0 + 1) == length)
    worst = 0.0; outside = []
    for fc in a.fcurves:
        p = prop(fc); lo, hi = UI[p]["min"], UI[p]["max"]
        vals = [fc.evaluate(f) for f in range(int(f0), int(f1) + 1)]
        if min(vals) < lo - 1e-4 or max(vals) > hi + 1e-4: outside.append((p, round(min(vals), 3), round(max(vals), 3)))
        if loop:
            worst = max(worst, abs(fc.evaluate(f0) - fc.evaluate(f1)))
            # tiling: second cycle equals first
            for f in range(int(f0), int(f1)): worst = max(worst, abs(fc.evaluate(f) - fc.evaluate(f + length)))
    if loop: r["loop_max_diff"] = round(worst, 6)
    r["outside_range"] = outside
    if not r["length_ok"] or outside or (loop and worst > 1e-3): res["problems"].append(name)
    res["actions"][name] = r
# blink timing
a = bpy.data.actions["CLA_blink"]; fc = a.fcurves[0]
series = [round(fc.evaluate(f), 2) for f in range(1, 7)]
res["blink_eye_open"] = series; res["blink_closed_frames(<0.25)"] = sum(1 for v in series if v < 0.25)
# talk pulse follows a test envelope
import claude_talk; import importlib; importlib.reload(claude_talk)
env = [0.0] * 6 + [abs(math.sin(i * 0.7)) * (0.3 + 0.7 * ((i // 8) % 2)) for i in range(48)] + [0.0] * 6      # 60 samples at 24 /s
rig.animation_data_create(); old = rig.animation_data.action
tmp = bpy.data.actions.new("TMP_talk"); rig.animation_data.action = tmp
claude_talk.bake_talk(rig, env, start_frame=1, fps=24, env_rate=24)
errs = []; lag_best = None; resp = []
for i in range(len(env)):
    bpy.context.scene.frame_set(1 + i)
    e = rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
    sz = e.pose.bones["squash"].scale; zi = 1 if abs(sz[1] - 1) > abs(sz[2] - 1) else 2
    sc = max(sz, key=lambda x: abs(x - 1)) if False else None
    h = e.pose.bones["squash"].scale[1]            # bone Y is the height axis of squash (see 04)
    resp.append(h); expect = 1 - 0.3 * (0 - 0.22 * env[i]); errs.append(abs(h - expect))
res["talk_envelope_max_err"] = round(max(errs), 5)
def corr(lag): 
    xs = env[max(0, -lag):len(env) - max(0, lag)]; ys = resp[max(0, lag):len(resp) - max(0, -lag)]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys))
res["talk_best_lag_frames"] = max(range(-3, 4), key=corr)
rig.animation_data.action = old; bpy.data.actions.remove(tmp)
bpy.context.scene.frame_set(1)
for k, v in {kk: vv["default"] for kk, vv in UI.items()}.items(): ctrl[k] = float(v)
json.dump(res, open(os.path.join(ROOT, "stills", "claude_action_checks.json"), "w"), indent=1)
result = {"problems": res["problems"], "blink": res["blink_eye_open"], "talk_err": res["talk_envelope_max_err"], "lag": res["talk_best_lag_frames"], "n_actions": len(res["actions"]),
          "loops": {n: res["actions"][n]["loop_max_diff"] for n in LOOPS}}
