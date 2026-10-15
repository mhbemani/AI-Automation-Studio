#!/usr/bin/env python3
"""face_sheet.py out.png tile_w img... : crop the head out of the emotion stills and tile them with labels"""
import sys
from PIL import Image, ImageDraw
out, tw, *files = sys.argv[1:]; tw = int(tw); tiles = []
for f in files:
    im = Image.open(f).convert("RGBA"); W, H = im.size; c = im.crop((int(W * 0.17), int(H * 0.36), int(W * 0.83), int(H * 0.68)))
    bg = Image.new("RGBA", c.size, (11, 16, 32, 255)); bg.alpha_composite(c); t = bg.convert("RGB").resize((tw, int(tw * c.height / c.width)), Image.LANCZOS)
    ImageDraw.Draw(t).text((6, 4), f.split("/")[-1].replace("emo_", "").replace(".png", ""), fill=(255, 255, 255)); tiles.append(t)
cols = 4; rows = (len(tiles) + cols - 1) // cols; h = tiles[0].height; s = Image.new("RGB", (cols * tw, rows * h))
for i, t in enumerate(tiles): s.paste(t, ((i % cols) * tw, (i // cols) * h))
s.save(out)
