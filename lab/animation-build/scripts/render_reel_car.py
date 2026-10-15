"""Host: preview reel for the car actions (Eevee draft 960x540, 24 fps). python3 scripts/render_reel_car.py"""
import subprocess, os, sys, shutil, glob
from PIL import Image, ImageDraw
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BL = [sys.executable, os.path.join(D, "bridge", "bl.py")]
FR = f"{D}/previews/reel_frames"; os.makedirs(FR, exist_ok=True)
def bl(code):
    r = subprocess.run(BL + ["exec", code], capture_output=True, text=True, cwd=D)
    if r.returncode: print("ERR", r.stderr[-400:])
SETUP = '''
exec(open("scripts/human_view_lib.py").read()); exec(open("scripts/_cam.py").read()); exec(open("scripts/car_test_lib.py").read()); studio(); iso("CAR_","ANIM_")
for o in bpy.data.objects:
    if o.name.startswith("CAR_"): o.hide_viewport=o.hide_render=False
bpy.data.objects["CAR_ctrl"].hide_render=True; carreset()
sc=bpy.context.scene; sc.render.resolution_x=960; sc.render.resolution_y=540; sc.render.resolution_percentage=100
sc.eevee.taa_render_samples=8; sc.render.image_settings.file_format="PNG"; sc.render.fps=24
'''
VIEW_L = ((6.5, -6.0, 2.6), (0.0, 0.0, 0.8)); VIEW_R = ((-6.5, -6.0, 2.6), (0.0, 0.0, 0.8))
def clip(name, strips, f1, view):
    d = f"{FR}/car_{name}"; shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    code = f'''
cam({view[0]},{view[1]},40)
ad=bpy.data.objects["CAR_ctrl"].animation_data_create(); ad.action=None
for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
for i,(an,st,rep) in enumerate({strips!r}):
    tr=ad.nla_tracks.new(); s=tr.strips.new(an,st,bpy.data.actions[an]); s.repeat=rep; s.extrapolation="HOLD" if i==0 else "HOLD_FORWARD"
sc=bpy.context.scene; sc.frame_start=1; sc.frame_end={f1}; sc.render.filepath="{d}/f_"
bpy.ops.render.render(animation=True)
for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
carreset()
'''
    bl(code); return d
def label(png, text, out):
    im = Image.open(png).convert("RGB"); dr = ImageDraw.Draw(im); dr.rectangle((0, 0, 960, 26), fill=(20, 20, 20)); dr.text((8, 7), text, fill=(255, 230, 80)); im.save(out)
bl(SETUP)
clips = [("CAR_wheel_spin x3 (12 frames each)", clip("spin", [("CAR_wheel_spin", 1, 3)], 36, VIEW_L), 6),
         ("CAR_steering_sway (96 loop)", clip("sway", [("CAR_steering_sway", 1, 1)], 96, VIEW_L), 4),
         ("CAR_steering_turn_left, then right", clip("turn", [("CAR_steering_turn_left", 1, 1), ("CAR_steering_turn_right", 25, 1)], 48, VIEW_L), 8),
         ("CAR_door_open_L then CAR_door_close_L", clip("doorL", [("CAR_door_open_L", 1, 1), ("CAR_door_close_L", 31, 1)], 54, VIEW_L), 6),
         ("CAR_door_open_R then CAR_door_close_R", clip("doorR", [("CAR_door_open_R", 1, 1), ("CAR_door_close_R", 31, 1)], 54, VIEW_R), 6)]
seq = f"{FR}/car_seq"; shutil.rmtree(seq, ignore_errors=True); os.makedirs(seq); n = 0
for lab, d, hold in clips:
    files = sorted(glob.glob(f"{d}/f_*.png"))
    for i, f in enumerate(files): label(f, f"{lab}   frame {i + 1}/{len(files)}", f"{seq}/{n:05d}.png"); n += 1
    for _ in range(hold): label(files[-1], f"{lab}   (hold)", f"{seq}/{n:05d}.png"); n += 1
out = f"{D}/previews/reel_car.mp4"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", f"{seq}/%05d.png", "-c:v", "libx264", "-crf", "30", "-preset", "veryfast", "-pix_fmt", "yuv420p", out])
print(out, os.path.getsize(out) // 1024, "KB", n, "frames")
