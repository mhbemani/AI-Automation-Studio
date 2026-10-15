"""Host: phase 3 preview reels (Eevee draft 960x540, 24 fps). python3 scripts/render_reel_m3.py human|claude  ->  previews/reel_human3_react.mp4 / reel_claude3_signature.mp4"""
import subprocess, os, sys, shutil, glob
from PIL import Image, ImageDraw
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(D, "scripts"))
BL = [sys.executable, os.path.join(D, "bridge", "bl.py")]
FR = f"{D}/previews/reel_frames"; os.makedirs(FR, exist_ok=True)
def bl(code):
    r = subprocess.run(BL + ["exec", code], capture_output=True, text=True, cwd=D)
    if r.returncode: print("ERR", r.stderr[-500:])
RES = 'sc=bpy.context.scene; sc.render.resolution_x=960; sc.render.resolution_y=540; sc.render.resolution_percentage=100; sc.eevee.taa_render_samples=8; sc.render.image_settings.file_format="PNG"; sc.render.fps=24\n'
def render(name, n, setup_play):
    d = f"{FR}/m3_{name}"; shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    bl(setup_play + f'\nsc=bpy.context.scene; sc.frame_start=1; sc.frame_end={n}; sc.render.filepath="{d}/f_"\nbpy.ops.render.render(animation=True)'); return d
def label(png, text, out):
    im = Image.open(png).convert("RGB"); dr = ImageDraw.Draw(im); dr.rectangle((0, 0, 960, 26), fill=(20, 20, 20)); dr.text((8, 7), text, fill=(255, 230, 80)); im.save(out)
