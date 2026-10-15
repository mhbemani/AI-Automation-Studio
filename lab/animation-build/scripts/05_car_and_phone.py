"""Milestone 4: car controls (wheels, steering, doors) and the phone with its hand socket.
Car: renames LU_NEW_CAR_* -> CAR_*, adds the empty CAR_ctrl (custom properties) and drivers:
  distance (m) / speed (m/s) -> wheel spin ; steer (-1..1, + = right) -> steering wheel (+-450 deg) and front wheels (+-28 deg);
  door_L / door_R (0..1) -> door hinge rotation (0..65 deg).
Phone: the 5x lineup phone becomes PHN_Phone at real size (the lineup shows it at 5x scale; mesh is 74 x 9 x 150 mm) parented to HUM_PhoneSocket, an empty on bone DEF-hand.R.
Idempotent. Run via bridge (cwd lab/animation-build)."""
import bpy, math
from mathutils import Vector as V, Matrix
WHEEL_R = 0.335
STEER_WHEEL_DEG, STEER_FRONT_DEG, DOOR_DEG = 450.0, 28.0, 65.0
WHEELS = {"front-left": True, "front-right": True, "back-left": False, "back-right": False}

def rename_car():
    for o in bpy.data.objects:
        if o.name.startswith("LU_NEW_CAR_"): o.name = "CAR_" + o.name[len("LU_NEW_CAR_"):]
    col = bpy.data.collections.get("CAR") or bpy.data.collections.new("CAR")
    if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
    for o in bpy.data.objects:
        if o.name.startswith("CAR_") and o.name != "CAR_ctrl":
            for c in list(o.users_collection): c.objects.unlink(o)
            col.objects.link(o)
    return col

def ground_car():
    """library convention: car root at the origin, no rotation, wheels touching z = 0, front = -Y (like the human and Claude).
    The lineup copy had the body 1.826 m above its root and the root rotated 90 deg; shift the direct children down once."""
    ext = bpy.data.objects["CAR_Exterior"]
    if not ext.get("grounded"):
        for o in bpy.data.objects:
            if o.parent == ext: o.location.z -= 1.826
        ext["grounded"] = True
    ext.location = (0, 0, 0); ext.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()

def prop_var(d, obj, name, prop):
    v = d.variables.new(); v.name = name; v.type = 'SINGLE_PROP'; v.targets[0].id = obj; v.targets[0].data_path = f'["{prop}"]'

def drive(target, path, idx, expr, ctrl, props):
    for fc in list(target.animation_data.drivers) if target.animation_data else []:
        if fc.data_path == path and fc.array_index == idx: target.animation_data.drivers.remove(fc)
    fc = target.driver_add(path, idx); d = fc.driver; d.type = 'SCRIPTED'; d.expression = expr
    for p in props: prop_var(d, ctrl, p, p)

def car_controls(col):
    ext = bpy.data.objects["CAR_Exterior"]
    for fc in list(ext.animation_data.drivers) if ext.animation_data else []:
        if fc.data_path in ('["door_L_open"]', '["door_R_open"]'): ext.animation_data.drivers.remove(fc)
    for k in ("door_L_open", "door_R_open"):
        if k in ext: del ext[k]
    ctrl = bpy.data.objects.get("CAR_ctrl")
    if ctrl: bpy.data.objects.remove(ctrl)
    ctrl = bpy.data.objects.new("CAR_ctrl", None); ctrl.empty_display_type = 'ARROWS'; ctrl.empty_display_size = 0.3
    col.objects.link(ctrl); ctrl.parent = ext; ctrl.location = (0, 0, 1.8); ctrl["anim_owner"] = "car"
    props = {"distance": (0.0, -1000.0, 1000.0, "metres rolled (wheel angle = distance / 0.335)"), "speed": (0.0, -60.0, 60.0, "m/s; adds speed*frame/24 to distance (auto roll)"),
             "steer": (0.0, -1.0, 1.0, "-1 left .. +1 right (+-450 deg wheel, +-28 deg front wheels)"),
             "door_L": (0.0, 0.0, 1.0, "driver door (+X side) 0 closed .. 1 open (65 deg)"), "door_R": (0.0, 0.0, 1.0, "passenger door (-X side) 0 closed .. 1 open (65 deg)")}
    for n, (dv, mn, mx, desc) in props.items():
        ctrl[n] = float(dv); ui = ctrl.id_properties_ui(n); ui.update(default=float(dv), description=desc); ui.update(min=mn, max=mx); ui.update(soft_min=mn, soft_max=mx)
    for name, front in WHEELS.items():
        w = bpy.data.objects[f"CAR_Wheel_{name}"]; w.rotation_mode = 'XYZ'
        drive(w, "rotation_euler", 0, f"(distance+speed*frame/24)/{WHEEL_R}", ctrl, ["distance", "speed"])   # +X = rolling forward (-Y)
        if front: drive(w, "rotation_euler", 2, f"-steer*radians({STEER_FRONT_DEG})", ctrl, ["steer"])
        else: w.rotation_euler[2] = 0
    sw = bpy.data.objects["CAR_SteeringWheel"]
    z0 = math.degrees(sw.rotation_euler[2]) % 360 if "steer_z0" not in sw else sw["steer_z0"]
    sw["steer_z0"] = z0
    n = sw.matrix_world.to_3x3().col[2]; back = ext.matrix_world.to_3x3() @ V((0, 1, 0))
    sgn = -1 if n.dot(back) > 0 else 1                       # + steer = clockwise for the driver
    drive(sw, "rotation_euler", 2, f"radians({z0})+{sgn}*steer*radians({STEER_WHEEL_DEG})", ctrl, ["steer"])
    dl, dr = bpy.data.objects["CAR_Door_L"], bpy.data.objects["CAR_Door_R"]
    drive(dl, "rotation_euler", 2, f"-radians({DOOR_DEG})*door_L", ctrl, ["door_L"])
    drive(dr, "rotation_euler", 2, f"radians({DOOR_DEG})*door_R", ctrl, ["door_R"])
    return ctrl

