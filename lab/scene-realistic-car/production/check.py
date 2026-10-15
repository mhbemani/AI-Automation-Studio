"""check.py — asserts the timeline and the mixed audio agree; prints a one-page summary. Exit 1 on any failed check."""
import json, math, re, sys
import soundfile as sf

t = json.load(open("timeline.json"))
d = json.load(open(t["meta"]["dialogue"]))
fps, N = t["meta"]["fps"], t["meta"]["totalFrames"]
end = N + 1                                    # exclusive end frame
shots, lines = t["shots"], t["lines"]
fails = []


def check(ok, msg):
    print(("PASS " if ok else "FAIL ") + msg)
    ok or fails.append(msg)


for f in ("out/audio_mix.wav", "out/audio_voices_only.wav"):
    try:
        i = sf.info(f)
        check(abs(i.frames / i.samplerate - N / fps) <= 1 / fps, f"{f}: {i.frames / i.samplerate:.4f} s vs timeline {N / fps:.4f} s (<= 1 frame)")
    except Exception as e:
        check(False, f"{f}: {e}")
check(shots[0]["startFrame"] == 1 and shots[-1]["endFrame"] == end and all(a["endFrame"] == b["startFrame"] for a, b in zip(shots, shots[1:])),
      f"shots tile [1, {end}) with no gaps or overlaps")
hold = t["meta"]["minHoldFrames"]
short = [s["id"] for s in shots if s["endFrame"] - s["startFrame"] < hold]
check(not short and hold == math.ceil(1.2 * fps), f"every shot holds >= {hold} frames (1.2 s){' ; short: ' + str(short) if short else ''}")
owner = {}
for l in lines:
    inside = [s for s in shots if s["startFrame"] <= l["startFrame"] and l["endFrame"] <= s["endFrame"]]
    owner[l["id"]] = inside[0]["id"] if len(inside) == 1 else None
    check(len(inside) == 1, f"line {l['id']} lies inside exactly one shot ({[s['id'] for s in inside]})")
    w = l["words"]
    check(len(w) == len(l["text"].split()) and all(l["startFrame"] <= x["startFrame"] < x["endFrame"] <= l["endFrame"] for x in w)
          and all(a["startFrame"] <= b["startFrame"] for a, b in zip(w, w[1:])), f"line {l['id']} words ordered and inside the line")
check(all(a["endFrame"] <= b["startFrame"] for a, b in zip(lines, lines[1:])), "lines do not overlap")
for sp in ("claude", "human"):
    e = json.load(open(f"envelope_{sp}.json"))
    check(len(e) == N and all(0 <= x <= 1 for x in e), f"envelope_{sp}.json: {len(e)} values in 0..1 (video {N} frames)")
allowed = set(d["emotionsAllowed"])
bad = [l["emotion"] for l in lines if l["emotion"] not in allowed] + [k["emotion"] for ks in t["emotionKeys"].values() for k in ks if k["emotion"] not in allowed]
check(not bad, f"all emotion names in emotionsAllowed{' ; bad: ' + str(bad) if bad else ''}")
check(all(1 <= k["frame"] <= N for ks in t["emotionKeys"].values() for k in ks), "emotion key frames inside the video")
c = t["motionCues"]
check(c["human_exit_start"] < c["human_at_curb"] < c["car_arrive_start"] < c["car_stopped"] < c["drive_start"] < c["door_closed"] < c["end"] == end, "motion cues in order")
p = t["phone"]
ps = next(s for s in shots if s["id"] == p["shotId"])
check(ps["startFrame"] <= p["startFrame"] < p["typingEndFrame"] < p["sendFrame"] < ps["endFrame"], "phone typing and send inside the phone shot")
try:
    L = open("work/loudness.txt").read()
    for f, i, tp in re.findall(r"(\S+\.wav):\s+I:\s+(-?[\d.]+) LUFS\s+Peak:\s+(-?[\d.]+)", L):
        check(abs(float(i) + 14) <= 0.3 and float(tp) <= -1.0, f"{f}: {i} LUFS (target -14.0 +/- 0.3), true peak {tp} dBTP (<= -1.0)")
except FileNotFoundError:
    check(False, "work/loudness.txt missing (run mix.sh)")

sec = lambda f: (f - 1) / fps
print(f"\n{'line':>4} {'who':6} {'start s':>8} {'end s':>7} {'dur s':>6} {'words':>5} {'wpm':>4}  shot  emotion")
for l in lines:
    dur = (l["endFrame"] - l["startFrame"]) / fps
    print(f"{l['id']:>4} {l['speaker']:6} {sec(l['startFrame']):8.2f} {sec(l['endFrame']):7.2f} {dur:6.2f} {len(l['words']):>5} {len(l['words']) / dur * 60:4.0f}  {owner[l['id']]}   {l['emotion']}")
spoken = sum(l["endFrame"] - l["startFrame"] for l in lines) / fps
print(f"\ntotal: {N} frames = {N / fps:.2f} s ({fps} fps); speech {spoken:.2f} s, {sum(len(l['words']) for l in lines)} words, "
      f"{sum(len(l['words']) for l in lines) / spoken * 60:.0f} wpm while speaking")
print("\ncut list (frames [start, end), seconds):")
for s in shots:
    print(f"  {s['id']} {s['shot']:5} {s['camera']:15} {s['startFrame']:>5}-{s['endFrame']:<5} {sec(s['startFrame']):6.2f}-{sec(s['endFrame']):6.2f}  ({(s['endFrame'] - s['startFrame']) / fps:.2f} s)")
print(f"\n{'ALL CHECKS PASSED' if not fails else str(len(fails)) + ' CHECK(S) FAILED'}")
sys.exit(1 if fails else 0)
