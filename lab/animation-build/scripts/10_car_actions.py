"""Milestone 7: car actions, keyed on the custom properties of CAR_ctrl (24 fps, fake users).
CAR_wheel_spin (12 frame loop = exactly one wheel revolution; `distance` keeps counting up through the cycle modifier),
CAR_steering_sway (96 loop), CAR_steering_turn_left / _right (24, ends turned 0.6 = 270 deg wheel / 17 deg front wheels),
CAR_door_open_L/R and CAR_door_close_L/R (24, eased).  Loops: key at length+1 equals key 1. Idempotent."""
import bpy, math
ctrl = bpy.data.objects["CAR_ctrl"]
R = 0.335
def build(name, keys, interp='BEZIER', cycles=None):
    old = bpy.data.actions.get(name)
    if old: bpy.data.actions.remove(old)
    a = bpy.data.actions.new(name); a.use_fake_user = True
    if ctrl.animation_data is None: ctrl.animation_data_create()
    ctrl.animation_data.action = a
    for f in sorted(keys):
        for p, v in keys[f].items():
            ctrl[p] = float(v); ctrl.keyframe_insert(f'["{p}"]', frame=f)
    for fc in a.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = interp
        if cycles:
            m = fc.modifiers.new('CYCLES')
            if cycles == "offset": m.mode_before = m.mode_after = 'REPEAT_OFFSET'
    ctrl.animation_data.action = None
    for p, d in (("distance", 0), ("speed", 0), ("steer", 0), ("door_L", 0), ("door_R", 0)): ctrl[p] = float(d)
    return a
def main():
    build("CAR_wheel_spin", {1: {"distance": 0.0}, 13: {"distance": 2 * math.pi * R}}, interp='LINEAR', cycles="offset")
    k = {}
    for f in range(1, 98, 4):
        ph = 2 * math.pi * ((f - 1) % 96) / 96
        k[f] = {"steer": 0.05 * math.sin(ph) + 0.025 * math.sin(2 * ph + 0.8)}
    k[97] = dict(k[1]); build("CAR_steering_sway", k, cycles="plain")
    for nm, sg in (("left", -1), ("right", 1)):
        build(f"CAR_steering_turn_{nm}", {1: {"steer": 0.0}, 8: {"steer": sg * 0.12}, 18: {"steer": sg * 0.64}, 24: {"steer": sg * 0.6}})
    for s in "LR":
        build(f"CAR_door_open_{s}", {1: {f"door_{s}": 0.0}, 5: {f"door_{s}": 0.03}, 14: {f"door_{s}": 0.85}, 20: {f"door_{s}": 0.99}, 24: {f"door_{s}": 1.0}})
        build(f"CAR_door_close_{s}", {1: {f"door_{s}": 1.0}, 6: {f"door_{s}": 0.96}, 15: {f"door_{s}": 0.12}, 21: {f"door_{s}": 0.01}, 24: {f"door_{s}": 0.0}})
    return sorted(a.name for a in bpy.data.actions if a.name.startswith("CAR_"))
result = main()
