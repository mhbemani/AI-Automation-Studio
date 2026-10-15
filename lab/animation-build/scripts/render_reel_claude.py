"""Host driver: preview reels for the Claude actions (Eevee draft 960x540, 24 fps, labelled), via the bridge Blender.
python3 scripts/render_reel_claude.py <group> ...   groups: emoeyes emobody emotions basics looks
Output: previews/reel_claude_<group>.mp4 (+ frames in previews/reel_frames/). Judge motion from these; strips: stills/claude_strip_<action>.jpg."""
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
exec(open("scripts/_cam.py").read()); exec(open("scripts/claude_test_lib.py").read()); studio(); iso("CLA_","RIG_Claude","ANIM_")
rig=bpy.data.objects["RIG_Claude"]; rig.hide_render=True; reset()
sc=bpy.context.scene; sc.render.resolution_x=960; sc.render.resolution_y=540; sc.render.resolution_percentage=100
sc.eevee.taa_render_samples=8; sc.render.image_settings.file_format="PNG"; sc.render.fps=24
cam((-1.2,-1.45,0.42),(-1.2,0,0.30),50)
'''
def render_clip(name, strips, f0, f1, outdir):
    """strips: list of (action, start_frame). Renders frames f0..f1 into outdir."""
    shutil.rmtree(outdir, ignore_errors=True); os.makedirs(outdir)
    code = f'''
rig=bpy.data.objects["RIG_Claude"]; ad=rig.animation_data_create(); ad.action=None
for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
for i,(an,st) in enumerate({strips!r}):
    tr=ad.nla_tracks.new(); s=tr.strips.new(an,st,bpy.data.actions[an]); s.blend_type="COMBINE"; s.extrapolation="NOTHING" if i else "HOLD_FORWARD"
sc=bpy.context.scene; sc.frame_start={f0}; sc.frame_end={f1}
sc.render.filepath="{outdir}/f_"
bpy.ops.render.render(animation=True)
for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
reset()
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
    out = f"{D}/previews/reel_claude_{group}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", f"{seq}/%05d.png", "-c:v", "libx264", "-crf", "30", "-preset", "veryfast", "-pix_fmt", "yuv420p", out])
    print(out, os.path.getsize(out) // 1024, "KB", n, "frames")
def group(g):
    bl(SETUP); clips = []
    if g == "emoeyes":
        for e in EMO: d = f"{FR}/emoeyes_{e}"; render_clip(e, [(f"CLA_emoeyes_{e}", 1)], 1, 8, d); clips.append((f"CLA_emoeyes_{e}", d, 14))
    elif g == "emobody":
        for e in EMO: d = f"{FR}/emobody_{e}"; render_clip(e, [(f"CLA_emobody_{e}", 1)], 1, 16, d); clips.append((f"CLA_emobody_{e}", d, 14))
    elif g == "emotions":      # eyes + body together, then a blink over the hold: the 'is it cute' reel
        for e in EMO:
            d = f"{FR}/emo_{e}"; render_clip(e, [(f"CLA_emoeyes_{e}", 1), (f"CLA_emobody_{e}", 1), ("CLA_blink", 22)], 1, 30, d); clips.append((f"both: {e} (+ blink at f22)", d, 6))
    elif g == "basics":
        d = f"{FR}/idle_blink"; render_clip("idle", [("CLA_idle", 1), ("CLA_blink", 30), ("CLA_blink", 70)], 1, 96, d); clips.append(("CLA_idle (+ CLA_blink at f30, f70)", d, 4))
        d = f"{FR}/talk"; render_clip("talk", [("CLA_talk_pulse", 1), ("CLA_talk_pulse", 13), ("CLA_talk_pulse", 25), ("CLA_talk_pulse", 37)], 1, 48, d); clips.append(("CLA_talk_pulse x4", d, 4))
    elif g == "looks":
        for n in ("left", "right", "up", "down", "camera"): d = f"{FR}/look_{n}"; render_clip(n, [(f"CLA_look_{n}", 1)], 1, 6, d); clips.append((f"CLA_look_{n}", d, 10))
        d = f"{FR}/look_around"; render_clip("la", [("CLA_look_around", 1)], 1, 60, d); clips.append(("CLA_look_around", d, 6))
    assemble(g, clips)
if __name__ == "__main__":
    for g in sys.argv[1:]: group(g)
