"""Phase 3 / milestone 3a: Claude's reactions and the pickup arrival, on ctrl props only.
CLA_react_proud_puff (24), CLA_react_oops (20), CLA_react_giggle (24 loop), CLA_pickup_arrival (72: runs 2.9 m toward -Y, brakes, turns 90 deg with move_y / yaw root props). Run via bridge after 04."""
import bpy, math, os
SKIP_MAIN40 = True
ROOT = os.environ.get("ANIM_ROOT") or os.path.dirname(os.path.abspath(__import__("bpy").data.filepath))
exec(open(os.path.join(ROOT, "scripts", "40_claude_locomotion.py")).read())
HAPPY = dict(eye_h_L=0.85, eye_h_R=0.85, eye_w=1.15, glint=1.5, blush=0.8, eye_y=-0.015)
def env(keys, f):
    """smooth interpolation through {frame: value}"""
    ks = sorted(keys)
    if f <= ks[0]: return keys[ks[0]]
    for a, b in zip(ks, ks[1:]):
        if f <= b: return keys[a] + (keys[b] - keys[a]) * sm((f - a) / (b - a))
    return keys[ks[-1]]
def blend_eyes(d, eyes, w):
    for k, v in eyes.items(): d[k] = DEFAULT[k] + (v - DEFAULT[k]) * w
# proud puff: stretches tall, chest out (leans back a little), arms out and up, blush, settle
def proud(f):
    w = env({1: 0, 8: 1, 17: 1, 24: 0}, f); s = env({1: 0, 6: 0.25, 10: 1, 17: 1, 24: 0}, f)
    d = dict(squash=-0.20 * w + 0.06 * (1 - w) * (f < 8), nod=-9 * w, arm_L=38 * s, arm_R=38 * s, arm_len_L=1.0 + 0.25 * s, arm_len_R=1.0 + 0.25 * s, arm_fwd_L=-8 * s, arm_fwd_R=-8 * s, hop=0.012 * s)
    blend_eyes(d, HAPPY, w); return d
build("CLA_react_proud_puff", {f: proud(f) for f in (1, 4, 6, 8, 10, 14, 17, 20, 24)})
# oops: sudden squash, damped wobble, eyes wide, arms flap up
def oops(f):
    t = max(0, f - 3) / 17.0; e = math.exp(-4.5 * t); sq = 0.4 * math.cos(11 * t) * e if f >= 3 else 0.4 * sm((f - 1) / 2.0)
    w = env({1: 0, 4: 1, 12: 0.8, 20: 0}, f)
    d = dict(squash=sq, lean=7 * math.sin(14 * t) * e if f >= 3 else 0, nod=-6 * w, arm_L=65 * w, arm_R=65 * w, arm_fwd_L=-10 * w, arm_fwd_R=-10 * w, hop=0.03 * w * max(0.0, math.sin(9 * t)) if f >= 3 else 0)
    blend_eyes(d, dict(eye_h_L=1.2, eye_h_R=1.2, eye_w=0.9, glint=1.3, blush=0.9), w); return d
build("CLA_react_oops", {f: oops(f) for f in range(1, 21)})
# giggle (24 loop): two quick bounces per cycle, squashing on landing, little shoulder-shake with the arms
def giggle(f):
    c = ((f - 1) % 24) / 24.0; b = abs(math.sin(2 * math.pi * 2 * c / 2 * 2)) if False else abs(math.sin(2 * math.pi * 2 * c))
    d = dict(hop=0.035 * b, squash=0.07 * (1 - b) - 0.05 * b, nod=3 + 2 * math.sin(4 * math.pi * c), lean=2.5 * math.sin(4 * math.pi * c + 1), arm_L=18 + 10 * (1 - b), arm_R=18 + 10 * (1 - b))
    blend_eyes(d, dict(HAPPY, eye_h_L=0.7, eye_h_R=0.7), 1.0); d["blush"] = 1.0; return d
build("CLA_react_giggle", {f: giggle(f) for f in range(1, 26)}, cycles=True)
# pickup arrival (72)
STRIDE_RUN = 0.571
def phase_cum(f):
    t = f - 1; v = lambda x: 1.0 if x >= 10 else sm(x / 10.0)
    # phase advances at v(t)*(1/16) cycles per frame; brakes between 40 and 52
    p = 0.0
    for i in range(0, t):
        x = i + 0.5; sp = (sm(x / 10.0) if x < 10 else 1.0) * (1 - sm((x - 40) / 12.0))
        p += sp / 16.0
    return p
def pickup(f):
    p = phase_cum(f); brake = sm((f - 44) / 12.0)
    g = plant(gait(p % 1.0, "run")[0])
    d = {}
    for k in set(g) | set(DEFAULT):
        if k.startswith("_"): continue
        gv = g.get(k, DEFAULT[k]); d[k] = gv + (DEFAULT[k] - gv) * brake if k in g and k not in ("bob",) else gv
    d["move_y"] = -STRIDE_RUN * p
    y = env({1: 0, 52: 0, 58: 1.0, 64: 1.06, 72: 1.0}, f); d["yaw"] = 90 * y
    d["turn"] = 14 * env({1: 0, 50: 0, 56: 1, 66: 1, 72: 0}, f) * (-1 if False else 1)
    d["squash"] = d.get("squash", 0) + 0.18 * env({1: 0, 46: 0, 50: 1, 56: 0}, f)      # braking squash
    d["nod"] = d.get("nod", 0) + 6 * env({1: 0, 46: 0, 50: 1, 58: 0}, f)
    blend_eyes(d, HAPPY, env({1: 0.5, 40: 0.5, 60: 1}, f)); return d
build("CLA_pickup_arrival", {f: pickup(f) for f in range(1, 73)})
result = {"travel_m": round(STRIDE_RUN * phase_cum(72), 3), "acts": sorted(a.name for a in bpy.data.actions if a.name.startswith(("CLA_react", "CLA_pickup")))}
