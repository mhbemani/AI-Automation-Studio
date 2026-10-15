import bpy, math
from mathutils import Vector as V
def setp(**kw):
    rig = bpy.data.objects["RIG_Claude"]; c = rig.pose.bones["ctrl"]
    for k, v in kw.items(): c[k] = v
    rig.update_tag(); bpy.context.view_layer.update()
def reset():
    rig = bpy.data.objects["RIG_Claude"]; c = rig.pose.bones["ctrl"]
    exec(open("scripts/04_claude_rig.py").read().split("PROPS = {")[0].split("def cleanup")[0], {}) if False else None
    for k in list(c.keys()):
        try: c[k] = c.id_properties_ui(k).as_dict()["default"]
        except Exception: pass
    for pb in rig.pose.bones:
        if pb.name != "ctrl": pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0)
    rig.update_tag(); bpy.context.view_layer.update()
def ev():
    return bpy.data.objects["RIG_Claude"].evaluated_get(bpy.context.evaluated_depsgraph_get())
def tail(bone): return V(ev().pose.bones[bone].tail)
def scale(bone): return tuple(round(x, 3) for x in ev().pose.bones[bone].scale)
def head(bone):
    rig = bpy.data.objects["RIG_Claude"]; return rig.pose.bones[bone].head
r3 = lambda v: tuple(round(x, 3) for x in v)
