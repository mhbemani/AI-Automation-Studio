"""Blender side of the performance system: apply solver channels (WORLD-aligned rotation / location / scale relative to the parent bone) to the rig.
The same conversion the character lab's baker used: bone-local = M^-1 * world-aligned * M with M = the bone's rest basis."""
import bpy
from mathutils import Vector, Quaternion

class Rig:
    def __init__(self, name="FacetRig"):
        self.obj = bpy.data.objects[name]; self.M = {b.name: b.matrix_local.to_3x3() for b in self.obj.data.bones}
        self.Mi = {k: m.inverted() for k, m in self.M.items()}
        for pb in self.obj.pose.bones: pb.rotation_mode = 'QUATERNION'
        ad = self.obj.animation_data or self.obj.animation_data_create(); ad.action = None
        for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
    def local(self, bone, q=None, l=None, s=None):
        M, Mi = self.M[bone], self.Mi[bone]; o = {}
        if q is not None: o["q"] = (Mi @ Quaternion(q).to_matrix() @ M).to_quaternion()
        if l is not None: o["l"] = Mi @ Vector(l)
        if s is not None: o["s"] = Vector([abs(x) for x in (Mi @ Vector(s))])
        return o
    def pose_frame(self, ch, i, frame=None):
        """set every driven bone to channel sample i; keyframe it when frame is given"""
        for bone, c in ch.items():
            pb = self.obj.pose.bones[bone]
            v = self.local(bone, c["q"][i] if "q" in c else None, c["l"][i] if "l" in c else None, c["s"][i] if "s" in c else None)
            if "q" in v: pb.rotation_quaternion = v["q"]
            if "l" in v: pb.location = v["l"]
            if "s" in v: pb.scale = v["s"]
            if frame is not None:
                if "q" in v: pb.keyframe_insert("rotation_quaternion", frame=frame)
                if "l" in v: pb.keyframe_insert("location", frame=frame)
                if "s" in v: pb.keyframe_insert("scale", frame=frame)
