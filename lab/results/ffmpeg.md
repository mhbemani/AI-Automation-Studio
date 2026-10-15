# Lab: ffmpeg — deterministic assembly

## 1. Verdict
**Works with caveats.** Merge, loudnorm, ducking, crossfade, 1080p/vertical export and thumbnail all work. The Homebrew FFmpeg has **no libass or freetype**, so `subtitles`/`drawtext` don't exist. Captions are burned in with Pillow-rendered PNG overlays instead, which works. whisper.cpp is viable for caption generation.

## 2. What I did
Machine: Apple M2, 8 GB RAM, macOS (Darwin 25.6). FFmpeg 9.0.2 (Homebrew, `/opt/homebrew/bin/ffmpeg`) with libx264, VideoToolbox, loudnorm, sidechaincompress and xfade. It lacks libass, freetype, `subtitles` and `drawtext`. Python 3 has Pillow 12.3.

Test media (all in `lab/ffmpeg/in/`):
```bash
say -v Samantha -o voice.aiff "Every time you open a website, ..." && ffmpeg -i voice.aiff -ar 48000 -ac 1 voice.wav
ffmpeg -f lavfi -i testsrc2=s=1920x1080:r=30:d=12 -c:v libx264 -pix_fmt yuv420p clipA.mp4
ffmpeg -f lavfi -i smptebars=s=1920x1080:r=30:d=8  -c:v libx264 -pix_fmt yuv420p clipB.mp4
ffmpeg -f lavfi -i sine=f=220:d=40 -f lavfi -i sine=f=330:d=40 -filter_complex "amix=inputs=2,volume=1.5" -ar 48000 music.wav   # tone "music", no copyright
# captions.srt hand-written, 3 cues
```
Items 1–4, 6 and 7 are all done by the one script `lab/ffmpeg/assemble.sh`:
```bash
./assemble.sh in/clipA.mp4 in/voice.wav in/captions.srt out/final in/music.wav
# -> out/final.mp4 (1080p), out/final_vertical.mp4 (1080x1920), out/final.jpg (thumbnail @4s); music arg optional
```
What it does:
- **Voice:** `loudnorm=I=-14:TP=-1.5:LRA=11`.
- **Music:** `volume=0.25`, then `sidechaincompress` keyed on the voice, then `amix`, then a final loudnorm.
- **Captions:** a Python/Pillow heredoc inside the script renders one transparent PNG per SRT cue. Each is overlaid with `enable='between(t,a,z)'`.
- **Video:** loops or trims to the audio length (`-stream_loop -1 -shortest`).
- **Vertical:** centre crop, with captions re-rendered at 1080 px wide.
- **Encode:** x264 CRF 18, yuv420p, 30 fps, AAC 192k at 48 kHz, `+faststart`.

Crossfade (item 5):
```bash
ffmpeg -i clipA.mp4 -i clipB.mp4 -filter_complex "[0:v][1:v]xfade=transition=fade:duration=1:offset=11[v]" -map "[v]" -c:v libx264 -pix_fmt yuv420p xfade.mp4
```
For audio, the equivalent is `acrossfade=d=1`. I did not test it.

Whisper (the user approved the install and the model download):
```bash
brew install whisper-cpp                                   # 1.9.4, ~2m45s incl. deps (global)
curl -L -o models/ggml-base.en.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin   # 148 MB
whisper-cli -m models/ggml-base.en.bin -f in/voice.wav -osrt -of out/whisper -ml 40 -sow
```

## 3. Output
All under `lab/ffmpeg/`:

| File | Size | Duration | Notes |
|---|---|---|---|
| `out/final.mp4` | 7.5 MB | 8.34 s | 1920x1080, h264, yuv420p, 30 fps, AAC |
| `out/final_vertical.mp4` | 4.2 MB | 8.34 s | 1080x1920 |
| `out/final.jpg` | 155 KB | n/a | Caption visible in thumbnail |
| `out/whisper.srt` | n/a | n/a | Whisper output |

