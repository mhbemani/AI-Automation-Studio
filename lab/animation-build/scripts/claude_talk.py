"""Talk pulse helpers (run inside Blender). The pulse is driven by the ctrl property `talk` (0..1).
bake_talk(rig, envelope, start_frame=1, fps=24, env_rate=None): keys `talk` on the rig, one key per frame, from an audio envelope
(list of floats 0..1; env_rate = samples per second of the envelope, default = fps). Replaces the keys it owns on `talk`."""
import bpy
def bake_talk(rig, envelope, start_frame=1, fps=24, env_rate=None, gain=1.0, smooth=0.0):
    env_rate = env_rate or fps
    ctrl = rig.pose.bones["ctrl"]
    if rig.animation_data is None: rig.animation_data_create()
    if rig.animation_data.action is None: rig.animation_data.action = bpy.data.actions.new("CLA_talk_baked")
    act = rig.animation_data.action
    for fc in list(act.fcurves):
        if fc.data_path == 'pose.bones["ctrl"]["talk"]': act.fcurves.remove(fc)
    n = int(len(envelope) / env_rate * fps)
    prev = 0.0
    for i in range(n + 1):
        t = i / fps; k = min(len(envelope) - 1, int(round(t * env_rate)))
        v = max(0.0, min(1.0, envelope[k] * gain))
        v = prev * smooth + v * (1 - smooth); prev = v
        ctrl["talk"] = v; ctrl.keyframe_insert('["talk"]', frame=start_frame + i)
    for fc in act.fcurves:
        if fc.data_path == 'pose.bones["ctrl"]["talk"]':
            for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
    return n + 1
