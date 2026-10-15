"""Numeric checks for the magic and self-drive actions (via bridge). Writes stills/magic_checks.json"""
import bpy, json
exp = {"MAG_ring_shoot": 24, "MAG_ring_wrap": 30, "MAG_ring_fade": 18, "CLA_magic_cast": 24, "CAR_self_drive_start": 48}
out = {n: {"frames": int(bpy.data.actions[n].frame_range[1] - bpy.data.actions[n].frame_range[0] + 1), "expected": L} for n, L in exp.items()}
root = bpy.data.objects["MAG_Root"]; car = bpy.data.objects["CAR_ctrl"]; rig = bpy.data.objects["RIG_Claude"]
def play(obj, n, f):
    ad = obj.animation_data_create(); ad.action = bpy.data.actions[n]; bpy.context.scene.frame_set(500); bpy.context.scene.frame_set(f)
    for o in bpy.data.objects:
        if o.name.startswith(("MAG_", "CAR_")): o.update_tag()
    bpy.context.view_layer.update()
    ev = lambda nm: bpy.data.objects[nm].evaluated_get(bpy.context.evaluated_depsgraph_get())
    return ev
ev = play(root, "MAG_ring_shoot", 24); out["shoot_end_ring_local_y"] = round(ev("MAG_Ring").location.y, 3); out["shoot_end_scale"] = round(ev("MAG_Ring").scale.x, 3)
ev = play(root, "MAG_ring_wrap", 30); out["wrap_end_scale"] = round(ev("MAG_Ring").scale.x, 3)
ev = play(root, "MAG_ring_fade", 18); out["fade_end"] = round(root["fade"], 3); out["sparkle_end"] = round(root["sparkle"], 3)
root.animation_data.action = None
play(car, "CAR_self_drive_start", 48); out["car_end"] = {k: round(car[k], 3) for k in ("distance", "dash_glow", "steer")}
play(car, "CAR_self_drive_start", 1); out["car_start"] = {k: round(car[k], 3) for k in ("distance", "dash_glow", "steer")}
car.animation_data.action = None
ctrl = rig.pose.bones["ctrl"]; a = bpy.data.actions["CLA_magic_cast"]
out["cast_max_arm_len"] = round(max(kp.co[1] for fc in a.fcurves if "arm_len" in fc.data_path for kp in fc.keyframe_points), 3)
out["cast_first_last_diff"] = round(max(abs(fc.evaluate(1) - fc.evaluate(24)) for fc in a.fcurves), 4)
for p, d in (("distance", 0), ("dash_glow", 0), ("steer", 0)): car[p] = float(d)
root["fade"] = 0.0; root["shot"] = 0.0; root["wrap"] = 0.0; root["size"] = 1.0; root["sparkle"] = 0.0; root["puff"] = 0.0; root["spin_rate"] = 1.0
json.dump(out, open("stills/magic_checks.json", "w"), indent=1); result = out
