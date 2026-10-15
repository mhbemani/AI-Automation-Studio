"""aim_magic(target_rig_local): turn MAG_Root (child of RIG_Claude, at his hands) to the target (rig-local metres) and set the ring's `dist`.
magic_or_reach(targets): plan_reach on arm targets; when any side is 'magic' returns the aim data to use CLA_magic_cast + MAG_ring_shoot/wrap/fade."""
import bpy, os
from mathutils import Vector
def aim_magic(target):
    r = bpy.data.objects["MAG_Root"]; d = Vector(target) - r.location
    r.rotation_mode = 'QUATERNION'; r.rotation_quaternion = d.to_track_quat('-Y', 'Z'); r["dist"] = float(d.length)
    for o in bpy.data.objects:
        if o.name.startswith("MAG_"): o.update_tag()
    bpy.context.view_layer.update(); return d.length
