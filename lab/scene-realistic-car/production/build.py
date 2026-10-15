"""build.py — dialogue_v2.json -> per-line WAVs (Kokoro) -> Whisper word times -> timeline.json, envelopes, voice tracks.

Writes: work/lines/NN.wav (trimmed line audio, 24 kHz), work/voice_{claude,human,all}.wav (placed on the timeline),
timeline.json, envelope_claude.json, envelope_human.json. Frame f (1-based) covers [(f-1)/24, f/24) s; all ranges are
[startFrame, endFrame) (end exclusive).
"""
import json, math, os, re, subprocess, sys
import numpy as np, soundfile as sf
from validate import validate

LAB = "lab"
KOKORO = (f"{LAB}/tts/models/kokoro-v1.0.int8.onnx", f"{LAB}/tts/models/voices-v1.0.bin")
WHISPER, WMODEL, FFMPEG = "/opt/homebrew/bin/whisper-cli", f"{LAB}/ffmpeg/models/ggml-base.en.bin", "/opt/homebrew/bin/ffmpeg"
FPS, SR = 24, 24000
SPF = SR // FPS                      # 1000 samples per frame: frame starts are sample exact
LEAD, TAIL = 0.5, 1.0                # s before line 1 / after the last line
MIN_HOLD = math.ceil(1.2 * FPS)      # 29 frames
TRIM_DB, PAD = -45, 0.03             # silence trim threshold (dBFS, 10 ms windows) and kept padding (s)
POV = {"claude": "CAM_HUMAN_POV", "human": "CAM_CLAUDE_POV"}  # speaker -> camera that shows them
OTHER = {"claude": "human", "human": "claude"}
os.makedirs("work/lines", exist_ok=True)
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
frame_at = lambda t: 1 + math.floor(t * FPS + 1e-9)   # frame containing time t
log = []


def say(*a):
    print(*a); log.append(" ".join(map(str, a)))


def spoken(text, pron):
    for k, v in pron.items():
        text = re.sub(rf"(?<![\w']){re.escape(k)}(?![\w'])", v, text)
    return text


