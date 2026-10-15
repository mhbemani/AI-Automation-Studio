"""Make the current pose the new rest pose: the mesh keeps the posed shape as its real shape (Edit Mode shows it),
the bones' rest positions move to the pose, weights unchanged. Run: Blender -b --factory-startup <blend> --python scripts/apply_pose_as_rest.py"""
import bpy
o = bpy.data.objects["HUM_Body"]; rig = bpy.data.objects["RIG_Human"]
for ob in (o, rig):
    bpy.context.view_layer.objects.active = ob
    if ob.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
posed = [p.name for p in rig.pose.bones if not p.matrix_basis.is_identity]
ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
assert len(ev.vertices) == len(o.data.vertices)
co = [v.co.copy() for v in ev.vertices]
for v, c in zip(o.data.vertices, co): v.co = c
o.data.update()
bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='POSE')
bpy.ops.pose.select_all(action='SELECT'); bpy.ops.pose.armature_apply(selected=False)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.update()
ev2 = o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
drift = max((a.co - b).length for a, b in zip(ev2.vertices, co))
print("REST applied pose of", posed, "| max drift after", round(drift * 1000, 3), "mm")
bpy.ops.wm.save_mainfile()
