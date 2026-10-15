"""Host: frames of Claude driving (car interior cutaway). python3 scripts/drive_sheet.py out.jpg  <claude_action>:<car_action or -> f1,f2,..."""
import subprocess, os, sys
from PIL import Image, ImageDraw
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BL = [sys.executable, os.path.join(D, "bridge", "bl.py")]
def bl(*a): return subprocess.run(BL + list(a), capture_output=True, text=True, cwd=D)
out = sys.argv[1]; specs = [a.split(":") for a in sys.argv[2:]]       # claude_action, car_action, frames
SETUP = '''
exec(open("scripts/_cam.py").read()); exec(open("scripts/rigtest_lib.py").read()); studio()
iso("CAR_","CLA_","RIG_Claude","ANIM_")
for o in bpy.data.objects:
    if o.name.startswith(("CAR_","CLA_","RIG_Claude")): o.hide_viewport=False; o.hide_render=False
for n in ("CAR_Ext_Body","CAR_Door_L","CAR_Door_R","CAR_Int_DoorCard_L","CAR_Int_DoorCard_R","CAR_ctrl","CAR_WheelGripPivot","CAR_WheelGrip_L","CAR_WheelGrip_R","CAR_Exterior","CAR_DoorAnchor_L"):
    if n in bpy.data.objects: bpy.data.objects[n].hide_render=True
for o in bpy.data.objects:
    if o.name.startswith("CAR_Wheel_"): o.hide_render=True
bpy.data.objects["RIG_Claude"].hide_render=True
bpy.data.objects["RIG_Claude"].location=(0.42,-0.19,0.81)
cam((0.55,-1.5,1.55),(0.42,-0.25,1.0),45)
'''
bl("exec", SETUP)
tiles = []
for ca, car, frames in specs:
    for f in frames.split(","):
        code = f'''
def nla2(rig, name):
    ad = rig.animation_data_create(); ad.action = None
    for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
    if name != "-":
        tr = ad.nla_tracks.new(); s = tr.strips.new(name, 1, bpy.data.actions[name]); s.extrapolation = "HOLD"
nla2(bpy.data.objects["RIG_Claude"], "{ca}"); nla2(bpy.data.objects["CAR_ctrl"], "{car}")
bpy.context.scene.frame_set(500); bpy.context.scene.frame_set({f})
'''
        bl("exec", code); p = f"{D}/previews/_drive_{ca}_{f}.png"; bl("snap", p, "ANIM_CAM", "--size", "400x400", "--render"); tiles.append((f"{ca[4:]} f{f}", p))
bl("exec", 'for o in (bpy.data.objects["RIG_Claude"], bpy.data.objects["CAR_ctrl"]):\n    for t in list(o.animation_data.nla_tracks): o.animation_data.nla_tracks.remove(t)\nbpy.data.objects["RIG_Claude"].location=(-1.2,0,0)')
cols = min(6, len(tiles)); rows = (len(tiles) + cols - 1) // cols
sh = Image.new("RGB", (400 * cols, 400 * rows), (40, 40, 40)); d = ImageDraw.Draw(sh)
for i, (lab, p) in enumerate(tiles): sh.paste(Image.open(p).convert("RGB"), ((i % cols) * 400, (i // cols) * 400)); d.text(((i % cols) * 400 + 5, (i // cols) * 400 + 4), lab, fill=(255, 230, 80))
sh.save(out, quality=88)
