"""Wheel grips for Claude's hands: CAR_WheelGripPivot (child of the steering wheel, turns only 15 percent as far as the wheel: hand-over-hand cheat)
with CAR_WheelGrip_L (car left = +X) and CAR_WheelGrip_R (-X) at +-0.20 (wheel local). Idempotent. Also puts the wheel's straight-ahead orientation in the pivot.
Run via bridge; needs 05_car_and_phone.py to have run (CAR_ctrl, drivers)."""
import bpy, math
sw = bpy.data.objects["CAR_SteeringWheel"]; ctrl = bpy.data.objects["CAR_ctrl"]
z0 = sw["steer_z0"]
for n in ("CAR_WheelGripPivot", "CAR_WheelGrip_L", "CAR_WheelGrip_R"):
    o = bpy.data.objects.get(n)
    if o: bpy.data.objects.remove(o)
col = bpy.data.collections["CAR"]
piv = bpy.data.objects.new("CAR_WheelGripPivot", None); piv.empty_display_type = 'PLAIN_AXES'; piv.empty_display_size = 0.05; col.objects.link(piv)
piv.parent = sw; piv.matrix_parent_inverse = bpy.data.objects["CAR_SteeringWheel"].matrix_world.inverted() @ sw.matrix_world   # identity relative placement
piv.parent = sw; piv.location = (0, 0, 0); piv.rotation_mode = 'XYZ'
# steering wheel: z rotation = z0 + sgn*steer*450deg (driver on CAR_SteeringWheel). Counter-rotate 85 percent of the steering part and all of z0
n_ = sw.matrix_world.to_3x3().col[2]; ext = bpy.data.objects["CAR_Exterior"]; back = ext.matrix_world.to_3x3() @ __import__("mathutils").Vector((0, 1, 0))
sgn = -1 if n_.dot(back) > 0 else 1
fc = piv.driver_add("rotation_euler", 2); d = fc.driver; d.type = 'SCRIPTED'; d.expression = f"-radians({z0}) - 0.85*{sgn}*steer*radians(450)"
v = d.variables.new(); v.name = "steer"; v.type = 'SINGLE_PROP'; v.targets[0].id = ctrl; v.targets[0].data_path = '["steer"]'
for side, x in (("L", 0.20), ("R", -0.20)):
    g = bpy.data.objects.new(f"CAR_WheelGrip_{side}", None); g.empty_display_type = 'SPHERE'; g.empty_display_size = 0.02; col.objects.link(g)
    g.parent = piv; g.location = (x, 0, 0); g["anim_owner"] = "car"
bpy.context.view_layer.update()
r = {s: tuple(round(x, 3) for x in bpy.data.objects[f"CAR_WheelGrip_{s}"].matrix_world.translation) for s in "LR"}
result = {"sgn": sgn, "grips_world(straight)": r, "wheel": tuple(round(x, 3) for x in sw.matrix_world.translation)}
