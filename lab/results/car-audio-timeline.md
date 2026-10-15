# Lab "car-audio" — voices, word timing, shot timeline and mix for the car scene

## 1. Verdict
**Works, with caveats.** One command (`lab/scene-lowpoly-car/production/run.sh`, about 50 s) does all of this:
- synthesises the 11 lines with Kokoro;
- times every word with Whisper;
- writes `timeline.json` (24 fps, 1335 frames = 55.62 s, 14 shots), plus the two per-frame envelopes;
- mixes the voices over FFmpeg-generated ambience at **-13.9 LUFS / -1.7 dBTP**;
- passes all 35 checks in `check.py`.

**I cannot hear audio.** Nothing here says the voices, the pronunciation or the ambience sound good; the creator has to listen. Whisper did not cleanly hear 3 of the 125 words (section 5).

## 2. What I did (reproduce)
```bash
cd lab/scene-lowpoly-car/production
./run.sh          # creates .venv (pip install kokoro-onnx soundfile) on first run, then validate -> build -> mix -> check
```
- The only installs were `kokoro-onnx 0.4.7` and `soundfile 0.14.0` (with their dependencies, onnxruntime 1.30, numpy 2.5.3), into the git-ignored `.venv`. Nothing was downloaded besides these.
- Models are referenced from `lab/tts/models/` and `lab/ffmpeg/models/`, not copied.

| script | does |
|---|---|
| `validate.py` | Dialogue rules: speakers, emotions, non-empty text, intro shots, exactly one `phoneText`. Has a built-in self-test with 4 injected faults. |
| `build.py` | 1. Synthesises each line with Kokoro, using `bf_emma` / `am_michael` at speed 0.95 (both verified to exist in `voices-v1.0.bin`) and the respelling map (whole words). Trims silence; caches by text+voice+speed.<br>2. Runs Whisper on each line and matches the words.<br>3. Writes `timeline.json`, `envelope_*.json` and the placed voice tracks. |
| `mix.sh` | Ambience synthesis, sidechain ducking, gain + limiter, two-pass loudnorm, ebur128 verification. |
| `check.py` | The checks from the spec plus a few more (words inside lines, cue order, phone inside its shot, loudness). Prints the summary to `checks.txt`. |

All rules and the full `timeline.json` schema are in `lab/scene-lowpoly-car/production/README.md`.

**Gotcha fixed:** Kokoro crashed with `Error processing file '<runner>/.../phontab'`. espeak-ng keeps its data path in a fixed buffer of about 160 characters, and this worktree's `.venv` path is longer, so it gets truncated. The old `lab/tts` venv had a short path. `build.py` copies the 19 MB espeak data to `work/espeak-ng-data`, a 131-character path, and passes that path. It is marked `ponytail:` in the code. If the checkout path gets longer, set `ESPEAK_DATA` to a shorter directory.

## 3. Output
| file | in git | size / length |
|---|---|---|
| `production/timeline.json` | yes | 1335 frames, 14 shots, 11 lines, 125 words |
| `production/envelope_claude.json`, `envelope_human.json` | yes | 1335 values each |
| `production/checks.txt` | yes | check output and summary |
| `out/audio_mix.wav` | no | 8.0 MB, 55.625 s, 48 kHz mono 24-bit |
| `out/audio_voices_only.wav` | no | 8.0 MB, 55.625 s |

The two WAVs are copied to `lab/scene-lowpoly-car/production/out/` (base checkout) and are also in the worktree at `<worktree>/lab/scene-lowpoly-car/production/out/`.

### Schedule (from `checks.txt`)
| line | who | start s | end s | dur s | words | wpm | shot | emotion |
|---|---|---|---|---|---|---|---|---|
| 1 | claude | 12.00 | 13.38 | 1.38 | 4 | 175 | S04 | happy |
| 2 | human | 13.71 | 19.17 | 5.46 | 14 | 154 | S05 | curious |
| 3 | claude | 19.50 | 24.62 | 5.12 | 17 | 199 | S06 | excited |
| 4 | human | 24.96 | 26.92 | 1.96 | 6 | 184 | S07 | surprised |
| 5 | claude | 27.25 | 33.62 | 6.38 | 18 | 169 | S08 | thoughtful |
| 6 | human | 33.96 | 35.58 | 1.62 | 7 | 258 | S09 | curious |
| 7 | claude | 35.92 | 42.83 | 6.92 | 24 | 208 | S10 | proud |
| 8 | human | 43.17 | 45.25 | 2.08 | 8 | 230 | S11 | curious |
| 9 | claude | 45.58 | 49.17 | 3.58 | 12 | 201 | S12 | happy |
| 10 | human | 49.50 | 51.08 | 1.58 | 4 | 152 | S13 | amused |
| 11 | claude | 51.42 | 54.62 | 3.21 | 11 | 206 | S14 | happy |

