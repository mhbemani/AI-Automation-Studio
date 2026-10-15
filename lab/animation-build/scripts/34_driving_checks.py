"""Checks of the driving actions (bridge): frame counts, loop closure, hand-to-grip error while holding the wheel, arm stretch (<= 2.3x), arm thickness. -> stills/driving_checks.json"""
import bpy, json, math, os
from mathutils import Vector as V
ROOT = os.environ.get("ANIM_ROOT") or os.path.dirname(os.path.abspath(__import__("bpy").data.filepath))
rig = bpy.data.objects["RIG_Claude"]; car = bpy.data.objects["CAR_ctrl"]
for o in bpy.data.objects:
    if o.name.startswith(("CLA_", "RIG_Claude", "CAR_")): o.hide_viewport = False
rig.location = (0.42, -0.19, 0.81); bpy.context.view_layer.update()
def nla(o, name):
    ad = o.animation_data_create(); ad.action = None
    for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
    if name != "-": s = ad.nla_tracks.new().strips.new(name, 1, bpy.data.actions[name]); s.extrapolation = "HOLD"
EXP = {"CLA_drive_hold_wheel": (96, "CAR_steering_sway"), "CLA_drive_steer_left": (24, "CAR_steering_turn_left"), "CLA_drive_steer_right": (24, "CAR_steering_turn_right"), "CLA_drive_hands_off": (18, "-"), "CLA_talk_arm_wiggle": (36, "-")}
ARM_GRIP = {"L": "R", "R": "L"}; res = {}
for n, (length, caract) in EXP.items():
    a = bpy.data.actions[n]; f0, f1 = a.frame_range; loop = n in ("CLA_drive_hold_wheel", "CLA_talk_arm_wiggle")
    r = {"range": [int(f0), int(f1)], "length_ok": (int(f1 - f0) == length) if loop else (int(f1 - f0 + 1) == length)}
    if loop: r["loop_max_diff"] = round(max(abs(fc.evaluate(f0) - fc.evaluate(f1)) for fc in a.fcurves), 6)
    nla(rig, n); nla(car, caract); bpy.context.scene.frame_set(500)
    err = []; st = []; thick = []
    if n.startswith("CLA_drive_h") or n.startswith("CLA_drive_steer"):
        for f in range(int(f0), int(f1) + 1):
            bpy.context.scene.frame_set(f); dg = bpy.context.evaluated_depsgraph_get(); e = rig.evaluated_get(dg)
            for side in "LR":
                if n.endswith("hands_off") and f > 6: continue
                tail = rig.matrix_world @ V(e.pose.bones[f"arm_{side}"].tail); head = rig.matrix_world @ V(e.pose.bones[f"arm_{side}"].head)
                g = V(bpy.data.objects[f"CAR_WheelGrip_{ARM_GRIP[side]}"].evaluated_get(dg).matrix_world.translation)
                if n.endswith("hands_off"): continue
                err.append((tail - g).length); st.append((tail - head).length / 0.1)
            o = bpy.data.objects["CLA_Arm_R"].evaluated_get(dg); me = o.to_mesh(); ws = [o.matrix_world @ v.co for v in me.vertices]; o.to_mesh_clear()
            ext = sorted([max(w[i] for w in ws) - min(w[i] for w in ws) for i in range(3)]); thick.append(ext[0])
        if err: r["hand_to_grip_error_cm"] = [round(min(err) * 100, 2), round(max(err) * 100, 2)]; r["arm_stretch_max"] = round(max(st), 2)
        r["arm_thickness_min_max_cm"] = [round(min(thick) * 100, 1), round(max(thick) * 100, 1)]
    res[n] = r
for o in (rig, car):
    for t in list(o.animation_data.nla_tracks): o.animation_data.nla_tracks.remove(t)
rig.location = (-1.2, 0, 0); bpy.context.view_layer.update()
json.dump(res, open(os.path.join(ROOT, "stills", "driving_checks.json"), "w"), indent=1)
result = res
