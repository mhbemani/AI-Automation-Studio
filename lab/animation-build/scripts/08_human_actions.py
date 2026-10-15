"""Milestone 6: human actions on RIG_Human (faceless, silver). Everything is Euler XYZ keys on the FK controls so actions can be
layered with the NLA (COMBINE adds the Euler values).
  HUM_pose_neutral   the creator's neutral standing pose (absolute, base layer)
  HUM_pose_seated    neutral upper body + seated legs/torso (absolute, base layer for the preview / car seat; not in the list)
  deltas (relative to the base pose, layer on top): HUM_seat_idle (96 loop), HUM_emobody_<8> (16, pose), HUM_talk_small (48 loop),
  HUM_talk_nod (14), HUM_look_at_<phone|claude|road|window|monitor> (10, pose)
Axes used when authoring (world, rest pose, he faces -Y, his left = +X): X + = nod forward, Y + = tilt to his left, Z + = turn to his left.
Run via bridge (cwd lab/animation-build). Idempotent."""
import bpy, json, math, sys, os
from mathutils import Matrix, Vector as V, Euler
ROOT = os.environ.get("ANIM_ROOT") or os.path.dirname(os.path.abspath(__import__("bpy").data.filepath))
exec(open(os.path.join(ROOT, "scripts", "rigtest_lib.py")).read())
rig = bpy.data.objects["RIG_Human"]
X, Y, Z = "X", "Y", "Z"
FINGERS = [f"{n}.{s}" for s in "LR" for n in [f"f_{f}.0{i}" for f in ("index", "middle", "ring", "pinky") for i in (1, 2, 3)] + [f"thumb.0{i}" for i in (1, 2, 3)]]
MASTERS = [f"{n}_master.{s}" for s in "LR" for n in ("f_index.01", "f_middle.01", "f_ring.01", "f_pinky.01", "thumb.01")]
UPPER = ["spine_fk.001", "spine_fk.002", "spine_fk.003", "neck", "head", "shoulder.L", "shoulder.R"]
LIMBS = [f"{n}.{s}" for s in "LR" for n in ("upper_arm_fk", "forearm_fk", "hand_fk", "thigh_fk", "shin_fk", "foot_fk", "toe_fk")]
BASE = ["torso", "hips", "spine_fk"] + UPPER + LIMBS + FINGERS

def setmode(names):
    for n in names: rig.pose.bones[n].rotation_mode = 'XYZ'
setmode(BASE + MASTERS)

def clear_pose():
    for pb in rig.pose.bones: pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()

def neutral_mats():
    return {n: Matrix(m) for n, m in json.loads(rig["neutral_pose"]).items()}
NEUTRAL = neutral_mats()
def to_neutral():
    clear_pose()
    for n, m in NEUTRAL.items(): rig.pose.bones[n].matrix_basis = m
    bpy.context.view_layer.update()

def new_action(name):
    old = bpy.data.actions.get(name)
    if old: bpy.data.actions.remove(old)
    a = bpy.data.actions.new(name); a.use_fake_user = True
    if rig.animation_data is None: rig.animation_data_create()
    rig.animation_data.action = a
    return a
def finish(a, interp='BEZIER', cycles=False):
    for fc in a.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = interp
        if cycles: fc.modifiers.new('CYCLES')
    rig.animation_data.action = None

def key_values(frame, vals):
    """vals: {bone: (loc3 or None, euler3)}"""
    for b, (loc, eul) in vals.items():
        pb = rig.pose.bones[b]; pb.rotation_mode = 'XYZ'
        pb.rotation_euler = eul; pb.keyframe_insert("rotation_euler", frame=frame, group=b)
        if loc is not None: pb.location = loc; pb.keyframe_insert("location", frame=frame, group=b)

# ---------------- absolute base poses
def abs_vals(bones):
    out = {}
    for b in bones:
        m = rig.pose.bones[b].matrix_basis; out[b] = (tuple(m.translation) if b == "torso" else None, tuple(m.to_euler('XYZ')))
    return out
def solve_hand(side, target, iters=60):
    """put the hand of FK arm `side` at `target` (armature space) by coordinate descent on the FK euler angles."""
    names = [f"upper_arm_fk.{side}", f"forearm_fk.{side}"]
    for n in names: rig.pose.bones[n].rotation_mode = 'XYZ'
    def err():
        bpy.context.view_layer.update()
        h = rig.evaluated_get(bpy.context.evaluated_depsgraph_get()).pose.bones[f"DEF-hand.{side}"].head
        return (V(h) - V(target)).length
    step = math.radians(8); best = err()
    for it in range(iters):
        improved = False
        for n in names:
            pb = rig.pose.bones[n]
            for ax in range(3):
                for sgn in (1, -1):
                    e = pb.rotation_euler.copy(); e[ax] += sgn * step; old = pb.rotation_euler.copy(); pb.rotation_euler = e
                    v = err()
                    if v < best - 1e-5: best = v; improved = True
                    else: pb.rotation_euler = old
        if not improved:
            step *= 0.5
            if step < math.radians(0.3): break
    return best

