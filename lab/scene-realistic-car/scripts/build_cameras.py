# Cameras + shot markers for the front-seat setup (creator, 2026-10-09: the human sits beside Claude; no mirror shots).
# Re-runnable; reads the characters' CURRENT eye positions (re-run after moving them); user_locked cameras are kept.
# Car-local frame: forward -Y, Claude (driver) +X, human (passenger) -X. Interior cameras are children of the car.
#   CAM_HUMAN_POV   (Claude speaks)  from the passenger side, ahead of Claude's face plane: Claude's face 3/4, driver
#                                    window and street behind him
#   CAM_CLAUDE_POV  (human speaks)   mirror image: the human's face 3/4, the right window and street behind him
#   CAM_INT_TwoShot (reactions)      from the dashboard: both, side by side
#   CAM_EST_Street, CAM_PHONE_CU     exterior pickup and the phone's chat screen (parented to the street human)
# Markers: one per shot of production/timeline.json, bound to its camera. 9:16 overrides in "v916" (set_aspect.py).
import bpy, json, os, math
from mathutils import Vector, Matrix

sc = bpy.context.scene
TL = json.load(open(os.path.join(os.path.dirname(bpy.data.filepath), "production", "timeline.json")))
car = bpy.data.objects["CAR_Exterior"]
for n in [o.name for o in bpy.data.objects if o.name.startswith("TMP_")]: bpy.data.objects.remove(bpy.data.objects[n])
probe = bpy.data.objects.get("CAR_MirrorProbe")
if probe: bpy.data.objects.remove(probe)            # no mirror shots any more
m = bpy.data.objects.get("CAR_RearViewMirror")
if m: m.animation_data_clear()

def camera(name, loc, target, lens, clip=0.05, parent=None, up=None):
    """loc/target in the parent's space (car-local for interior cameras, world otherwise)."""
    c = bpy.data.objects.get(name)
    if not c:
        c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); bpy.data.collections["04_CAMERAS"].objects.link(c)
    if c.get("user_locked"): return c
    c["cs_owner"] = "cameras"; c.pop("provisional", None)
    c.parent = parent; c.matrix_parent_inverse = Matrix(); c.animation_data_clear()
    for k in ("rest_loc", "rest_rot"): c.pop(k, None)
    d = Vector(target) - Vector(loc)
    if up is None: q = d.to_track_quat("-Z", "Y")
    else:
        z = -d.normalized(); x = Vector(up).cross(z).normalized(); q = Matrix((x, z.cross(x), z)).transposed().to_quaternion()
    c.location = loc; c.rotation_mode = "XYZ"; c.rotation_euler = q.to_euler()
    c.data.lens = lens; c.data.clip_start = clip; c.data.clip_end = 600; c.data.shift_x = c.data.shift_y = 0
    c.data.sensor_fit = "AUTO"
    return c

# --- interior: built at the first interior frame (seated human exists, car standing)
FI = next(s["startFrame"] for s in TL["shots"] if s["shot"] == "INT")
sc.frame_set(FI); bpy.context.view_layer.update()
CWI = car.matrix_world.inverted()
eyes_c = CWI @ (sum((bpy.data.objects[f"CHAR_Claude_Eye_{s}"].matrix_world @ Vector((0, 0, 0.07)) for s in "LR"), Vector()) / 2)
hum = bpy.data.objects["CHAR_Human"]; hb = hum.pose.bones["head"]
eyes_h = CWI @ (hum.matrix_world @ hb.head.lerp(hb.tail, 0.35) + hum.matrix_world.to_3x3() @ Vector((0, -0.09, 0)))   # rig faces -Y

cam_h = camera("CAM_HUMAN_POV", (-0.50, -0.66, 1.10), eyes_c + Vector((-0.06, 0.10, -0.12)), 17, parent=car)   # 3/4 front: his face needs a camera ahead of it
cam_c = camera("CAM_CLAUDE_POV", (0.26, -0.50, 1.08), eyes_h + Vector((0.0, 0.10, -0.16)), 22, parent=car)
cam_2 = camera("CAM_INT_TwoShot", (0.0, -0.80, 1.02), (0.0, 0.40, 0.92), 16, parent=car)
cam_h["v916"] = (22, 0.0, 0.0); cam_c["v916"] = (22, 0.0, 0.0); cam_2["v916"] = (11, 0.0, 0.0)

# --- exterior pickup: a long lens from 28 m down the street (parking lane, east of the pickup), looking west: the
# compression puts the human at the door and the car arriving head-on behind him in one frame, the human >=150 px tall
# at 960x540 (the stylised scene's human was ~50 px).
sc.frame_set(1); bpy.context.view_layer.update()
cam_e = camera("CAM_EST_Street", Vector((30.0, -5.6, 1.6)), Vector((3.0, -5.3, 1.05)), 95)
cam_e["v916"] = (130, -0.40, 0.0)   # vertical: the frame is ~half as wide; centred on the human (same size), the car enters right

# --- phone close-up: from just above his eyes onto the screen; parented to the street human (contract)
st, scr = bpy.data.objects["CHAR_Human_Street"], bpy.data.objects["PROP_Phone_Screen"]
kb = st.pose.bones["head"]
eye_w = st.matrix_world @ kb.head.lerp(kb.tail, 0.35)
S = scr.matrix_world; ctr = S @ Vector((0, 0, 0.069)); up = (S.to_3x3() @ Vector((0, 0, 1))).normalized()
loc = ctr + (eye_w - ctr).normalized() * 0.20
cam_p = camera("CAM_PHONE_CU", loc, ctr, 30, clip=0.01, up=up)   # screen fills the frame height
bpy.context.view_layer.update(); mw = cam_p.matrix_world.copy(); cam_p.parent = st; cam_p.matrix_parent_inverse = st.matrix_world.inverted(); cam_p.matrix_world = mw
cam_p["v916"] = (40, 0.0, 0.0)
for c in (cam_h, cam_c, cam_2, cam_e, cam_p): c["lens169"] = c.data.lens

# --- shot markers from the timeline (each switches the camera)
for mk in [mk for mk in sc.timeline_markers if mk.name.startswith("SHOT") or mk.name.startswith("S")]: sc.timeline_markers.remove(mk)
for s in TL["shots"]:
    sc.timeline_markers.new(f"{s['id']}_{s['camera'][4:]}", frame=s["startFrame"]).camera = bpy.data.objects[s["camera"]]
sc.frame_start, sc.frame_end = 1, TL["meta"]["totalFrames"]
sc.frame_set(1)
result = {"eyes_claude_car": [round(v, 2) for v in eyes_c], "eyes_human_car": [round(v, 2) for v in eyes_h],
          "markers": len(sc.timeline_markers), "frames": sc.frame_end, "first_interior": FI}
