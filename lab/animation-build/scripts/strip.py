"""frame strip from rendered frames: python3 scripts/strip.py <frames_dir> <out.jpg> <step> [first last] [cols]"""
import sys, glob
from PIL import Image, ImageDraw
d, out, step = sys.argv[1], sys.argv[2], int(sys.argv[3])
files = sorted(glob.glob(f"{d}/f_*.png"))
a = int(sys.argv[4]) if len(sys.argv) > 4 else 1; b = int(sys.argv[5]) if len(sys.argv) > 5 else len(files)
cols = int(sys.argv[6]) if len(sys.argv) > 6 else 6
sel = list(range(a, b + 1, step)); T = (300, 178)
rows = (len(sel) + cols - 1) // cols
sh = Image.new("RGB", (T[0] * cols, T[1] * rows), (40, 40, 40)); dr = ImageDraw.Draw(sh)
for i, f in enumerate(sel):
    im = Image.open(files[f - 1]).convert("RGB").crop((0, 0, 960, 540)).resize(T)
    sh.paste(im, ((i % cols) * T[0], (i // cols) * T[1])); dr.text(((i % cols) * T[0] + 4, (i // cols) * T[1] + 4), f"f{f}", fill=(255, 230, 80))
sh.save(out, quality=88)
