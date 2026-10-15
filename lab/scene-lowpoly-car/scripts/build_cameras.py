# Interior cameras + rear-view mirror aim + mirror reflection mode. Re-runnable; reads the
# characters' CURRENT eye positions, so it follows the creator's edits (re-run after moving them).
# Car-local frame: forward -Y, driver (Claude) +X, human back right -X.
import bpy, math
from mathutils import Vector, Matrix

MIRROR_MODE = "probe"   # "probe": planar light probe (true mirror view) | "ssr": screen-space ray tracing only

import json, os
sc = bpy.context.scene
# Interior part is built at the first interior frame: the car stands at the pickup (heading +X, as when first built), poses are
# neutral, and the seated human exists (animate.py hides him before that frame; hidden objects are not evaluated).
_tl = json.load(open(os.path.join(os.path.dirname(bpy.data.filepath), "production", "timeline.json")))
FI = next((s["startFrame"] for s in _tl["shots"] if s["shot"] == "INT"), 1)
sc.frame_set(FI); bpy.context.view_layer.update()
car = bpy.data.objects["CAR_Exterior"]; CW = car.matrix_world
L = lambda v: CW @ Vector(v)   # car-local -> world

def eyes_claude():
    e = [bpy.data.objects[f"CHAR_Claude_Eye_{s}"] for s in "LR"]
    return sum((o.matrix_world @ Vector((0, 0, 0.065)) for o in e), Vector()) / 2

def eyes_human():
    a = bpy.data.objects["CHAR_Human"].evaluated_get(bpy.context.evaluated_depsgraph_get()); pb = a.pose.bones["Head"]   # evaluated: the original's pose data can be stale after a frame change
    return a.matrix_world @ (pb.head.lerp(pb.tail, 0.45) + Vector((0.1, 0, 0)))   # rig +X = his forward

def camera(name, loc, target, lens, clip=0.05, parent=car):
    c = bpy.data.objects.get(name)
    if not c:
        c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); bpy.data.collections["04_CAMERAS"].objects.link(c)
    if c.get("user_locked"): return c
    c.parent = parent   # interior cameras follow the car; world placement below either way
    c.matrix_parent_inverse = parent.matrix_world.inverted() if parent else Matrix()
    c.animation_data_clear()   # animate.py re-keys its handheld drift; its rest_loc/rest_rot props are stale after a rebuild
    for k in ("rest_loc", "rest_rot"): c.pop(k, None)
    c.location = loc
    c.rotation_mode = "XYZ"; c.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    c.data.lens = lens; c.data.clip_start = clip; c.data.clip_end = 400
    return c

C, H = eyes_claude(), eyes_human()
mirror = bpy.data.objects["CAR_RearViewMirror"]; glass = bpy.data.objects["CAR_RearViewMirror_Glass"]
M = glass.matrix_world @ Vector((0, 0.001, 0.047))   # glass face centre

# CAM_HUMAN_POV: beside his head (0.35 m to his right, just under the roof): at his eyes Claude filled the
# frame. Frames Claude's right/back on the left third, the mirror (Claude's eyes) upper centre, the road.
# Picked from 6 tested positions (2026-10-08, see SCENE_NOTES).
cam_h = camera("CAM_HUMAN_POV", L((-0.8, 0.92, 2.02)), L((0.12, -0.6, 1.72)), 33)
# CAM_CLAUDE_POV: Claude's eye line but 0.4 m further back (the cabin is short; a camera AT the eyes cannot
# fit the mirror in frame). clip_start 0.45 cuts Claude's own body out of the shot; the road, the wheel
# and the mirror stay in.
cam_c = camera("CAM_CLAUDE_POV", C + (CW.to_3x3() @ Vector((-0.04, 0.4, 0.12))), L((0.05, -3.0, 1.7)), 24, clip=0.45)
# 9:16 (Shorts) overrides, applied by scripts/set_aspect.py: (lens, shift_x, shift_y). 16:9 uses lens above, no shift.
cam_h["v916"] = (56, -0.06, 0.01)   # 33 mm in 9:16 shows the roof lining and the headrest
cam_c["v916"] = (24, 0.07, 0.0)     # brings the mirror back in from the right edge
for c in (cam_h, cam_c): c.data.shift_x = c.data.shift_y = 0; c["lens169"] = c.data.lens

