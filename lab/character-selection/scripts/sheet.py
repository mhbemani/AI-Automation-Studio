"""Grid sheet: rows = poses, cols = views. Run: python3 scripts/sheet.py <prefix> <out.jpg> <views,comma> <poses...>"""
import sys
from PIL import Image, ImageDraw
prefix, out, views, poses = sys.argv[1], sys.argv[2], sys.argv[3].split(","), sys.argv[4:]
T = 400
sheet = Image.new("RGB", (T * len(views), T * len(poses)), (40, 40, 40))
d = ImageDraw.Draw(sheet)
for r, p in enumerate(poses):
    for c, v in enumerate(views):
        im = Image.open(f"{prefix}_{p}_{v}.png").convert("RGB").resize((T, T))
        sheet.paste(im, (c * T, r * T)); d.text((c * T + 8, r * T + 6), f"{p} / {v}", fill=(255, 230, 80))
sheet.save(out, quality=85)
