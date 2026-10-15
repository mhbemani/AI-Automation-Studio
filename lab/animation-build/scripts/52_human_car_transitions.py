"""Phase 3 / milestone 3c: HUM_stand_to_sit_car (72) and HUM_sit_to_stand_car (72, the same plan played backwards with a bigger duck). Absolute full-body actions in the seat frame
(origin = the seated rig origin; passenger door on his right = -X). He starts standing beside the door facing +X (psi 90), ducks, steps in with the right foot and then the left,
turns to face -Y while the left foot settles, and sits (pelvis clamped so no leg overstretches; planted feet never slide, they pivot). Legs stay IK, the last frames crossfade into
the FK seated legs (IK_FK 0 -> 1). Ends exactly on HUM_pose_seated. Run via bridge after 51 (needs the seated pose json)."""
import bpy, math, os, json
ROOT = os.environ.get("ANIM_ROOT") or os.path.dirname(os.path.abspath(__import__("bpy").data.filepath))
SKIP_MAIN = True
exec(open(os.path.join(ROOT, "scripts", "30_human_seated.py")).read().split("def main3")[0])
ANK = LL.ANKLE_H
S_TORSO = V(rig.data.bones["torso"].head_local) + V((0.0, 0.1, -0.40))        # seated pelvis (torso bone head), same offsets as build_seat_base
HIP = {s: V(rig.data.bones[f"DEF-thigh.{s}"].head_local) - V(rig.data.bones["torso"].head_local) for s in "LR"}
LEGLEN = (V(rig.data.bones["DEF-thigh.L"].tail_local) - V(rig.data.bones["DEF-thigh.L"].head_local)).length + (V(rig.data.bones["DEF-shin.L"].tail_local) - V(rig.data.bones["DEF-shin.L"].head_local)).length
FIN = {"L": (0.211, -0.178), "R": (-0.165, -0.104)}                           # seated ankle positions (measured on HUM_pose_seated)
def env(keys, f):
    ks = sorted(keys)
    if f <= ks[0]: return keys[ks[0]]
    for a, b in zip(ks, ks[1:]):
        if f <= b: return tuple(x + (y - x) * sm((f - a) / (b - a)) for x, y in zip(keys[a], keys[b])) if isinstance(keys[a], tuple) else keys[a] + (keys[b] - keys[a]) * sm((f - a) / (b - a))
    return keys[ks[-1]]
def step(f, a, b, p0, p1, h):
    """foot from p0 to p1 between frames a..b with an arc of height h; planted outside"""
    if f <= a: return p0, 0.0
    if f >= b: return p1, 0.0
    u = (f - a) / (b - a); s = sm(u)
    return (p0[0] + (p1[0] - p0[0]) * s, p0[1] + (p1[1] - p0[1]) * s), h * math.sin(math.pi * u)
RP0, LP0 = (-0.80, -0.15), (-0.80, 0.05); RP1, LP1 = (-0.42, -0.15), (-0.38, 0.05)
def plan(f, duck_k=1.0):
    P = env({1: (-0.80, -0.05), 10: (-0.80, -0.05), 26: (-0.60, -0.08), 40: (-0.40, -0.05), 56: (-0.12, 0.05), 72: (S_TORSO.x, S_TORSO.y)}, f)
    zp = env({1: 0.965, 10: 0.94, 26: 0.88, 40: 0.84, 56: 0.76, 72: S_TORSO.z}, f)
    psi = 90.0 if f <= 36 else 90.0 * (1 - sm((f - 36) / 30.0))
    Rf, Rl = step(f, 10, 24, RP0, RP1, 0.28); Rf, Rl = (Rf, Rl) if f < 40 else step(f, 40, 52, RP1, FIN["R"], 0.10)
    Lf, Ll = step(f, 26, 38, LP0, LP1, 0.25); Lf, Ll = (Lf, Ll) if f < 46 else step(f, 46, 62, LP1, FIN["L"], 0.15)
    feet = {"R": (Rf, Rl), "L": (Lf, Ll)}
    # the pelvis may not be higher than the legs allow (hip joint to the ankle target <= 0.97 leg length)
    ca, sa = math.cos(math.radians(psi)), math.sin(math.radians(psi)); zmax = zp
    for s, (pos, lift) in feet.items():
        h = HIP[s]; hx = P[0] + h.x * ca - h.y * sa; hy = P[1] + h.x * sa + h.y * ca
        dh = math.hypot(pos[0] - hx, pos[1] - hy); r = 0.97 * LEGLEN
        zm = (ANK + lift) + math.sqrt(max(r * r - dh * dh, 0.0)) - h.z
        zmax = min(zmax, zm)
    duck = (28 * env({1: 0, 10: 0.6, 26: 1.0, 40: 1.0, 56: 0.5, 72: 0.0}, f)) * duck_k
    arm_w = sm((f - 38) / 30.0); fk = sm((f - 64) / 8.0)
    return dict(P=P, z=zmax, psi=psi, feet=feet, duck=duck, arm_w=arm_w, fk=fk, lowered=zp - zmax)
