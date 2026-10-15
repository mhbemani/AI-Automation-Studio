"""blender -b facet.blend -P render_clip.py -- --timeline t.json --out out/name --preset draft|final --camera full|half|corner
       [--audio narration.wav | --mouth mouth.json] [--aspect 16:9|9:16|1:1] [--keep-frames] [--png-only] [--mux-audio]
Timeline: {"fps":30,"duration":12.0,"events":[{"t":0,"action":"enter"},{"t":1,"action":"talk"},...]}
An event's action runs until the next event (loops repeat, one-shots fall back to a 'talk' loop; 'exit' holds its last pose)."""
import bpy, sys, os, json, shutil, subprocess, argparse, time
from mathutils import Vector, Euler
from math import radians as rad
HERE = os.path.dirname(os.path.abspath(bpy.data.filepath)) if bpy.data.filepath else os.getcwd()
sys.path.insert(0, HERE)
import stagecfg, lipsync

FPS = 30; XFADE = 6   # frames of cross-fade between actions
rig = bpy.data.objects["FacetRig"]; sc = bpy.context.scene
VALID = sorted(a.name for a in bpy.data.actions if a.name != "lipsync")

def die(msg): print("\nERROR: " + msg, file=sys.stderr); sys.stdout.flush(); sys.exit(2)

ap = argparse.ArgumentParser(prog="render_clip.py")
ap.add_argument("--timeline", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--preset", choices=list(stagecfg.QUALITY), default="draft")
ap.add_argument("--camera", choices=list(stagecfg.CAMERAS), default="full")
ap.add_argument("--aspect", choices=list(stagecfg.ASPECTS)); ap.add_argument("--audio"); ap.add_argument("--mouth")
ap.add_argument("--keep-frames", action="store_true"); ap.add_argument("--png-only", action="store_true")
ap.add_argument("--mux-audio", action="store_true", help="also put the narration into the webm (default: video only)")
ap.add_argument("--max-frames", type=int, help="debug: render only the first N frames")
try: args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:])
except SystemExit as e: sys.exit(2)

# ---- validate timeline up front
try: tl = json.load(open(args.timeline))
except Exception as e: die("cannot read timeline %s: %s" % (args.timeline, e))
if tl.get("fps", FPS) != FPS: die("timeline fps must be %d (actions are authored at %d fps), got %r" % (FPS, FPS, tl.get("fps")))
dur = tl.get("duration")
if not isinstance(dur, (int, float)) or dur <= 0: die("timeline.duration must be a positive number of seconds")
ev = tl.get("events")
if not isinstance(ev, list) or not ev: die("timeline.events must be a non-empty list")
last = -1
for i, e in enumerate(ev):
    if not isinstance(e, dict) or "t" not in e or "action" not in e: die('events[%d] needs {"t": seconds, "action": name}' % i)
    if e["action"] not in VALID: die("events[%d]: unknown action %r. Valid actions: %s" % (i, e["action"], ", ".join(VALID)))
    if not isinstance(e["t"], (int, float)) or e["t"] < last or e["t"] >= dur: die("events[%d].t=%r must be ascending and < duration (%s)" % (i, e["t"], dur))
    last = e["t"]
if args.audio and not os.path.exists(args.audio): die("audio file not found: " + args.audio)

# ---- mouth data (before any rendering)
mouth = None
if args.mouth: mouth = json.load(open(args.mouth))
elif args.audio:
    env = lipsync.envelope(args.audio, FPS); b, n = lipsync.accents(env, FPS); mouth = {"frames": env, "blinks": b, "nods": n}

N = int(round(dur * FPS)); sc.frame_start, sc.frame_end = 1, N
ad = rig.animation_data or rig.animation_data_create(); ad.action = None
for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)

# ---- chain actions with NLA: one track per event (later = higher = fades in over the earlier)
segs = []   # (action, t0, t1)
for i, e in enumerate(ev):
    t0 = e["t"]; t1 = ev[i + 1]["t"] if i + 1 < len(ev) else dur
    a = bpy.data.actions[e["action"]]; alen = (a["frames"] - 1) / FPS
    if a["loop"] or t1 - t0 <= alen: segs.append((a, t0, t1, a["loop"]))
    else:
        segs.append((a, t0, t0 + alen, False))
        if e["action"] != "exit": segs.append((bpy.data.actions["talk"], t0 + alen, t1, True))   # hold-in-character filler
        else: segs[-1] = (a, t0, t1, False)
