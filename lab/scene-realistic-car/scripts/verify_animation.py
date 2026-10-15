# Numeric checks of the animation against production/timeline.json. Run in the live Blender (bl.py file) or headless;
# prints a report and raises at the end if any check failed. Moves the current frame (restores frame 1).
import bpy, os, json, math
import numpy as np
from mathutils import Vector
exec(open(os.path.join(os.path.dirname(bpy.data.filepath), "scripts", "_anim_util.py")).read())
sc = bpy.context.scene; O = bpy.data.objects
out, bad = [], []
def check(name, ok, detail=""):
    out.append(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")
    if not ok: bad.append(name)

# 1. shots: markers match the timeline frame by frame; the active camera at the first and last frame of every shot
mk = sorted((m.frame, m.camera.name if m.camera else None) for m in sc.timeline_markers)
want = sorted((s["startFrame"], s["camera"]) for s in SHOTS)
check("markers == timeline shot starts and cameras", mk == want, f"{len(mk)} markers")
check("frame range 1..N at 24 fps", (sc.frame_start, sc.frame_end, sc.render.fps) == (1, N, FPS), f"{sc.frame_start}..{sc.frame_end} @ {sc.render.fps}")
wrong = []
for s in SHOTS:
    for f in (s["startFrame"], s["endFrame"] - 1):
        sc.frame_set(f)
        if sc.camera.name != s["camera"]: wrong.append((s["id"], f, sc.camera.name))
check("active camera correct at first/last frame of all 14 shots", not wrong, str(wrong))
sc.frame_set(1)
# 2. mirror keys at every interior cut
ma = O["CAR_RearViewMirror"].animation_data.action
fcs = [ma.fcurves.find("rotation_euler", index=i) for i in range(3)]
cuts = [s["startFrame"] for s in SHOTS if s["shot"] == "INT"]
have = [all(any(int(k.co[0]) == c for k in fc.keyframe_points) for fc in fcs) for c in cuts]
check("mirror aim key at every interior cut", all(have), f"{sum(have)}/{len(cuts)} cuts")
# 3. car: stationary 253..277, at the curb, within 0.3 m of the human
pos = {}
for f in (252, 253, 260, 270, 277):
    sc.frame_set(f); pos[f] = O["CAR_Exterior"].matrix_world.translation.copy()
check("car stationary frames 253-277", max((pos[f] - pos[253]).length for f in (253, 260, 270, 277)) < 1e-3, f"at {tuple(round(v,2) for v in pos[253])}")
check("car has come to rest at 253 (last step < 0.01 m)", (pos[252] - pos[253]).length < 0.01, f"step {(pos[252]-pos[253]).length:.4f} m")
sc.frame_set(CUES["car_stopped"])
door = O["CAR_Exterior"].matrix_world @ Vector((-0.48, 0.97, 0))        # rear-right seat / door position
hum = O["CHAR_Human_Street"].matrix_world.translation
check("human within 0.3 m (along the road) of the rear door at the curb", abs(door.x - hum.x) <= 0.3, f"door ({door.x:.2f},{door.y:.2f}) human ({hum.x:.2f},{hum.y:.2f}); lateral gap {abs(door.y-hum.y):.2f} m (curb to car side)")
# 4. speed profile smooth
et = O["CITY_DrivePath"].data.animation_data.action.fcurves.find("eval_time")
L = O["CITY_DrivePath"]["length_m"]
d = np.array([et.evaluate(f) / 100 for f in FRAMES]); v = np.diff(d) * FPS; a = np.diff(v) * FPS
check("speed never negative, ends at 8.5 m/s", v.min() > -1e-6 and abs(v[-1] - 8.5) < 0.01, f"min {v.min():.2f} end {v[-1]:.3f}")
check("no speed jump (max |accel| < 5 m/s2 = 0.5 g)", np.abs(a).max() < 5.0, f"max accel {np.abs(a).max():.2f} m/s2 at frame {int(np.abs(a).argmax())+2}")
j = np.diff(a) * FPS
check("smooth departure (jerk after drive_start < 8 m/s3)", np.abs(j[CUES['drive_start']:]).max() < 8, f"max jerk {np.abs(j[CUES['drive_start']:]).max():.2f}")
# 5. lap position: measured car travel between sample frames == commanded distance (follows the lane path, no jumps)
samples = (300, 400, 600, 800, 1000, 1200, 1335); P = {}
for f in samples:
    sc.frame_set(f); P[f] = O["CAR_Exterior"].matrix_world.translation.copy()
pts = [O["CITY_DrivePath"].matrix_world @ Vector(p.co[:3]) for p in O["CITY_DrivePath"].data.splines[0].points]
segl = np.array([(pts[(i + 1) % len(pts)] - pts[i]).length for i in range(len(pts))]); cum = np.concatenate([[0], np.cumsum(segl)])
def arclen(p):                                                          # arclength of the nearest point on the lane polyline
    best = (1e9, 0)
    for i in range(len(pts)):
        a_, b_ = pts[i], pts[(i + 1) % len(pts)]; t = max(0, min(1, (p - a_).dot(b_ - a_) / (b_ - a_).length_squared))
        dd = (a_ + (b_ - a_) * t - p).length
        if dd < best[0]: best = (dd, cum[i] + t * segl[i])
    return best
errs = []
for f in samples:
    dd, s_m = arclen(P[f]); exp = (d[f - 1]) % L
    errs.append((f, round(dd, 2), round(((s_m - exp + L / 2) % L) - L / 2, 2)))
check("car stays on the lane path and at the commanded arclength (+-0.5 m)", all(e[1] < 0.3 and abs(e[2]) < 0.5 for e in errs), f"(frame, off-path m, arclength err m): {errs}")
travel = d[-1] - d[CUES["drive_start"] - 1]
check("distance driven after drive_start", 330 < travel < 400, f"{travel:.1f} m in {(N - CUES['drive_start'] + 1) / FPS:.1f} s; end arclength {d[-1] % L:.1f} m of {L:.0f}")
# 6. visibility: seated human only in interior shots, street human/phone only before the first interior shot
FI = cuts[0]; vis = {}
for f in (FI - 1, FI):
    sc.frame_set(f); vis[f] = (O["CHAR_Human"].hide_render, O["CHAR_Human_Mesh"].hide_render, O["CHAR_Human_Street"].hide_render, O["PROP_Phone"].hide_render)
check("seated human hidden before the cut and shown from it", vis[FI - 1][:2] == (True, True) and vis[FI][:2] == (False, False), str(vis))
check("street human + phone shown until the cut and hidden after", vis[FI - 1][2:] == (False, False) and vis[FI][2:] == (True, True))
# 7. phone typing: visible characters follow the timeline formula
ph = TL["phone"]; bad_ph = []
for f in (ph["startFrame"] - 1, ph["startFrame"] + 1, ph["startFrame"] + 13, ph["typingEndFrame"], ph["sendFrame"] - 1, ph["sendFrame"]):
    sc.frame_set(f)
    shown = [o for o in O if o.name.startswith("PROP_Phone_Type_") and not o.hide_render]
    n_ = max((len(o.data.body.replace("\n", " ")) for o in shown), default=0) if f < ph["sendFrame"] else 0
    exp = 0 if f < ph["startFrame"] else min(len(ph["phoneText"]), int((f - ph["startFrame"]) * ph["charsPerSec"] / FPS)) if f < ph["sendFrame"] else 0
    sent = not O["PROP_Phone_Sent"].hide_render
    if n_ != exp or (sent != (f >= ph["sendFrame"])): bad_ph.append((f, n_, exp, sent))
check("typed characters follow the timeline formula; sent bubble from sendFrame", not bad_ph, str(bad_ph))
sc.frame_set(1)
out.append(f"\n{len(out) - len(bad)}/{len(out)} checks passed")
result = "\n".join(out)
if bad: raise AssertionError(result)
