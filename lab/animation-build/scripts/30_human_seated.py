"""Phase 2 / milestone 3: seated passenger actions (absolute full-body actions; legs FK, arms FK, hands resting on the thighs):
HUM_pass_hands_lap (96 loop), HUM_pass_turn_to_claude (24, ends turned to the driver on his left), HUM_pass_look_out_window (120 loop, looking out of the
right window), HUM_pass_lean_forward (20, toward the dash monitor), HUM_talk_hand_gesture_a (36 loop). Seat height about 0.45 m (hips at 0.52 m)."""
import bpy, math, os, sys
SKIP_MAIN = True
ROOT = os.environ.get("ANIM_ROOT") or os.path.dirname(os.path.abspath(__import__("bpy").data.filepath))
exec(open(os.path.join(ROOT, "scripts", "20_human_locomotion.py")).read())
def build_seat_base():
    to_neutral()
    for s in "LR": rig.pose.bones[f"thigh_parent.{s}"]["IK_FK"] = 1.0
    move_world(rig, "torso", (0, 0.1, -0.40))
    for s in "LR": rot_world(rig, f"thigh_fk.{s}", X, -90); rot_world(rig, f"shin_fk.{s}", X, 90)
    bpy.context.view_layer.update()
    for s_, sx in (("L", 1), ("R", -1)): solve_hand(s_, (0.042 + sx * 0.10, -0.12, 0.635))
    return {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
def solve_hand(side, target, iters=60):
    names = [f"upper_arm_fk.{side}", f"forearm_fk.{side}"]
    for n in names: rig.pose.bones[n].rotation_mode = 'XYZ'
    def err():
        bpy.context.view_layer.update(); h = rig.evaluated_get(bpy.context.evaluated_depsgraph_get()).pose.bones[f"DEF-hand.{side}"].head; return (V(h) - V(target)).length
    step = math.radians(8); best = err()
    for it in range(iters):
        improved = False
        for n in names:
            pb = rig.pose.bones[n]
            for ax in range(3):
                for sgn in (1, -1):
                    e = pb.rotation_euler.copy(); e[ax] += sgn * step; old = pb.rotation_euler.copy(); pb.rotation_euler = e; v = err()
                    if v < best - 1e-5: best = v; improved = True
                    else: pb.rotation_euler = old
        if not improved:
            step *= 0.5
            if step < math.radians(0.3): break
    return best
SEAT = build_seat_base()
# the creator fixed the hands by hand (arms, wrists, fingers, both sides): scripts/seated_hands_pose.json overrides the solved arm pose
HANDS_FILE = os.path.join(ROOT, "scripts", "seated_hands_pose.json")
if os.path.exists(HANDS_FILE):
    for n_, m_ in json.load(open(HANDS_FILE)).items(): SEAT[n_] = Matrix(m_)
FING_L = [f for f in FINGERS]
def seated(ops=(), local=(), idle_f=None, relax=0.0):
    """returns a function f -> applies the seated base + breathing + ops; used as `extra` of apply() through a descriptor-free path."""
    def apply_seat(f):
        for pb in rig.pose.bones: pb.matrix_basis = Matrix.Identity(4)
        for n, m in SEAT.items(): rig.pose.bones[n].matrix_basis = m
        for s in "LR": rig.pose.bones[f"thigh_parent.{s}"]["IK_FK"] = 1.0; rig.pose.bones[f"upper_arm_parent.{s}"]["IK_FK"] = 1.0
        rig.update_tag(); bpy.context.view_layer.update()
        if idle_f is not None:                       # breathing and sway like HUM_seat_idle
            ph = 2 * math.pi * ((idle_f - 1) % 96) / 96; r = math.radians
            for b, axis, deg in (("spine_fk.001", X, 0.6 * math.sin(2 * ph)), ("spine_fk.002", X, 0.9 * math.sin(2 * ph + .2)), ("spine_fk.003", X, 1.1 * math.sin(2 * ph + .4)), ("spine_fk.001", Y, 1.2 * math.sin(ph + .3)),
                                 ("neck", X, 0.4 * math.sin(2 * ph + .9)), ("head", X, 0.8 * math.sin(2 * ph + .9) + 0.5 * math.sin(ph)), ("head", Y, 1.5 * math.sin(ph + 1)), ("head", Z, 1.2 * math.sin(ph))):
                rot_world(rig, b, axis, deg)
            rot_world(rig, "shoulder.L", Y, -0.9 * math.sin(2 * ph + .5)); rot_world(rig, "shoulder.R", Y, 0.9 * math.sin(2 * ph + .5))
        for fn in FING_L:                            # relaxed fingers
            pb = rig.pose.bones[fn]; e = pb.rotation_euler.copy(); e[0] += math.radians(relax); pb.rotation_euler = e
        for b, ax, deg in ops: rot_world(rig, b, ax, deg)
        for b, deg in local:
            pb = rig.pose.bones[b]; pb.rotation_mode = 'XYZ'; e = pb.rotation_euler.copy(); e[0] += math.radians(deg); pb.rotation_euler = e
        rig.update_tag(); bpy.context.view_layer.update()
    return apply_seat
def build_seated_action(name, frames, fn, cycles=False):
    """fn(f) -> callable that poses the rig. Reuses build_action by faking a descriptor whose apply() is replaced."""
    global apply
    real_apply = apply
    try:
        apply = lambda d: d(None)
        return build_action(name, frames, fn, cycles=cycles)
    finally: apply = real_apply
def main3():
    # hands in the lap: breathing, tiny sway (96 loop)
    build_seated_action("HUM_pass_hands_lap", list(range(1, 98, 4)), lambda f: seated(idle_f=1 if f == 97 else f), cycles=True)
    # turn to Claude (24): spine/neck/head turn to his left (+X), a little lean, eased with overshoot
    def turn(f):
        t = {1: 0, 5: 0.0, 14: 1.12, 19: 1.0, 24: 1.0}; k = sm((f - 4) / 16.0) * (1 + 0.12 * math.sin(math.pi * min(1, (f - 4) / 16.0)) if f > 4 else 1) if f > 4 else 0.0
        return seated(idle_f=1, ops=[("spine_fk.002", Z, 6 * k), ("spine_fk.003", Z, 9 * k), ("neck", Z, 14 * k), ("head", Z, 28 * k), ("head", Y, 4 * k), ("shoulder.R", Z, -4 * k)])
    build_seated_action("HUM_pass_turn_to_claude", list(range(1, 25)), turn)
    # look out of the right window (120 loop): turned to his right (-Z), slow drift
    def window(f):
        ph = 2 * math.pi * ((f - 1) % 120) / 120
        return seated(idle_f=1 + (f - 1) * 0.8, ops=[("spine_fk.003", Z, -9 + 1.0 * math.sin(ph)), ("neck", Z, -20 + 2.0 * math.sin(ph + .5)), ("head", Z, -34 + 3.0 * math.sin(ph + 1.0)), ("head", X, 3 + 1.5 * math.sin(2 * ph))])
    build_seated_action("HUM_pass_look_out_window", list(range(1, 122, 4)), lambda f: window(1 if f == 121 else f), cycles=True)
    # lean forward toward the dash (20): ends leaning with the head looking down at the monitor
    def lean(f):
        k = sm((f - 1) / 15.0)
        return seated(idle_f=1, ops=[("spine_fk.001", X, 9 * k), ("spine_fk.002", X, 8 * k), ("spine_fk.003", X, 7 * k), ("neck", X, 5 * k), ("head", X, 6 * k)])
    build_seated_action("HUM_pass_lean_forward", list(range(1, 21)), lean)
    # talk hand gesture (36 loop): the right hand lifts from the lap, opens and turns palm up, then returns
    def gesture(f):
        ph = 2 * math.pi * ((f - 1) % 36) / 36; g = 0.5 - 0.5 * math.cos(ph)       # 0 -> 1 -> 0
        gs = 0.5 - 0.5 * math.cos(2 * ph)
        return seated(idle_f=1 + (f - 1) * 2, relax=-22 * g, ops=[("upper_arm_fk.R", X, -22 * g), ("forearm_fk.R", X, -38 * g), ("hand_fk.R", X, -10 * g * gs), ("upper_arm_fk.R", Z, -8 * g),
                                                                         ("head", X, 1.5 * math.sin(2 * ph)), ("head", Z, 2.0 * math.sin(ph))])
    build_seated_action("HUM_talk_hand_gesture_a", list(range(1, 38, 2)), lambda f: gesture(1 if f == 37 else f), cycles=True)
    build_seated_action("HUM_pose_seated", [1], lambda f: seated())
    to_neutral()
    for s in "LR": rig.pose.bones[f"thigh_parent.{s}"]["IK_FK"] = 1.0; rig.pose.bones[f"upper_arm_parent.{s}"]["IK_FK"] = 1.0
    return sorted(a.name for a in bpy.data.actions if a.name.startswith(("HUM_pass_", "HUM_talk_hand", "HUM_pose_seated")))
result = main3()