- The crossfade test (12 s + 8 s, 1 s overlap) gave exactly 19.0 s, as expected. I deleted the file; the command is above.
- The big MP4s are partly an artefact of noisy test patterns. Real content will be smaller.

## 4. Measurements
- **Assemble:** `assemble.sh` produced the 1080p and vertical MP4s plus the thumbnail from 8.3 s of media in **9.4 s wall** (24 s user CPU, x264 software encode). That is about 1.1x real time on 8 GB, including music ducking and 3 caption overlays.
- **Crossfade encode:** 6.2 s wall for 19 s of 1080p.
- **Loudness:** the final mix measured **-14.2 LUFS** (EBU R128 integrated), LRA 0.9. Single-pass loudnorm landed within 0.2 LU, which is fine for YouTube.
- **Ducking:** the music bed measured -32.6 dB mean undisturbed and -51.8 dB while the voice talks. That is about 19 dB of reduction with `ratio=8:threshold=0.02`, which is more aggressive than a typical "bed" mix. Try `ratio=3–4` to get a gentler 8–10 dB dip.
- **Whisper base.en on M2:** ~0.95 s total for 8.3 s of audio (encode 324 ms, Metal GPU). The first run took 11 s wall (Metal shader compile and model load). That is about 9x faster than real time.
- **Whisper accuracy:** words were correct on clean TTS speech. Its line breaks follow its own timing, not sentence boundaries, e.g. "...a server," / "the server answers" / "with a page that simple loop powers the". It added no punctuation boundary between "page" and "that", so you must edit or segment the lines.

## 5. Problems & caveats
- **No libass or freetype in the Homebrew build.** `-vf subtitles=...` and `drawtext` fail. Workarounds:
  - (a) PNG overlays via Pillow, as in the script. Static styling only, no word-by-word karaoke, and the PNGs are hard-coded to the SRT cue timing.
  - (b) `brew install ffmpeg` from a tap with libass, or a static build (e.g. evermeet or johnvansickle builds). Not tested here.
  - (c) Render captions in Remotion and use FFmpeg only for audio, concat and encode. This is probably the best fit for the studio.
- **Font:** the script uses `/System/Library/Fonts/Helvetica.ttc` by default (override with `FONT=...`). I have not checked that font's licence for redistributed brand use, so pick an open-licence font (e.g. Inter, OFL) for the brand.
- **Loudnorm is single-pass.** It is dynamic and approximate. For exact targets use the two-pass `measured_I/LRA/TP` approach. It was not needed here, but long content with big dynamics may drift.
- **Video is looped or trimmed to the voice length.** The script does not retime or cross-cut multiple clips. For a multi-clip scene, concat/xfade first, then run the script.
- **Audio crossfade (`acrossfade`) is untested.**
- **Software x264 on 8 GB:** fine for 30–120 s videos. VideoToolbox (`h264_videotoolbox`) exists for speed, but I did not test its quality.
- **Test media is synthetic.** Visual quality of real footage, and a real music bed, are untested.
- **Install footprint:** `brew install whisper-cpp` is global (the user approved it). The model sits in `lab/ffmpeg/models/` (148 MB).
- **Whisper licensing:** whisper.cpp is MIT, and the OpenAI Whisper model weights are MIT.

## 6. Recommendation
- Use FFmpeg as the final assembly step: it is deterministic, fast and free. Wrap `assemble.sh` (or its logic) in an n8n "Execute Command" node.
- Generate captions with whisper.cpp (`base.en`, near-instant on the M2) from the narration audio. Then do a quick human pass on line breaks, or re-segment by sentence, before the SRT goes into the pipeline.
- Prefer Remotion for styled and animated captions. Keep the PNG-overlay path as the plain fallback.
- Next experiments, in order:
  1. Run the script with a real Pexels clip, real TTS voice (Kokoro/Piper) and a genuine CC0 music bed.
  2. Gentler ducking (`ratio=3–4`) and a two-pass loudnorm.
  3. Compare libass via a static FFmpeg build against the PNG approach.
  4. Time `h264_videotoolbox` against x264 at 60–120 s.
