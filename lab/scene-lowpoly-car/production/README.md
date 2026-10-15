# car-scene production: audio + timeline

Turns `dialogue_v1.json` into voices, a mixed soundtrack and `timeline.json`, the file the animation/render step reads. No Blender here.

## Run everything (one command)
```bash
lab/scene-lowpoly-car/production/run.sh
```
About 50 s on the M2 (Kokoro synthesis is most of it; unchanged lines are cached in `work/lines/*.key`). Steps, one at a time:
`validate.py` (dialogue rules) -> `build.py` (Kokoro TTS, Whisper word times, timeline, envelopes, voice tracks) -> `mix.sh` (ambience, ducking, loudness) -> `check.py` (writes `checks.txt`).
First run creates `.venv` with `kokoro-onnx soundfile`. Uses the models in `lab/tts/models/`, `/opt/homebrew/bin/whisper-cli` + `lab/ffmpeg/models/ggml-base.en.bin`, `/opt/homebrew/bin/ffmpeg`.

| file | in git | what |
|---|---|---|
| `timeline.json` | yes | master timeline (schema below) |
| `envelope_claude.json`, `envelope_human.json` | yes | one mouth/voice value 0..1 per video frame |
| `checks.txt` | yes | output of `check.py` |
| `out/audio_mix.wav` | no | final soundtrack: 48 kHz mono 24-bit, exactly `totalFrames/24` s, -14 LUFS, true peak <= -1.5 dBTP |
| `out/audio_voices_only.wav` | no | the same voices without ambience, same length and loudness target |
| `work/` | no | per-line WAVs, Whisper JSON, `voice_{claude,human,all}.wav` (24 kHz, placed on the timeline), `build_log.txt`, `loudness.txt` |

## Frame convention
24 fps, the first frame is **1**. Frame `f` covers `[(f-1)/24, f/24)` seconds. Every range is `[startFrame, endFrame)`, so the end is **exclusive**: a shot `{startFrame: 1, endFrame: 97}` is frames 1..96 (4.0 s). The next range starts at the previous `endFrame`. The video is frames `1..meta.totalFrames`. In the audio, frame `f` starts at sample `(f-1) * 2000` (48 kHz).

## `timeline.json` schema
```
meta        { fps: 24, totalFrames, totalSeconds, firstFrame: 1, frameRanges, dialogue, voices{claude,human:{engine,voice,speed}},
              pronunciation{word: respelling}, gapBetweenLinesSec, leadInSec: 0.5, tailSec: 1.0, minHoldFrames: 29,
              tools{kokoro-onnx, onnxruntime, kokoroModel, whisper, ffmpeg} }
shots       [ { id "S01".., shot "EST"|"PHONE"|"INT", camera, startFrame, endFrame } ]   ordered, tiles [1, totalFrames+1)
lines       [ { id, speaker "claude"|"human", emotion, text, startFrame, endFrame,
                words: [ { w (script word incl. punctuation), startFrame, endFrame } ] } ]
emotionKeys { claude: [ {frame, emotion, intensity 0..1} ], human: [...] }   sorted by frame, hold until the next key
envelopes   { claude: "envelope_claude.json", human: "envelope_human.json", length: totalFrames, index: "value[i] is frame i+1" }
phone       { shotId, phoneText, startFrame, charsPerSec: 12, typingEndFrame, sendFrame, visibleChars (formula) }
motionCues  { human_exit_start, human_at_curb, car_arrive_start, car_stopped, door_closed, drive_start, end }   frame numbers
motionCueAssumptions { same keys: the rule used }
```

### Rules used to build it
- **Schedule:** intro shots back to back (durations from the dialogue). The first interior shot starts right after the intro; line 1 starts 0.5 s (12 frames) later. Each line clip (Kokoro audio with silence trimmed at -45 dBFS, 30 ms padding kept) starts on a frame boundary. `endFrame` is the first frame after the clip. The next line starts `round(0.35*24) = 8` frames later. The video ends 1.0 s (24 frames) after the last line.
- **Cuts:** Claude speaks -> `CAM_HUMAN_POV`, human speaks -> `CAM_CLAUDE_POV`. A cut lands on the line's `startFrame` (its first word). The gap stays on the previous shot. Two lines in a row from the same speaker stay in one shot. A cut that would leave the previous shot shorter than 29 frames (1.2 s) is moved later to frame 29 of that shot. With this dialogue no cut needed moving or merging: the shortest interior shot is 1.92 s.
- **Words:** Whisper (`-ml 1 -sow`) runs on each line clip. Script words are matched to Whisper tokens greedily (a word may be 1 to 3 tokens, after respelling). A word with no match is spaced evenly between its matched neighbours, and `build.py` logs it.
- **Emotion keys:** the speaker gets the line's emotion at intensity 0.8, 4 frames before `startFrame`. The listener gets a reaction at intensity 0.4, 6 frames after `startFrame`: `amused` for happy/amused/proud lines and `curious` for the others. Both go back to `neutral` (0.0) at the line's `endFrame`. Both start `neutral` at frame 1.
- **Envelopes:** per-frame RMS of the speaker's own placed voice track, then fast attack (0.7 per frame) and slow release (0.18 per frame, about 5 frames). Each speaker's loudest frame is 1.0. Values below 0.03 are 0.
- **Phone:** typing starts 0.5 s into the PHONE shot at 12 chars/s and ends after `ceil(len/12*24)` frames. Send is 6 frames later.
- **Motion cues:** these are assumptions, also written into the file. The human leaves the door 0.5 s into the first EST shot and reaches the curb 1.0 s before it ends. The car arrives from the start of the pickup EST shot and stops 3.0 s later. `door_closed` falls 0.8 s after the pickup shot ends, which is off screen across the cut. `drive_start` is the first interior frame. `end` is the exclusive end.

## Mix (`mix.sh`, FFmpeg synthesis only, nothing downloaded)
The voices are placed sample-accurately by `build.py`. Ambience, all generated by FFmpeg:
- **City:** brown noise, band-limited 60 to 900 Hz, for the whole video.
- **Car arrival:** a pink-noise swell, band-passed around 400 Hz. It starts at `car_arrive_start`, rises for 3 s and fades out over 1 s.
- **Engine:** a 55 Hz sine plus harmonics with slow pitch and level wobble, low-passed at 240 Hz. It starts at `drive_start` with a 1.5 s fade-in.

The ambience bus is ducked by the voices (`sidechaincompress` ratio 3.5). Loudness is set in three steps:
1. Gain to about -12 LUFS, then `alimiter` at -3.1 dBFS. Speech peaks are too high for a purely linear -14 LUFS / -1.5 dBTP.
2. `loudnorm` pass 1 measures.
3. `loudnorm` pass 2 applies the result in **linear** mode, which is only a small turn-down.

`work/loudness.txt` holds the ebur128 verification.
