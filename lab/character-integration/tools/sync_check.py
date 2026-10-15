"""dev tool: sync_check.py <id> — intended vs actual times, measured on the rendered files (needs numpy: use the lab/tts venv python)
  words   : whisper on the final mp4's audio vs intended narration word times (audio chain: align -> adelay -> mix -> loudnorm -> mux)
  packets : first video frame where each packet's colour appears in out/<id>/final.mp4 vs intended launch time (Remotion frame clock)
  char    : pose-change onset in the character clip's alpha silhouette after each timeline event (expected lag: up to the 6-frame cross-fade)
  mouth   : best lag between narration loudness and the dark-mouth pixel count in the character clip (0 = in sync)"""
import sys, os, json, subprocess, re, statistics
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); id = sys.argv[1]
W = f"{ROOT}/work/{id}"; O = f"{ROOT}/out/{id}"; FPS = 30
sync = json.load(open(f"{W}/sync.json")); proj = json.load(open(f"{W}/project.json")); tl = json.load(open(f"{W}/timeline.json"))
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
rep = {}
def stats(xs): xs = sorted(abs(x) for x in xs); return dict(n=len(xs), mean_ms=round(sum(xs) / len(xs), 1), p95_ms=round(xs[int(.95 * (len(xs) - 1))], 1), max_ms=round(xs[-1], 1)) if xs else dict(n=0)

# 1. words: whisper on the final mix (mp4 audio) and on the clean aligned narration.wav
model = os.environ.get("WHISPER_MODEL", f"{ROOT}/../ffmpeg/models/ggml-base.en.bin")
def words_drift(src, tag):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vn", "-ac", "1", "-ar", "16000", f"{W}/{tag}16k.wav"], check=True)
    subprocess.run(["whisper-cli", "-m", model, "-f", f"{W}/{tag}16k.wav", "-ml", "1", "-sow", "-oj", "-of", f"{W}/{tag}_words", "-np"], capture_output=True, check=True)
    ws = [(norm(x["text"]), x["offsets"]["from"] / 1000) for x in json.load(open(f"{W}/{tag}_words.json"))["transcription"] if norm(x["text"])]
    p = 0; d = []
    for w in sync["words"]:
        for j in range(p, min(p + 4, len(ws))):
            if ws[j][0] == norm(w["w"]): d.append((ws[j][1] - w["at"]) * 1000); p = j + 1; break
    return {**stats(d), "matched": f"{len(d)}/{len(sync['words'])}", "signed_mean_ms": round(statistics.mean(d), 1)}
rep["words_final_mp4"] = words_drift(f"{O}/final.mp4", "fin"); rep["words_narration_wav"] = words_drift(f"{W}/narration.wav", "nar")

# 2. packets: colour appearance in the 16:9 video
def frames(path, t0, t1, w=480, h=270):
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}", "-i", path, "-vf", f"fps={FPS},scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(r, np.uint8).reshape(-1, h, w, 3).astype(int)
pk = []
for k in sorted((q for s in proj["scenes"] if s["type"] == "flow" for q in [(s, x) for x in s["packets"]]), key=lambda q: q[0]["startSec"] + q[1]["at"]):
    s, q = k; at = s["startSec"] + q["at"]; t0 = max(0, at - 0.5)
    fr = frames(f"{O}/final.mp4", t0, at + 0.5); c = np.array([int(q["color"][i:i + 2], 16) for i in (1, 3, 5)])
    cnt = (np.abs(fr[:, :200] - c).max(axis=3) < 14).sum(axis=(1, 2))  # rows above the caption rect (captions also use amber); base = np.median(cnt[:8])
    base = np.median(cnt[:8])
    hit = next((i for i, v in enumerate(cnt) if i > 8 and v > base + 25), None)
    if hit is not None: pk.append(dict(label=q["label"], intended=round(at, 3), observed=round(t0 + hit / FPS, 3), drift_ms=round((t0 + hit / FPS - at) * 1000, 1)))
rep["packets"] = {**stats([x["drift_ms"] for x in pk]), "of": sum(len(s["packets"]) for s in proj["scenes"] if s["type"] == "flow"), "signed_mean_ms": round(statistics.mean([x["drift_ms"] for x in pk]), 1) if pk else None, "detail": pk}

# 3+4. character clip: silhouette onset per event, mouth vs loudness
cs = proj["character"]["file"]; S = 360
raw = subprocess.run(["ffmpeg", "-v", "error", "-c:v", "libvpx-vp9", "-i", f"{W}/{cs}", "-vf", f"scale={S}:{S}", "-pix_fmt", "rgba", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
cl = np.frombuffer(raw, np.uint8).reshape(-1, S, S, 4)
mask = cl[..., 3] > 128; e = np.array([0] + [int((mask[i] ^ mask[i - 1]).sum()) for i in range(1, len(mask))], float)
ons = []
for ev in tl["events"][1:]:
    fe = round(ev["t"] * FPS); b = e[max(1, fe - 12):fe - 1]
    if len(b) < 4: continue
    thr = b.mean() + 4 * b.std() + 20
    hit = next((i for i in range(fe - 2, min(len(e), fe + 14)) if e[i] > thr), None)
    ons.append(dict(action=ev["action"], t=ev["t"], onset_lag_ms=None if hit is None else round((hit - fe) / FPS * 1000, 1)))
got = [o["onset_lag_ms"] for o in ons if o["onset_lag_ms"] is not None]
rep["character_events"] = {**stats(got), "events": len(ons), "no_onset_found": len(ons) - len(got), "signed_mean_ms": round(statistics.mean(got), 1) if got else None, "detail": ons}
sys.path.insert(0, f"{ROOT}/../character"); import lipsync
env = np.array(lipsync.envelope(f"{W}/narration.wav", FPS)); n = min(len(env), len(cl))
rgb = cl[..., :3].astype(int); head = (slice(0, int(S * 0.55)),)
dark = ((rgb[..., 0] < 70) & (rgb[..., 1] < 38) & (rgb[..., 2] < 75) & (cl[..., 3] > 200))[:, :int(S * 0.55)].sum(axis=(1, 2)).astype(float)
def z(x): return (x - x.mean()) / (x.std() + 1e-9)
best = max(range(-10, 11), key=lambda L: float((z(dark[max(0, L):n + min(0, L)]) * z(env[max(0, -L):n - max(0, L)])).mean()))
cor = {L: round(float((z(dark[max(0, L):n + min(0, L)]) * z(env[max(0, -L):n - max(0, L)])).mean()), 3) for L in (-3, -2, -1, 0, 1, 2, 3)}
rep["mouth_vs_narration"] = {"best_lag_frames": best, "best_lag_ms": round(best / FPS * 1000, 1), "corr_at_lags": cor}
rep["video"] = {"durationSec": proj["durationSec"], "frames_in_clip": len(cl), "expected_frames": round(proj["durationSec"] * FPS)}
json.dump(rep, open(f"{O}/sync_report.json", "w"), indent=1)
print(json.dumps({k: {a: b for a, b in v.items() if a != "detail"} for k, v in rep.items()}, indent=1))
