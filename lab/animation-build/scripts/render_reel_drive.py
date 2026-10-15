"""Host: reel of Claude driving (car interior cutaway, car wheel actions play with him). python3 scripts/render_reel_drive.py"""
import subprocess, os, sys, shutil, glob
from PIL import Image, ImageDraw
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BL = [sys.executable, os.path.join(D, "bridge", "bl.py")]
FR = f"{D}/previews/reel_frames"; os.makedirs(FR, exist_ok=True)
def bl(code):
    r = subprocess.run(BL + ["exec", code], capture_output=True, text=True, cwd=D)
    if r.returncode: print("ERR", r.stderr[-500:])
SETUP = open(f"{D}/scripts/drive_sheet.py").read().split("SETUP = '''")[1].split("'''")[0] + '''
sc=bpy.context.scene; sc.render.resolution_x=960; sc.render.resolution_y=540; sc.render.resolution_percentage=100; sc.eevee.taa_render_samples=8; sc.render.image_settings.file_format="PNG"; sc.render.fps=24
'''
def clip(name, strips, n):
    d = f"{FR}/dr_{name}"; shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    code = f'''
for o in (bpy.data.objects["RIG_Claude"], bpy.data.objects["CAR_ctrl"]):
    ad=o.animation_data_create(); ad.action=None
    for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
for o,(an,st) in {strips!r}:
    pass
'''
    code = f'''
S={strips!r}
for oname,(an,st) in S:
    o=bpy.data.objects[oname]; ad=o.animation_data_create(); ad.action=None
    for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
for oname,(an,st) in S:
    o=bpy.data.objects[oname]; s=o.animation_data.nla_tracks.new().strips.new(an,st,bpy.data.actions[an]); s.extrapolation="HOLD"
sc=bpy.context.scene; sc.frame_start=1; sc.frame_end={n}; sc.render.filepath="{d}/f_"
bpy.ops.render.render(animation=True)
for oname,(an,st) in S:
    for t in list(bpy.data.objects[oname].animation_data.nla_tracks): bpy.data.objects[oname].animation_data.nla_tracks.remove(t)
'''
    bl(code); return d
def label(png, text, out):
    im = Image.open(png).convert("RGB"); dr = ImageDraw.Draw(im); dr.rectangle((0, 0, 960, 26), fill=(20, 20, 20)); dr.text((8, 7), text, fill=(255, 230, 80)); im.save(out)
bl(SETUP)
clips = [("CLA_drive_hold_wheel + CAR_steering_sway (one loop)", clip("hold", [("RIG_Claude", ("CLA_drive_hold_wheel", 1)), ("CAR_ctrl", ("CAR_steering_sway", 1))], 96), 4),
         ("CLA_drive_steer_right + CAR_steering_turn_right", clip("sr", [("RIG_Claude", ("CLA_drive_steer_right", 1)), ("CAR_ctrl", ("CAR_steering_turn_right", 1))], 24), 12),
         ("CLA_drive_steer_left + CAR_steering_turn_left", clip("sl", [("RIG_Claude", ("CLA_drive_steer_left", 1)), ("CAR_ctrl", ("CAR_steering_turn_left", 1))], 24), 12),
         ("CLA_drive_hands_off", clip("off", [("RIG_Claude", ("CLA_drive_hands_off", 1))], 18), 12),
         ("CLA_talk_arm_wiggle (two loops)", clip("wig", [("RIG_Claude", ("CLA_talk_arm_wiggle", 1))], 72), 4)]
seq = f"{FR}/dr_seq"; shutil.rmtree(seq, ignore_errors=True); os.makedirs(seq); n = 0
for lab, d, hold in clips:
    files = sorted(glob.glob(f"{d}/f_*.png"))
    for i, f in enumerate(files): label(f, f"{lab}   frame {i + 1}/{len(files)}", f"{seq}/{n:05d}.png"); n += 1
    for _ in range(hold): label(files[-1], f"{lab}   (hold)", f"{seq}/{n:05d}.png"); n += 1
out = f"{D}/previews/reel_claude_driving.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", f"{seq}/%05d.png", "-c:v", "libx264", "-crf", "30", "-preset", "veryfast", "-pix_fmt", "yuv420p", out])
bl('bpy.data.objects["RIG_Claude"].location=(-1.2,0,0)')
print(out, os.path.getsize(out) // 1024, "KB", n, "frames")
