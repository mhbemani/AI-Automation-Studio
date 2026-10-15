"""Phase 2 / milestone 1: standing and walking (IK legs). Absolute full-body actions on RIG_Human (Euler XYZ keys, legs in IK mode):
HUM_stand_idle (96 loop), HUM_walk_cycle (24 loop, in place: the scene moves him 1.2 m per cycle), HUM_stand_to_walk (12, ends at walk phase 0),
HUM_walk_to_stand (12, starts at walk phase 0), HUM_stop_from_walk (18), HUM_walk_out_building (72, has root motion).
Run via bridge (cwd lab/animation-build). Idempotent."""
import bpy, math, sys, os, json
from mathutils import Matrix, Vector as V, Quaternion, Euler
ROOT = os.environ.get("ANIM_ROOT") or os.path.dirname(os.path.abspath(__import__("bpy").data.filepath))
exec(open(os.path.join(ROOT, "scripts", "rigtest_lib.py")).read())
sys.path.insert(0, os.path.join(ROOT, "scripts")); import importlib, locomotion_lib as LL; importlib.reload(LL)
rig = bpy.data.objects["RIG_Human"]; STRIDE = 1.2
exec(open(os.path.join(ROOT, "scripts", "phone_lib.py")).read())
rig = bpy.data.objects["RIG_Human"]
X, Y, Z = "X", "Y", "Z"
FINGERS = [f"{n}.{s}" for s in "LR" for n in [f"f_{f}.0{i}" for f in ("index", "middle", "ring", "pinky") for i in (1, 2, 3)] + [f"thumb.0{i}" for i in (1, 2, 3)]]
LIMBS = [f"{n}.{s}" for s in "LR" for n in ("upper_arm_fk", "forearm_fk", "hand_fk", "thigh_fk", "shin_fk", "foot_fk", "toe_fk")]
SPINE = ["torso", "hips", "spine_fk", "spine_fk.001", "spine_fk.002", "spine_fk.003", "neck", "head", "shoulder.L", "shoulder.R"]
IKB = [f"{n}.{s}" for s in "LR" for n in ("foot_ik", "toe_ik", "hand_ik")]
ALL = SPINE + LIMBS + FINGERS + IKB + ["root", "phone_hold.R"]
for n in ALL: rig.pose.bones[n].rotation_mode = 'XYZ'
# the creator's hand-edited holding-phone pose (scripts/phone_hold_pose.json): applied as a delta on top of the neutral pose, scaled by snap_w (0..1)
SNAP_FILE = os.path.join(ROOT, "scripts", "phone_hold_pose.json")
SNAP = {n: Matrix(m) for n, m in json.load(open(SNAP_FILE))["bones"].items()} if os.path.exists(SNAP_FILE) else {}
SNAP_BONES = ["shoulder.R", "upper_arm_fk.R", "forearm_fk.R", "hand_fk.R", "phone_hold.R", "spine_fk.001", "spine_fk.002", "spine_fk.003", "neck", "head"] + [f for f in FINGERS if f.endswith(".R")]
NEUTRAL = {n: Matrix(m) for n, m in json.loads(rig["neutral_pose"]).items()}
def to_neutral():
    for pb in rig.pose.bones: pb.matrix_basis = Matrix.Identity(4)
    for n, m in NEUTRAL.items(): rig.pose.bones[n].matrix_basis = m
    for s in "LR":
        rig.pose.bones[f"thigh_parent.{s}"]["IK_FK"] = 0.0; rig.pose.bones[f"upper_arm_parent.{s}"]["IK_FK"] = 1.0
    rig.update_tag(); bpy.context.view_layer.update()
