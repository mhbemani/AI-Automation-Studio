#!/usr/bin/env python3
"""Contact sheet of live-Blender snapshots (client side; needs the bridge + Pillow).
  snapgrid.py out.png COLS [--render] [--w 480] FRAME[@CAMERA] ...     (no @CAMERA: the camera the markers pick)
Each cell is labelled with its frame and camera. --render uses a real Eevee render (slow, shows the mirror)."""
import subprocess, sys, os, tempfile
from PIL import Image, ImageDraw
here = os.path.dirname(os.path.abspath(__file__)); bl = os.path.join(here, "bl.py")
a = sys.argv[1:]; out, cols = a[0], int(a[1]); rest = a[2:]
render = "--render" in rest; rest = [x for x in rest if x != "--render"]
w = 480
if "--w" in rest: i = rest.index("--w"); w = int(rest[i + 1]); del rest[i:i + 2]
cells = []
for spec in rest:
    f, _, cam = spec.partition("@")
    pick = "bpy.context.scene.frame_set(%s)" % f
    r = subprocess.run([sys.executable, bl, "exec", pick + "\nresult = bpy.context.scene.camera.name"], capture_output=True, text=True)
    cam = cam or r.stdout.strip().split("result: ")[-1]
    p = os.path.join(tempfile.gettempdir(), "snapgrid_%s.png" % f)
    subprocess.run([sys.executable, bl, "snap", p, cam] + (["--render"] if render else []), check=True, capture_output=True)
    im = Image.open(p).convert("RGB"); h = int(im.height * w / im.width); im = im.resize((w, h))
    ImageDraw.Draw(im).text((6, 4), f"f{f} {cam}", fill=(255, 255, 0)); cells.append(im)
h = cells[0].height; rows = (len(cells) + cols - 1) // cols
sheet = Image.new("RGB", (cols * w, rows * h))
for i, im in enumerate(cells): sheet.paste(im, ((i % cols) * w, (i // cols) * h))
sheet.save(out); print(out)