def build_base():
    to_neutral()
    a = new_action("HUM_pose_neutral"); key_values(1, abs_vals(BASE)); finish(a)
    to_neutral()
    move_world(rig, "torso", (0, 0.1, -0.40))
    for s in "LR":
        rot_world(rig, f"thigh_fk.{s}", X, -90); rot_world(rig, f"shin_fk.{s}", X, 90)
    bpy.context.view_layer.update()
    for s_, sx in (("L", 1), ("R", -1)):
        solve_hand(s_, (0.042 + sx * 0.10, -0.12, 0.635))
    a = new_action("HUM_pose_seated"); key_values(1, abs_vals(BASE)); finish(a)
    to_neutral()

# ---------------- deltas
AMP = 1.6   # the creator's faceless human needs readable body language at two-shot size
def delta_from_ops(ops, extra_master=None, amp=None):
    """apply world-axis ops on top of the neutral pose; return {bone: euler delta (local, relative to neutral)}."""
    to_neutral()
    N = {b: rig.pose.bones[b].matrix_basis.copy() for b in UPPER + MASTERS}
    amp = AMP if amp is None else amp
    for bone, ax, deg in ops:
        if ax != "local": deg = deg * amp
        if ax == "local": pb = rig.pose.bones[bone]; pb.rotation_mode = 'XYZ'; e = pb.rotation_euler.copy(); e[0] += math.radians(deg); pb.rotation_euler = e; bpy.context.view_layer.update()
        else: rot_world(rig, bone, ax, deg)
    out = {}
    for b in UPPER + MASTERS:
        q = N[b].inverted() @ rig.pose.bones[b].matrix_basis
        e = q.to_euler('XYZ'); 
        if max(abs(x) for x in e) > 1e-5: out[b] = tuple(e)
    to_neutral()
    return out

def shoulder_up(side, deg): return (f"shoulder.{side}", Y, -deg if side == "L" else deg)
def fingers(deg): return [(m, "local", deg) for m in MASTERS]

PROFILE_DEFAULT = {1: 0.0, 3: -0.08, 9: 1.12, 12: 0.97, 16: 1.0}
EMO = {   # ops are (bone, axis, degrees); see the axes in the header; profile = {frame: factor}
 "neutral":    ([], PROFILE_DEFAULT),
 "happy":      ([("spine_fk.001", X, -3), ("spine_fk.003", X, -6), ("neck", X, -5), ("head", X, -9), ("head", Y, 5), shoulder_up("L", 2), shoulder_up("R", 2)], {1: 0, 3: -0.05, 10: 1.15, 13: 0.98, 16: 1.0}),
 "curious":    ([("spine_fk.002", X, 3), ("spine_fk.003", X, 3), ("neck", Z, 6), ("head", Z, 10), ("head", Y, 8), ("head", X, 4)], {1: 0, 6: 0.0, 8: 0.4, 14: 1.05, 16: 1.0}),
 "excited":    ([("spine_fk.001", X, 5), ("spine_fk.002", X, 5), ("spine_fk.003", X, -5), ("neck", Z, 6), ("head", Z, 16), ("head", X, -7), shoulder_up("L", 5), shoulder_up("R", 5)] + fingers(-25), {1: 0, 4: -0.1, 8: 1.2, 11: 0.96, 16: 1.0}),
 "surprised":  ([("spine_fk.002", X, -4), ("neck", X, -4), ("head", X, -6), shoulder_up("L", 6), shoulder_up("R", 6)] + fingers(-35), {1: 0, 4: 1.2, 8: 0.95, 16: 1.0}),
 "thoughtful": ([("spine_fk.003", X, 3), ("neck", X, 4), ("head", X, 10), ("head", Z, -15)], {1: 0, 8: 0.7, 16: 1.0}),
 "proud":      ([("spine_fk.001", X, -2), ("spine_fk.003", X, -6), ("neck", X, -2), ("head", X, -5), shoulder_up("L", -2), shoulder_up("R", -2)], {1: 0, 8: 0.85, 16: 1.0}),
 "amused":     ([("spine_fk.003", X, 3), ("head", X, 9), ("head", Z, 9), ("head", Y, -5), shoulder_up("L", 6), shoulder_up("R", 6)], {1: 0, 3: 1.25, 5: 0.9, 7: 1.12, 9: 1.0, 16: 1.0}),
}
LOOKS = {   # profile {1: 0, 6: 1.1, 10: 1.0}
 "road":    [("head", X, -4)],
 "claude":  [("spine_fk.003", Z, 8), ("neck", Z, 17), ("head", Z, 30), ("head", Y, 3)],
 "window":  [("spine_fk.003", Z, -10), ("neck", Z, -22), ("head", Z, -35)],
 "phone":   [("spine_fk.003", X, 6), ("neck", X, 12), ("head", X, 28)],
 "monitor": [("neck", Z, 6), ("head", Z, 12), ("head", X, 7)],
}
def scaled(delta, k): return {b: (None, tuple(x * k for x in e)) for b, e in delta.items()}
def build_pose_action(name, delta, profile, nframes):
    a = new_action(name)
    for f, k in sorted(profile.items()): key_values(f, scaled(delta, k) if delta else {b: (None, (0, 0, 0)) for b in ("head",)})
    finish(a); a["frames"] = f"1-{nframes}"
