"""Cushion rig: CUS_Cushion (copy of the lineup's V3-A cushion, scale baked) parented to RIG_Claude (object), driven by the ctrl properties cus_*:
on the ground under his feet (he stands at root hop = top height 0.215) / hugged upright in front of him / thrown to its resting place (cus_dx/dy/dz, relative to his origin), with a Squash shape key that
follows how deep his feet sink into it. Idempotent. Run via bridge after 04_claude_rig.py."""
import bpy, math
from mathutils import Matrix
rig = bpy.data.objects["RIG_Claude"]
src = bpy.data.objects["LU_V3A_Cushion"]
old = bpy.data.objects.get("CUS_Cushion")
if old: bpy.data.objects.remove(old)
for m in list(bpy.data.meshes):
    if m.name.startswith("CUS_"): bpy.data.meshes.remove(m)
o = src.copy(); o.data = src.data.copy(); o.data.name = "CUS_Cushion"; o.name = "CUS_Cushion"; o["anim_owner"] = "claude"
if o.data.shape_keys: o.data.shape_keys.name = "CUS_Cushion_keys"
col = bpy.data.collections.get("CUSHION") or bpy.data.collections.new("CUSHION")
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
col.objects.link(o)
o.parent = None; o.matrix_world = Matrix.Identity(4); o.scale = src.scale
bpy.context.view_layer.update()
# bake the (non-uniform) scale into the mesh, including the Squash key
o.hide_viewport = False; o.hide_render = False; o.hide_set(False)
bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
o.location = (0, 0, 0); bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
for k in ("squash_manual", "rigify_owner_rig"):
    if k in o: del o[k]
zmax = max(v.co.z for v in o.data.vertices); zmin = min(v.co.z for v in o.data.vertices)
o["top_offset"] = zmax
o.parent = rig; o.matrix_parent_inverse = Matrix.Identity(4); o.location = (0, 0, -zmax)
o.rotation_mode = 'XYZ'; o.animation_data_clear()
def drv(path, idx, expr, props, obj=o):
    fc = obj.driver_add(path, idx) if idx is not None else obj.driver_add(path); d = fc.driver; d.type = 'SCRIPTED'; d.expression = expr
    for p in props:
        v = d.variables.new(); v.name = p; v.type = 'SINGLE_PROP'; v.targets[0].id = rig; v.targets[0].data_path = f'pose.bones["ctrl"]["{p}"]'
for i in range(3): drv("scale", i, "1.0 if cus_show > 0.5 else 0.0001", ["cus_show"])
HELD = (0.0, -0.30, 0.27)
# position: start place = under his feet (top at his feet) or hugged in front; thrown: moves to the resting place with an arc
drv("location", 0, f"(1-cus_toss)*cus_held*{HELD[0]} + cus_toss*cus_dx", ["cus_held", "cus_toss", "cus_dx"])
drv("location", 1, f"(1-cus_toss)*cus_held*{HELD[1]} + cus_toss*cus_dy", ["cus_held", "cus_toss", "cus_dy"])
drv("location", 2, f"(1-cus_toss)*((1-cus_held)*({-zmin}) + cus_held*{HELD[2]}) + cus_toss*cus_dz + cus_arc", ["cus_held", "cus_toss", "cus_dz", "cus_arc"])
drv("rotation_euler", 0, "radians(90*cus_held*(1-cus_toss)) + radians(cus_tumble)", ["cus_held", "cus_toss", "cus_tumble"])
# squash shape key: depth of his feet below the cushion top (root bone world z), only while he stands on it, plus the manual value
sk = o.data.shape_keys.key_blocks["Squash"]
if o.data.shape_keys.animation_data:
    for fc in list(o.data.shape_keys.animation_data.drivers): o.data.shape_keys.animation_data.drivers.remove(fc)
fc = sk.driver_add("value"); d = fc.driver; d.type = 'SCRIPTED'
d.expression = f"(1-cus_held)*max(0, min(1, (cz + {zmax} - rz)/0.115)) + cus_squash"
for name, tgt, path in (("cus_held", None, 'pose.bones["ctrl"]["cus_held"]'), ("cus_squash", None, 'pose.bones["ctrl"]["cus_squash"]')):
    v = d.variables.new(); v.name = name; v.type = 'SINGLE_PROP'; v.targets[0].id = rig; v.targets[0].data_path = path
v = d.variables.new(); v.name = "cz"; v.type = 'TRANSFORMS'; v.targets[0].id = o; v.targets[0].transform_type = 'LOC_Z'; v.targets[0].transform_space = 'WORLD_SPACE'
v = d.variables.new(); v.name = "rz"; v.type = 'TRANSFORMS'; v.targets[0].id = rig; v.targets[0].bone_target = "root"; v.targets[0].transform_type = 'LOC_Z'; v.targets[0].transform_space = 'WORLD_SPACE'
o.data.shape_keys.id_data.use_fake_user = False
bpy.context.view_layer.update()
result = {"zmax": round(zmax, 3), "zmin": round(zmin, 3), "dims": [round(x, 3) for x in o.dimensions], "mats": [m.name for m in o.data.materials]}