if ev[0]["t"] > 0: segs.insert(0, (bpy.data.actions["enter" if ev[0]["action"] == "enter" else "idle"], 0, ev[0]["t"], False))
for k, (a, t0, t1, loop) in enumerate(segs):
    tr = ad.nla_tracks.new(); tr.name = "%02d_%s" % (k, a.name)
    alen = (a["frames"] - 1) / FPS
    end = t1 + (XFADE / FPS if k + 1 < len(segs) else 0)
    s = tr.strips.new(a.name, int(round(1 + t0 * FPS)), a)
    s.action_frame_start, s.action_frame_end = 1, a["frames"]
    length = (end - t0) * FPS
    if loop: s.repeat = max(1.0, length / (a["frames"] - 1)); s.use_sync_length = False
    s.frame_end = 1 + t0 * FPS + (length if loop else min(length, a["frames"] - 1))
    if k > 0: s.blend_in = XFADE; s.blend_type = 'REPLACE'
    s.extrapolation = 'HOLD' if k == 0 else 'HOLD_FORWARD' if k + 1 == len(segs) else 'NOTHING'
    if not loop and k + 1 == len(segs): s.extrapolation = 'HOLD_FORWARD'

# ---- lipsync layers: mouth (replace) + blink/nod (combine, multiplies scale / composes rotation)
def local_scale(bone, wz):
    m = rig.data.bones[bone].matrix_local.to_3x3().inverted() @ Vector((1, 1, wz)); return [abs(x) for x in m]
def local_q(bone, e):
    m = rig.data.bones[bone].matrix_local.to_3x3(); return (m.inverted() @ Euler([rad(a) for a in e]).to_matrix() @ m).to_quaternion()
def make_layer(name, blend, fill):
    a = bpy.data.actions.new(name); ad.action = a
    for bn in ("mouth", "eye_L", "eye_R", "head"): rig.pose.bones[bn].rotation_mode = 'QUATERNION'
    fill()
    ad.action = None
    tr = ad.nla_tracks.new(); tr.name = name; s = tr.strips.new(name, 1, a); s.blend_type = blend
    s.frame_end = max(s.frame_end, N + 1); s.extrapolation = 'HOLD_FORWARD'
if mouth:
    fr = mouth["frames"]
    def f_mouth():
        pb = rig.pose.bones["mouth"]
        for i in range(N):
            v = fr[i] if i < len(fr) else 0.0
            pb.scale = local_scale("mouth", 0.14 + 0.86 * v); pb.keyframe_insert("scale", frame=i + 1)
    def f_blink():
        eyes = [rig.pose.bones["eye_L"], rig.pose.bones["eye_R"]]; head = rig.pose.bones["head"]
        bl = mouth.get("blinks", []); nods = mouth.get("nods", [])
        for i in range(N):
            t = i / FPS
            z = 1.0
            for b in bl:
                if b <= t <= b + 0.16: z = 1 - 0.88 * __import__("math").sin(__import__("math").pi * (t - b) / 0.16)
            nd = 0.0
            for n in nods:
                if n - 0.05 <= t <= n + 0.35: nd = 5.0 * __import__("math").sin(__import__("math").pi * (t - n + 0.05) / 0.4)
            for e in eyes: e.scale = local_scale("eye_L", z); e.keyframe_insert("scale", frame=i + 1)
            head.rotation_quaternion = local_q("head", (nd, 0, 0)); head.keyframe_insert("rotation_quaternion", frame=i + 1)
    make_layer("lipsync", 'REPLACE', f_mouth); make_layer("blink_nod", 'COMBINE', f_blink)

# ---- camera / quality, render
cam = bpy.data.objects["STAGE_camera"]; stagecfg.apply(sc, cam, args.camera, args.preset, args.aspect)
out = os.path.abspath(args.out); os.makedirs(out, exist_ok=True)
for f in os.listdir(out):
    if f.startswith("f_") and f.endswith(".png"): os.remove(os.path.join(out, f))
sc.render.filepath = os.path.join(out, "f_")
if args.max_frames: sc.frame_end = min(N, args.max_frames)
t0 = time.time(); bpy.ops.render.render(animation=True); t_render = time.time() - t0
print("RENDER_SECONDS %.1f frames %d %dx%d" % (t_render, sc.frame_end, sc.render.resolution_x, sc.render.resolution_y))
if args.png_only: print("PNG sequence:", out); sys.exit(0)

ff = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
webm = out.rstrip("/") + ".webm"
cmd = [ff, "-v", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(out, "f_%04d.png")]
if args.mux_audio and args.audio: cmd += ["-i", args.audio, "-c:a", "libopus", "-b:a", "96k", "-shortest"]
cmd += ["-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "28", "-auto-alt-ref", "0", "-row-mt", "1", "-deadline", "good", "-cpu-used", "4", webm]
t0 = time.time(); subprocess.run(cmd, check=True); print("ENCODE_SECONDS %.1f -> %s (%.2f MB)" % (time.time() - t0, webm, os.path.getsize(webm) / 1e6))
if not args.keep_frames:
    for f in os.listdir(out):
        if f.startswith("f_") and f.endswith(".png"): os.remove(os.path.join(out, f))
    os.rmdir(out)
