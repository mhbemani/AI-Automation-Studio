"""Before/after sheet: for each pose a row with the old and new render of each view side by side.
Run: python3 scripts/compare_sheet.py <prefix_old> <prefix_new> <out.jpg> <views,comma> <poses...>"""
import sys
from PIL import Image, ImageDraw
po, pn, out, views, poses = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4].split(","), sys.argv[5:]
T = 300
o = Image.new("RGB", (T * 2 * len(views), T * len(poses)), (30, 30, 30)); d = ImageDraw.Draw(o)
for r, p in enumerate(poses):
    for c, v in enumerate(views):
        for k, (pre, lab) in enumerate(((po, "before"), (pn, "after"))):
            x = (2 * c + k) * T
            o.paste(Image.open(f"{pre}_{p}_{v}.png").convert("RGB").resize((T, T)), (x, r * T))
            d.text((x + 6, r * T + 4), f"{p} / {v} / {lab}", fill=(255, 230, 80) if k else (180, 180, 180))
o.save(out, quality=85)
