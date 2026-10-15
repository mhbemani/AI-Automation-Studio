# Shared helpers for drive_car.py / animate.py (loaded with exec; no imports of ours needed).
# Animation here is plain F-curves with one key per frame (linear) or per cut (constant): they render the same in
# the GUI and in `blender -b`, with no drivers, handlers or add-ons. Actions are named ANIM_* and are ours:
# every run deletes the previous ANIM_* action of an ID before writing a new one.
import bpy, json, os, math, random

BLEND_DIR = os.path.dirname(bpy.data.filepath)
PROD = os.path.join(BLEND_DIR, "production")
TL = json.load(open(os.path.join(PROD, "timeline.json")))
FPS = TL["meta"]["fps"]; N = TL["meta"]["totalFrames"]
CUES = TL["motionCues"]; SHOTS = TL["shots"]
FRAMES = list(range(1, N + 1))

def new_action(idb, name=None):
    """Fresh ANIM_<name> action on `idb` (object, curve data...), slot assigned. A foreign action is left alone (returns None)."""
    ad = idb.animation_data_create()
    if ad.action is not None and not ad.action.name.startswith("ANIM_"):
        return None
    if ad.action is not None: bpy.data.actions.remove(ad.action)
    act = bpy.data.actions.new("ANIM_" + (name or idb.name)); ad.action = act
    ad.action_slot = act.slots.new(idb.id_type, idb.name)
    return act

def get_action(idb, name=None):
    """The ANIM_* action already on `idb` (this run), else a fresh one; None if the ID has someone else's action."""
    ad = idb.animation_data
    if ad and ad.action and ad.action.name.startswith("ANIM_"): return ad.action
    return new_action(idb, name)

def key(act, path, idx, frames, values, interp="LINEAR"):
    if act is None: return None
    old = act.fcurves.find(path, index=idx)
    if old: act.fcurves.remove(old)
    fc = act.fcurves.new(path, index=idx)
    fc.keyframe_points.add(len(frames))
    co = []
    for f, v in zip(frames, values): co += [f, v]
    fc.keyframe_points.foreach_set("co", co)
    for k in fc.keyframe_points: k.interpolation = interp
    fc.update(); return fc

def smoothstep(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)

def travelled(f, D=15.0, speed=8.5, accel_s=3.5):
    """Metres travelled along the path, 0 = the pickup stop. See drive_car.py for the phases."""
    a, st, ds = CUES["car_arrive_start"], CUES["car_stopped"], CUES["drive_start"]
    T = (st - a) / FPS; v0 = 2 * D / T
    if f <= a: return -D - v0 * (a - f) / FPS
    if f <= st:
        u = (f - a) / (st - a); return -D + D * (2 * u - u * u)
    if f <= ds: return 0.0
    t = (f - ds) / FPS; x = min(t / accel_s, 1.0)
    return speed * accel_s * (x ** 3 - x ** 4 / 2) + speed * max(t - accel_s, 0.0)
