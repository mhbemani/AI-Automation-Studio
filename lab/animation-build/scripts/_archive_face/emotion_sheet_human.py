"""Host driver: human face emotion contact sheets (large + 70 px face + 15 px face). python3 scripts/emotion_sheet_human.py [tag]"""
import subprocess, os, sys
from PIL import Image, ImageDraw
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BL = [sys.executable, os.path.join(D, "bridge", "bl.py")]
def bl(*a): return subprocess.run(BL + list(a), capture_output=True, text=True, cwd=D)
tag = sys.argv[1] if len(sys.argv) > 1 else "v1"
NAMES = ["neutral", "happy", "curious", "excited", "surprised", "thoughtful", "proud", "amused", "Blink", "MouthOpen"]
OUT = f"{D}/previews/emo_human_{tag}"; os.makedirs(OUT, exist_ok=True)
bl("exec", 'exec(open("scripts/_cam.py").read()); exec(open("scripts/rigtest_lib.py").read()); studio(); iso("HUM_Body","HUM_Face","RIG_Human","ANIM_"); r=bpy.data.objects["RIG_Human"]; r.hide_render=True; reset_pose(r,True); cam((0.036,-0.7,1.60),(0.036,0.1,1.60),85)')
for n in NAMES:
    bl("exec", f'k=bpy.data.objects["HUM_Face"].data.shape_keys.key_blocks\nfor b in k: b.value=0\nif {n!r} in k: k[{n!r}].value=1.0')
    bl("snap", f"{OUT}/{n}.png", "ANIM_CAM", "--size", "600x600", "--render")
bl("exec", 'k=bpy.data.objects["HUM_Face"].data.shape_keys.key_blocks\nfor b in k: b.value=0')
T = 300
big = Image.new("RGB", (T * 5, T * 2), (40, 40, 40)); d = ImageDraw.Draw(big)
for i, n in enumerate(NAMES):
    im = Image.open(f"{OUT}/{n}.png").convert("RGB").resize((T, T)); big.paste(im, ((i % 5) * T, (i // 5) * T)); d.text(((i % 5) * T + 6, (i // 5) * T + 4), n, fill=(255, 230, 80))
big.save(f"{D}/stills/human_emotions_{tag}_large.jpg", quality=88)
# target sizes: face height (hairline->chin) = 0.165 m; on the 600 px tile 0.7 m wide -> ~291 px. 70 px face -> scale .24 ; 15 px -> .05
def strip(scale, up, name):
    w = int(600 * scale); row = Image.new("RGB", (w * up * len(NAMES), w * up), (40, 40, 40))
    for i, n in enumerate(NAMES):
        im = Image.open(f"{OUT}/{n}.png").convert("RGB").resize((w, w), Image.LANCZOS).resize((w * up, w * up), Image.NEAREST)
        row.paste(im, (i * w * up, 0))
    row.save(f"{D}/stills/{name}", quality=90)
strip(0.24, 2, f"human_emotions_{tag}_70px.jpg"); strip(0.05, 6, f"human_emotions_{tag}_15px.jpg")
