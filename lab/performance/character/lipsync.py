#!/usr/bin/env python3
"""Amplitude lip sync (no deps): narration WAV -> mouth.json  {fps, frames:[0..1 per frame], blinks:[s], nods:[s]}.
usage: lipsync.py narration.wav [mouth.json] [--fps 30]"""
import json, math, random, struct, subprocess, sys, wave, tempfile, os

def read_mono(path):
    try:
        w = wave.open(path)
        if w.getsampwidth() != 2: raise wave.Error("not 16 bit")
        ch, sr, raw = w.getnchannels(), w.getframerate(), w.readframes(w.getnframes())
    except (wave.Error, EOFError):           # float/24-bit WAV: let ffmpeg normalise
        tmp = tempfile.mktemp(suffix=".wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-ac", "1", "-c:a", "pcm_s16le", tmp], check=True)
        w = wave.open(tmp); ch, sr, raw = 1, w.getframerate(), w.readframes(w.getnframes()); os.remove(tmp)
    s = struct.unpack("<%dh" % (len(raw) // 2), raw)
    return ([sum(s[i:i + ch]) / ch for i in range(0, len(s), ch)] if ch > 1 else list(s)), sr

def envelope(path, fps=30, thr=0.10, attack=0.65, release=0.30):
    s, sr = read_mono(path); hop = sr / fps; win = int(sr * 0.04)
    rms = []
    for f in range(int(len(s) / hop) + 1):
        c = int(f * hop); seg = s[max(0, c - win // 2): c + win // 2]
        rms.append(math.sqrt(sum(x * x for x in seg) / len(seg)) if seg else 0.0)
    srt = sorted(rms); ref = srt[int(len(srt) * 0.95)] or 1.0           # p95 = "loud syllable"
    out, y = [], 0.0
    for r in rms:
        x = min(1.0, r / ref); x = max(0.0, (x - thr) / (1 - thr)) ** 0.75
        y += (x - y) * (attack if x > y else release)                      # fast open, slower close
        out.append(round(y, 3))
    return out

def accents(env, fps, seed=3):
    rng = random.Random(seed); T = len(env) / fps
    nods, last = [], -1.0
    for i in range(1, len(env) - 1):                                      # emphasised peaks
        if env[i] > 0.85 and env[i] >= env[i - 1] and env[i] > env[i + 1] and i / fps - last > 0.9: nods.append(round(i / fps, 3)); last = i / fps
    blinks, t = [], rng.uniform(0.8, 2.0)
    while t < T:
        blinks.append(round(t, 3)); t += rng.uniform(2.4, 4.8)
    return blinks, nods

if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    fps = int(sys.argv[sys.argv.index("--fps") + 1]) if "--fps" in sys.argv else 30
    if "--fps" in sys.argv: a.remove(str(fps))
    if not a: sys.exit(__doc__)
    env = envelope(a[0], fps); b, n = accents(env, fps)
    dst = a[1] if len(a) > 1 else "mouth.json"
    json.dump({"fps": fps, "frames": env, "blinks": b, "nods": n}, open(dst, "w"))
    print("%s: %d frames (%.1fs), mean open %.2f, %d blinks, %d nods" % (dst, len(env), len(env) / fps, sum(env) / len(env), len(b), len(n)))
