"""Host driver: Claude emotion contact sheets. python3 scripts/claude_sheet.py [tag]
rows: eyes only, body only, combined; large tiles + a small-size strip (Claude ~110 px wide)."""
import subprocess, os, sys
from PIL import Image, ImageDraw
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(D, "scripts")); import claude_presets as cp
BL = [sys.executable, os.path.join(D, "bridge", "bl.py")]
def bl(*a): return subprocess.run(BL + list(a), capture_output=True, text=True, cwd=D)
tag = sys.argv[1] if len(sys.argv) > 1 else "v1"
OUT = f"{D}/previews/emo_claude_{tag}"; os.makedirs(OUT, exist_ok=True)
bl("exec", 'exec(open("scripts/_cam.py").read()); exec(open("scripts/claude_test_lib.py").read()); studio(); iso("CLA_","RIG_Claude","ANIM_"); bpy.data.objects["RIG_Claude"].hide_render=True; reset(); cam((-1.2,-1.55,0.40),(-1.2,0,0.30),50)')
rows = {"eyes": lambda e: cp.preset(e, "neutral"), "body": lambda e: cp.preset("neutral", e), "both": lambda e: cp.preset(e, e)}
for r, f in rows.items():
    for e in cp.EMOTIONS:
        bl("exec", f'reset(); setp(**{f(e)!r})')
        bl("snap", f"{OUT}/{r}_{e}.png", "ANIM_CAM", "--size", "480x360", "--render")
bl("exec", "reset()")
T = (320, 240)
big = Image.new("RGB", (T[0] * 8, T[1] * 3), (40, 40, 40)); d = ImageDraw.Draw(big)
for ri, r in enumerate(rows):
    for ci, e in enumerate(cp.EMOTIONS):
        im = Image.open(f"{OUT}/{r}_{e}.png").convert("RGB").resize(T); big.paste(im, (ci * T[0], ri * T[1])); d.text((ci * T[0] + 5, ri * T[1] + 4), f"{r}: {e}", fill=(255, 230, 80))
big.save(f"{D}/stills/claude_emotions_{tag}_large.jpg", quality=88)
# small: whole picture at 1/3 -> Claude ~ 110 px wide, shown 2x
s = Image.new("RGB", (160 * 2 * 8, 120 * 2 * 3), (40, 40, 40))
for ri, r in enumerate(rows):
    for ci, e in enumerate(cp.EMOTIONS):
        im = Image.open(f"{OUT}/{r}_{e}.png").convert("RGB").resize((160, 120), Image.LANCZOS).resize((320, 240), Image.NEAREST); s.paste(im, (ci * 320, ri * 240))
s.save(f"{D}/stills/claude_emotions_{tag}_small.jpg", quality=90)