def assemble(outname, clips):
    seq = f"{FR}/{outname}_seq"; shutil.rmtree(seq, ignore_errors=True); os.makedirs(seq); n = 0
    for lab, d, hold in clips:
        files = sorted(glob.glob(f"{d}/f_*.png"))
        for i, f in enumerate(files): label(f, f"{lab}   frame {i + 1}/{len(files)}", f"{seq}/{n:05d}.png"); n += 1
        for _ in range(hold): label(files[-1], f"{lab}   (hold)", f"{seq}/{n:05d}.png"); n += 1
    out = f"{D}/previews/{outname}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", f"{seq}/%05d.png", "-c:v", "libx264", "-crf", "30", "-preset", "veryfast", "-pix_fmt", "yuv420p", out])
    print(out, os.path.getsize(out) // 1024, "KB", n, "frames")
def human():
    SV = lambda loc, tgt, seat: f'exec(open("scripts/human_view_lib.py").read()); setup_view(cam_loc={loc}, cam_tgt={tgt}, lens=50, seat={seat})\nbpy.data.objects["HUM_Body"].hide_viewport=bpy.data.objects["HUM_Body"].hide_render=False\n{RES}'
    bl(SV((1.1, -2.0, 1.3), (0.0, 0.0, 0.95), True)); cl = []
    for act, n, hold in (("HUM_react_startle", 16, 10), ("HUM_react_laugh", 36, 8), ("HUM_react_impressed", 30, 8), ("HUM_react_shake_head", 18, 8), ("HUM_phone_to_seat_idle", 36, 10)):
        cl.append((act, render(act, n, f'nla([("{act}",1,"REPLACE")])'), hold))
    bl(SV((0.9, -3.6, 1.6), (-0.4, 0.0, 0.8), True))
    for act, n, hold in (("HUM_stand_to_sit_car", 72, 12), ("HUM_sit_to_stand_car", 72, 12)):
        cl.append((act + " (door is on his right, -X)", render(act, n, f'nla([("{act}",1,"REPLACE")])'), hold))
    bl('nla_clear()'); assemble("reel_human3_react", cl)
def claude():
    SETUP = f'''
exec(open("scripts/_cam.py").read()); exec(open("scripts/claude_test_lib.py").read()); exec(open("scripts/magic_test_lib.py").read()); exec(open("scripts/magic_lib.py").read()); studio(); iso("CLA_","RIG_Claude","CUS_","MAG_","ANIM_")
for o in bpy.data.objects:
    if o.name.startswith(("CLA_","RIG_Claude","CUS_","MAG_")): o.hide_viewport=False; o.hide_render=False
for o in list(bpy.data.objects):
    if o.name=="ANIM_floor": bpy.data.objects.remove(o)
    elif o.name in ("ANIM_seat", "ANIM_seatback"): o.hide_viewport=True; o.hide_render=True
bpy.ops.mesh.primitive_plane_add(size=40, location=(0,0,-0.002)); fl=bpy.context.active_object; fl.name="ANIM_floor"
fm=bpy.data.materials.get("ANIM_floor") or bpy.data.materials.new("ANIM_floor"); fm.use_nodes=True; fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.35,.36,.38,1); fl.data.materials.append(fm)
rig=bpy.data.objects["RIG_Claude"]; rig.hide_render=True; rig.location=(0,0,0)
{RES}'''
    def play(act, cus, view, magic=False):
        cams = {"wide": "cam((1.3,-3.2,1.3),(-0.5,0,0.5),40)", "close": "cam((1.4,-1.7,0.7),(-0.1,0,0.3),45)", "run": "cam((2.4,-2.6,1.2),(0.0,-0.8,0.2),45)", "magic": "cam((2.3,-2.2,1.1),(0.1,-0.7,0.4),40)"}[view]
        code = f'''reset(); mag_reset(); bpy.data.objects["CUS_Cushion"].hide_render={not cus}
ad=rig.animation_data_create(); ad.action=None
for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
s=ad.nla_tracks.new().strips.new("{act}",1,bpy.data.actions["{act}"]); s.extrapolation="HOLD"
{cams}'''
        return code
    bl(SETUP); cl = []
    for act, n, cus, view, hold in (("CLA_cushion_throw_and_jump", 72, True, "wide", 10), ("CLA_cushion_jump", 60, True, "wide", 4), ("CLA_cushion_run_carry", 32, True, "wide", 4), ("CLA_cushion_sit", 96, True, "close", 4),
                                    ("CLA_react_proud_puff", 24, False, "close", 8), ("CLA_react_oops", 20, False, "close", 8), ("CLA_react_giggle", 48, False, "close", 4), ("CLA_pickup_arrival", 72, False, "run", 12)):
        cl.append((act, render(act, n, play(act, cus, view)), hold))
    # magic: cast + ring on a target
    code = '''reset(); mag_reset(); bpy.data.objects["CUS_Cushion"].hide_render=True; aim_magic((0.0,-1.4,0.38)); bpy.data.objects["MAG_Root"]["wrap_to"]=0.7
def strips(obj, seq):
    ad=obj.animation_data_create(); ad.action=None
    for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
    for n,st in seq:
        tr=ad.nla_tracks.new(); s=tr.strips.new(n,st,bpy.data.actions[n]); s.extrapolation="HOLD" if st==seq[0][1] else "NOTHING"
strips(rig,[("CLA_magic_cast",1)]); strips(bpy.data.objects["MAG_Root"],[("MAG_ring_shoot",8),("MAG_ring_wrap",31),("MAG_ring_fade",61)])
cam((2.3,-2.2,1.1),(0.1,-0.7,0.4),40)'''
    cl.append(("CLA_magic_cast + MAG_ring_shoot / wrap / fade", render("magic", 78, code), 12))
    bl('''for o in (rig, bpy.data.objects["MAG_Root"]):
    for t in list(o.animation_data.nla_tracks): o.animation_data.nla_tracks.remove(t)
reset(); mag_reset(); bpy.data.objects["MAG_Root"].rotation_mode="XYZ"; bpy.data.objects["MAG_Root"].rotation_euler=(0,0,0); rig.location=(-1.2,0,0)''')
    assemble("reel_claude3_signature", cl)
if __name__ == "__main__":
    for g in sys.argv[1:]: {"human": human, "claude": claude}[g]()
