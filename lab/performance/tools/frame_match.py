#!/usr/bin/env python3
"""Frame-mapping check: which frame of REFERENCE does each frame of RENDER actually show?  (catches duplicated / skipped / shifted video frames)
usage: frame_match.py render.mp4 reference.mp4 [--crop W:H:X:Y] [--shifts 3]
For k in -K..K it computes the per-frame mean |render[n] - ref[n+k]| and prints, per frame, the k with the smallest difference.
A perfect 1:1 mapping gives best k = 0 on every frame (static moments are ambiguous and are excluded when the minimum is not clear)."""
import sys, re, subprocess, tempfile, os, argparse, collections, json
ap = argparse.ArgumentParser(); ap.add_argument("render"); ap.add_argument("ref"); ap.add_argument("--crop"); ap.add_argument("--shifts", type=int, default=3); ap.add_argument("--json")
a = ap.parse_args(); K = a.shifts
def series(k):
    tmp = tempfile.mktemp(suffix=".txt"); c = ("crop=%s," % a.crop) if a.crop else ""
    fc = "[0:v]trim=start_frame=%d,setpts=PTS-STARTPTS,%sformat=gray[a];[1:v]trim=start_frame=%d,setpts=PTS-STARTPTS,%sformat=gray[b];[a][b]blend=all_mode=difference,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=%s" % (K, c, K + k, c, tmp)
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.render, "-i", a.ref, "-filter_complex", fc, "-f", "null", "-"], capture_output=True, text=True)
    if r.returncode: sys.exit(r.stderr[-400:])
    v = [float(x) for x in re.findall(r"YAVG=([\d.]+)", open(tmp).read())]; os.remove(tmp); return v
S = {k: series(k) for k in range(-K, K + 1)}
n = min(len(v) for v in S.values()) - K; best = []
for i in range(n):
    ks = sorted(S, key=lambda k: S[k][i]); b, s = ks[0], ks[1]
    best.append((b, S[b][i], S[0][i], S[s][i]))
cnt = collections.Counter(b for b, _, _, _ in best); amb = sum(1 for b, m, z, s in best if s - m < 0.02)
off = [i + K for i, (b, m, z, s) in enumerate(best) if b != 0 and s - m >= 0.02]
print("frames %d | best shift histogram %s | ambiguous(static) %d | frames not showing ref[n]: %d (%s...) | mean diff at k=0: %.3f, at best k: %.3f" % (n, dict(sorted(cnt.items())), amb, len(off), off[:15], sum(z for _, _, z, _ in best) / n, sum(m for _, m, _, _ in best) / n))
if a.json: json.dump({"best": [b for b, *_ in best], "k0": [z for _, _, z, _ in best]}, open(a.json, "w"))
