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
exec(open("scripts/human_view_lib.py").read()); setup_view(cam_loc=(5.2,0.3,1.0), cam_tgt=(0,0.3,0.85), lens=45, seat=False)
rig=bpy.data.objects["RIG_Human"]; nla_clear()
sc=bpy.context.scene; sc.render.resolution_x=960; sc.render.resolution_y=540; sc.render.resolution_percentage=100
sc.eevee.taa_render_samples=8; sc.render.image_settings.file_format="PNG"; sc.render.fps=24
# floor + markers every 0.6 m along Y (the walk goes toward -Y)
for o in list(bpy.data.objects):
    if o.name.startswith("ANIM_mark") or o.name=="ANIM_floor": bpy.data.objects.remove(o)
bpy.ops.mesh.primitive_plane_add(size=40, location=(0,0,-0.002)); fl=bpy.context.active_object; fl.name="ANIM_floor"
fm=bpy.data.materials.get("ANIM_floor") or bpy.data.materials.new("ANIM_floor"); fm.use_nodes=True; fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.35,.36,.38,1); fl.data.materials.append(fm)
mm=bpy.data.materials.get("ANIM_markm") or bpy.data.materials.new("ANIM_markm"); mm.use_nodes=True; mm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.9,.35,.1,1)
for i in range(24):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0.55,i*0.6-6,0.0)); o=bpy.context.active_object; o.name=f"ANIM_mark{i}"; o.scale=(0.5,0.04,0.004); o.data.materials.append(mm); o["y0"]=i*0.6-6
'''
def clip(name, action, n, travel=None, hold=0):
    d = f"{FR}/h2_{name}"; shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    # travel: metres the floor markers scroll per frame (in place walks); root-motion actions use travel=None and move the human instead
    code = f'''
nla([("{action}",1,"REPLACE")])
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
nla_clear()
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
    out = f"{D}/previews/reel_human2_{group}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", f"{seq}/%05d.png", "-c:v", "libx264", "-crf", "30", "-preset", "veryfast", "-pix_fmt", "yuv420p", out])
    print(out, os.path.getsize(out) // 1024, "KB", n, "frames")
def group(g):
    bl(SETUP); V = 1.2 / 24
    if g == "phone":
        bl('cam((1.3,-2.3,1.45),(-0.05,-0.1,1.25),50); bpy.context.scene.frame_set(1)\nfor o in bpy.data.objects:\n    if o.name.startswith("PHN_") or o.name=="HUM_Body": o.hide_viewport=o.hide_render=False\nbpy.data.objects["HUM_PhoneSocket"].hide_render=True')
        cl = []
        for lab, act, n, hold in (("HUM_phone_raise", "HUM_phone_raise", 20, 8), ("HUM_phone_hold_read (one loop)", "HUM_phone_hold_read", 96, 4), ("HUM_phone_type (two loops)", "HUM_phone_type", 96, 4),
                                  ("HUM_phone_show_claude (Claude is on his left)", "HUM_phone_show_claude", 24, 10), ("HUM_phone_lower_pocket", "HUM_phone_lower_pocket", 30, 6)):
            cl.append((lab, clip("ph_" + act[10:], act, n), hold))
        bl('cam((5.2,0.3,1.0),(0,0.3,0.85),45)')
        cl.append(("HUM_walk_texting x3 (in place, floor scrolls)", clip("ph_walk", "HUM_walk_texting", 72, travel=1.2 / 24), 4))
        assemble("phone", cl); return
    if g == "seated":
        bl('exec(open("scripts/human_view_lib.py").read()); setup_view(cam_loc=(1.1,-2.0,1.3), cam_tgt=(0.0,0.0,0.95), lens=50, seat=True)\nsc=bpy.context.scene; sc.render.resolution_x=960; sc.render.resolution_y=540; sc.render.resolution_percentage=100; sc.eevee.taa_render_samples=8\nbpy.data.objects["HUM_Body"].hide_viewport=bpy.data.objects["HUM_Body"].hide_render=False\nbpy.data.objects["PHN_Phone"]["phone_visible"]=0.0; bpy.data.objects["HUM_PhoneSocket"].hide_render=True')
        cl = []
        for lab, act, n, hold in (("HUM_pass_hands_lap (one loop)", "HUM_pass_hands_lap", 96, 4), ("HUM_pass_turn_to_claude (Claude is on his left)", "HUM_pass_turn_to_claude", 24, 14), ("HUM_pass_look_out_window (one loop)", "HUM_pass_look_out_window", 120, 4),
                                  ("HUM_pass_lean_forward", "HUM_pass_lean_forward", 20, 12), ("HUM_talk_hand_gesture_a (two loops)", "HUM_talk_hand_gesture_a", 72, 4)):
            cl.append((lab, clip("se_" + act[9:], act, n), hold))
        assemble("seated", cl); return
    if g == "locomotion":
        cl = []
        d = clip("walk", "HUM_walk_cycle", 72, travel=-V * -1 * 0 + V * 1.0)   # markers scroll toward +Y (he walks to -Y)
        cl.append(("HUM_walk_cycle x3 (in place, floor scrolls 1.2 m per cycle)", d, 4))
        d = clip("idle", "HUM_stand_idle", 96); cl.append(("HUM_stand_idle", d, 4))
        d = clip("s2w", "HUM_stand_to_walk", 12); cl.append(("HUM_stand_to_walk", d, 6))
        d = clip("w2s", "HUM_walk_to_stand", 12); cl.append(("HUM_walk_to_stand", d, 6))
        d = clip("stop", "HUM_stop_from_walk", 18); cl.append(("HUM_stop_from_walk", d, 8))
        d = clip("out", "HUM_walk_out_building", 72); cl.append(("HUM_walk_out_building (root motion)", d, 6))
        assemble(g, cl)
if __name__ == "__main__":
    for g in sys.argv[1:]: group(g)
