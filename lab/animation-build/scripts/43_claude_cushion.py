"""Phase 3 / milestone 1b: Claude and his cushion, all on the ctrl properties (the cushion follows through its drivers, see 42_cushion_rig.py):
CLA_cushion_jump (60 loop, the lineup's jump), CLA_cushion_run_carry (16 loop, hugging the cushion), CLA_cushion_hold_to_throw (18), CLA_cushion_throw_and_jump (72: throws the
cushion to its resting place and jumps onto it), CLA_cushion_sit / _sleep / _happy_stand (96 loops), CLA_stand_to_cushion_sit (24). Run via bridge."""
import bpy, math, os
SKIP_MAIN40 = True
ROOT = os.environ.get("ANIM_ROOT") or os.path.dirname(os.path.abspath(__import__("bpy").data.filepath))
exec(open(os.path.join(ROOT, "scripts", "40_claude_locomotion.py")).read())
_build40 = build
def build(name, keys, **kw):
    for d in keys.values(): d["cus_show"] = 1.0       # the cushion is hidden by default (cus_show 0)
    return _build40(name, keys, **kw)
def idle_first():
    d = {}
    for fc in bpy.data.actions["CLA_idle"].fcurves: d[fc.data_path.split('"')[3]] = fc.evaluate(1)
    return d
