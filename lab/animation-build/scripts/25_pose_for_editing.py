"""Put RIG_Human in the standing-holding-phone pose (hold_read frame 1) as a MANUAL pose (no action) and set up the view, so the creator can
adjust it by hand in the open Blender window. Afterwards `26_read_phone_pose.py` reads the edited pose."""
import bpy, math
from mathutils import Matrix, Vector as V
rig = bpy.data.objects["RIG_Human"]; body = bpy.data.objects["HUM_Body"]
# 1. everything visible, nothing animated
for o in bpy.data.objects:
    if o.name.startswith(("HUM_", "PHN_", "RIG_Human", "ANIM_CAM")) or o.name in ("HUM_PhoneSocket",):
        o.hide_viewport = False; o.hide_set(False)
for o in list(bpy.data.objects):
    if o.name.startswith("ANIM_mark") or o.name in ("ANIM_floor", "ANIM_seat", "ANIM_seatback"): bpy.data.objects.remove(o)
rig.hide_render = False
# 2. copy the animated pose of HUM_phone_hold_read frame 1 into the manual pose
ad = rig.animation_data_create(); ad.action = bpy.data.actions["HUM_phone_hold_read"]
bpy.context.scene.frame_set(500); bpy.context.scene.frame_set(1)
e = rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
vals = {pb.name: pb.matrix_basis.copy() for pb in e.pose.bones}
ik = {n: e.pose.bones[n]["IK_FK"] for n in ("thigh_parent.L", "thigh_parent.R", "upper_arm_parent.L", "upper_arm_parent.R")}
ad.action = None
for n, m in vals.items():
    pb = rig.pose.bones[n]
    if pb.rotation_mode not in ('QUATERNION',): pass
    pb.matrix_basis = m
for n, v in ik.items(): rig.pose.bones[n]["IK_FK"] = v
for n in ("ANIM_CAM",): pass
# 3. bone collections: show what is needed for the right arm, hands, torso, head; hide the rest
SHOW = ("Torso", "Fingers", "Arm.R (IK)", "Arm.L (FK)", "Arm.R (FK)", "Leg.L (IK)", "Leg.R (IK)", "Root")
for c in rig.data.collections_all: c.is_visible = c.name in SHOW
rig.data.display_type = 'OCTAHEDRAL'; rig.show_in_front = True; rig.data.show_names = False
# 4. view: a camera looking at the upper body from his front-left, viewport in camera view, rig active in Pose mode
cam = bpy.data.objects.get("ANIM_CAM")
if cam:
    cam.location = (0.95, -1.35, 1.45); cam.rotation_euler = (V((-0.05, -0.1, 1.28)) - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = 45
    bpy.context.scene.camera = cam
bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True); bpy.context.view_layer.objects.active = rig
for w in bpy.context.window_manager.windows:
    for a in w.screen.areas:
        if a.type == 'VIEW_3D':
            sp = a.spaces[0]; sp.shading.type = 'SOLID'; sp.overlay.show_bones = True
            try: sp.region_3d.view_perspective = 'CAMERA'
            except Exception: pass
try: bpy.ops.object.mode_set(mode='POSE')
except Exception as ex: print("mode_set:", ex)
bpy.context.view_layer.update()
phone = bpy.data.objects["HUM_PhoneSocket"].evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.translation
result = {"mode": rig.mode, "phone_world": [round(x, 3) for x in phone], "ik_fk": ik}