sm = LL.sstep
# The scan's stance is not symmetric (hips centre x = 0.042; the right ankle is 7 cm behind its hip and the right foot toes out 30 deg,
# the left 6 deg). Walking and standing use a symmetric stance: ankles 3 cm outside each hip joint, both feet 6 deg toe-out.
TOE_OUT = 6.0
def stance(side):
    b = rig.data.bones; hip = V(b[f"DEF-thigh.{side}"].head_local); P = V(b[f"foot_ik.{side}"].head_local)
    sx = 1 if side == "L" else -1
    d = V(b[f"DEF-toe.{side}"].tail_local) - V(b[f"DEF-foot.{side}"].head_local)
    des = math.atan2(-math.cos(math.radians(TOE_OUT)), sx * math.sin(math.radians(TOE_OUT)) * -1 * -1) if False else None
    a_rest = math.atan2(d.y, d.x); a_des = math.atan2(-math.cos(math.radians(TOE_OUT)), sx * math.sin(math.radians(TOE_OUT)))
    return V((hip.x + sx * 0.03 - P.x, hip.y - P.y, 0.0)), a_des - a_rest
# ---------------- pose descriptors (pure data) and their application
def lerp(a, b, t): return a + (b - a) * t
def walk_desc(p, amp=1.0, stride=STRIDE):
    c = math.cos(2 * math.pi * p)
    d = {"foot": {}, "toe_w": {}}
    for s, ph in (("L", p % 1.0), ("R", (p + 0.5) % 1.0)):
        fwd, up, pitch = LL.foot(ph, stride, 0.24)
        if ph < LL.T_FLAT: w = sm(ph / LL.T_FLAT)
        elif ph < LL.T_TOEOFF: w = 1.0
        else: w = 1 - sm((ph - LL.T_TOEOFF) / (1 - LL.T_TOEOFF) / 0.4)
        d["foot"][s] = (fwd, up, pitch); d["toe_w"][s] = w
    d["torso"] = (0.02 * amp * math.sin(2 * math.pi * p), 0.0, -0.035 + 0.015 * amp * math.cos(4 * math.pi * (p - 0.3)))
    d["pelvis_yaw"] = -4.0 * amp * c; d["chest_yaw"] = 6.0 * amp * c; d["head_yaw"] = -3.0 * amp * c
    d["arm"] = {"L": 20.0 * amp * c, "R": -20.0 * amp * c}; d["elbow"] = {"L": -(18 - 10 * c * amp), "R": -(18 + 10 * c * amp)}
    return d
def stand_desc():
    return {"foot": {s: (0.0, LL.ANKLE_H, 0.0) for s in "LR"}, "toe_w": {s: 1.0 for s in "LR"}, "torso": (0.0, 0.0, 0.0), "pelvis_yaw": 0.0, "chest_yaw": 0.0, "head_yaw": 0.0,
            "arm": {"L": 0.0, "R": 0.0}, "elbow": {"L": 0.0, "R": 0.0}}
def mix(a, b, t):
    if isinstance(a, dict): return {k: mix(a[k], b[k], t) for k in a}
    if isinstance(a, tuple): return tuple(lerp(x, y, t) for x, y in zip(a, b))
    return lerp(a, b, t)
