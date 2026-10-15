"""Host: render Claude 'both' emotions big, 4x2 sheet. python3 scripts/claude_cute.py tag [emotion ...]"""
import subprocess, os, sys, importlib
from PIL import Image, ImageDraw
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(D, "scripts")); import claude_presets as cp
BL = [sys.executable, os.path.join(D, "bridge", "bl.py")]
def bl(*a): return subprocess.run(BL + list(a), capture_output=True, text=True, cwd=D)
tag = sys.argv[1]; names = sys.argv[2:] or cp.EMOTIONS
OUT = f"{D}/previews/cute_{tag}"; os.makedirs(OUT, exist_ok=True)
bl("exec", 'exec(open("scripts/_cam.py").read()); exec(open("scripts/claude_test_lib.py").read()); studio(); iso("CLA_","RIG_Claude","ANIM_"); bpy.data.objects["RIG_Claude"].hide_render=True; reset(); cam((-1.2,-1.45,0.42),(-1.2,0,0.30),50)')
for e in names:
    bl("exec", f'reset(); setp(**{cp.preset(e, e)!r})'); bl("snap", f"{OUT}/{e}.png", "ANIM_CAM", "--size", "560x420", "--render")
bl("exec", "reset()")
T = (560, 420); cols = 4; rows = (len(names) + cols - 1) // cols
sh = Image.new("RGB", (T[0] * cols, T[1] * rows), (40, 40, 40)); d = ImageDraw.Draw(sh)
for i, e in enumerate(names):
    sh.paste(Image.open(f"{OUT}/{e}.png").convert("RGB"), ((i % cols) * T[0], (i // cols) * T[1])); d.text(((i % cols) * T[0] + 6, (i // cols) * T[1] + 4), e, fill=(255, 230, 80))
sh.save(f"{D}/stills/claude_cute_{tag}.jpg", quality=88)
