#!/usr/bin/env python3
"""dev tool: sheet.py out.png bg_hex cols tile_w img1 img2 ...  (RGBA stills composited over bg, optional label = filename)"""
import sys
from PIL import Image, ImageDraw
out, bg, cols, tw, *files = sys.argv[1:]; cols = int(cols); tw = int(tw)
ims = [Image.open(f).convert("RGBA") for f in files]
th = int(tw * ims[0].height / ims[0].width); rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGBA", (cols * tw, rows * th), "#" + bg.lstrip("#"))
for i, (im, f) in enumerate(zip(ims, files)):
    t = Image.new("RGBA", im.size, "#" + bg.lstrip("#")); t.alpha_composite(im)
    t = t.resize((tw, th), Image.LANCZOS); d = ImageDraw.Draw(t)
    d.text((6, 4), f.split("/")[-1].replace(".png", ""), fill=(255, 255, 255, 200) if bg.lstrip("#")[:1] in "01" else (0, 0, 0, 200))
    sheet.paste(t, ((i % cols) * tw, (i // cols) * th))
sheet.convert("RGB").save(out)