# Mirror aim per shot (film cheat: the mirror re-angles at each cut, nobody sees it). The normal bisects
# camera -> mirror -> the other character's eyes. Stored on the mirror and keyframed at the
# shot markers below. Camera .location is world here (parent inverse).
mirror.rotation_mode = "XYZ"   # glass faces the mirror's local +Y
def aim(cam_pos, eyes):
    n = ((cam_pos - M).normalized() + (eyes - M).normalized()).normalized()
    return tuple((CW.to_3x3().inverted() @ n).to_track_quat("Y", "Z").to_euler())
mirror["M_local"] = tuple(CW.inverted() @ M)   # glass centre in car space: animate.py re-aims the mirror per frame from it
mirror["aim_CAM_HUMAN_POV"] = aim(cam_h.location, C)
mirror["aim_CAM_CLAUDE_POV"] = aim(cam_c.location, H)

# Reflection mode.
ee = sc.eevee; ee.use_raytracing = True; ee.ray_tracing_method = "SCREEN"
ee.ray_tracing_options.resolution_scale = "1"
probe = bpy.data.objects.get("CAR_MirrorProbe")
if MIRROR_MODE == "probe":
    if not probe:
        probe = bpy.data.objects.new("CAR_MirrorProbe", bpy.data.lightprobes.new("CAR_MirrorProbe", "PLANE"))
        bpy.data.collections["02_CAR"].objects.link(probe)
    probe.parent = glass; probe.location = (0, 0.002, 0.047)   # just in front of the glass face
    probe.rotation_euler = (math.radians(-90), 0, 0)   # probe normal (local +Z) -> glass +Y
    probe.scale = (0.17, 0.047, 1); probe.data.clip_start = 0.01; probe.data.influence_distance = 0.05
    probe["cs_owner"] = "car"
elif probe:
    bpy.data.objects.remove(probe)

# Exterior establishing shot: from the north sidewalk, west of the exit building, looking across the street
# at its door, the human, and the pickup spot (the car arrives from behind the camera, west).
camera("CAM_EST_Street", Vector((-10, 7, 2.2)), Vector((4, -6, 1.8)), 24, parent=None)

sc.frame_set(1); bpy.context.view_layer.update()   # the street human only exists before the first interior shot
# Phone close-up: turn the phone's screen (its -Y) toward his face, then shoot over his right shoulder.
st, ph = bpy.data.objects["CHAR_Human_Street"], bpy.data.objects["PROP_Phone"]
hb, kb = st.pose.bones["RightHand"], st.pose.bones["Head"]
hand = st.matrix_world @ hb.tail; head = st.matrix_world @ kb.head.lerp(kb.tail, 0.45)
to_face = (head - hand).normalized()
if not ph.get("user_locked"):
    ph.matrix_world = Matrix.Translation(hand + to_face * 0.03) @ (-to_face).to_track_quat("Y", "Z").to_matrix().to_4x4()
bpy.context.view_layer.update()
fwd = st.matrix_world.to_3x3() @ Vector((1, 0, 0))   # rig +X is his forward
tgt = ph.matrix_world @ Vector((0, 0, 0.08))   # centre of the screen
cam0 = head + fwd * 0.12 + Vector((0, 0, 0.04))
camera("CAM_PHONE_CU", tgt + (cam0 - tgt) * 0.62, tgt, 40, clip=0.02, parent=None)   # 62% of the way: the message fills the frame

# Shot markers (placeholder timing, 24 fps; real timing comes from the voice track). Each marker switches
# the camera; the mirror angle is keyframed (constant) at each interior cut.
SHOTS = [(1, "CAM_EST_Street"), (73, "CAM_PHONE_CU"), (121, "CAM_EST_Street"), (193, "CAM_HUMAN_POV"),
         (265, "CAM_CLAUDE_POV"), (337, "CAM_HUMAN_POV"), (409, "CAM_CLAUDE_POV")]
for mk in [mk for mk in sc.timeline_markers if mk.name.startswith("SHOT")]: sc.timeline_markers.remove(mk)
mirror.animation_data_clear()
for i, (f, cn) in enumerate(SHOTS):
    sc.timeline_markers.new(f"SHOT{i + 1:02d}_{cn[4:]}", frame=f).camera = bpy.data.objects[cn]
    if "aim_" + cn in mirror:
        mirror.rotation_euler = mirror["aim_" + cn]; mirror.keyframe_insert("rotation_euler", frame=f)
for fc in mirror.animation_data.action.fcurves:
    for k in fc.keyframe_points: k.interpolation = "CONSTANT"
sc.frame_start, sc.frame_end = 1, 480
sc.frame_set(1)

result = {"claude_eyes": [round(v, 2) for v in C], "human_eyes": [round(v, 2) for v in H],
          "mirror": [round(v, 2) for v in M]}
