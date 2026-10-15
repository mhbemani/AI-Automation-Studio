#!/usr/bin/env python3
"""clip_sheet.py out.png frames_dir start end step [tile=300]: contact sheet of consecutive character frames (RGBA over navy), 8 columns"""
import sys
from PIL import Image, ImageDraw
out, d, a, b, st = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]); tw = int(sys.argv[6]) if len(sys.argv) > 6 else 300
fr = list(range(a, b + 1, st)); cols = 8; rows = (len(fr) + cols - 1) // cols; s = Image.new("RGB", (cols * tw, rows * tw), (11, 16, 32))
for i, f in enumerate(fr):
    im = Image.open(f"{d}/f_{f + 1:04d}.png").convert("RGBA"); bg = Image.new("RGBA", im.size, (11, 16, 32, 255)); bg.alpha_composite(im)
    t = bg.convert("RGB").crop((int(im.width * 0.1), int(im.height * 0.08), int(im.width * 0.9), int(im.height * 0.92))).resize((tw, tw)); ImageDraw.Draw(t).text((4, 4), str(f), fill=(255, 255, 255)); s.paste(t, ((i % cols) * tw, (i // cols) * tw))
s.save(out)
