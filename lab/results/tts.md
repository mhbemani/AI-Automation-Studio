# Lab "tts" — local TTS (Kokoro, Piper)

## 1. Verdict
**Works with caveats.** Kokoro (int8 ONNX) runs locally and is licence-clean for commercial use, but is slow on this 8 GB M2 (RTF ~0.8–0.95, i.e. barely faster than real time). Piper is ~20x faster but its only voice I tried (lessac) is **not licensed for commercial use**. I could not listen to the audio, so the quality assessment below is unverified. The creator must listen.

## 2. What I did (reproduce)
```bash
cd lab/tts
python3 -m venv .venv && .venv/bin/pip install kokoro-onnx soundfile piper-tts   # Python 3.14.5, worked
mkdir models && cd models
curl -fLO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx   # 92 MB
curl -fLO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin          # 28 MB
B=https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium
curl -fLO $B/en_US-lessac-medium.onnx; curl -fLO $B/en_US-lessac-medium.onnx.json                                  # 63 MB
cd .. && .venv/bin/python tts.py kokoro && .venv/bin/python tts.py piper
```
Downloads were approved (int8 only, ~183 MB total). Curl was truncated twice on first try; use `-C -` to resume. espeak-ng needs no brew install (bundled via `espeakng-loader`).
`tts.py` = 4 sentences (46 words "what happens when you click Login" + 14-word jargon sentence: "The API returns a JWT over HTTPS, and the user record lives in PostgreSQL."), synthesised sentence by sentence.

## 3. Output (`lab/tts/out/`)
| file | size | duration |
|---|---|---|
| kokoro_af_heart.wav | 1.0 MB | 20.97 s |
| kokoro_af_bella.wav | 1.1 MB | 21.99 s |
| kokoro_am_michael.wav | 1.1 MB | 23.51 s |
| kokoro_bf_emma.wav | 0.9 MB | 19.65 s |
| piper_lessac.wav | 0.9 MB | 19.69 s |

`timings_*.json` hold generation time and **sentence-level start/end timestamps** per voice.

## 4. Measurements
Machine: Apple M2, 8 GB RAM, arm64, macOS (Darwin 25.6). CPU-only ONNX Runtime 1.30.

| voice | gen time | audio | RTF (gen/audio) |
|---|---|---|---|
| kokoro af_heart | 16.9 s | 21.0 s | 0.80 |
| kokoro af_bella | 19.4 s | 22.0 s | 0.88 |
| kokoro am_michael | 21.3 s | 23.5 s | 0.91 |
| kokoro bf_emma | 18.8 s | 19.7 s | 0.96 |
| piper lessac-medium | 0.8 s | 19.7 s | 0.04 |

(Warm model, excluding load.) A 90 s narration would take ~75 s with Kokoro int8 — fine for batch, not interactive. I didn't test the fp32 model or CoreML; RTF may differ. Pace: ~60 words in ~20 s ≈ 180 wpm incl. pauses, brisk but plausible for explainers (Kokoro `speed` param can slow it).

**Timestamps:** neither kokoro-onnx 0.4.7 nor Piper API gives word-level timings. I got sentence-level by timing each synthesised sentence and accumulating (exact, since I concatenate). For word-level captions/animation sync: run Whisper-style forced alignment (e.g. `whisper.cpp` / `faster-whisper` word_timestamps, or `stable-ts`) over the WAV. Untested here.

## 5. Problems & caveats
**Licences (commercial YouTube use):**
- kokoro-onnx code: MIT (verified from installed LICENSE).
- Kokoro-82M weights (hexgrad): Apache-2.0 per the HF model card; voices have no separate stated restriction (all 54 under same card). Card says training used permissive/public-domain audio **plus synthetic audio from closed commercial TTS** — a low but non-zero provenance risk; not a licence restriction. Keep a credits/licence note. I did not independently verify each voice file; the four I used (af_heart, af_bella, am_michael, bf_emma) are part of that same release.
- espeak-ng (phonemizer, bundled): GPL-3.0. Affects distributing software that bundles it, not the generated audio; fine for internal use.
- Piper engine: current `piper-tts` 1.8.0 is GPL-3.0-or-later (same caveat: code only, not output).
- **Piper voice en_US-lessac-medium: NOT OK for commercial use.** Model card points to the Lessac Blizzard 2013 licence, which (fetched) excludes commercial use incl. synthetic voices trained on it. Don't use it for monetised videos. Other Piper voices have different datasets/licences; check each model card before use.

**Quality:** I can't hear audio in this environment, so I make no claim about naturalness, robotic-ness, or whether JWT/PostgreSQL/HTTPS are pronounced right. General prior (unverified here): Kokoro is widely regarded as the most natural free local TTS, good prosody, occasional odd stress on acronyms; Piper lessac is clearer-but-flatter/more robotic. Jargon likely needs respelling ("jay-double-you-tee", "post-gress-Q-L") or phoneme overrides — test by ear.

**Vs. creator's own voice:** own recording will be more engaging, brandable, no licence/provenance doubt, and handles jargon correctly; costs recording time, needs quiet room + re-takes for script edits. TTS wins on speed of iteration, consistency, and re-rendering after script changes (zero marginal effort). Reasonable hybrid: TTS for drafts/timing, own voice for finals if TTS sounds flat.

## 6. Recommendation
Use Kokoro (af_heart or similar) as the default narration engine for drafts and possibly finals; skip Piper lessac for commercial work. Next experiments, in order: (1) creator listens to the 5 WAVs (incl. jargon sentence) and rates them; (2) Whisper word-timestamp alignment on `kokoro_af_heart.wav` to confirm caption sync; (3) try fp32 model / CoreML provider for speed/quality; (4) test a pronunciation-override approach for jargon.
