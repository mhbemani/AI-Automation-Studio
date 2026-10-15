#!/usr/bin/env python3
"""Aim + timing verification from the REAL evaluated rig (Blender pose + the real camera), independent of the solver's own maths.
usage: verify_performance.py --work ../pipeline/work/1 --aspect 16:9 [--out DIR] [--skip-blender]
 1. Blender (no render) evaluates the keyed pose for EVERY frame and projects hand wrist/tip, shoulders, eye and the face-normal point to video pixels
    (clip rect of that frame x real camera) -> verify_all_<tag>.json
 2. Aim: per point_at/track (and the other aimed gestures, informational) the perpendicular distance from the target pixel to the finger ray (wrist->tip, extended)
    at the apex (and mid-flight for track), plus the angle between finger direction and the direction to the target, and for gaze the 2D angle between the face
    direction and the direction to the target.
 3. Timing: per beat, the apex measured from the clip (extremum / arrival detectors on the measured hand/eye positions) vs the cue-word onset frame.
Writes aim_report_<tag>.json/.md and sync_report_<tag>.json (+ prints a summary)."""
import json, math, os, subprocess, sys, argparse
LAB = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ap = argparse.ArgumentParser(); ap.add_argument("--work", required=True); ap.add_argument("--aspect", default="16:9"); ap.add_argument("--out"); ap.add_argument("--skip-blender", action="store_true")
a = ap.parse_args(); tag = "16x9" if a.aspect == "16:9" else "9x16"; W = a.work; out = a.out or W
perf = json.load(open(f"{W}/performance_{tag}.json")); geom = json.load(open(f"{W}/geometry.json"))[a.aspect]; fps = perf["fps"]
if not a.skip_blender:
    json.dump({"frames": [{"frame": f, "rect": geom["rect"][f]} for f in range(perf["frames"])]}, open(f"{W}/verify_in_all_{tag}.json", "w"))
    cmd = [os.environ.get("BLENDER", "/Applications/Blender.app/Contents/MacOS/Blender"), "-b", f"{LAB}/character/facet.blend", "-P", f"{LAB}/character/render_performance.py", "--", "--perf", f"{W}/performance_{tag}.json",
           "--camera-cfg", f"{LAB}/pipeline/character.json", "--verify", f"{W}/verify_in_all_{tag}.json", "--verify-out", f"{W}/verify_all_{tag}.json", "--no-render"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode or "VERIFY" not in r.stdout: sys.exit("blender failed: " + (r.stdout + r.stderr)[-800:])
V = {r["frame"]: r for r in json.load(open(f"{W}/verify_all_{tag}.json"))["frames"]}
def d(p, q): return math.hypot(p[0] - q[0], p[1] - q[1])
def ang(v, w):
    n = math.hypot(*v) * math.hypot(*w); return 0.0 if n < 1e-9 else math.degrees(math.acos(max(-1, min(1, (v[0] * w[0] + v[1] * w[1]) / n))))
AIM = {"point_at", "track"}; AIMX = {"present", "offer", "hold_palm", "grip"}
rows = []
for b in perf["beats"]:
    if b["gesture"] not in AIM | AIMX: continue
    for label, f, tp in (("apex", b["apexFrame"], b["targetApex"]),) + ((("mid", b["midFrame"], b["targetMid"]),) if b["gesture"] == "track" else ()):
        v = V[f]; s = b["side"]; w, t_ = v["wrist_" + s], v["tip_" + s]; fd = (t_[0] - w[0], t_[1] - w[1]); to = (tp[0] - w[0], tp[1] - w[1])
        # finger ray miss distance (perpendicular distance of the target from the line through wrist and tip, target must be in front)
        L = math.hypot(*fd); miss = abs(fd[0] * to[1] - fd[1] * to[0]) / L if L > 1e-6 else 1e9
        # arm line (shoulder -> tip) for bent-hand gestures
        sh = v["shoulder_" + s]; ad = (t_[0] - sh[0], t_[1] - sh[1]); atg = (tp[0] - sh[0], tp[1] - sh[1]); La = math.hypot(*ad); miss_arm = abs(ad[0] * atg[1] - ad[1] * atg[0]) / La if La > 1e-6 else 1e9
        eye = v["eye"]; gd = (v["gaze_pt"][0] - eye[0], v["gaze_pt"][1] - eye[1]); tgd = (tp[0] - eye[0], tp[1] - eye[1])
        rows.append({"scene": b["scene"], "gesture": b["gesture"], "where": label, "frame": f, "target": b["target"], "hand": s, "target_px": [round(x, 1) for x in tp], "tip_px": [round(x, 1) for x in t_],
                     "finger_ray_miss_px": round(miss, 1), "finger_angle_deg": round(ang(fd, to), 1), "arm_ray_miss_px": round(miss_arm, 1), "gaze_angle_deg": round(ang(gd, tgd), 1), "strict": b["gesture"] in AIM, "reduced": bool(b.get("reduced"))})
strict = [r for r in rows if r["strict"]]
aim = {"aspect": a.aspect, "frameWidth": geom["width"], "rows": rows, "strict_count": len(strict),
       "strict_max_miss_px": max((r["finger_ray_miss_px"] for r in strict), default=None), "strict_mean_miss_px": round(sum(r["finger_ray_miss_px"] for r in strict) / max(1, len(strict)), 1),
       "strict_max_angle_deg": max((r["finger_angle_deg"] for r in strict), default=None), "strict_max_gaze_deg": max((r["gaze_angle_deg"] for r in strict), default=None),
       "strict_within_60px": sum(1 for r in strict if r["finger_ray_miss_px"] <= 60), "all_other_max_arm_miss_px": max((r["arm_ray_miss_px"] for r in rows if not r["strict"]), default=None)}
json.dump(aim, open(f"{out}/aim_report_{tag}.json", "w"), indent=1)
md = ["# Aim report %s (frame width %d px)\n" % (a.aspect, geom["width"]), "| scene | gesture | at | frame | target | hand | finger-ray miss px | finger angle deg | gaze angle deg |", "|---|---|---|---|---|---|---|---|---|"]
for r in rows: md.append("| %s | %s%s | %s | %d | %s | %s | %.0f%s | %.1f | %.1f |" % (r["scene"], r["gesture"], " (toned down)" if r["reduced"] else "", r["where"], r["frame"], r["target"], r["hand"], r["finger_ray_miss_px"], "" if r["strict"] else " (arm %.0f)" % r["arm_ray_miss_px"], r["finger_angle_deg"], r["gaze_angle_deg"]))
open(f"{out}/aim_report_{tag}.md", "w").write("\n".join(md) + "\n")

# ---- timing: measured apex from the rendered pose
def ser(key, i, f): return V[f][key][i]
def window(b, lo, hi): return range(max(0, b["apexFrame"] + int(round(lo * fps))), min(perf["frames"] - 1, b["apexFrame"] + int(round(hi * fps))) + 1)
def extremum(b, key, idx, mode, lo, hi): return (max if mode == "max" else min)(list(window(b, lo, hi)), key=lambda f: ser(key, idx, f))
def target_at(b, f):   # target pixel of this beat at frame f (static or moving packet), None for viewer/self
    sc = geom["scenes"][b["si"]]; kind, _, arg = b["target"].partition(":")
    if kind == "diagram": return sc["diagram"]
    if kind == "node": return sc["nodes"][arg]
    if kind == "text": l = sc["text"][int(arg)]; return [l["cx"], l["cy"]]
    if kind == "packet": pk = sc["packets"][int(arg)]; return pk["xy"][max(0, min(len(pk["xy"]) - 1, f - pk["startFrame"]))]
    return None
def miss_at(b, f, arm=False):
    v = V[f]; s = b["side"]; tp = target_at(b, f); p0 = v[("shoulder_" if arm else "wrist_") + s]; p1 = v["tip_" + s]
    fd = (p1[0] - p0[0], p1[1] - p0[1]); to = (tp[0] - p0[0], tp[1] - p0[1]); L = math.hypot(*fd)
    return abs(fd[0] * to[1] - fd[1] * to[0]) / L if L > 1e-6 else 1e9
def arrival(b, arm=False, thr=15.0):   # first frame from which the finger ray stays within thr px of the target for 3 frames (None = already on target when the lead-in starts: merged aims)
    f0 = max(0, b["apexFrame"] - int(round((b["lead"] + 0.2) * fps)))
    if miss_at(b, f0, arm) <= thr: return None
    for f in range(f0, min(perf["frames"] - 4, b["apexFrame"] + int(0.4 * fps))):
        if all(miss_at(b, k, arm) <= thr for k in range(f, f + 4)): return f
    return None
def reach(b, getter, lo_back, win=0.12, frac=0.95):
    f0 = max(0, b["apexFrame"] - int(lo_back * fps)); base = getter(f0); fa = range(b["apexFrame"], min(perf["frames"] - 1, b["apexFrame"] + int(win * fps)) + 1)
    peak = max(d(getter(f), base) for f in fa)
    if peak < 8: return None
    for f in range(f0, b["apexFrame"] + int(win * fps) + 1):
        if d(getter(f), base) >= frac * peak: return f
    return None
def settle(b, getter, win_lo, win_hi=0.2, frac=0.12):
    """the pose comes to rest: first frame after the speed peak of the approach at which the speed is <= frac of that peak (None = no clear approach, e.g. the arm was already there)"""
    f0 = max(1, b["apexFrame"] - int(round(win_lo * fps))); f1 = min(perf["frames"] - 2, b["apexFrame"] + int(round(win_hi * fps)))
    sp = {f: d(getter(f), getter(f - 1)) for f in range(f0, f1 + 1)}
    fp = max(sp, key=sp.get)
    if sp[fp] < 2.0 or fp > b["apexFrame"] + 2: return None
    for f in range(fp, f1 + 1):
        if sp[f] <= frac * sp[fp]: return f
    return None
sync = []
for b in perf["beats"]:
    g = b["gesture"]; s = b["side"] or "R"; m = None; how = ""
    lead = b["lead"] + 0.1
    if g in ("beat", "beat_repeat"): m = extremum(b, "tip_" + s, 1, "max", -0.07, 0.2); how = "lowest fingertip (strike)"
    elif g == "nod": m = extremum(b, "eye", 1, "max", -0.12, 0.25); how = "lowest eye (head down)"
    elif g == "shake_head": m = extremum(b, "eye", 0, "min", -0.15, 0.15); how = "first head-turn extreme"
    elif g in ("wave", "shrug"): m = extremum(b, "wrist_" + s, 1, "min", -0.15, 0.2); how = "highest wrist"
    elif g in AIM | AIMX | {"press", "point_viewer", "point_self"}: m = settle(b, lambda f: V[f]["tip_" + s], b["lead"] + 0.15); how = "fingertip comes to rest (speed <= 12% of its approach peak)"
    elif g == "lean_in": m = settle(b, lambda f: V[f]["eye"], lead + 0.2, 0.4); how = "eye comes to rest"
    elif g == "open_arms": m = settle(b, lambda f: V[f]["tip_R"], lead + 0.2, 0.25); how = "right hand comes to rest"
    onset = b["onsetFrame"]; sync.append({"scene": b["scene"], "gesture": g, "cue": b["cue"], "onsetFrame": onset, "solverApexFrame": b["apexFrame"], "measuredApexFrame": m, "method": how, "shifted_s": b.get("shift"),
                                          "errorFramesSolver": b["apexFrame"] - onset, "errorFramesMeasured": None if m is None else m - onset, "errorMsMeasured": None if m is None else round((m - onset) * 1000 / fps)})
meas = [x for x in sync if x["errorFramesMeasured"] is not None and not x["shifted_s"]]
st = {"beats": len(sync), "measured": len(meas), "solver_max_abs_frames": max(abs(x["errorFramesSolver"]) for x in sync if not x["shifted_s"]),
      "measured_mean_ms": round(sum(x["errorMsMeasured"] for x in meas) / max(1, len(meas)), 1), "measured_mean_abs_ms": round(sum(abs(x["errorMsMeasured"]) for x in meas) / max(1, len(meas)), 1), "measured_max_abs_ms": max((abs(x["errorMsMeasured"]) for x in meas), default=None),
      "measured_within_2_frames": sum(1 for x in meas if abs(x["errorFramesMeasured"]) <= 2), "shifted_beats": [x["scene"] for x in sync if x["shifted_s"]]}
json.dump({"aspect": a.aspect, "summary": st, "beats": sync}, open(f"{out}/sync_report_{tag}.json", "w"), indent=1)
print("AIM  strict beats %d: max miss %.0f px, mean %.1f px, max finger angle %.1f deg, max gaze angle %.1f deg, within 60px: %d/%d" % (len(strict), aim["strict_max_miss_px"], aim["strict_mean_miss_px"], aim["strict_max_angle_deg"], aim["strict_max_gaze_deg"], aim["strict_within_60px"], len(strict)))
print("SYNC", json.dumps(st))
