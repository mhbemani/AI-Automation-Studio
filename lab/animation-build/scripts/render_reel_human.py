"""Host driver: preview reels for the Claude actions (Eevee draft 960x540, 24 fps, labelled), via the bridge Blender.
python3 scripts/render_reel_human.py <group> ...   groups: emobody basics looks
Output: previews/reel_human_<group>.mp4 (+ frames in previews/reel_frames/). Judge motion from these; strips: stills/claude_strip_<action>.jpg."""
import subprocess, os, sys, shutil, glob
from PIL import Image, ImageDraw
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BL = [sys.executable, os.path.join(D, "bridge", "bl.py")]
EMO = ["neutral", "happy", "curious", "excited", "surprised", "thoughtful", "proud", "amused"]
FR = f"{D}/previews/reel_frames"; os.makedirs(FR, exist_ok=True)
def bl(code, **kw):
    r = subprocess.run(BL + ["exec", code], capture_output=True, text=True, cwd=D, **kw)
    if r.returncode: print("ERR", r.stderr[-400:])
    return r.stdout
SETUP = '''
exec(open("scripts/human_view_lib.py").read()); setup_view(cam_loc=(1.0,-2.1,1.3), cam_tgt=(0.03,0.0,1.0), lens=45)
rig=bpy.data.objects["RIG_Human"]; nla_clear()
sc=bpy.context.scene; sc.render.resolution_x=960; sc.render.resolution_y=540; sc.render.resolution_percentage=100
sc.eevee.taa_render_samples=8; sc.render.image_settings.file_format="PNG"; sc.render.fps=24
'''
def render_clip(name, strips, f0, f1, outdir):
    """strips: [(action, start)] layered over HUM_pose_seated. Renders frames f0..f1."""
    shutil.rmtree(outdir, ignore_errors=True); os.makedirs(outdir)
    full = [("HUM_pose_seated", 1, "REPLACE")] + [(a, st, "COMBINE") for a, st in strips]
    code = f'''
nla({full!r})
sc=bpy.context.scene; sc.frame_start={f0}; sc.frame_end={f1}; sc.render.filepath="{outdir}/f_"
bpy.ops.render.render(animation=True)
nla_clear(); reset_pose(bpy.data.objects["RIG_Human"],True)
'''
    bl(code)
def label(png, text, out):
    im = Image.open(png).convert("RGB"); d = ImageDraw.Draw(im); d.rectangle((0, 0, 960, 26), fill=(20, 20, 20)); d.text((8, 7), text, fill=(255, 230, 80)); im.save(out)
def assemble(group, clips):
    """clips: list of (label, frames_dir, hold_after, nframes_names)"""
    seq = f"{FR}/{group}_seq"; shutil.rmtree(seq, ignore_errors=True); os.makedirs(seq); n = 0
    for lab, d, hold in clips:
        files = sorted(glob.glob(f"{d}/f_*.png"))
        for i, f in enumerate(files):
            label(f, f"{lab}   frame {i + 1}/{len(files)}", f"{seq}/{n:05d}.png"); n += 1
        for _ in range(hold): label(files[-1], f"{lab}   (hold)", f"{seq}/{n:05d}.png"); n += 1
    out = f"{D}/previews/reel_human_{group}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", f"{seq}/%05d.png", "-c:v", "libx264", "-crf", "30", "-preset", "veryfast", "-pix_fmt", "yuv420p", out])
    print(out, os.path.getsize(out) // 1024, "KB", n, "frames")
def group(g):
    bl(SETUP); clips = []
    if g == "emobody":
        for e in EMO: d = f"{FR}/h_emobody_{e}"; render_clip(e, [(f"HUM_emobody_{e}", 1)], 1, 16, d); clips.append((f"HUM_emobody_{e}", d, 16))
    elif g == "basics":
        d = f"{FR}/h_idle"; render_clip("idle", [("HUM_seat_idle", 1)], 1, 96, d); clips.append(("HUM_seat_idle (96 loop)", d, 4))
        d = f"{FR}/h_talk"; render_clip("talk", [("HUM_seat_idle", 1), ("HUM_talk_small", 1), ("HUM_talk_small", 49)], 1, 96, d); clips.append(("HUM_seat_idle + HUM_talk_small x2", d, 4))
        d = f"{FR}/h_nod"; render_clip("nod", [("HUM_seat_idle", 1), ("HUM_talk_nod", 8), ("HUM_talk_nod", 40)], 1, 56, d); clips.append(("HUM_talk_nod at f8 and f40 (over idle)", d, 4))
    elif g == "looks":
        for t in ("road", "claude", "window", "phone", "monitor"): d = f"{FR}/h_look_{t}"; render_clip(t, [(f"HUM_look_at_{t}", 1)], 1, 10, d); clips.append((f"HUM_look_at_{t}", d, 16))
    assemble(g, clips)
if __name__ == "__main__":
    for g in sys.argv[1:]: group(g)