def apply(d, extra=None):
    to_neutral()
    x, y, z = d["torso"]; move_world(rig, "torso", (x, y, z))
    rot_world(rig, "spine_fk", Z, d["pelvis_yaw"])
    for b, k in (("spine_fk.001", 0.17), ("spine_fk.002", 0.41), ("spine_fk.003", 0.42)): rot_world(rig, b, Z, d["chest_yaw"] * k)
    rot_world(rig, "head", Z, d["head_yaw"])
    for s in "LR":
        rot_world(rig, f"upper_arm_fk.{s}", X, d["arm"][s]); rot_world(rig, f"forearm_fk.{s}", X, d["elbow"][s])
        fwd, up, pitch = d["foot"][s]
        pb = rig.pose.bones[f"foot_ik.{s}"]; bn = rig.data.bones[f"foot_ik.{s}"]
        P = V(bn.head_local); Mrest = bn.matrix_local.copy()
        off, dyaw = stance(s)
        delta = Matrix.Translation(off + V((0, -fwd, up - LL.ANKLE_H))) @ Matrix.Translation(P) @ Matrix.Rotation(math.radians(-pitch), 4, "X") @ Matrix.Rotation(dyaw, 4, "Z") @ Matrix.Translation(-P)
        pb.matrix = delta @ Mrest; bpy.context.view_layer.update()
        tb = rig.data.bones[f"toe_ik.{s}"]; Mt = tb.matrix_local.copy(); follow = delta @ Mt
        flat = (Matrix.Rotation(dyaw, 3, "Z") @ Mt.to_3x3()).to_quaternion()      # flat on the ground, with the yaw correction
        q = follow.to_quaternion().slerp(flat, d["toe_w"][s])
        T = Matrix.Translation(follow.translation) @ q.to_matrix().to_4x4()
        rig.pose.bones[f"toe_ik.{s}"].matrix = T; bpy.context.view_layer.update()
    if "snap_w" in d: apply_snap(d["snap_w"])
    for b, ax, deg in d.get("ops", []): rot_world(rig, b, ax, deg)
    for b, deg in d.get("local", []):
        pb = rig.pose.bones[b]; pb.rotation_mode = 'XYZ'; e = pb.rotation_euler.copy(); e[0] += math.radians(deg); pb.rotation_euler = e
    if "phone" in d:                      # right hand holds the phone: IK arm blended by w (1 = fully IK)
        ph = d["phone"]; tx, ty, tz = d["torso"]
        pos = (ph["pos"][0] + tx, ph["pos"][1] + ty, ph["pos"][2] + tz)
        set_hand_ik(phone_matrix(pos, ph.get("eyes", (0.04, 0.0, 1.62))))
        rig.pose.bones["upper_arm_parent.R"]["IK_FK"] = 1.0 - ph["w"]
    rig.update_tag(); bpy.context.view_layer.update()
    if extra: extra()
HAND_GROUP = ("hand_fk.R", "phone_hold.R") + tuple(f for f in FINGERS if f.endswith(".R"))
def apply_snap(w):
    """w = weight 0..1, or (w_arm, w_hand) to stagger the arm/body and the hand/fingers/phone."""
    for b in SNAP_BONES:
        wb = (w[1] if b in HAND_GROUP else w[0]) if isinstance(w, tuple) else w
        pb = rig.pose.bones[b]; Nb = NEUTRAL.get(b, Matrix.Identity(4)); S = SNAP.get(b, Nb)
        delta = Nb.inverted() @ S
        q = Quaternion((1, 0, 0, 0)).slerp(delta.to_quaternion(), wb)
        pb.matrix_basis = pb.matrix_basis @ (Matrix.Translation(delta.translation * wb) @ q.to_matrix().to_4x4())
    bpy.context.view_layer.update()
# ---------------- capture + key
def values(prev=None):
    out = {}
    for n in ALL:
        pb = rig.pose.bones[n]; m = pb.matrix_basis
        e = m.to_euler('XYZ', Euler(prev[n][1], 'XYZ')) if prev else m.to_euler('XYZ')      # continuous with the previous frame (no +-pi flips)
        out[n] = (tuple(m.translation), tuple(e))
    out["_ikfk"] = {p: rig.pose.bones[p]["IK_FK"] for p in ("thigh_parent.L", "thigh_parent.R", "upper_arm_parent.L", "upper_arm_parent.R")}
    return out
