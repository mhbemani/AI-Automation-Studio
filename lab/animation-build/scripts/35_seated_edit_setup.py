"""Set the character up so the creator can fix the seated hands by hand: seated pose (HUM_pass_hands_lap frame 1) as a manual pose, seat box for reference,
both arms (FK) and all finger joints visible as plain bones, viewport zoomed on the lap. Afterwards read with 36_read_seated_pose.py."""
import bpy, math
from mathutils import Matrix, Vector as V
rig = bpy.data.objects["RIG_Human"]; body = bpy.data.objects["HUM_Body"]
if bpy.context.object and bpy.context.object.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
for o in bpy.data.objects:
    o.hide_select = False
    if o.name.startswith(("HUM_", "RIG_Human")): o.hide_viewport = False; o.hide_set(False)
bpy.data.objects["PHN_Phone"]["phone_visible"] = 0.0
# 1. the pose, as a manual pose
ad = rig.animation_data_create(); ad.action = bpy.data.actions["HUM_pass_hands_lap"]
bpy.context.scene.frame_set(500); bpy.context.scene.frame_set(1)
e = rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
vals = {pb.name: pb.matrix_basis.copy() for pb in e.pose.bones}; ik = {n: e.pose.bones[n]["IK_FK"] for n in ("thigh_parent.L", "thigh_parent.R", "upper_arm_parent.L", "upper_arm_parent.R")}
ad.action = None
for pb in rig.pose.bones: pb.matrix_basis = Matrix.Identity(4)
for n, m in vals.items(): rig.pose.bones[n].matrix_basis = m
for n, v in ik.items(): rig.pose.bones[n]["IK_FK"] = v
bpy.context.view_layer.update()
# 2. a seat to see the thighs against
col = bpy.data.collections["HUMAN"]
for n in ("ANIM_seat", "ANIM_seatback"):
    o = bpy.data.objects.get(n)
    if o: bpy.data.objects.remove(o)
mat = bpy.data.materials.get("ANIM_seatmat") or bpy.data.materials.new("ANIM_seatmat"); mat.diffuse_color = (.12, .12, .14, 1)
for n, loc, sc in (("ANIM_seat", (0.03, 0.12, 0.2), (0.5, 0.55, 0.4)), ("ANIM_seatback", (0.03, 0.42, 0.65), (0.5, 0.08, 0.7))):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.active_object; o.name = n; o.scale = sc; o.data.materials.append(mat); o.display_type = 'SOLID'; o.hide_select = True; o["anim_debug"] = 1
# 3. what the creator sees
body.hide_select = True
for o in bpy.data.objects:
    if o.name.startswith("PHN_") or o.name == "HUM_PhoneSocket": o.hide_select = True
SHOW = ("Arm.L (FK)", "Arm.R (FK)", "Fingers (Detail)")
for c in rig.data.collections_all: c.is_visible = c.name in SHOW
rig.data.show_bone_custom_shapes = False; rig.data.display_type = 'OCTAHEDRAL'; rig.data.show_names = False; rig.show_in_front = True
for b in rig.data.bones: b.select = False
for oo in bpy.context.selected_objects: oo.select_set(False)
rig.select_set(True); bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='POSE')
rig.data.bones.active = rig.data.bones["hand_fk.R"]; rig.data.bones["hand_fk.R"].select = True
tgt = V((0.04, -0.12, 0.72))
for w in bpy.context.window_manager.windows:
    for a in w.screen.areas:
        if a.type == 'VIEW_3D':
            sp = a.spaces[0]; r3 = sp.region_3d; r3.view_perspective = 'PERSP'; sp.shading.show_xray = True; sp.shading.xray_alpha = 0.2; sp.overlay.show_bones = True; sp.show_region_ui = True
            loc = tgt + V((0.55, -0.85, 0.6)); r3.view_rotation = (tgt - loc).to_track_quat('-Z', 'Y'); r3.view_location = tgt; r3.view_distance = 1.15; a.tag_redraw()
result = {"mode": rig.mode, "ik_fk": ik}
