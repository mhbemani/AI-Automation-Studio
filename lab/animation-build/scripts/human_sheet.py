"""Host: final-pose contact sheet of HUM_emobody_* / look_at_* on the seated base. python3 scripts/human_sheet.py emobody|looks tag"""
import subprocess, os, sys
from PIL import Image, ImageDraw
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BL = [sys.executable, os.path.join(D, "bridge", "bl.py")]
def bl(*a): return subprocess.run(BL + list(a), capture_output=True, text=True, cwd=D)
kind, tag = sys.argv[1], sys.argv[2]
EMO = ["neutral", "happy", "curious", "excited", "surprised", "thoughtful", "proud", "amused"]
names = {"emobody": [f"HUM_emobody_{e}" for e in EMO], "looks": [f"HUM_look_at_{t}" for t in ("road", "claude", "window", "phone", "monitor")]}[kind]
last = {"emobody": 16, "looks": 10}[kind]
OUT = f"{D}/previews/human_{kind}_{tag}"; os.makedirs(OUT, exist_ok=True)
r = bl("exec", 'exec(open("scripts/human_view_lib.py").read()); setup_view(cam_loc=(0.15,-1.5,1.4), cam_tgt=(0.03,0.0,1.22), lens=60)')
print(r.stderr[-300:])
VIEWS = {"front": ((0.15,-1.9,1.38),(0.03,0.0,1.2)), "left": ((1.9,-0.6,1.38),(0.03,0.0,1.2))}
for n in names:
    r = bl("exec", f'nla([("HUM_pose_seated",1,"REPLACE"),({n!r},1,"COMBINE")]); bpy.context.scene.frame_set({last})')
    if r.returncode: print(r.stderr[-300:])
    for v,(loc,tgt) in VIEWS.items():
        bl("exec", f"cam({loc},{tgt},60)")
        bl("snap", f"{OUT}/{n}_{v}.png", "ANIM_CAM", "--size", "460x460", "--render")
bl("exec", 'nla_clear(); reset_pose(bpy.data.objects["RIG_Human"],True)')
T = (300, 300); per = 2; cols = 4 if kind == "emobody" else 6
sh = Image.new("RGB", (T[0] * cols, T[1] * ((len(names) * per + cols - 1) // cols)), (40, 40, 40)); d = ImageDraw.Draw(sh)
for i, n in enumerate(names):
    for j, v in enumerate(VIEWS):
        k = i * per + j; sh.paste(Image.open(f"{OUT}/{n}_{v}.png").convert("RGB").resize(T), ((k % cols) * T[0], (k // cols) * T[1])); d.text(((k % cols) * T[0] + 5, (k // cols) * T[1] + 4), f"{n[4:]} / {v}", fill=(255, 230, 80))
sh.save(f"{D}/stills/human_{kind}_{tag}.jpg", quality=88)