- Speech: 39.3 s, 191 wpm while speaking. That is brisk; lines 6 and 8 are at 230 to 258 wpm.
- Cuts: the intro is S01 EST 0 to 4.0 s, S02 PHONE 4.0 to 7.5 s, S03 EST 7.5 to 11.5 s. Then 11 interior shots alternate, starting with S04 `CAM_HUMAN_POV` at 11.50 s (the 0.5 s lead-in, then line 1).
- The shortest interior shot is S13 at 1.92 s. No cut needed delaying and no lines were merged, because every line is longer than 1.2 s and the speakers strictly alternate. The code handles both cases and logs them.
- Motion cues (frames):

  | cue | frame |
  |---|---|
  | human_exit_start | 13 |
  | human_at_curb | 73 |
  | car_arrive_start | 181 |
  | car_stopped | 253 |
  | drive_start | 277 |
  | door_closed | 296 |
  | end | 1336 (exclusive) |

  The car approach is assumed to take 3 s. `door_closed` happens off screen, after the cut to the interior.
- Phone: typing runs from frame 109 to 157 (24 characters at 12 chars/s), send at frame 163, inside the PHONE shot (frames 97 to 181).

## 4. Measurements
- Machine: Apple M2, 8 GB.
- Full `run.sh` from an empty TTS cache: 49 s wall clock, 68 s CPU. Kokoro plus 11 Whisper runs are about 44 s of that; the mix is about 6 s. Steps run strictly one after another, and no background processes are left. I did not measure peak RAM for the full run.

**Loudness** (`work/loudness.txt`, ebur128 with true peak):

| file | integrated | true peak | loudnorm pass 2 |
|---|---|---|---|
| audio_mix.wav | -13.9 LUFS | -1.7 dBTP | linear |
| audio_voices_only.wav | -13.9 LUFS | -1.7 dBTP | linear |

Plain two-pass loudnorm only reached -15.2 LUFS, because speech peaks limited the gain. The fix is a gain stage to about -12 LUFS plus `alimiter` at -3.1 dBFS before the two passes, which then stay linear.

**Ambience levels** (LUFS of segments of the mix):

| segment | level |
|---|---|
| city noise only (0.5 to 7 s) | -43.8 |
| car-arrival swell (9.5 to 11.5 s) | -39.4 |
| engine + city, no speech, tail | -33.9 |
| speech, line 3 | -13.1 |

So the ambience sits 20 to 30 LU under the voices. During speech the sidechain (ratio 3.5) pushes it down further.

## 5. Problems and what to listen for
Whisper (base.en) transcription versus the script:
- **Line 1, "Hop in."**: Whisper heard "hopins". Kokoro may slur "Hop in" into one word, or add an s. Both word times are interpolated.
- **Line 11, "see them move"**: Whisper heard "see the move". That could be Kokoro dropping the m, or just Whisper. The time for "them" is interpolated.

All other 122 words matched.

Words most at risk and the respellings applied:

| word | line | respelling |
|---|---|---|
| Login | 2 | **"log in"**. Whisper heard "log in", so the word timing matched. Listen for stress: it should sound like the noun "LOG-in", not the verb. |
| API | — | `API -> "A P I"` is in the map, but no line contains "API", so it is not used. |
| hash | 5 | none |
| token | 7 | none |
| encrypted | 5 | none |

Whisper heard hash, token and encrypted correctly, which suggests they are intelligible, but that is not proof.

Also listen for:
- "Ooh" (line 3) and "Huh." (line 10): Kokoro interjections can come out as spelled sounds.
- The emotions: Kokoro has no emotion control. The `emotion` fields only drive the animation keys, so every line is read in the voice's neutral style.
- `bf_emma` uses the en-gb phonemiser and `am_michael` en-us. That is intended, but it mixes accents.
- Whether the engine hum (55 Hz) is audible at all on laptop speakers, and whether the brown noise sounds like a city or like hiss.

Other caveats:
- Word end frames come from Whisper's token ends, which are approximate (about ±1 to 2 frames). Line start and end come from the trimmed audio itself, so the cuts are exact.
- Emotion reactions are a fixed rule (`amused` or `curious`), not authored.

## 6. Recommendation
Next steps, in order:
1. **The creator listens** to `out/audio_mix.wav`, especially lines 1, 2, 3, 10 and 11 and the ambience balance. Fix pronunciation by adding entries to `pronunciation` in `dialogue_v1.json` (for example `"Hop in": "hop, in"`) and re-run `run.sh`; only the changed lines are re-synthesised.
2. If the pace feels rushed (lines 6 and 8 are about 250 wpm), lower the human's `speed` to 0.9.
3. The animation step can consume `timeline.json` and the envelopes as they are. Mouth = envelope, keys = `emotionKeys`, cameras = `shots`, intro motion = `motionCues`.
