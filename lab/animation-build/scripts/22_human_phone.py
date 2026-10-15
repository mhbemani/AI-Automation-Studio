"""Phase 2 / milestone 2 (v2): phone actions built on the CREATOR'S holding-phone pose (scripts/phone_hold_pose.json, FK right arm, phone carried by the bone phone_hold.R).
HUM_pose_stand_phone (1, absolute pose asset), HUM_phone_raise (20), HUM_phone_hold_read (96 loop), HUM_phone_type (48 loop), HUM_phone_lower_pocket (30),
HUM_phone_show_claude (24), HUM_walk_texting (24 loop). The legs stay IK (planted feet); the arm is FK so it follows the body."""
import bpy, math, os, sys
SKIP_MAIN = True
ROOT = os.environ.get("ANIM_ROOT") or os.path.dirname(os.path.abspath(__import__("bpy").data.filepath))
exec(open(os.path.join(ROOT, "scripts", "20_human_locomotion.py")).read())
def bump(f, a, b): return math.sin(math.pi * (f - a) / (b - a)) ** 2 if a <= f <= b else 0.0
def idle_desc(f):
    ph = 2 * math.pi * ((f - 1) % 96) / 96; d = stand_desc()
    d["torso"] = (0.010 * math.sin(ph), 0.0, 0.004 * math.sin(2 * ph)); d["pelvis_yaw"] = 1.2 * math.sin(ph + .5); d["chest_yaw"] = -1.0 * math.sin(ph + .5)
    d["arm"] = {"L": 1.5 * math.sin(2 * ph + .5), "R": 0.0}
    return d
def holding(d, w=1.0, ops=(), local=()):
    d = dict(d); d["snap_w"] = w; d["ops"] = list(ops); d["local"] = list(local); d["arm"] = dict(d["arm"], R=0.0); d["elbow"] = dict(d["elbow"], R=0.0); return d
def main2():
    build_action("HUM_pose_stand_phone", [1], lambda f: holding(stand_desc()))
    build_action("HUM_phone_raise", list(range(1, 21)), lambda f: holding(idle_desc(1), w=(sm((f - 1) / 19.0), sm((f + 2) / 19.0))))      # hand leads by 3 frames: the phone is already turned when it rises (least face-on flash)
    def read(f):
        ph = 2 * math.pi * ((f - 1) % 96) / 96; sc_ = bump(f, 18, 30) + bump(f, 58, 70)
        return holding(idle_desc(f), ops=[("head", X, 1.2 * math.sin(2 * ph)), ("hand_fk.R", X, 1.0 * math.sin(2 * ph + 0.7))], local=[("thumb.02.R", 14 * sc_), ("thumb.03.R", 18 * sc_)])
    build_action("HUM_phone_hold_read", list(range(1, 98, 4)), lambda f: read(1 if f == 97 else f), cycles=True)
    TAPS = [3, 8, 12, 19, 24, 28, 35, 40, 44]
    def typ(f):
        ph = 2 * math.pi * ((f - 1) % 48) / 48; tap = max(bump(f, t - 2, t + 2) for t in TAPS)
        return holding(idle_desc(1 + (f - 1) * 2), ops=[("head", X, 0.8 * math.sin(ph)), ("hand_fk.R", X, -2.5 * tap)], local=[("thumb.02.R", 10 * tap), ("thumb.03.R", 24 * tap)])
    build_action("HUM_phone_type", list(range(1, 50, 2)), lambda f: typ(1 if f == 49 else f), cycles=True)
    build_action("HUM_phone_lower_pocket", list(range(1, 31)), lambda f: holding(idle_desc(1), w=(1 - sm((f - 1) / 22.0), 1 - sm((f + 2) / 22.0))))
    def show(f):
        t = sm((f - 1) / 18.0)
        return holding(idle_desc(1), ops=[("upper_arm_fk.R", Z, 26 * t), ("forearm_fk.R", Z, 12 * t), ("hand_fk.R", Z, 30 * t), ("head", Z, 22 * t), ("neck", Z, 8 * t), ("spine_fk.003", Z, 4 * t)])
    build_action("HUM_phone_show_claude", list(range(1, 25)), show)
    def wt(f):
        p = (f - 1) / 24; return holding(walk_desc(p % 1.0, 0.85), ops=[("head", X, 1.0 * math.sin(4 * math.pi * p))])
    build_action("HUM_walk_texting", list(range(1, 26)), wt, cycles=True)
    to_neutral()
    for s in "LR": rig.pose.bones[f"thigh_parent.{s}"]["IK_FK"] = 1.0; rig.pose.bones[f"upper_arm_parent.{s}"]["IK_FK"] = 1.0
    return sorted(a.name for a in bpy.data.actions if a.name.startswith(("HUM_phone", "HUM_walk_text", "HUM_pose_stand_phone")))
if "SKIP_MAIN2" not in globals(): result = main2()