ARMS = [f"{n}.{s}" for s in "LR" for n in ("shoulder", "upper_arm_fk", "forearm_fk", "hand_fk")] + FINGERS
def apply_car(d):
    to_neutral()
    psi = math.radians(d["psi"]); Zr = Matrix.Rotation(psi, 3, "Z")
    rot_world(rig, "torso", "Z", d["psi"])
    pb = rig.pose.bones["torso"]; M = pb.matrix.copy(); M.translation = V((d["P"][0], d["P"][1], d["z"])); pb.matrix = M; bpy.context.view_layer.update()
    ax = Zr @ V((1, 0, 0))
    for b, k in (("spine_fk.001", 0.25), ("spine_fk.002", 0.35), ("spine_fk.003", 0.40)): rot_world(rig, b, ax, d["duck"] * k)
    rot_world(rig, "neck", ax, -d["duck"] * 0.15); rot_world(rig, "head", ax, d["duck"] * 0.1)
    for s in "LR":
        (x, y), lift = d["feet"][s]
        bn = rig.data.bones[f"foot_ik.{s}"]; P = V(bn.head_local); Mrest = bn.matrix_local.copy(); off, dyaw = stance(s)
        delta = Matrix.Translation(V((x - P.x, y - P.y, lift))) @ Matrix.Translation(P) @ Matrix.Rotation(psi, 4, "Z") @ Matrix.Rotation(math.radians(-18 * min(1.0, lift / 0.1)), 4, "X") @ Matrix.Rotation(dyaw, 4, "Z") @ Matrix.Translation(-P)
        rig.pose.bones[f"foot_ik.{s}"].matrix = delta @ Mrest; bpy.context.view_layer.update()
        tb = rig.data.bones[f"toe_ik.{s}"]; Mt = tb.matrix_local.copy(); follow = delta @ Mt
        flat = (Matrix.Rotation(psi + dyaw, 3, "Z") @ Mt.to_3x3()).to_quaternion(); w = sm(1 - lift / 0.05)
        q = follow.to_quaternion().slerp(flat, w); T = Matrix.Translation(follow.translation + V((0, 0, 0))) @ q.to_matrix().to_4x4()
        rig.pose.bones[f"toe_ik.{s}"].matrix = T; bpy.context.view_layer.update()
    w = d["arm_w"]
    for b in ARMS:
        A = NEUTRAL[b]; B = SEAT[b]; q = A.to_quaternion().slerp(B.to_quaternion(), w); loc = A.translation.lerp(B.translation, w)
        rig.pose.bones[b].matrix_basis = Matrix.Translation(loc) @ q.to_matrix().to_4x4()
    for n in ("thigh_fk", "shin_fk", "foot_fk", "toe_fk"):
        for s in "LR": rig.pose.bones[f"{n}.{s}"].matrix_basis = SEAT[f"{n}.{s}"]
    for s in "LR": rig.pose.bones[f"thigh_parent.{s}"]["IK_FK"] = float(d["fk"]); rig.pose.bones[f"upper_arm_parent.{s}"]["IK_FK"] = 1.0
    rig.update_tag(); bpy.context.view_layer.update()
def build_car(name, frames, fn):
    global apply
    real = apply
    try:
        apply = lambda d: apply_car(d); return build_action(name, frames, fn)
    finally: apply = real
FR = list(range(1, 73))
build_car("HUM_stand_to_sit_car", FR, lambda f: plan(f))
build_car("HUM_sit_to_stand_car", FR, lambda f: plan(73 - f, duck_k=1.25))
to_neutral()
for s in "LR": rig.pose.bones[f"thigh_parent.{s}"]["IK_FK"] = 1.0; rig.pose.bones[f"upper_arm_parent.{s}"]["IK_FK"] = 1.0
result = {"leglen": round(LEGLEN, 3), "max_pelvis_lowering_m": round(max(plan(f)["lowered"] for f in FR), 3), "seat_pelvis": [round(x, 3) for x in S_TORSO]}
