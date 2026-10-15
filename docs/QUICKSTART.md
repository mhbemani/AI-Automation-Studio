# Quickstart: storyboard to video

This turns `lab/integration/storyboard.json` into a narrated 1080p video and a 9:16 vertical video, with no paid services, running on your own machine: Kokoro (voice) -> Whisper (word timing) -> Remotion (animation) -> FFmpeg (audio and encode).

Tested on 2026-10-15 from a fresh clone on macOS (Apple M2, 8 GB), Python 3.14.5, Node 24.16, FFmpeg 9.0.2, whisper.cpp from Homebrew. Linux may work but is untested; Windows is untested.

## 1. Install the tools

```bash
brew install node ffmpeg whisper-cpp     # provides node, ffmpeg and the whisper-cli command
python3 --version                        # any recent Python 3
```

## 2. Clone, keeping the path short

```bash
git clone <repo-url> studio
cd studio
```

Keep the project folder path short (for example `~/studio`). The speech engine (espeak) cuts off very long data paths: with a 189-character path it failed with `Error processing file '.../phontab': No such file or directory`, with a path of about 95 characters it worked.

## 3. Download the voice and timing models (about 256 MB)

```bash
cd lab/tts
python3 -m venv .venv
.venv/bin/pip install -r requirements.freeze.txt
mkdir -p models && cd models
curl -fLO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx   # 88 MB
curl -fLO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin          # 27 MB
cd ../..                                  # back to lab/
mkdir -p ffmpeg/models
curl -fL -o ffmpeg/models/ggml-base.en.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin   # 141 MB
```

## 4. Install the animation engine

```bash
cd integration/remotion
npm ci
cd ..                                     # now in lab/integration
```

The first render may also download a headless Chrome and the Inter font, so keep internet on for it.

## 5. Make the video

Run from `lab/integration`:

```bash
mkdir -p work/1 && cp storyboard.json work/1/
../tts/.venv/bin/python stages/tts.py 1   # narration with Kokoro
node stages/align.mjs 1                   # Whisper word times -> work/1/project.json
node stages/render.mjs 1                  # Remotion: silent 16:9 and 9:16 video
node stages/assemble.mjs 1                # add the voice, normalise loudness, write the MP4s
ls out/1
```

Result of the test run (26.3 s each): `out/1/final.mp4` (1920x1080, 2.4 MB) and `out/1/final_vertical.mp4` (1080x1920, 2.4 MB). On an M2 the stages take roughly: voice 20 s, timing 2 s, render 40-50 s, assemble 1 s (see `lab/results/integration.md` for measurements). Run the stages one at a time; they are heavy for an 8 GB machine.

## 6. Make your own video

Copy `storyboard.json`, edit it, and use a new id:

```bash
mkdir -p work/2 && cp my-storyboard.json work/2/storyboard.json
# then run the four stage commands from step 5 with 2 instead of 1
```

- `voice.main`: a Kokoro voice, for example `bf_emma` (British) or `af_heart`.
- `scenes`: each has a `narration` and a `type`:
  - `typography`: add `onScreen`, a list of lines that appear on screen.
  - `flow`: add `nodes` (names of boxes) and `packets` (`from`, `to`, `label`), which animate between the boxes.
- `pronunciation`: optional word -> respelling map for words the voice gets wrong.

The storyboard is validated before anything runs, so mistakes give a readable message (for example `packet[0].to "Cache" is not a node`).

## 7. Automation with n8n (optional)

`lab/integration/n8n/` has a Docker Compose file and a workflow that run the same four stages from a webhook, track status in Postgres and wait for a manual approval. The steps are in `lab/results/integration.md`. They were tested by the author but not re-run in this fresh-clone test.

## Known limits

- Voice quality and pronunciation have not been checked by ear; the Whisper step matched 78 of 78 words in the test run.
- The first scene type is simple (typography and a three-box flow diagram); the pipeline has no music bed and no publishing step.
- The 3D scenes (Blender) are not part of this quickstart.
