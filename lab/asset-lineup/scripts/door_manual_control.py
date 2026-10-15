"""Let the doors be opened by hand: select a door and rotate it (R Z, or the Z rotation field), or animate its Z rotation directly.
  * the old driver (root door_L_open / door_R_open -> door rotation) is removed, the doors are closed (rotation 0)
  * the door can only turn about its own hinge (the anchor): rotation X/Y, location and scale are locked
  * Limit Rotation: Door_L (+x side) opens toward negative Z, 0 to -65 degrees; Door_R (-x side) toward positive Z, 0 to +65; it cannot swing into the car
  * root custom properties door_L_open / door_R_open now only READ the door angle (0 = closed ... 1 = 65 degrees), driven from the rotation
Reads IN.blend, writes OUT.blend (never the input):
  Blender -b --factory-startup IN.blend --python lab/asset-lineup/scripts/door_manual_control.py -- OUT.blend"""
import bpy, math, sys
out = sys.argv[sys.argv.index("--") + 1]
P = lambda n: bpy.data.objects["LU_NEW_CAR_" + n]
root = P("Exterior"); MAXO = math.radians(65)
for sx, side in ((1, "L"), (-1, "R")):
    d = P("Door_" + side)
    ad = d.animation_data
    if ad:
        for fc in [f for f in ad.drivers if f.data_path == "rotation_euler"]: ad.drivers.remove(fc)
    d.rotation_mode = "XYZ"; d.rotation_euler = (0, 0, 0)
    d.lock_rotation = (True, True, False); d.lock_location = (True, True, True); d.lock_scale = (True, True, True)
    for c in [c for c in d.constraints if c.type == "LIMIT_ROTATION"]: d.constraints.remove(c)
    lim = d.constraints.new("LIMIT_ROTATION"); lim.name = "DoorSwing"; lim.owner_space = "LOCAL"; lim.use_limit_z = True
    lim.min_z, lim.max_z = (-MAXO, 0.0) if sx > 0 else (0.0, MAXO)
    key = f"door_{side}_open"
    if key in root.keys(): del root[key]
    root[key] = 0.0; root.id_properties_ui(key).update(min=0.0, max=1.0, description=f"{side} door angle, read-only: 0 closed ... 1 = 65 degrees (rotate the door itself)")
    if root.animation_data:
        for fc in [f for f in root.animation_data.drivers if f.data_path == f'["{key}"]']: root.animation_data.drivers.remove(fc)
    fc = root.driver_add(f'["{key}"]'); dr = fc.driver; dr.type = "SCRIPTED"
    v = dr.variables.new(); v.name = "r"; v.type = "TRANSFORMS"; v.targets[0].id = d; v.targets[0].transform_type = "ROT_Z"; v.targets[0].transform_space = "LOCAL_SPACE"
    dr.expression = f"max(0, min(1, {-sx} * r / {MAXO:.6f}))"
bpy.ops.wm.save_as_mainfile(filepath=out, copy=False)
print("saved", out)
