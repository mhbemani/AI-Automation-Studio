"""Rebind HUM_Body to RIG_Human's CURRENT bones (keeps hand-edited bone positions): clears old weights, reruns automatic weights.
Run: Blender -b --factory-startup character_selection_lab.blend --python scripts/rebind.py"""
import bpy
rig, body = bpy.data.objects["RIG_Human"], bpy.data.objects["HUM_Body"]
for ob in (body, rig):  # a file saved in Edit Mode binds to nothing (all-zero weights) unless we leave it first
    bpy.context.view_layer.objects.active = ob
    if ob.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.objects.active = rig
for m in [m for m in body.modifiers if m.type == 'ARMATURE']: body.modifiers.remove(m)
body.vertex_groups.clear()
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); rig.select_set(True)
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
print("BIND", len(body.vertex_groups), "groups; unweighted verts", sum(1 for v in body.data.vertices if not v.groups))
bpy.ops.wm.save_mainfile()
