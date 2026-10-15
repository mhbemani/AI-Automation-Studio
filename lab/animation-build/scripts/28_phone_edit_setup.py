"""Edit setup for the holding-phone pose (creator edits by hand): adds a control bone `phone_hold.R` that carries the phone (so the phone is
posed like any bone), shows the right wrist + all finger joints, zooms the viewport onto the hand. Run via bridge, rig in Pose or Object mode."""
import bpy, math
from mathutils import Matrix, Vector as V
rig = bpy.data.objects["RIG_Human"]; sock = bpy.data.objects["HUM_PhoneSocket"]
if bpy.context.object and bpy.context.object.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.update()
W = sock.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.copy()          # phone world pose right now
# 1. the bone, built in the REST pose frame of the socket: head at the phone centre, along the phone's long axis
for o in bpy.context.selected_objects: o.select_set(False)
rig.select_set(True); bpy.context.view_layer.objects.active = rig
saved = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}; props = {n: rig.pose.bones[n]["IK_FK"] for n in ("upper_arm_parent.R", "upper_arm_parent.L", "thigh_parent.L", "thigh_parent.R")}
for pb in rig.pose.bones: pb.matrix_basis = Matrix.Identity(4)
bpy.context.view_layer.update()
Wrest = sock.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.copy()
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
if "phone_hold.R" in eb: eb.remove(eb["phone_hold.R"])
b = eb.new("phone_hold.R"); b.head = Wrest.translation; b.tail = Wrest.translation + Wrest.to_3x3().col[2] * 0.12
b.align_roll(Wrest.to_3x3().col[1]); b.parent = eb["DEF-hand.R"]; b.use_connect = False; b.use_deform = False
bpy.ops.object.mode_set(mode='POSE')
for n, m in saved.items(): rig.pose.bones[n].matrix_basis = m
for n, v in props.items(): rig.pose.bones[n]["IK_FK"] = v
pb = rig.pose.bones["phone_hold.R"]; pb.rotation_mode = 'XYZ'
col = rig.data.collections_all.get("Phone") or rig.data.collections.new("Phone")
col.assign(rig.data.bones["phone_hold.R"]); col.is_visible = True
rig.data.bones["phone_hold.R"].color.palette = 'THEME04'; pb.color.palette = 'THEME04'
bpy.context.view_layer.update()
# 2. the socket now hangs on the new bone, same world position
sock.parent = rig; sock.parent_type = 'BONE'; sock.parent_bone = "phone_hold.R"; sock.matrix_parent_inverse = Matrix.Identity(4)
bpy.context.view_layer.update()
P = sock.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.copy()
sock.matrix_parent_inverse = P.inverted() @ W
bpy.context.view_layer.update()
err = (sock.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.translation - W.translation).length
# 3. what the creator sees: right wrist (FK), every finger joint, the phone bone; the rest hidden
SHOW = ("Arm.R (FK)", "Fingers", "Fingers (Detail)", "Phone")
for c in rig.data.collections_all: c.is_visible = c.name in SHOW
body = bpy.data.objects["HUM_Body"]; body.hide_select = True
for o in bpy.data.objects:
    if o.name.startswith("PHN_"): o.hide_select = True
for bn in rig.data.bones: bn.select = False
rig.data.bones.active = rig.data.bones["phone_hold.R"]; rig.data.bones["phone_hold.R"].select = True
rig.data.show_bone_custom_shapes = False; rig.data.display_type = 'OCTAHEDRAL'; rig.data.show_names = True
# 4. view on the hand
tgt = W.translation
for w in bpy.context.window_manager.windows:
    for a in w.screen.areas:
        if a.type == 'VIEW_3D':
            sp = a.spaces[0]; r3 = sp.region_3d; r3.view_perspective = 'PERSP'; sp.shading.show_xray = True; sp.shading.xray_alpha = 0.2
            loc = tgt + V((0.55, -0.55, 0.25)); r3.view_rotation = (tgt - loc).to_track_quat('-Z', 'Y'); r3.view_location = tgt; r3.view_distance = 0.7
            sp.overlay.show_bones = True; sp.show_region_ui = True; a.tag_redraw()
result = {"socket_error_m": round(err, 5), "mode": rig.mode, "fingers_detail_bones": sum(1 for bn in rig.data.bones if bn.collections and any(c.name == "Fingers (Detail)" for c in bn.collections) and bn.name.endswith(".R"))}
