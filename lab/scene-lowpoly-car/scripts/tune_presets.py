#!/usr/bin/env python3
"""Preset tuning driver (client side): renders 3 representative frames per config headless, prints time + error vs. a reference.
  tune_presets.py draft|final label=--set... ...   e.g.  tune_presets.py draft s16= s8='--set taa_render_samples=8'
The first (warm-up) frame of every run is discarded; frames: 230 EST, 700 HUMAN_POV (mirror), 620 CLAUDE_POV (mirror)."""
import subprocess, sys, os, csv, shlex, shutil
from PIL import Image, ImageChops, ImageStat
B = "/Applications/Blender.app/Contents/MacOS/Blender"; here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
preset = sys.argv[1]; FR = [230, 700, 620]; res = {}
def run(label, extra):
    out = os.path.join(root, "production/out", f"tune_{preset}_{label}"); shutil.rmtree(out, ignore_errors=True)
    tag = f"_tune_{label}"; logp = os.path.join(root, f"production/out/frame_times_{preset}{tag}.csv")
    if os.path.exists(logp): os.remove(logp)
    cmd = [B, "-b", os.path.join(root, "scene.blend"), "-P", os.path.join(here, "render_sequence.py"), "--", "--preset", preset, "--frames", "231," + ",".join(map(str, FR)), "--out", out, "--tag", tag] + extra
    p = subprocess.run(["/usr/bin/time", "-l"] + cmd, capture_output=True, text=True)
    rss = [l.split()[0] for l in p.stderr.splitlines() if "maximum resident" in l]
    t = {int(r["frame"]): float(r["seconds"]) for r in csv.DictReader(open(logp))}
    return out, t, int(rss[0]) / 1048576 if rss else 0
for spec in sys.argv[2:]:
    label, _, extra = spec.partition("="); out, t, rss = run(label, shlex.split(extra)); res[label] = (out, t, rss)
ref = res.get("ref")
for label, (out, t, rss) in res.items():
    err = ""
    if ref and label != "ref":
        e = [sum(ImageStat.Stat(ImageChops.difference(Image.open(f"{out}/f{f:05d}.png").convert("RGB"), Image.open(f"{ref[0]}/f{f:05d}.png").convert("RGB"))).mean) / 3 for f in FR]
        err = " err vs ref: " + " ".join(f"{x:.2f}" for x in e)
    print(f"{label:14s} " + " ".join(f"f{f}:{t[f]:5.2f}s" for f in FR) + f"  mean {sum(t[f] for f in FR) / len(FR):.2f}s  rss {rss:.0f} MB{err}")
