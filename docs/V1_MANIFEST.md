# V1 manifest: the first version of the studio system

Written on 2026-10-13 and updated on 2026-10-14 (animation library added; see section 4b and the revised gaps). This is the content of release 1.0.0. This is a **snapshot of the working set**, not a finished product: it says what exists, where it lives, what was decided, and what is still missing. Read this first when picking the project up.

## Decisions that define v1
- $0 beyond Claude Pro; Apple M2 with 8 GB RAM, so heavy stages run one at a time. Eevee only, 1K textures, footprint target <= 2.5 GB per render.
- Voices: local Kokoro (`af_heart` = Claude, `am_michael` = human in the car scene; `bf_emma` main for the diagram pipeline). Timing: whisper.cpp. No paid TTS.
- The look: game-style / animated-film "realistic-leaning", low poly, not photoreal. The earlier toy low-poly look is kept only as a reference.
- The human is the **rigged scan** "Lowpoly Male Standing" (BlenderKit, Royalty Free). Creator decision of 2026-10-13: it stays a **plain silver-grey faceless scan, no colours, no eyes or mouth**; human emotions are body language only (the face scripts are archived in `lab/animation-build/scripts/_archive_face/`). The from-scratch character and the 66K "Oscar" were rejected and removed.
- Claude (the orange squarish character, "V3-A", cute eyes and blush) has **body and eye emotions only, no mouth**, and now has a small armature with emotion sliders.
- Licences: BlenderKit assets only for the car, parked car and human (the creator's login; the agent never handles credentials); everything else CC0 or built by script. Credits in each scene's `ASSETS.md`.
- Workflow: one agent per task from a written brief; Opus 5.5 for creative or clean-build work, Sonnet 5.5 for simple assembly; no publishing automation until the creator says so; commit after each finished batch.

## What is in v1
### 1. The 3D story scene: `lab/scene-realistic-car/`
A closed ring-road city (about 360 x 216 m, instanced buildings, street furniture, parked cars), a yellow 1970s coupe with a built interior, Claude, the human, a phone with a chat UI, five cameras with 9:16 variants and shot markers, golden-hour lighting, and a voiced timeline (dialogue v2, about 72 s, 14 lines, Kokoro voices, envelopes and emotion keys).
- Working file: `scene.blend` (about 30 MB, **not in git**); rebuild with the scripts in `scripts/` in the order documented in `SCENE_NOTES.md`; the CC0 packs are fetched by `scripts/fetch_assets.py`, the two BlenderKit files must be copied from the creator's BlenderKit cache (see `ASSETS.md`).
- Budgets met (measured with `lab/tools/polycount.py`): about 153K triangles in camera on average, draft frames 0.5-1.3 s, 1080p 2-4 s, footprint 2.1 GB draft / 2.5 GB at 1080p.
- Voice build: `production/run.sh` (Kokoro + Whisper -> `timeline.json`, envelopes, mix). Audio files are in `production/out/` (not in git).
- The scene's human and Claude are still the **older** ones (rigid chunks / the rounded block). They are to be replaced by the lineup assets.
- Reports: `lab/results/realistic-scene.md`, `realistic-scene-diet.md`, `scene-polycount-comparison.md`.

### 2. The current asset set: `lab/asset-lineup/`
`lineup.blend` (about 22 MB, **not in git**, the creator's working file, open in their Blender) holds, at real scale under the same lighting, new and old versions for comparison. New: **Claude V3-A** (with his cushion, a jump loop and a magic ring), the hero **car** (doors, wheels, steering wheel, dash monitor), the **phone** (chat UI, typing), a smoothed **parked car**, the **human scan** (snapshot). Old low-poly Claude, car, phone and human are included as references. Build/refresh scripts and the per-asset table (`asset_table.json`) are in the folder; report `lab/results/asset-lineup.md`.

### 3. The human rig: `lab/character-selection/`
The scan rig worked on step by step with the creator: 49 bones, five-finger welded hands with 30 finger bones, weights, test poses. `NOTES.md` has the done list and the left-to-do list; `EMOTIONS.md` the emotion work. Work file: `character_selection_lab.blend` (4 MB, not in git; a dated snapshot is in `snapshots/`, the live copy is in the agent's worktree `<worktree>/lab/character-selection/`).

### 4. The animation list: `lab/animation-library/ANIMATION_LIST.md`
About 100 animations in 10 groups (seated, walking, phone, talking, emotions, looks, reactions, driving, cushion and magic, transitions) with names (`HUM_`, `CLA_`, `CAR_`, `PHN_`, `MAG_`), shots, loop or one-shot, frames at 24 fps, priority and what each drives, plus a build order (foundations first).

### 4b. The animation library (added on 2026-10-14): `lab/animation-library/` and `lab/animation-build/`
`library_v1.blend` (4.25 MB, **not in git**): the finished rigs with controls (silver Rigify human at 1.75 m, Claude with armature and `ctrl` custom properties driving eyes, glints, blush, arms, squash, lean and talk, the hero car with wheel/steering/door controls, the phone with its hand socket, Claude's cushion and the magic ring) plus **113 actions** (fake users, marked as assets). `CONTRACT.md` documents every rig's bones, properties, shape keys and how to play actions; `ANIMATION_LIST.md` has a status column (done / partial / todo). 16 labelled preview reels are in `lab/animation-build/previews/` (small mp4s, git-ignored): watch these to judge motion. The whole work file `anim_work.blend` can be rebuilt from `lab/animation-build/scripts/` in the order at the top of `lab/results/animation-build-report.md` (phases 1 and 2 of that order were not re-run from nothing; phase 3 was). Per-phase reports: `lab/results/animation-build-phase1.md`, `-phase2.md`, `-phase3.md`.
Numbers: human 4,024 tris, Claude 1,212, car 19,700, phone 476, cushion + magic 4,922; a draft render of all rigs takes 1.0 s at 498 MB peak. Done: foundations, walking, phone, seated set, Claude driving, Claude walk/run, cushion set, magic ring and cast, reactions, pickup arrival, phone-to-seat. Partial: `HUM_stand_to_sit_car` / `HUM_sit_to_stand_car` (plausible choreography, not fitted to the real door and seat). Not built: `HUM_turn_in_place`, `HUM_seatbelt_on`, `CAR_drive_path`, `CAR_body_sway`, monitor on/off, other phase 4 extras.

### 5. The earlier stylised sample: `lab/scene-lowpoly-car/`
Scripts, notes, stills and the first sample video (`production/out/sample_draft.mp4`, 55.6 s, plus a 10 s 1080p excerpt). Heavy files (scene, assets, backups, audio) are in `archive/scene-lowpoly-car-heavy.tar.gz`; extract it into the folder to run the scripts again. Measured render cost: draft 49 min for the full video, final estimated 2.7 h.

### 6. The diagram-video pipeline (the other half of the studio)
`lab/remotion` (JSON-driven scenes), `lab/integration` and `lab/character-integration` (storyboard to MP4 through a host runner and n8n), `lab/performance` (scripted presenter synced to diagrams, frame-exact compositing), `lab/character` (the Facet placeholder presenter), `lab/n8n` (Docker n8n + Postgres), `lab/tts`, `lab/ffmpeg`, `lab/voice-guide` (voice-cloning guide). All with reports in `lab/results/`. Works end to end for a draft in about 6 minutes; not used for the 3D scene.

### 7. Shared tools
`lab/tools/polycount.py` (polygon budgets by asset and in camera), the live Blender bridge (`bridge/studio_bridge.py` + `bl.py` in each scene lab: lets an agent run code and take snapshots in the creator's open Blender; localhost only, token, every call one undo step).

## Known gaps (the backlog after 1.0.0)
1. **Scene integration:** the animated rigs and the lineup assets are not in the realistic scene yet. The scene still has the older Claude, car parts and human; the change list is in `lab/results/animation-build-phase1.md` and `-phase2.md` (section 7): replace the old object animation by the rigs and actions, key the car controls, fit Claude to the driver-seat origin, key the cushion landing, fit the car entry and exit to the real door and seat, phone visibility and pocketing.
2. **Not built yet:** the items listed in 4b, plus the rest of the list's phase 4 extras (not read in detail yet).
3. **Never verified:** motion in real time (the agents only saw numbers and frame strips), audio quality, 9:16 with the new animation, a full render of the new scene, hoodie poke-through and thumb symmetry on the human.
4. **Looks to decide:** the magic ring is faint and thin at medium distance (brighter and thicker?), human reactions are subtle without a face, the car entry idea (step in sideways, turn, sit) needs the creator's OK before it is fitted.
5. Licences to re-check before publishing: BlenderKit Royalty Free terms for the car, parked car and human; Remotion's company licence if the team grows to four or more; Kokoro's training-data note; n8n's Sustainable Use licence.

## Next step
Integrate the library into the realistic scene (recommended), render a first sample of the new scene and measure the footprint with city, car and both rigs; then phase 4 extras. Decisions are the creator's: integration first or extras first, the ring's look, the car entry idea.
