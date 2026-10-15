"""Phase 2 / milestone 4: Claude driving actions. Placement convention: RIG_Claude origin at CLAUDE_DRIVER_SEAT in car space (car at the origin, front -Y),
hands follow the wheel grips CAR_WheelGrip_L/R through aim_L/aim_R (properties aim_follow_*, arm_aim_*); the arm pivots slide on the wall to follow the grips
(arm_y_*, arm_z_*), the arms stretch to the grips (at most 2.3x). Actions: CLA_drive_hold_wheel (96 loop), CLA_drive_steer_left/right (24), CLA_drive_hands_off (18),
CLA_talk_arm_wiggle (36 loop). Everything keyed on the ctrl properties. Run via bridge."""
import bpy, math, os, sys
from mathutils import Vector as V
ROOT = os.environ.get("ANIM_ROOT") or os.path.dirname(os.path.abspath(__import__("bpy").data.filepath))
sys.path.insert(0, os.path.join(ROOT, "scripts")); import claude_reach as CR
rig = bpy.data.objects["RIG_Claude"]; ctrl = rig.pose.bones["ctrl"]; car = bpy.data.objects["CAR_ctrl"]
SEAT = V((0.42, -0.19, 0.81))
for o in bpy.data.objects:
    if o.name.startswith(("CLA_", "RIG_Claude", "CAR_")): o.hide_viewport = False
UI = {k: ctrl.id_properties_ui(k).as_dict() for k in ctrl.keys()}
DEFAULT = {k: v["default"] for k, v in UI.items()}
def clamp(k, v): return float(max(UI[k]["min"], min(UI[k]["max"], float(v))))
def setp(**kw):
    for k, v in kw.items(): ctrl[k] = float(v)
def upd(): rig.update_tag(); car.update_tag(); bpy.data.objects["CAR_SteeringWheel"].update_tag(); bpy.data.objects["CAR_WheelGripPivot"].update_tag(); bpy.context.view_layer.update()
def reset(): 
    for k, v in DEFAULT.items(): ctrl[k] = float(v)
    car["steer"] = 0.0; upd()
def ev(): return rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
def head_world(bone): return rig.matrix_world @ V(ev().pose.bones[bone].head)
def grip_world(side): return V(bpy.data.objects[f"CAR_WheelGrip_{side}"].evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.translation)
ARM_GRIP = {"L": "R", "R": "L"}            # arm_L (-X) holds the grip on the car's right (-X), arm_R the one on the car's left
def solve(steer, base):
    """slides for both arms so that the grips are as close as possible; returns props and the stretch ratios."""
    car["steer"] = float(steer); setp(**base); setp(arm_aim_L=0, arm_aim_R=0); upd()
    out = {}; worst = 0.0
    for side in "LR":
        g = grip_world(ARM_GRIP[side]); best = None
        for sy in [-0.09 + 0.03 * i for i in range(7)]:
            for sz in [-0.10 + 0.025 * i for i in range(11)]:
                setp(**{f"arm_y_{side}": sy, f"arm_z_{side}": sz}); upd()
                d = (head_world(f"arm_{side}") - g).length
                if best is None or d < best[0] - 1e-6: best = (d, sy, sz)
        d0, y0, z0 = best                                  # refine around the coarse optimum
        for dy in (-0.02, -0.01, 0.0, 0.01, 0.02):
            for dz in (-0.0125, -0.00625, 0.0, 0.00625, 0.0125):
                sy, sz = min(0.09, max(-0.09, y0 + dy)), min(0.15, max(-0.10, z0 + dz)); setp(**{f"arm_y_{side}": sy, f"arm_z_{side}": sz}); upd()
                d = (head_world(f"arm_{side}") - g).length
                if d < best[0] - 1e-6: best = (d, sy, sz)
        out[f"arm_y_{side}"], out[f"arm_z_{side}"] = best[1], best[2]; worst = max(worst, best[0] / CR.ARM_LEN)
        setp(**{f"arm_y_{side}": best[1], f"arm_z_{side}": best[2]})
    return out, worst
def build(name, keys, interp='BEZIER', cycles=False):
    old = bpy.data.actions.get(name)
    if old: bpy.data.actions.remove(old)
    a = bpy.data.actions.new(name); a.use_fake_user = True; rig.animation_data_create().action = a
    props = sorted({p for d in keys.values() for p in d})
    for f in sorted(keys):
        for p in props: ctrl[p] = clamp(p, keys[f].get(p, DEFAULT[p]))
        for p in props: ctrl.keyframe_insert(f'["{p}"]', frame=f, group="CLA_ctrl")
    for fc in a.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = interp
        if cycles: fc.modifiers.new('CYCLES')
    rig.animation_data.action = None; reset(); return a