def build_all_poses():
    for e, (ops, prof) in EMO.items():
        d = delta_from_ops(ops)
        build_pose_action(f"HUM_emobody_{e}", d, prof, 16)
    for t, ops in LOOKS.items():
        d = delta_from_ops(ops)
        build_pose_action(f"HUM_look_at_{t}", d, {1: 0, 6: 1.1, 10: 1.0}, 10)

def ed(**k): return k
def build_loops():
    # HUM_seat_idle: 96 frame loop, keys every 4
    a = new_action("HUM_seat_idle")
    for f in range(1, 98, 4):
        ph = 2 * math.pi * ((f - 1) % 96) / 96; r = math.radians
        d = {"spine_fk.001": (r(0.6 * math.sin(2 * ph)), r(1.2 * math.sin(ph + .3)), 0), "spine_fk.002": (r(0.9 * math.sin(2 * ph + .2)), 0, 0), "spine_fk.003": (r(1.1 * math.sin(2 * ph + .4)), 0, r(0.8 * math.sin(ph + 2))),
             "neck": (r(0.4 * math.sin(2 * ph + .9)), 0, r(0.6 * math.sin(ph))), "head": (r(0.8 * math.sin(2 * ph + .9) + 0.5 * math.sin(ph)), r(1.5 * math.sin(ph + 1)), r(1.2 * math.sin(ph))),
             "shoulder.L": (0, r(-0.9 * math.sin(2 * ph + .5)), 0), "shoulder.R": (0, r(0.9 * math.sin(2 * ph + .5)), 0)}
        key_values(f, {b: (None, e) for b, e in d.items()})
    finish(a, cycles=True)
    # HUM_talk_small: 48 loop (periods 12/24/48), keys every 3
    a = new_action("HUM_talk_small")
    for f in range(1, 50, 3):
        t = (f - 1); r = math.radians; w = lambda p: 2 * math.pi * t / p
        hx = 2.5 * math.sin(w(12)) + 1.5 * math.sin(w(24) + .7)
        d = {"head": (r(hx), r(2.2 * math.sin(w(24) + 1.2)), r(2.0 * math.sin(w(48) + .3))), "neck": (r(0.4 * hx), 0, 0), "spine_fk.003": (r(0.8 * math.sin(w(12) + .5)), 0, 0),
             "shoulder.L": (0, r(-1.2 * math.sin(w(24) + .4)), 0), "shoulder.R": (0, r(1.2 * math.sin(w(24) + .4)), 0)}
        if f == 49: d = prevfirst
        if f == 1: prevfirst = d
        key_values(f, {b: (None, e) for b, e in d.items()})
    finish(a, cycles=True)
    # HUM_talk_nod: 14
    a = new_action("HUM_talk_nod"); r = math.radians
    for f, hx in {1: 0, 4: -2.5, 7: 9, 10: 4, 14: 0}.items():
        key_values(f, {"head": (None, (r(hx), 0, 0)), "neck": (None, (r(0.4 * hx), 0, 0)), "spine_fk.003": (None, (r(0.15 * hx), 0, 0))})
    finish(a); a["frames"] = "1-14"

def main():
    build_base(); build_all_poses(); build_loops()
    clear_pose(); to_neutral()
    return sorted(a.name for a in bpy.data.actions if a.name.startswith("HUM_"))
result = main()
