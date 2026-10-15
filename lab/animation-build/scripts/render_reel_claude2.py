"""Host: preview of phase 2 human locomotion, side view with scrolling floor markers (feet must stick to the markers).
python3 scripts/render_reel_human2.py locomotion"""
import subprocess, os, sys, shutil, glob
from PIL import Image, ImageDraw
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BL = [sys.executable, os.path.join(D, "bridge", "bl.py")]
FR = f"{D}/previews/reel_frames"; os.makedirs(FR, exist_ok=True)
def bl(code):
    r = subprocess.run(BL + ["exec", code], capture_output=True, text=True, cwd=D)
    if r.returncode: print("ERR", r.stderr[-500:])
SETUP = '''
exec(open("scripts/_cam.py").read()); exec(open("scripts/claude_test_lib.py").read()); studio(); iso("CLA_","RIG_Claude","CUS_","ANIM_","MAG_")
rig=bpy.data.objects["RIG_Claude"]; rig.hide_render=True; rig.location=(0,0,0); reset()
for o in list(bpy.data.objects):
    if o.name.startswith("ANIM_mark") or o.name=="ANIM_floor": bpy.data.objects.remove(o)
bpy.ops.mesh.primitive_plane_add(size=40, location=(0,0,-0.002)); fl=bpy.context.active_object; fl.name="ANIM_floor"
fm=bpy.data.materials.get("ANIM_floor") or bpy.data.materials.new("ANIM_floor"); fm.use_nodes=True; fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.35,.36,.38,1); fl.data.materials.append(fm)
mm=bpy.data.materials.get("ANIM_markm") or bpy.data.materials.new("ANIM_markm"); mm.use_nodes=True; mm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.9,.35,.1,1)
for i in range(30):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0.55,i*0.2-3,0.0)); o=bpy.context.active_object; o.name=f"ANIM_mark{i}"; o.scale=(0.3,0.015,0.004); o.data.materials.append(mm); o["y0"]=i*0.2-3
sc=bpy.context.scene; sc.render.resolution_x=960; sc.render.resolution_y=540; sc.render.resolution_percentage=100
sc.eevee.taa_render_samples=8; sc.render.image_settings.file_format="PNG"; sc.render.fps=24
cam((2.4,-0.1,0.45),(0,-0.1,0.28),40)
'''
HELP = '''
def nla_c(strips):
    ad=rig.animation_data_create(); ad.action=None
    for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
    for an,st in strips:
        s=ad.nla_tracks.new().strips.new(an,st,bpy.data.actions[an]); s.extrapolation="HOLD"
def nla_c_clear():
    for t in list(rig.animation_data.nla_tracks): rig.animation_data.nla_tracks.remove(t)
    reset()
'''
def clip(name, action, n, travel=None, hold=0):
    d = f"{FR}/h2_{name}"; shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    # travel: metres the floor markers scroll per frame (in place walks); root-motion actions use travel=None and move the human instead
    code = f'''
nla_c([("{action}",1)])
tr = {travel!r}
for o in bpy.data.objects:
    if o.name.startswith("ANIM_mark"):
        o.animation_data_clear()
        if tr:
            o.location.y = o["y0"]; o.keyframe_insert("location", index=1, frame=1); o.location.y = o["y0"] + tr*{n}; o.keyframe_insert("location", index=1, frame={n})
            for fc in o.animation_data.action.fcurves:
                for k in fc.keyframe_points: k.interpolation="LINEAR"
        else: o.location.y = o["y0"]
sc=bpy.context.scene; sc.frame_start=1; sc.frame_end={n}; sc.render.filepath="{d}/f_"
bpy.ops.render.render(animation=True)
nla_c_clear()
for o in bpy.data.objects:
    if o.name.startswith("ANIM_mark"): o.animation_data_clear()
'''
    bl(code); return d
def label(png, text, out):
    im = Image.open(png).convert("RGB"); dr = ImageDraw.Draw(im); dr.rectangle((0, 0, 960, 26), fill=(20, 20, 20)); dr.text((8, 7), text, fill=(255, 230, 80)); im.save(out)
def assemble(group, clips):
    seq = f"{FR}/{group}_seq"; shutil.rmtree(seq, ignore_errors=True); os.makedirs(seq); n = 0
    for lab, d, hold in clips:
        files = sorted(glob.glob(f"{d}/f_*.png"))
        for i, f in enumerate(files): label(f, f"{lab}   frame {i + 1}/{len(files)}", f"{seq}/{n:05d}.png"); n += 1
        for _ in range(hold): label(files[-1], f"{lab}   (hold)", f"{seq}/{n:05d}.png"); n += 1
    out = f"{D}/previews/reel_claude2_{group}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", f"{seq}/%05d.png", "-c:v", "libx264", "-crf", "30", "-preset", "veryfast", "-pix_fmt", "yuv420p", out])
    print(out, os.path.getsize(out) // 1024, "KB", n, "frames")
def group(g):
    bl(SETUP); bl(HELP)
    if g == "locomotion":
        cl = []
        d = clip("walk", "CLA_walk_cycle", 72, travel=0.4 / 24); cl.append(("CLA_walk_cycle x3 (in place, floor scrolls 0.4 m per cycle)", d, 4))
        d = clip("run", "CLA_run_cycle", 64, travel=0.5714 / 16); cl.append(("CLA_run_cycle x4 (0.57 m per cycle)", d, 4))
        d = clip("i2w", "CLA_idle_to_walk", 10); cl.append(("CLA_idle_to_walk", d, 6))
        d = clip("w2i", "CLA_walk_to_idle", 10); cl.append(("CLA_walk_to_idle", d, 6))
        assemble(g, cl)
if __name__ == "__main__":
    for g in sys.argv[1:]: group(g)