def build_action(name, frames, desc_fn, cycles=False, root_fn=None):
    old = bpy.data.actions.get(name)
    if old: bpy.data.actions.remove(old)
    a = bpy.data.actions.new(name); a.use_fake_user = True
    if rig.animation_data is None: rig.animation_data_create()
    rig.animation_data.action = a
    series = {}; prev_f = None
    for f in frames:
        apply(desc_fn(f))
        if root_fn:
            rig.pose.bones["root"].location = root_fn(f); rig.update_tag(); bpy.context.view_layer.update()
        series[f] = values(series[prev_f] if prev_f in series else None); prev_f = f
    first, last = frames[0], frames[-1]
    props_series = {f: series[f].pop("_ikfk") for f in frames}
    for n in ALL:
        var_loc = any(max(abs(series[f][n][0][i] - series[first][n][0][i]) for i in range(3)) > 1e-5 for f in frames)
        var_rot = any(max(abs(series[f][n][1][i] - series[first][n][1][i]) for i in range(3)) > 1e-5 for f in frames)
        pb = rig.pose.bones[n]
        for f in (frames if (var_loc or var_rot) else [first, last]):
            loc, eul = series[f][n]
            pb.rotation_euler = eul; pb.location = loc
            if var_rot or not var_loc: pb.keyframe_insert("rotation_euler", frame=f, group=n)
            if var_loc or n in ("torso", "foot_ik.L", "foot_ik.R", "root"): pb.keyframe_insert("location", frame=f, group=n)
    for p in ("thigh_parent.L", "thigh_parent.R", "upper_arm_parent.L", "upper_arm_parent.R"):
        vary = any(abs(props_series[f][p] - props_series[first][p]) > 1e-6 for f in frames)
        for f in (frames if vary else [first, last]):
            rig.pose.bones[p]["IK_FK"] = float(props_series[f][p]); rig.pose.bones[p].keyframe_insert('["IK_FK"]', frame=f)
    for fc in a.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'
        if cycles: fc.modifiers.new('CYCLES')
    rig.animation_data.action = None
    return a, series
def main():
    log = {}
    # stand idle (96 loop, key every 4)
    def idle(f):
        ph = 2 * math.pi * ((f - 1) % 96) / 96; d = stand_desc()
        d["torso"] = (0.010 * math.sin(ph), 0.0, 0.004 * math.sin(2 * ph)); d["pelvis_yaw"] = 1.2 * math.sin(ph + .5); d["chest_yaw"] = -1.0 * math.sin(ph + .5); d["head_yaw"] = 1.5 * math.sin(ph + 1)
        d["arm"] = {"L": 1.5 * math.sin(2 * ph + .5), "R": 1.5 * math.sin(2 * ph + .9)}
        return d
    build_action("HUM_stand_idle", list(range(1, 98, 4)), idle, cycles=True)
    # walk cycle 24 loop, key every frame 1..25
    build_action("HUM_walk_cycle", list(range(1, 26)), lambda f: walk_desc((f - 1) / 24), cycles=True)
    # stand -> walk (12) / walk -> stand (12)
    build_action("HUM_stand_to_walk", list(range(1, 13)), lambda f: mix(stand_desc(), walk_desc(0.0), sm((f - 1) / 11)))
    build_action("HUM_walk_to_stand", list(range(1, 13)), lambda f: mix(walk_desc(0.0), stand_desc(), sm((f - 1) / 11)))
    # stop from walk (18): speed ramps down (phase time-warp), the last 6 frames gather the feet
    def stop(f):
        q = (f - 1) / 17; p = 0.5 * (1 - (1 - q) ** 2) * (17 / 24); amp = 1 - 0.7 * q
        d = walk_desc(p, amp); return mix(d, stand_desc(), sm((f - 12) / 6)) if f > 12 else d
    build_action("HUM_stop_from_walk", list(range(1, 19)), stop)
    # walk out of the building (72): accelerate over 24 frames, then steady; root motion forward (-Y)
    def pcum(f):                                   # phase (cycles) with speed ramping 0 -> 1 cycle/s over the first second
        t = (f - 1) / 24.0
        return 0.5 * t * t if t < 1 else 0.5 + (t - 1)
    def out(f):
        p = pcum(f); return mix(stand_desc(), walk_desc(p, 1.0), sm((f - 1) / 12))
    build_action("HUM_walk_out_building", list(range(1, 73)), out, root_fn=lambda f: (0.0, -STRIDE * pcum(f), 0.0))
    to_neutral()
    for s in "LR": rig.pose.bones[f"thigh_parent.{s}"]["IK_FK"] = 1.0
    return sorted(a.name for a in bpy.data.actions if a.name in ("HUM_stand_idle", "HUM_walk_cycle", "HUM_stand_to_walk", "HUM_walk_to_stand", "HUM_stop_from_walk", "HUM_walk_out_building"))
if "SKIP_MAIN" not in globals(): result = main()
