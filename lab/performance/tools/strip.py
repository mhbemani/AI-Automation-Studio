#!/usr/bin/env python3
"""strip.py <outdir> <png...>: contact strip (3 columns) of the apex stills, labelled with scene/beat/gesture/frame. Tiles are cropped around the character and the target."""
import sys, json, os
from PIL import Image, ImageDraw
out, files = sys.argv[1], sys.argv[2:]
meta = {m["file"]: m for m in json.load(open(os.path.join(out, "beats.json")))}
TW = 640; tiles = []
for f in files:
    im = Image.open(f).convert("RGB"); m = meta[os.path.basename(f)]
    h = int(TW * im.height / im.width); t = im.resize((TW, h), Image.LANCZOS); d = ImageDraw.Draw(t)
    d.rectangle((0, 0, TW, 20), fill=(0, 0, 0)); d.text((6, 4), "s%s b%s %s -> %s  f%s  %s" % (m["scene"], m["j"], m["gesture"], m["target"], m["apexFrame"], m["emotion"]), fill=(255, 255, 255))
    tiles.append(t)
cols = 3; rows = (len(tiles) + cols - 1) // cols; th = max(t.height for t in tiles)
sheet = Image.new("RGB", (cols * TW, rows * th), (0, 0, 0))
for i, t in enumerate(tiles): sheet.paste(t, ((i % cols) * TW, (i // cols) * th))
scene = sorted({m["scene"] for m in meta.values()}); name = os.path.join(out, "strip_scene%s.png" % "-".join(str(s) for s in scene))
sheet.save(name); print(name)
# zoom strip: the character square of each apex frame (face, hands and the cross/dot visible), 4 columns
ZW = 420; z = []
for f in files:
    im = Image.open(f).convert("RGB"); m = meta[os.path.basename(f)]; l, t, S = m["rect"]
    x0, y0 = int(l + S * 0.12), int(t + S * 0.08); x1, y1 = int(l + S * 0.92), int(t + S * 0.92)
    c = Image.new("RGB", (x1 - x0, y1 - y0), (0, 0, 0)); c.paste(im.crop((max(0, x0), max(0, y0), min(im.width, x1), min(im.height, y1))), (max(0, -x0), max(0, -y0)))
    c = c.resize((ZW, int(ZW * c.height / c.width)), Image.LANCZOS); d = ImageDraw.Draw(c); d.rectangle((0, 0, ZW, 16), fill=(0, 0, 0))
    d.text((4, 3), "s%s b%s %s [%s] f%s" % (m["scene"], m["j"], m["gesture"], m["emotion"], m["apexFrame"]), fill=(255, 255, 255)); z.append(c)
cols = 4; rows = (len(z) + cols - 1) // cols; zh = max(c.height for c in z); zs = Image.new("RGB", (cols * ZW, rows * zh), (0, 0, 0))
for i, c in enumerate(z): zs.paste(c, ((i % cols) * ZW, (i // cols) * zh))
zname = name.replace("strip_", "zoom_"); zs.save(zname); print(zname)