# ---------------- phone
def phone_collection():
    col = bpy.data.collections.get("PHONE") or bpy.data.collections.new("PHONE")
    if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
    for o in list(bpy.data.objects):
        if o.name.startswith("LU_NEW_PROP_"):
            nn = "PHN_" + o.name[len("LU_NEW_PROP_"):]
            if nn.endswith("_5x"): nn = nn[:-3]
            o.name = nn
    for o in bpy.data.objects:
        if o.name.startswith("PHN_"):
            for c in list(o.users_collection): c.objects.unlink(o)
            col.objects.link(o)
    root = bpy.data.objects["PHN_Phone"]; root.parent = None
    root.rotation_euler = (0, 0, 0); root.location = (0, 0, 0); root.scale = (1, 1, 1)
    return root

def palm_frame(rig, side="R"):
    b = rig.data.bones
    h = V(b[f"DEF-hand.{side}"].head_local); mid = V(b[f"DEF-f_middle.01.{side}"].head_local); th = V(b[f"DEF-thumb.01.{side}"].head_local)
    d = (mid - h).normalized(); t = (th - h)
    n = d.cross(t).normalized()
    if side == "R": n = -n
    centre = h.lerp(mid, 0.5)
    return centre, d, n

def socket(rig, root):
    o = bpy.data.objects.get("HUM_PhoneSocket")
    if o: bpy.data.objects.remove(o)
    o = bpy.data.objects.new("HUM_PhoneSocket", None); o.empty_display_type = 'ARROWS'; o.empty_display_size = 0.08
    bpy.data.collections["HUMAN"].objects.link(o); o["anim_owner"] = "human"
    centre, d, n = palm_frame(rig, "R")
    zs = d; ys = -n; xs = ys.cross(zs)
    pos = centre + n * 0.03 + d * 0.04              # phone back on the palm, long axis along the fingers, sticking out past the finger bases
    W = Matrix(((xs.x, ys.x, zs.x, pos.x), (xs.y, ys.y, zs.y, pos.y), (xs.z, ys.z, zs.z, pos.z), (0, 0, 0, 1)))
    # evaluate with the rig in rest pose so that the bind-pose frame is exact
    saved = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
    for pb in rig.pose.bones: pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    o.parent = rig; o.parent_type = 'BONE'; o.parent_bone = "DEF-hand.R"; o.matrix_parent_inverse = Matrix.Identity(4)
    bpy.context.view_layer.update()
    P = o.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.copy()
    o.matrix_parent_inverse = P.inverted() @ rig.matrix_world @ W
    for pb in rig.pose.bones: pb.matrix_basis = saved[pb.name]
    bpy.context.view_layer.update()
    root.parent = o; root.matrix_parent_inverse = Matrix.Identity(4)
    return o

def main():
    col = rename_car(); ground_car(); ctrl = car_controls(col)
    root = phone_collection(); rig = bpy.data.objects["RIG_Human"]
    s = socket(rig, root)
    return ctrl.name, s.name
result = main()
