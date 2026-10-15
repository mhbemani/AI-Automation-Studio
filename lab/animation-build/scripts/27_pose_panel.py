"""A small sidebar panel (N, tab "Phone Pose") with one button per control the creator needs for the holding-phone pose.
Lives in the open session only (not saved in the file as UI code)."""
import bpy
class ANIM_OT_select_bone(bpy.types.Operator):
    bl_idname = "anim.select_bone"; bl_label = "Select control"; bl_options = {'UNDO'}
    bone: bpy.props.StringProperty()
    def execute(self, ctx):
        rig = bpy.data.objects["RIG_Human"]
        if ctx.mode != 'POSE' or ctx.object != rig:
            for o in ctx.selected_objects: o.select_set(False)
            rig.select_set(True); ctx.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='POSE')
        for b in rig.data.bones: b.select = False
        b = rig.data.bones[self.bone]; b.hide = False; b.select = True; rig.data.bones.active = b
        return {'FINISHED'}
class ANIM_OT_select_phone(bpy.types.Operator):
    bl_idname = "anim.select_phone_socket"; bl_label = "Select phone (to move it inside the hand)"
    def execute(self, ctx):
        if ctx.object and ctx.object.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
        for o in ctx.selected_objects: o.select_set(False)
        s = bpy.data.objects["HUM_PhoneSocket"]; s.select_set(True); ctx.view_layer.objects.active = s
        return {'FINISHED'}
GROUPS = []
for side, title in (("R", "RIGHT"), ("L", "LEFT")):
    GROUPS.append((f"{title} arm", [(f"upper_arm_fk.{side}", "upper arm"), (f"forearm_fk.{side}", "forearm"), (f"hand_fk.{side}", "wrist")]))
    for fname, label in (("thumb", "thumb"), ("f_index", "index"), ("f_middle", "middle"), ("f_ring", "ring"), ("f_pinky", "little")):
        GROUPS.append((f"{title} {label}", [(f"{fname}.0{i}.{side}", f"{label} joint {i}" + (" (base)" if i == 1 else " (tip)" if i == 3 else "")) for i in (1, 2, 3)]))
class ANIM_PT_seated_hands(bpy.types.Panel):
    bl_label = "Seated hands"; bl_idname = "ANIM_PT_seated_hands"; bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'; bl_category = "Seated Hands"
    def draw(self, ctx):
        l = self.layout
        l.label(text="Click a name, then press R (rotate) in the viewport")
        for title, items in GROUPS:
            box = l.box(); box.label(text=title)
            col = box.column(align=True)
            for name, text in items:
                op = col.operator("anim.select_bone", text=f"{text}  [{name}]"); op.bone = name
for c in (ANIM_PT_seated_hands, ANIM_OT_select_phone, ANIM_OT_select_bone):
    try: bpy.utils.unregister_class(c)
    except Exception: pass
for c in (ANIM_OT_select_bone, ANIM_OT_select_phone, ANIM_PT_seated_hands): bpy.utils.register_class(c)
for w in bpy.context.window_manager.windows:
    for a in w.screen.areas:
        if a.type == 'VIEW_3D': a.spaces[0].show_region_ui = True
result = "panel registered"