def lerp(a, b, t): return a + (b - a) * t
HAPPY_EYES = dict(eye_h_L=0.85, eye_h_R=0.85, eye_w=1.15, glint=1.5, blush=0.8, eye_y=-0.015)
BASE = 0.215  # root height when standing on the cushion (cushion bottom on the ground)
def main2():
    log = {}
    # --- jump on the cushion (lineup keys: root height 0.21 -> crouch -0.109, jump +0.30, land -0.092, hop +0.12; squash from the scale keys)
    J = {1: (0.0, 0.0, 5, 0), 9: (-0.109, 0.4, -12, 8), 19: (0.30, -0.333, 85, -8), 29: (0.0, 0.0, 20, 0), 34: (-0.092, 0.333, -8, 5), 43: (0.12, -0.133, 55, -6), 51: (0.0, 0.0, 15, 0), 61: (0.0, 0.0, 5, 0)}
    build("CLA_cushion_jump", {f: dict(hop=BASE + h, squash=sq, arm_L=a, arm_R=a, nod=n, **HAPPY_EYES) for f, (h, sq, a, n) in J.items()}, cycles=True)
    # --- run carrying the cushion: the run gait, arms hugging the cushion in front of him
    keys = {}
    for f in range(1, 17):
        d = plant(gait(((f - 1) % 16) / 16, "run")[0])
        d.update(cus_held=1.0, arm_fwd_L=72, arm_fwd_R=72, arm_len_L=1.7, arm_len_R=1.7, arm_y_L=-0.08, arm_y_R=-0.08, arm_L=0, arm_R=0, nod=6 + 1.0 * math.sin(4 * math.pi * (f - 1) / 16))
        keys[f] = d
    keys[17] = dict(keys[1]); build("CLA_cushion_run_carry", keys, interp='LINEAR', cycles=True)
    # --- hold the cushion, wind up, release (18): ends with the cushion just leaving
    HOLD = dict(cus_held=1.0, arm_fwd_L=72, arm_fwd_R=72, arm_len_L=1.7, arm_len_R=1.7, arm_y_L=-0.08, arm_y_R=-0.08, nod=4)
    def throw_phase(f):
        """frames 1..18 of the wind-up and release: returns props."""
        if f <= 8:   t = sm((f - 1) / 7.0); return {**HOLD, "nod": 4 - 12 * t, "squash": 0.28 * t, "arm_fwd_L": 72 - 40 * t, "arm_fwd_R": 72 - 40 * t, "arm_len_L": 1.7 - 0.5 * t, "arm_len_R": 1.7 - 0.5 * t, "cus_tumble": -20 * t}
        t = sm((f - 8) / 10.0); return {**HOLD, "nod": -8 + 22 * t, "squash": 0.28 - 0.58 * t, "arm_fwd_L": 32 + 60 * t, "arm_fwd_R": 32 + 60 * t, "arm_len_L": 1.2 + 0.8 * t, "arm_len_R": 1.2 + 0.8 * t, "cus_toss": 0.10 * t, "cus_tumble": -20 + 40 * t, "cus_arc": 0.08 * t}
    build("CLA_cushion_hold_to_throw", {f: throw_phase(f) for f in range(1, 19)})
    # --- throw to the resting place and jump onto it (72)
    k = {}
    for f in range(1, 73):
        if f <= 18: d = throw_phase(f)
        else:
            u = sm((f - 18) / 16.0) if f <= 34 else 1.0                                   # flight of the cushion f18..34
            d = {**HOLD, "cus_toss": 0.10 + 0.90 * u, "cus_arc": 0.08 + 0.5 * math.sin(math.pi * min(1.0, (f - 18) / 16.0)), "cus_tumble": 20 + 340 * u,
                 "arm_fwd_L": 92 - 70 * sm((f - 18) / 10.0), "arm_fwd_R": 92 - 70 * sm((f - 18) / 10.0), "arm_len_L": 2.0 - 1.0 * sm((f - 18) / 10.0), "arm_len_R": 2.0 - 1.0 * sm((f - 18) / 10.0), "nod": 14 - 14 * sm((f - 18) / 10.0), "squash": -0.3 * (1 - sm((f - 18) / 8.0)), "arm_y_L": -0.08 * (1 - sm((f - 18) / 10.0)), "arm_y_R": -0.08 * (1 - sm((f - 18) / 10.0))}
            d["cus_held"] = 1.0
            if f >= 34: d["cus_arc"] = 0.0; d["cus_tumble"] = 360.0
            if 30 <= f < 38:                                                                 # crouch before the jump
                t = sm((f - 30) / 7.0); d.update(squash=0.4 * t, hop=-0.05 * t, nod=-4 * t, arm_L=-10 * t, arm_R=-10 * t, **{p: 0 for p in ()})
            if 38 <= f <= 56:                                                                # the jump: root travels to the cushion, arc in height
                u2 = (f - 38) / 18.0; d.update(jump_t=sm(u2), hop=0.34 * math.sin(math.pi * u2) - 0.05 * (1 - sm(u2 * 3)), squash=-0.3 * math.sin(math.pi * min(1.0, u2 * 1.2)) , arm_L=80 * math.sin(math.pi * u2), arm_R=80 * math.sin(math.pi * u2), nod=-6 * math.sin(math.pi * u2), **HAPPY_EYES)
            if f > 56:                                                                       # landing dip, settle, happy
                t = (f - 56) / 16.0; d.update(jump_t=1.0, hop=-0.085 * math.exp(-5 * t) * math.cos(8 * t), squash=0.45 * math.exp(-5 * t) * math.cos(8 * t), arm_L=20 * (1 - sm(t)), arm_R=20 * (1 - sm(t)), **HAPPY_EYES)
            if f > 38 and "hop" not in d: d["hop"] = 0.0
            d.setdefault("jump_t", 0.0 if f < 38 else 1.0)
        k[f] = d
    build("CLA_cushion_throw_and_jump", k)
    # --- sitting / sleeping / happy standing on the cushion (96 loops)
    def sit(f, sleep=False):
        ph = 2 * math.pi * ((f - 1) % 96) / 96
        d = dict(hop=BASE - 0.07, squash=0.06 + (0.05 * math.sin(2 * ph) if sleep else 0.02 * math.sin(2 * ph)), nod=(12 if sleep else 3), lean=1.0 * math.sin(ph), arm_L=-25, arm_R=-25, blush=0.4, eye_h_L=0.9, eye_h_R=0.9, glint=1.2)
        for kk in (1, 2, 3, 4): d.update({f"leg_rot_{kk}": 75, f"leg_len_{kk}": 0.75, f"leg_y_{kk}": -0.06})
        if sleep: d.update(eye_open=0.0, glint=0.0, nod=14 + 1.5 * math.sin(2 * ph))
        return d
    build("CLA_cushion_sit", {f: sit(f) for f in range(1, 98, 4)}, cycles=True)
    build("CLA_cushion_sleep", {f: sit(f, True) for f in range(1, 98, 4)}, cycles=True)
    def happy(f):
        c = ((f - 1) % 48) / 48
        d = dict(hop=BASE, bob=0.012 * abs(math.sin(2 * math.pi * c)), squash=0.04 * math.sin(4 * math.pi * ((f - 1) % 96) / 96), arm_L=22 + 10 * math.sin(2 * math.pi * c), arm_R=22 - 10 * math.sin(2 * math.pi * c), lean=3 * math.sin(2 * math.pi * ((f - 1) % 96) / 96))
        d.update(HAPPY_EYES); d["blush"] = 1.0; return d
    build("CLA_cushion_happy_stand", {f: happy(f) for f in range(1, 98, 4)}, cycles=True)
    a0 = idle_first(); a0['hop'] = BASE; s0 = sit(1); props = set(a0) | set(s0)
    build("CLA_stand_to_cushion_sit", {f: {p: lerp(a0.get(p, DEFAULT[p]), s0.get(p, DEFAULT[p]), sm((f - 1) / 18.0)) for p in props} for f in range(1, 25)})
    return sorted(a.name for a in bpy.data.actions if a.name.startswith(("CLA_cushion", "CLA_stand_to")))
result = main2()
