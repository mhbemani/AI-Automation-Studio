"""Numeric checks for the Claude cushion actions (run via bridge). Writes stills/claude_cushion_checks.json"""
import bpy, json
rig = bpy.data.objects["RIG_Claude"]; c = rig.pose.bones["ctrl"]; cus = bpy.data.objects["CUS_Cushion"]
exp = {"CLA_cushion_jump": 60, "CLA_cushion_run_carry": 16, "CLA_cushion_hold_to_throw": 18, "CLA_cushion_throw_and_jump": 72, "CLA_cushion_sit": 96, "CLA_cushion_sleep": 96, "CLA_cushion_happy_stand": 96, "CLA_stand_to_cushion_sit": 24}
out = {}
for n, L in exp.items():
    a = bpy.data.actions[n]; r = a.frame_range; fcs = a.fcurves
    loop = max((abs(fc.evaluate(r[0]) - fc.evaluate(r[1])) for fc in fcs), default=0) if n in ("CLA_cushion_jump", "CLA_cushion_run_carry", "CLA_cushion_sit", "CLA_cushion_sleep", "CLA_cushion_happy_stand") else None
    out[n] = {"frames": int(r[1] - r[0] + 1), "expected": L, "loop_diff": None if loop is None else round(loop, 5)}
ad = rig.animation_data_create()
for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
def at(n, f):
    for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
    for k in list(c.keys()):
        try: c[k] = c.id_properties_ui(k).as_dict()["default"]
        except Exception: pass
    s = ad.nla_tracks.new().strips.new(n, 1, bpy.data.actions[n]); s.extrapolation = "HOLD"
    bpy.context.scene.frame_set(500); bpy.context.scene.frame_set(f); bpy.context.view_layer.update()
    return rig.matrix_world @ rig.pose.bones["root"].head, cus.matrix_world.translation.copy(), cus.data.shape_keys.key_blocks["Squash"].value
rz, cp, sq = at("CLA_cushion_throw_and_jump", 72)
out["throw_end"] = {"root_z": round(rz.z, 3), "cushion_z": round(cp.z, 3), "root_minus_cushion_z": round(rz.z - cp.z, 3), "squash": round(sq, 3)}
rz, cp, sq = at("CLA_cushion_sit", 1)
out["sit_f1"] = {"root_z": round(rz.z, 3), "cushion_bottom_world_z": round(cp.z - 0.099, 3), "squash": round(sq, 3)}
for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
for k in list(c.keys()):
    try: c[k] = c.id_properties_ui(k).as_dict()["default"]
    except Exception: pass
bpy.context.view_layer.update()
json.dump(out, open("stills/claude_cushion_checks.json", "w"), indent=1); result = out
