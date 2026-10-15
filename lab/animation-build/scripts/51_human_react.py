"""Phase 3 / milestone 3b: seated human reactions (the car is where they happen; no face, body language only), absolute actions on the creator's seated pose:
HUM_react_startle (16), HUM_react_laugh (36), HUM_react_impressed (30), HUM_react_shake_head (18); HUM_phone_to_seat_idle (36: the phone arm eases from the creator's
holding-phone pose into the seated hands) and PHN_phone_pocket (36: phone_visible 1 -> 0 at the end). Run via bridge."""
import bpy, math, os, json
ROOT = os.environ.get("ANIM_ROOT") or os.path.dirname(os.path.abspath(__import__("bpy").data.filepath))
SKIP_MAIN = True
src30 = open(os.path.join(ROOT, "scripts", "30_human_seated.py")).read().split("def main3")[0]
exec(src30)
def env(keys, f):
    ks = sorted(keys)
    if f <= ks[0]: return keys[ks[0]]
    for a, b in zip(ks, ks[1:]):
        if f <= b: return keys[a] + (keys[b] - keys[a]) * sm((f - a) / (b - a))
    return keys[ks[-1]]
def startle(f):
    k = env({1: 0, 3: 1.0, 6: 1.0, 11: 0.45, 16: 0.12}, f)
    ops = [("spine_fk.001", X, -4 * k), ("spine_fk.002", X, -6 * k), ("spine_fk.003", X, -7 * k), ("neck", X, -5 * k), ("head", X, -9 * k), ("shoulder.L", Y, -7 * k), ("shoulder.R", Y, 7 * k),
           ("upper_arm_fk.L", X, -16 * k), ("upper_arm_fk.R", X, -16 * k), ("forearm_fk.L", X, -26 * k), ("forearm_fk.R", X, -26 * k), ("hand_fk.L", X, -12 * k), ("hand_fk.R", X, -12 * k), ("head", Z, 4 * k)]
    return seated(idle_f=1, ops=ops, relax=-18 * k)
build_seated_action("HUM_react_startle", list(range(1, 17)), startle)
def laugh(f):
    e = env({1: 0, 5: 1, 26: 1, 36: 0.0}, f); b = 0.5 + 0.5 * math.sin(2 * math.pi * 5 * (f - 1) / 36 - math.pi / 2)    # five beats
    ops = [("spine_fk.001", X, (-2 + 3 * b) * e), ("spine_fk.002", X, (-3 + 4 * b) * e), ("spine_fk.003", X, (-4 + 5 * b) * e), ("neck", X, -3 * e), ("head", X, (-9 + 4 * b) * e), ("head", Z, 3 * math.sin(2 * math.pi * f / 36) * e),
           ("shoulder.L", Y, (-3 - 4 * b) * e), ("shoulder.R", Y, (3 + 4 * b) * e), ("upper_arm_fk.L", X, -10 * e), ("upper_arm_fk.R", X, -10 * e), ("forearm_fk.L", X, -18 * e), ("forearm_fk.R", X, -18 * e)]
    return seated(idle_f=1, ops=ops)
build_seated_action("HUM_react_laugh", list(range(1, 37)), laugh)
def impressed(f):
    lean = env({1: 0, 8: 1, 22: 1, 30: 0.0}, f); nod = env({1: 0, 6: -0.5, 14: 1.0, 20: 0.35, 30: 0}, f)
    ops = [("spine_fk.002", X, -3 * lean), ("spine_fk.003", X, -4 * lean), ("neck", X, -2 * lean + 3 * nod), ("head", X, -2 * lean + 9 * nod), ("shoulder.L", Y, -2.5 * lean), ("shoulder.R", Y, 2.5 * lean), ("head", Z, 2 * lean)]
    return seated(idle_f=1, ops=ops)
build_seated_action("HUM_react_impressed", list(range(1, 31)), impressed)
def shake(f):
    t = (f - 1) / 17.0; a = math.sin(2 * math.pi * 2.0 * t) * (1 - 0.6 * t) * math.sin(math.pi * min(1.0, t * 1.15 + 0.0)) ** 0.5
    ops = [("head", Z, 22 * a), ("neck", Z, 8 * a), ("spine_fk.003", Z, 2 * a), ("head", X, 1.5 * abs(a))]
    return seated(idle_f=1, ops=ops)
build_seated_action("HUM_react_shake_head", list(range(1, 19)), shake)
# phone -> seat idle: blend the phone arm group from the creator's holding-phone pose to the seated hands (matrix blend), the head eases down from reading
GROUP = [b for b in SNAP_BONES]
def p2s(f):
    t = sm((f - 3) / 28.0); base = seated(idle_f=1)
    def apply_p2s(_):
        base(None)
        for b in GROUP:
            if b not in SNAP: continue
            A = SNAP[b]; B = rig.pose.bones[b].matrix_basis.copy()
            q = A.to_quaternion().slerp(B.to_quaternion(), t); loc = A.translation.lerp(B.translation, t)
            rig.pose.bones[b].matrix_basis = Matrix.Translation(loc) @ q.to_matrix().to_4x4()
        rig.update_tag(); bpy.context.view_layer.update()
    return apply_p2s
build_seated_action("HUM_phone_to_seat_idle", list(range(1, 37)), p2s)
# the phone object: visible while he holds it, gone (in the pocket) at the end
ph = bpy.data.objects["PHN_Phone"]
old = bpy.data.actions.get("PHN_phone_pocket")
if old: bpy.data.actions.remove(old)
a = bpy.data.actions.new("PHN_phone_pocket"); a.use_fake_user = True; ph.animation_data_create().action = a
for f, v in ((1, 1.0), (28, 1.0), (30, 0.0), (36, 0.0)):
    ph["phone_visible"] = float(v); ph.keyframe_insert('["phone_visible"]', frame=f)
for fc in a.fcurves:
    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
ph.animation_data.action = None; ph["phone_visible"] = 1.0
to_neutral()
for s in "LR": rig.pose.bones[f"thigh_parent.{s}"]["IK_FK"] = 1.0; rig.pose.bones[f"upper_arm_parent.{s}"]["IK_FK"] = 1.0
result = sorted(a.name for a in bpy.data.actions if a.name.startswith(("HUM_react", "HUM_phone_to_seat", "PHN_phone_pocket")))
