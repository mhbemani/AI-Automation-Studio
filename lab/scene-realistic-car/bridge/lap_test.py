#!/usr/bin/env python3
"""Full-lap check (client side, live Blender): N samples evenly around CITY_DrivePath seen from CAMERA
(parented to the car). The path's keyed eval_time is muted while sampling and restored afterwards.
  lap_test.py out.png [CAMERA] [N] [--render]"""
import subprocess, sys, os, tempfile, json
from PIL import Image, ImageDraw
here = os.path.dirname(os.path.abspath(__file__)); bl = os.path.join(here, "bl.py")
a = [x for x in sys.argv[1:] if x != "--render"]; render = "--render" in sys.argv
out = a[0]; cam = a[1] if len(a) > 1 else "CAM_CLAUDE_POV"; n = int(a[2]) if len(a) > 2 else 10

def ex(code):
    r = subprocess.run([sys.executable, bl, "exec", code], capture_output=True, text=True, check=True)
    return r.stdout.strip().split("result: ")[-1]

ex("""import bpy
cu = bpy.data.objects["CITY_DrivePath"].data
for fc in (cu.animation_data.action.fcurves if cu.animation_data and cu.animation_data.action else []): fc.mute = True
result = cu.path_duration""")
cells = []
try:
    for i in range(n):
        info = ex(f"""import bpy
cu = bpy.data.objects["CITY_DrivePath"].data; cu.eval_time = cu.path_duration * {i} / {n}
bpy.context.view_layer.update(); car = bpy.data.objects["CAR_Exterior"]
import math
result = [round(v, 1) for v in car.matrix_world.translation] + [round(math.degrees(car.matrix_world.to_euler().z), 1)]""")
        p = os.path.join(tempfile.gettempdir(), f"lap_{i}.png")
        subprocess.run([sys.executable, bl, "snap", p, cam] + (["--render"] if render else []), check=True, capture_output=True)
        im = Image.open(p).convert("RGB"); w = 480; im = im.resize((w, int(im.height * w / im.width)))
        ImageDraw.Draw(im).text((6, 4), f"{100 * i // n}% lap  car {info}", fill=(255, 255, 0)); cells.append(im)
        print(i, info)
finally:
    ex("""import bpy
cu = bpy.data.objects["CITY_DrivePath"].data
for fc in (cu.animation_data.action.fcurves if cu.animation_data and cu.animation_data.action else []): fc.mute = False
bpy.context.scene.frame_set(bpy.context.scene.frame_current)
result = "restored\"""")
cols = 5; h = cells[0].height; rows = (len(cells) + cols - 1) // cols
sheet = Image.new("RGB", (cols * 480, rows * h))
for i, im in enumerate(cells): sheet.paste(im, ((i % cols) * 480, (i // cols) * h))
sheet.save(out); print(out)
