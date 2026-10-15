#!/usr/bin/env python3
"""Temporal-flicker meter (stdlib + ffmpeg only).
usage: flicker_check.py <video | png-pattern like frames/f_%04d.png> [--label NAME] [--alpha] [--crop W:H:X:Y] [--scale 480]
                        [--start N --frames M] [--json out.json] [--vp9]
Per frame it measures, over the (cropped) region:
  d1 = mean |frame[n]-frame[n-1]|          (0..255, luma, or the alpha plane with --alpha)
  d2 = mean |frame[n]-2*frame[n-1]+frame[n-2]|   (second difference: smooth motion ~0, pops and flicker large)
Flags:  spike  = d1[n] > 2.5 x mean(d1[n-1], d1[n+1])  AND d1[n] above a noise floor (0.05)
        rough  = jaggedness of the d1 series (smooth motion ~0.02-0.1, stutter/flicker > 0.3);  dups = frames repeating the previous one while moving
  (d2/hf are kept in the JSON only: antialiased edges make hf ~1.2-1.4 even for perfectly smooth motion, so it is not a usable absolute scale)
Also prints median d1 (the noise/motion baseline)."""
import sys, re, json, subprocess, statistics, argparse, os, tempfile

def run(path, alpha, crop, scale, start, frames, vp9, rate):
    pre = ["-c:v", "libvpx-vp9"] if (vp9 or path.endswith(".webm")) else []
    inp = ["-framerate", str(rate)] if "%" in path else []
    sel = ["-ss", str(start / rate)] if start else []
    out = []
    for stage in ("d1", "d2"):
        vf = []
        if alpha: vf += ["format=yuva420p", "alphaextract"]
        else: vf += ["format=gray"]
        if crop: vf += ["crop=%s" % crop]
        if scale: vf += ["scale=%d:-2:flags=area" % scale]   # area filter keeps differences honest (no extra aliasing)
        vf += ["format=gray"]
        if stage == "d1": vf += ["tblend=all_expr='abs(A-B)'"]
        else: vf += ["tblend=all_expr='clip((A-B)/2+128,0,255)'", "tblend=all_expr='abs(A-B)*2'"]
        vf += ["signalstats", "metadata=print:key=lavfi.signalstats.YAVG:file=%s" % "{TMP}"]
        tmp = tempfile.mktemp(suffix=".txt"); vf[-1] = vf[-1].replace("{TMP}", tmp)
        cmd = ["ffmpeg", "-v", "error", "-y"] + pre + inp + sel + ["-i", path] + (["-frames:v", str(frames)] if frames else []) + ["-vf", ",".join(vf), "-f", "null", "-"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode: sys.exit("ffmpeg failed: " + r.stderr[-500:])
        vals = [float(m) for m in re.findall(r"YAVG=([\d.]+)", open(tmp).read())]; os.remove(tmp)
        out.append(vals)
    return out

def analyse(d1, d2, label, start=0):
    # d1[0] is blend of frame0 with itself (0); d1[i] = diff(i, i-1). d2[i] valid from i>=2
    n = len(d1); spikes = []
    for i in range(2, n - 1):
        nb = (d1[i - 1] + d1[i + 1]) / 2
        if d1[i] > 0.05 and d1[i] > 2.5 * max(nb, 0.02): spikes.append({"frame": i + start, "d1": round(d1[i], 3), "ratio": round(d1[i] / max(nb, 0.02), 1)})
    m1 = statistics.mean(d1[1:]); m2 = statistics.mean(d2[2:]) if len(d2) > 2 else 0
    # rough = how jagged the d1 series itself is: mean |d1[n] - (d1[n-1]+d1[n+1])/2| / mean(d1)   (smooth motion ~0.02-0.1; stutter/flicker >0.3)
    rough = statistics.mean(abs(d1[i] - (d1[i - 1] + d1[i + 1]) / 2) for i in range(2, n - 1)) / max(m1, 1e-9)
    # dups = frames that look like a repeat of the previous frame (d1 << neighbours) while the picture is moving
    dups = sum(1 for i in range(2, n - 1) if d1[i] < 0.25 * min(d1[i - 1], d1[i + 1]) and min(d1[i - 1], d1[i + 1]) > 0.3)
    return {"label": label, "frames": n, "d1_mean": round(m1, 4), "d1_median": round(statistics.median(d1[1:]), 4), "d1_max": round(max(d1), 3),
            "d2_mean": round(m2, 4), "hf": round(m2 / m1, 3) if m1 > 1e-9 else 0, "rough": round(rough, 3), "dups": dups, "spikes": len(spikes), "spike_list": spikes}

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("path"); ap.add_argument("--label"); ap.add_argument("--alpha", action="store_true")
    ap.add_argument("--crop"); ap.add_argument("--scale", type=int, default=0); ap.add_argument("--start", type=int, default=0); ap.add_argument("--frames", type=int, default=0)
    ap.add_argument("--json"); ap.add_argument("--vp9", action="store_true"); ap.add_argument("--rate", type=int, default=30)
    a = ap.parse_args()
    d1, d2 = run(a.path, a.alpha, a.crop, a.scale, a.start, a.frames, a.vp9, a.rate)
    res = analyse(d1, d2, a.label or os.path.basename(a.path), a.start); res["series_d1"] = [round(x, 3) for x in d1]
    if a.json: json.dump(res, open(a.json, "w"))
    s = ", ".join("%d(x%.1f)" % (x["frame"], x["ratio"]) for x in res["spike_list"][:12])
    print("%-34s frames %4d  d1 mean %.3f median %.3f max %.2f | rough %.2f dups %d | spikes %d %s" % (res["label"], res["frames"], res["d1_mean"], res["d1_median"], res["d1_max"], res["rough"], res["dups"], res["spikes"], s))