def trim(a):
    """drop Kokoro's leading/trailing silence: first/last 10 ms window above TRIM_DB, keep PAD."""
    w = SR // 100
    rms = np.sqrt(np.mean(a[: len(a) // w * w].reshape(-1, w) ** 2, axis=1) + 1e-12)
    loud = np.nonzero(20 * np.log10(rms) > TRIM_DB)[0]
    p = int(PAD * SR)
    return a[max(0, loud[0] * w - p): min(len(a), (loud[-1] + 1) * w + p)]


def synth(d):
    import shutil, espeakng_loader
    from kokoro_onnx import Kokoro, EspeakConfig
    # espeak-ng keeps its data path in a ~160-char buffer; the venv path in this worktree is longer and gets truncated
    # (crash: "Error processing file .../phontab"). A copy under work/ keeps the path short enough (131 chars here).
    # ponytail: breaks again if the checkout path grows by ~25 chars; then point ESPEAK_DATA at a shorter dir.
    esd = os.environ.get("ESPEAK_DATA", "work/espeak-ng-data")
    if not os.path.isdir(esd):
        shutil.copytree(espeakng_loader.get_data_path(), esd)
    k = None
    for l in d["lines"]:
        v = d["voices"][l["speaker"]]
        key = json.dumps([spoken(l["text"], d["pronunciation"]), v["voice"], v["speed"]])
        wav, keyf = f"work/lines/{l['id']:02d}.wav", f"work/lines/{l['id']:02d}.key"
        if os.path.exists(wav) and os.path.exists(keyf) and open(keyf).read() == key:
            continue                                           # cached: same text, voice and speed
        if k is None:
            k = Kokoro(*KOKORO, espeak_config=EspeakConfig(data_path=esd))
            missing = {x["voice"] for x in d["voices"].values()} - set(k.get_voices())
            if missing:
                sys.exit(f"voices not in voices file: {sorted(missing)}")
        a, sr = k.create(json.loads(key)[0], voice=v["voice"], speed=v["speed"], lang="en-gb" if v["voice"][0] == "b" else "en-us")
        assert sr == SR, sr
        sf.write(wav, trim(np.asarray(a, dtype=np.float32)), SR)
        open(keyf, "w").write(key)
        say(f"synth line {l['id']}: {json.loads(key)[0]!r}")


def whisper_words(l, pron, dur):
    """script words with (from, to) seconds inside the line clip; greedy match to Whisper tokens, gaps interpolated."""
    base = f"work/lines/{l['id']:02d}"
    subprocess.run([FFMPEG, "-v", "error", "-y", "-i", base + ".wav", "-ar", "16000", "-ac", "1", base + "_16k.wav"], check=True)
    subprocess.run([WHISPER, "-m", WMODEL, "-f", base + "_16k.wav", "-ml", "1", "-sow", "-oj", "-of", base + "_w", "-np", "-t", "4"], check=True, capture_output=True)
    ws = [(norm(x["text"]), x["offsets"]["from"] / 1000, x["offsets"]["to"] / 1000) for x in json.load(open(base + "_w.json"))["transcription"]]
    ws = [x for x in ws if x[0]]
    heard = " ".join(x[0] for x in ws)
    words, p = l["text"].split(), 0
    at, to = [None] * len(words), [None] * len(words)
    for i, w in enumerate(words):
        target = norm(spoken(w, pron))
        for j in range(p, min(p + 4, len(ws))):
            for n in range(1, 4):                              # a script word may be 1-3 Whisper tokens ("it's", "A P I")
                if "".join(x[0] for x in ws[j: j + n]) == target:
                    at[i], to[i], p = ws[j][1], ws[j + n - 1][2], j + n
                    break
            if at[i] is not None:
                break
    miss = [w for w, a in zip(words, at) if a is None]
    for i in range(len(words)):                                # interpolate unmatched words between neighbours
        if at[i] is None:
            a = i - 1
            b = next((j for j in range(i + 1, len(words)) if at[j] is not None), len(words))
            t0 = to[a] if a >= 0 else 0.0
            t1 = at[b] if b < len(words) else dur
            span = (t1 - t0) / (b - a)
            at[i], to[i] = t0 + span * (i - a - 1), t0 + span * (i - a)
    return [(w, min(max(a, 0), dur), min(max(t, a + 1 / FPS), dur)) for w, a, t in zip(words, at, to)], miss, heard


def envelope(track, nframes):
    """per-frame RMS, fast attack / slow release, normalised so the speaker's loudest frame is 1, gated to 0 in silence."""
    rms = np.sqrt(np.mean(track[: nframes * SPF].reshape(nframes, SPF) ** 2, axis=1))
    sm, e = [], 0.0
    for x in rms:
        e += (0.7 if x > e else 0.18) * (x - e)               # attack ~1 frame, release ~5 frames
        sm.append(e)
    sm = np.array(sm) / (max(sm) or 1)
    return [0.0 if x < 0.03 else round(float(x), 4) for x in sm]


def main():
    d = json.load(open("dialogue_v2.json"))
    if (err := validate(d)):
        sys.exit("dialogue invalid:\n  " + "\n  ".join(err))
    synth(d)

    # intro shots
    shots, f = [], 1
    for i, s in enumerate(d["intro"]):
        n = round(s["durationSec"] * FPS)
        shots.append({"id": f"S{len(shots) + 1:02d}", "shot": s["shot"], "camera": s["camera"], "startFrame": f, "endFrame": f + n})
        f += n
    drive = f
    phone_i = next(i for i, s in enumerate(d["intro"]) if "phoneText" in s)

    # lines: each trimmed clip starts on a frame boundary; next line starts gap frames after the previous clip's end frame
    gap = round(d["gapBetweenLinesSec"] * FPS)
    lines, start, clips = [], drive + round(LEAD * FPS), []
    for l in d["lines"]:
        a, _ = sf.read(f"work/lines/{l['id']:02d}.wav", dtype="float32")
        dur = len(a) / SR
        words, miss, heard = whisper_words(l, d["pronunciation"], dur)
        if miss:
            say(f"line {l['id']}: {len(miss)} word(s) not matched to Whisper, interpolated: {miss} | whisper heard: {heard!r}")
        t0 = (start - 1) / FPS
        end = start + math.ceil(len(a) / SPF)
        lines.append({"id": l["id"], "speaker": l["speaker"], "emotion": l["emotion"], "text": l["text"], "startFrame": start, "endFrame": end,
                      "words": [{"w": w, "startFrame": frame_at(t0 + a0), "endFrame": max(frame_at(t0 + a0) + 1, min(end, frame_at(t0 + a1)))} for w, a0, a1 in words]})
        clips.append((l["speaker"], (start - 1) * SPF, a))
        start = end + gap
    last = lines[-1]["endFrame"] + round(TAIL * FPS)           # exclusive end of the video
    total = last - 1

    # interior cuts: cut on the line's first word when the speaker changes; the gap stays on the previous shot.
    # first interior shot starts at the end of the intro (it carries the lead-in). A cut that would leave the previous
    # shot shorter than MIN_HOLD is delayed to MIN_HOLD (reported); same-speaker runs are merged into one shot.
    first = {"id": "", "shot": "INT", "camera": POV[lines[0]["speaker"]], "startFrame": drive, "endFrame": None}
    interior = [first]
    for l in lines[1:]:
        cam = POV[l["speaker"]]
        if cam == interior[-1]["camera"]:
            say(f"line {l['id']}: same speaker as previous shot, held (no cut)")
            continue
        cut = max(l["startFrame"], interior[-1]["startFrame"] + MIN_HOLD)
        if cut != l["startFrame"]:
            say(f"line {l['id']}: cut delayed {cut - l['startFrame']} frame(s) to keep the 1.2 s minimum hold")
        interior[-1]["endFrame"] = cut
        interior.append({"id": "", "shot": "INT", "camera": cam, "startFrame": cut, "endFrame": None})
    interior[-1]["endFrame"] = last
    for s in interior:
        s["id"] = f"S{len(shots) + 1:02d}"
        shots.append(s)

    # emotion keys: speaker key 4 frames before the line, listener reaction 6 frames after it starts, both neutral at line end
    REACT = {"happy": "amused", "amused": "amused", "proud": "amused", "excited": "curious", "surprised": "curious", "thoughtful": "curious", "curious": "curious", "neutral": "neutral"}
    keys = {"claude": {1: ("neutral", 0.0)}, "human": {1: ("neutral", 0.0)}}
    for l in lines:
        s, o = l["speaker"], OTHER[l["speaker"]]
        keys[s][max(1, l["startFrame"] - 4)] = (l["emotion"], 0.8)
        keys[o][l["startFrame"] + 6] = (REACT[l["emotion"]], 0.4)
        keys[s][l["endFrame"]] = keys[o][l["endFrame"]] = ("neutral", 0.0)
    emotion_keys = {sp: [{"frame": fr, "emotion": e, "intensity": i} for fr, (e, i) in sorted(k.items())] for sp, k in keys.items()}

    # voice tracks placed sample exactly, envelopes
    nsamp = total * SPF
    tracks = {"claude": np.zeros(nsamp, np.float32), "human": np.zeros(nsamp, np.float32)}
    for sp, at, a in clips:
        tracks[sp][at: at + len(a)] += a
    for sp, t in tracks.items():
        sf.write(f"work/voice_{sp}.wav", t, SR)
        json.dump(envelope(t, total), open(f"envelope_{sp}.json", "w"), separators=(",", ":"))
    sf.write("work/voice_all.wav", tracks["claude"] + tracks["human"], SR)

    # phone typing and motion cues
    ps = shots[phone_i]
    text = d["intro"][phone_i]["phoneText"]
    typ = ps["startFrame"] + 12
    typ_end = typ + math.ceil(len(text) / 12 * FPS)
    phone = {"shotId": ps["id"], "phoneText": text, "startFrame": typ, "charsPerSec": 12, "typingEndFrame": typ_end, "sendFrame": typ_end + 6,
             "visibleChars": "min(len, floor((frame - startFrame) * charsPerSec / fps)) for frame >= startFrame"}
    assert phone["sendFrame"] < ps["endFrame"], "phone text does not fit its shot"
    est = [s for s in shots[: len(d["intro"])] if s["shot"] == "EST"]
    cues = {"human_exit_start": est[0]["startFrame"] + 12, "human_at_curb": est[0]["endFrame"] - 24,
            "car_arrive_start": est[1]["startFrame"], "car_stopped": est[1]["startFrame"] + 3 * FPS,
            "door_closed": drive + round(0.8 * FPS), "drive_start": drive, "end": last}

    ver = lambda c: (subprocess.run(c, capture_output=True, text=True).stdout.splitlines() or ["?"])[0]
    from importlib.metadata import version
    tl = {"meta": {"fps": FPS, "totalFrames": total, "totalSeconds": round(total / FPS, 4), "firstFrame": 1, "frameRanges": "[startFrame, endFrame) end exclusive",
                   "dialogue": "dialogue_v2.json", "voices": d["voices"], "pronunciation": d["pronunciation"], "gapBetweenLinesSec": d["gapBetweenLinesSec"],
                   "leadInSec": LEAD, "tailSec": TAIL, "minHoldFrames": MIN_HOLD,
                   "tools": {"kokoro-onnx": version("kokoro-onnx"), "onnxruntime": version("onnxruntime"), "kokoroModel": os.path.basename(KOKORO[0]),
                             "whisper": f"whisper-cli ({os.path.basename(WMODEL)})", "ffmpeg": ver([FFMPEG, "-version"])}},
          "shots": shots, "lines": lines, "emotionKeys": emotion_keys,
          "envelopes": {"claude": "envelope_claude.json", "human": "envelope_human.json", "length": total, "index": "value[i] is frame i+1"},
          "phone": phone, "motionCues": cues,
          "motionCueAssumptions": {"human_exit_start": "0.5 s into the first EST shot", "human_at_curb": "1.0 s before the first EST shot ends",
                                   "car_arrive_start": "start of the pickup EST shot", "car_stopped": "car approach takes 3.0 s",
                                   "door_closed": "0.8 s after the pickup shot ends (happens off screen at the cut)", "drive_start": "first interior frame",
                                   "end": "exclusive end frame of the video"}}
    json.dump(tl, open("timeline.json", "w"), indent=1)
    open("work/build_log.txt", "w").write("\n".join(log) + "\n")
    print(f"timeline.json: {total} frames, {total / FPS:.2f} s, {len(shots)} shots, {len(lines)} lines")


if __name__ == "__main__":
    main()
