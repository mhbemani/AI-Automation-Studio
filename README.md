# AI Educational Media Studio

A small AI-assisted studio that produces short educational videos (software, AI, backend, the internet) and a 3D story format (a human and Claude talking in a car). Human = creative director and approver; Claude = ideas, research, scripts, scene building; n8n = orchestration; Remotion, FFmpeg and Blender = deterministic production; local Kokoro TTS and whisper.cpp for voice and timing. Budget: $0 beyond Claude Pro. Machine: Apple M2, 8 GB RAM, so heavy stages run one at a time.

**Start here:** [docs/V1_MANIFEST.md](docs/V1_MANIFEST.md) (what version 1 contains, where everything is, what is missing). Project rules for every agent: [lab/BRIEF.md](lab/BRIEF.md). Original plans: `Sources/`.

**Run it:** [docs/QUICKSTART.md](docs/QUICKSTART.md) turns a storyboard into a narrated MP4 with a few commands (tested from a fresh clone).

## Demo
A 26-second explainer generated from `lab/integration/storyboard.json` with the quickstart (silent preview below; [watch it with narration](docs/media/demo.mp4)):

![Demo: storyboard to video](docs/media/demo.gif)

## Map
| Folder | What it is |
|---|---|
| `Sources/` | the two founding plan documents (vision; the $0 stack) |
| `docs/` | v1 manifest |
| `lab/results/` | one report per finished experiment (read these first when picking something up) |
| `lab/tools/` | shared tools (`polycount.py`: polygon budgets) |
| `lab/scene-realistic-car/` | the 3D story scene: ring-road city, cameras, lighting, voiced timeline, rebuild scripts |
| `lab/scene-lowpoly-car/` | the earlier stylised sample (scripts, notes, stills, sample video; heavy files in `archive/`) |
| `lab/asset-lineup/` | `lineup.blend`: current Claude, car, phone, human scan side by side, with the old assets for comparison |
| `lab/character-selection/` | rigging the human scan (notes, scripts, emotions) |
| `lab/animation-library/` | the list of animations to prebuild |
| `lab/remotion`, `integration`, `character-integration`, `performance`, `character`, `blender` | the diagram-video pipeline (Remotion scenes driven by JSON, narration, captions, the Facet placeholder presenter) |
| `lab/n8n`, `tts`, `ffmpeg`, `voice-guide` | orchestration (Docker n8n + Postgres), local voices, FFmpeg assembly, voice-cloning guide |
| `archive/` | compressed heavy files of retired scenes (git-ignored, re-extractable) |

## Not in git (by design, see the manifest for where each lives)
`.blend` files, downloaded asset packs, model weights, rendered media, `node_modules`, tokens. Rebuild notes are in each lab's README or notes file.

## Licence and credits
My own code and docs are under the [MIT licence](LICENSE). Third-party software and models keep their own licences; nothing below is redistributed in this repository, it is downloaded or installed separately:

| Component | Used for | Licence |
|---|---|---|
| [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) (weights) and [kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx) | local text-to-speech | Apache-2.0 (weights, per the model card) and MIT (code) |
| [whisper.cpp](https://github.com/ggml-org/whisper.cpp) and the OpenAI Whisper `base.en` weights | word timing | MIT |
| [Remotion](https://www.remotion.dev/) | animation and rendering | Remotion licence: free for individuals and teams of up to 3, a company licence is needed from 4 people |
| Inter font (via `@remotion/google-fonts`) | captions and titles | SIL Open Font License 1.1 |
| [n8n](https://n8n.io/) (Docker) | optional orchestration | Sustainable Use License |
| FFmpeg, Node.js, Python packages, Docker, PostgreSQL | tooling | their own licences, installed separately |
| Blender | the 3D labs | GPL |
| Kenney, Quaternius and Poly Haven packs | 3D scenes | CC0; each lab's `ASSETS.md` lists source and licence |

BlenderKit models used in the realistic 3D scene (two cars and a human scan, all "Royalty Free") are **not** part of this repository and cannot be redistributed. No voice samples or cloned voices are included; cloning a person's voice requires that person's consent.
