"""Compose the emotion image pack from render_emotions.py output: one card per emotion (body shot + face close-up,
title and the EMOTIONS.md description) and an overview grid. Run: python3 scripts/emotion_pack.py <render_dir> <out_dir>"""
import sys, os, re
from PIL import Image, ImageDraw, ImageFont
src, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
rows = {}
for line in open(os.path.join(os.path.dirname(__file__), "..", "EMOTIONS.md")):
    m = re.match(r"\| (\d\d) \| ([^|]+)\| ([^|]+)\| ([^|]+)\| ([^|]+)\|", line)
    if m: rows[m.group(1)] = [x.strip() for x in m.groups()[1:]]
try: font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 26); small = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 19)
except OSError: font = small = ImageFont.load_default()
cards = []
for f in sorted(os.listdir(src)):
    m = re.match(r"EMO_(\d\d)_(.+)_body\.png", f)
    if not m: continue
    nn, name = m.groups(); info = rows.get(nn, [name, "", "", ""])
    body = Image.open(os.path.join(src, f)).convert("RGB").resize((560, 720))
    face = Image.open(os.path.join(src, f"EMO_{nn}_{name}_face.png")).convert("RGB").resize((480, 480))
    card = Image.new("RGB", (1080, 860), (24, 24, 26)); d = ImageDraw.Draw(card)
    card.paste(body, (10, 120)); card.paste(face, (590, 120))
    d.text((14, 12), f"{nn}  {info[0]}", font=font, fill=(255, 225, 120))
    d.text((14, 52), f"brow: {info[1]}", font=small, fill=(220, 220, 220))
    d.text((14, 80), f"head: {info[2]}   body: {info[3]}", font=small, fill=(220, 220, 220))
    d.text((594, 610), "face close-up (no eyes, no mouth:", font=small, fill=(150, 150, 150))
    d.text((594, 634), "only the brow ridge moves)", font=small, fill=(150, 150, 150))
    p = os.path.join(out, f"{nn}_{name}.jpg"); card.save(p, quality=85); cards.append((nn, info[0], body, face))
cols = 6; W = 300
grid = Image.new("RGB", (cols * W, ((len(cards) + cols - 1) // cols) * (W * 2 + 40)), (24, 24, 26)); d = ImageDraw.Draw(grid)
for k, (nn, title, body, face) in enumerate(cards):
    x, y = (k % cols) * W, (k // cols) * (W * 2 + 40)
    grid.paste(body.resize((W, int(W * 720 / 560)))  .crop((0, 0, W, W + 60)), (x, y + 30)); grid.paste(face.resize((W, W)), (x, y + 30 + W + 10 - 50 + 50))
    d.text((x + 6, y + 6), f"{nn} {title}", font=small, fill=(255, 225, 120))
grid.save(os.path.join(out, "00_overview.jpg"), quality=85)
print("PACK", len(cards), "cards ->", out)
