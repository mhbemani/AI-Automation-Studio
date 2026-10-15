#!/usr/bin/env python3
"""Per-shot render timing: samples `--n` evenly spread frames of every shot (default 8, min(n, shot length)), renders them headless
(one Blender process, warm-up frame discarded) and prints min/mean/max seconds per shot plus the extrapolated sequence total.
  measure_shots.py draft|final [--n 8]"""
import subprocess, sys, os, csv, json, shutil
B = "/Applications/Blender.app/Contents/MacOS/Blender"; here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
preset = sys.argv[1]; n = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 8
tl = json.load(open(os.path.join(root, "production/timeline.json")))
pick = []
for s in tl["shots"]:
    L = s["endFrame"] - s["startFrame"]; k = min(n, L)
    pick += [s["startFrame"] + int((i + 0.5) * L / k) for i in range(k)]
out = os.path.join(root, "production/out", f"measure_{preset}"); shutil.rmtree(out, ignore_errors=True)
logp = os.path.join(root, f"production/out/frame_times_{preset}_measure.csv")
if os.path.exists(logp): os.remove(logp)
frames = [pick[0] + 0] + pick      # first frame rendered twice-ish: the warm-up is the copy under a different name
cmd = [B, "-b", os.path.join(root, "scene.blend"), "-P", os.path.join(here, "render_sequence.py"), "--", "--preset", preset,
       "--frames", ",".join(map(str, [pick[0] + 1] + pick)), "--out", out, "--tag", "_measure"]
p = subprocess.run(["/usr/bin/time", "-l"] + cmd, capture_output=True, text=True)
print("\n".join(l.strip() for l in p.stderr.splitlines() if "maximum resident" in l or "peak memory" in l or " real" in l))
rows = list(csv.DictReader(open(logp)))[1:]
tot = 0
print(f"{'shot':5s} {'camera':16s} {'frames':>6s} {'n':>3s} {'min':>6s} {'mean':>6s} {'max':>6s}  est. total")
for s in tl["shots"]:
    r = [float(x["seconds"]) for x in rows if x["shot"] == s["id"]]; L = s["endFrame"] - s["startFrame"]; est = L * sum(r) / len(r); tot += est
    print(f"{s['id']:5s} {s['camera']:16s} {L:6d} {len(r):3d} {min(r):6.2f} {sum(r)/len(r):6.2f} {max(r):6.2f}  {est:7.0f} s")
print(f"TOTAL estimated for {tl['meta']['totalFrames']} frames: {tot:.0f} s = {tot/60:.1f} min = {tot/3600:.2f} h  (mean {tot/tl['meta']['totalFrames']:.2f} s/frame)")
