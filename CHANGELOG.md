# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html). How a release is cut: [docs/RELEASING.md](docs/RELEASING.md).

## [Unreleased]

## [1.0.0] - 2026-10-15

First release: the working set of the studio system, as described in [docs/V1_MANIFEST.md](docs/V1_MANIFEST.md).

### Added
- **Diagram-video pipeline.** Remotion scenes driven by JSON (flow diagrams, kinetic typography, word-synced captions, transitions); local Kokoro narration with whisper.cpp word timing; FFmpeg assembly with single-pass loudness normalisation to -14 LUFS (measured about -15 LUFS); a host-side runner and an n8n + PostgreSQL workflow with status tracking, failure notes and an approval gate. A storyboard becomes a narrated 1080p and a 9:16 video; a draft run takes about 6 minutes on an Apple M2 with 8 GB.
- **Scripted presenter.** A low-poly placeholder presenter whose gestures, gaze and blinks are driven by the narration, the on-screen text and the diagram; frame-exact compositing that removed character flicker.
- **3D story scene** (`lab/scene-realistic-car`). A closed ring-road city, a yellow coupe with an interior, Claude, a human, a phone with a chat screen, five cameras with 9:16 variants and shot markers, golden-hour lighting, a voiced timeline (14 lines, about 72 seconds), rebuild scripts, and measured render costs (draft 0.5-1.3 s per frame, 1080p 2-4 s, 2.1-2.5 GB footprint).
- **Asset lineup** (`lab/asset-lineup`). Scripts that build one file with the new and the old Claude, car, phone and human side by side, with comparison cameras and a refresh script.
- **Animation library** (`lab/animation-library`, `lab/animation-build`). Rigs with controls for the human, Claude, the car, the phone, Claude's cushion and the magic ring; 113 actions; `CONTRACT.md` describing every rig; the animation list with a status column; rebuild scripts and numeric checks.
- **Tools.** `lab/tools/polycount.py` (polygon budgets by asset and in camera) and a localhost Blender bridge for running scripts and snapshots in an open Blender session.
- **Quickstart and licence.** MIT licence, `docs/QUICKSTART.md` (storyboard to MP4, tested from a fresh clone) and a licence and credits table in the README.
- **Repository safety.** `docs/GIT_RULES.md`, a pre-commit hook in `.githooks/` that blocks large files, 3D/audio/archive files, secrets and personal paths, and `docs/RELEASING.md` with the release process and the asset rules.
- **Docs.** Project manifest, lab briefs, one report per experiment under `lab/results/`, and the two founding plan documents under `Sources/`.

### Known limitations
- The `.blend` files are not part of the repository or of any release zip: they contain BlenderKit (Royalty Free) models, see `docs/RELEASING.md`.
- The animation library is not yet integrated into the 3D scene, and no motion has been reviewed in real time beyond the preview reels.
