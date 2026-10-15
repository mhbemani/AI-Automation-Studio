"""Shared camera/render presets (used by build_stage.py, render_clip.py, stills.py)."""
import bpy, math
from math import radians as rad
from mathutils import Vector

CAMERAS = {   # name: (target_z, frame_height_in_units, azimuth_deg, elevation_deg, default_aspect)
    "full":   (1.20, 3.45, 24, 9, "16:9"),     # character ~70% of frame height
    "half":   (1.78, 2.15, 20, 5, "16:9"),     # waist-up
    "corner": (1.22, 2.95, 24, 9, "1:1"),      # tight full body for picture-in-picture
}
QUALITY = {   # preset: (short_side_px, samples)
    "draft": (720, 16), "final": (1080, 32),
}
ASPECTS = {"16:9": (16, 9), "9:16": (9, 16), "1:1": (1, 1)}
LENS = 50

def resolution(preset, aspect):
    short, _ = QUALITY[preset]; w, h = ASPECTS[aspect]
    k = short / min(w, h)
    return int(round(w * k / 2) * 2), int(round(h * k / 2) * 2)

def apply(scene, cam_obj, camera, preset, aspect=None):
    tz, vis_h, az, el, dasp = CAMERAS[camera]
    aspect = aspect or dasp
    sc = scene; w, h = resolution(preset, aspect)
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, 100
    sc.render.fps = 30
    sc.eevee.taa_render_samples = QUALITY[preset][1]
    cam = cam_obj.data; cam.lens = LENS; cam.sensor_fit = 'AUTO'; cam.sensor_width = 36
    d = vis_h * LENS / (36 * h / max(w, h))              # distance so frame height == vis_h
    # narrow portrait: make sure the character also fits horizontally (width ~2.4 incl. raised arms)
    d = max(d, 3.0 * LENS / (36 * w / max(w, h)))
    a, e = rad(az), rad(el)
    pos = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * d + Vector((0, 0, tz))
    cam_obj.location = pos
    cam_obj.rotation_euler = (Vector((0, 0, tz)) - pos).to_track_quat('-Z', 'Y').to_euler()
    cam.clip_start, cam.clip_end = 0.5, 60
    sc.camera = cam_obj
