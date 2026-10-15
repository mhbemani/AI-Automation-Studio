"""Host: frame sheet of one or more human actions. python3 scripts/action_sheet.py out.jpg view action:frames,frames ...   view: seat | stand
e.g. python3 scripts/action_sheet.py stills/x.jpg seat HUM_pass_turn_to_claude:1,8,14,24"""
import subprocess, os, sys
from PIL import Image, ImageDraw
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BL = [sys.executable, os.path.join(D, "bridge", "bl.py")]
def bl(*a): return subprocess.run(BL + list(a), capture_output=True, text=True, cwd=D)
out, view = sys.argv[1], sys.argv[2]; specs = [a.split(":") for a in sys.argv[3:]]
VIEWS = {"seat": ((1.1, -1.9, 1.35), (0.0, 0.0, 0.95), True), "stand": ((1.3, -2.3, 1.45), (-0.05, -0.1, 1.25), False), "enter": ((0.9, -3.6, 1.6), (-0.4, 0.0, 0.8), True), "enterside": ((3.3, 0.2, 1.4), (-0.4, 0.0, 0.75), True), "seatfront": ((0.1, -2.2, 1.3), (0.03, 0.0, 0.95), True)}
loc, tgt, seat = VIEWS[view]
r = bl("exec", f'exec(open("scripts/human_view_lib.py").read()); setup_view(cam_loc={loc}, cam_tgt={tgt}, lens=50, seat={seat})\nbpy.data.objects["HUM_Body"].hide_viewport=bpy.data.objects["HUM_Body"].hide_render=False\nbpy.data.objects["HUM_PhoneSocket"].hide_render=True')
tiles = []
for act, frames in specs:
    for f in frames.split(","):
        vis = 1.0 if ("phone" in act or "texting" in act) else 0.0
        bl("exec", f'bpy.data.objects["PHN_Phone"]["phone_visible"]={vis}; nla([("{act}",1,"REPLACE")]); bpy.context.scene.frame_set(500); bpy.context.scene.frame_set({f})')
        p = f"{D}/previews/_sheet_{act}_{f}.png"; bl("snap", p, "ANIM_CAM", "--size", "360x420", "--render"); tiles.append((f"{act[4:]} f{f}", p))
bl("exec", 'nla_clear(); reset_pose(bpy.data.objects["RIG_Human"],True)')
cols = min(6, len(tiles)); rows = (len(tiles) + cols - 1) // cols
sh = Image.new("RGB", (360 * cols, 420 * rows), (40, 40, 40)); d = ImageDraw.Draw(sh)
for i, (lab, p) in enumerate(tiles): sh.paste(Image.open(p).convert("RGB"), ((i % cols) * 360, (i // cols) * 420)); d.text(((i % cols) * 360 + 5, (i // cols) * 420 + 4), lab, fill=(255, 230, 80))
sh.save(out, quality=88)
