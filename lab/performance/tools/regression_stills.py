#!/usr/bin/env python3
"""No-regression check: stills of the new render vs the approved video's stills, with the CHARACTER region masked out.
usage: regression_stills.py <new_stills_dir> <approved_stills_dir> <geometry.json> [--out report.json]
Files are h_<sec>.png / v_<sec>.png (stages/stills.mjs naming). The mask is the character clip square (+10% margin) of that frame from geometry.json
(the square contains the character, its shadow blob and every pose); everything else - backdrop, diagrams, packets, text, captions - must be pixel-identical
(tolerance: per-pixel max channel difference <= 2, i.e. PNG/JPEG-free but allows sub-pixel animation rounding)."""
import sys, os, json
from PIL import Image, ImageChops
new, old, geo = sys.argv[1:4]; G = json.load(open(geo)); res = []
for f in sorted(os.listdir(old)):
    if not f.endswith(".png") or not os.path.exists(os.path.join(new, f)): continue
    tag = "16:9" if f[0] == "h" else "9:16"; sec = float(f[2:-4]); fr = int(round(sec * 30)); r = G[tag]["rect"][min(fr, len(G[tag]["rect"]) - 1)]
    a = Image.open(os.path.join(old, f)).convert("RGB"); b = Image.open(os.path.join(new, f)).convert("RGB")
    m = r[2] * 0.1; box = (int(r[0] - m), int(r[1] - m), int(r[0] + r[2] + m), int(r[1] + r[2] + m))
    d = ImageChops.difference(a, b).convert("L"); mask = Image.new("L", d.size, 255); mask.paste(0, box)
    d = ImageChops.multiply(d, mask.point(lambda v: 1 if v else 0)); hist = d.histogram(); n = sum(hist[3:]); mx = max((i for i, c in enumerate(hist) if c), default=0)
    res.append({"file": f, "pixels_over_2": n, "max_diff": mx, "masked_box": box})
bad = [x for x in res if x["pixels_over_2"] > 0]
out = {"compared": len(res), "identical_outside_character": len(res) - len(bad), "differing": bad}
if "--out" in sys.argv: json.dump(out, open(sys.argv[sys.argv.index("--out") + 1], "w"), indent=1)
print("regression: %d stills compared, %d identical outside the character region, %d differ" % (len(res), len(res) - len(bad), len(bad)))
for x in bad[:10]: print("  ", x["file"], "px>2:", x["pixels_over_2"], "max", x["max_diff"])