def main():
    rig.location = SEAT; upd(); log = {}
    HOLD = dict(arm_aim_L=1, arm_aim_R=1, aim_follow_L=1, aim_follow_R=1)
    # --- hold the wheel (96 loop; keys every 4): the wheel sways a little (CAR_steering_sway), road bumps, eyes on the road
    k = {}; worst = 0.0
    for f in range(1, 98, 2):
        ph = 2 * math.pi * ((f - 1) % 96) / 96; steer = 0.05 * math.sin(ph) + 0.025 * math.sin(2 * ph + 0.8)
        base = dict(nod=10 + 0.8 * math.sin(2 * ph), bob=0.004 * math.sin(3 * ph), squash=0.012 * math.sin(2 * ph + .5), look_y=-0.012, lean=1.2 * math.sin(ph))
        sl, w = solve(steer, base); worst = max(worst, w); k[f] = {**HOLD, **base, **sl}
    k[97] = dict(k[1]); build("CLA_drive_hold_wheel", k, cycles=True); log["hold_wheel_max_stretch"] = round(worst, 2)
    # --- steer left / right (24): the car action's steer curve, lean into the turn, eyes follow; the body turn gain with the smallest stretch is used
    for nm, sg in (("left", -1), ("right", 1)):
        a = bpy.data.actions[f"CAR_steering_turn_{nm}"]; fc = a.fcurves[0]
        def keys_for(gain, nod, frames, lg=-4.5):
            kk = {}; worst = 0.0
            for f in frames:
                steer = fc.evaluate(f); t = steer / 0.6
                base = dict(nod=nod, lean=lg * t, look_x=0.02 * t, look_y=-0.012, turn=gain * t, bob=0.0)
                sl, w = solve(steer, base); worst = max(worst, w); kk[f] = {**HOLD, **base, **sl}
            return kk, worst
        best = None
        for nod in (10, 13, 16):                               # lean in more when the wheel is turned far, turn the body a little toward the hands
            for gain in (-8, -4, 0, 4, 8):
                for lg in (-9, -4.5, 0, 4.5, 9):
                    kk, w = keys_for(gain, nod, (12, 18, 24), lg)
                    if best is None or w < best[0] - 1e-6: best = (w, gain, nod, lg)
        kk, w = keys_for(best[1], best[2], range(1, 25), best[3])
        build(f"CLA_drive_steer_{nm}", kk); log[f"steer_{nm}_max_stretch"] = round(w, 2); log[f"steer_{nm}_turn_gain_nod_lean"] = (best[1], best[2], best[3])
    # --- hands off the wheel (18): arms release and open
    sl0, _ = solve(0.0, dict(nod=10, look_y=-0.012)); start = {**HOLD, "nod": 10, "look_y": -0.012, **sl0}
    zero_slide = {p: 0.0 for p in ("arm_y_L", "arm_y_R", "arm_z_L", "arm_z_R")}
    k = {1: start,
         6: {**start, "arm_aim_L": 0.7, "arm_aim_R": 0.7, "bob": 0.03, "arm_L": 20, "arm_R": 20, **{p: v * 0.5 for p, v in sl0.items()}, "nod": 3, "squash": -0.15},
         12: {**start, "arm_aim_L": 0.0, "arm_aim_R": 0.0, "aim_follow_L": 1, "aim_follow_R": 1, "arm_L": 46, "arm_R": 46, **zero_slide, "nod": 0, "bob": 0.02, "squash": -0.08, "look_y": 0.0, "glint": 1.3},
         18: {"arm_aim_L": 0.0, "arm_aim_R": 0.0, "aim_follow_L": 0.0, "aim_follow_R": 0.0, "arm_L": 38, "arm_R": 38, "nod": 0, "look_y": 0.0, "glint": 1.2, **zero_slide}}
    build("CLA_drive_hands_off", k)
    # --- talk arm wiggle (36 loop, keys every 3): the arms move a little while he speaks
    k = {}
    for f in range(1, 38, 3):
        ph = 2 * math.pi * ((f - 1) % 36) / 36
        k[f] = dict(arm_L=10 + 9 * math.sin(ph), arm_R=10 + 9 * math.sin(ph + 2.4), arm_fwd_L=5 * math.sin(2 * ph), arm_fwd_R=5 * math.sin(2 * ph + 1.2), arm_z_L=0.02 * math.sin(ph + 1), arm_z_R=0.02 * math.sin(ph + 3.4))
    k[37] = dict(k[1]); build("CLA_talk_arm_wiggle", k, cycles=True)
    rig.location = (-1.2, 0, 0); upd()
    return log
result = main()
