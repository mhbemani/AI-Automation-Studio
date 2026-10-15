# animation-build: session report for the project lead

Branch `<task branch>` (worktree `<worktree>`). Phases 1, 2 and 3 of the animation library are done, reported and committed; the creator reviewed phases 1 and 2 and said "good for now" after phase 3. They chose **not** to start the next phase now.

## What was delivered
- **Library:** `lab/animation-library/library_v1.blend` (4.25 MB, 104 objects, **113 actions**, collections HUMAN, CLAUDE, CAR, PHONE, CUSHION, MAGIC; also copied to `lab/animation-library/library_v1.blend`; gitignored). Contract: `lab/animation-library/CONTRACT.md` (phases 1-3). Statuses: last column of `lab/animation-library/ANIMATION_LIST.md`.
- **Phase 1 (foundations):** silver faceless human (Rigify, 1.75 m, creator decision: no face, no colours), Claude armature with `ctrl` properties, car controls, 59 actions. Report `lab/results/animation-build-phase1.md`.
- **Phase 2 (story scenes):** walk/stand with IK and a symmetric stance, phone set built on the creator's own hand-posed pose, chat reveal, seated passenger set (hands fixed by the creator in Blender), Claude driving with stretching arms (max 2.3x, never thinner; arms and legs slide around their own side). Report `lab/results/animation-build-phase2.md`.
- **Phase 3 (signature moments):** Claude walk/run, the cushion rig and 8 cushion actions, the magic ring (`MAG_*`) with `CLA_magic_cast`, `CAR_self_drive_start` (dash glow), Claude and seated-human reactions, `CLA_pickup_arrival`, `HUM_phone_to_seat_idle`, `HUM_stand_to_sit_car` / `HUM_sit_to_stand_car`. Report `lab/results/animation-build-phase3.md`.
- **Previews:** `lab/animation-build/previews/*.mp4` (phase 3: `reel_claude2_locomotion.mp4`, `reel_claude3_signature.mp4`, `reel_human3_react.mp4`). Checks as JSON in `lab/animation-build/stills/*_checks.json`.
- Last commits: `590d1b5`, `8f31805`, `6a9e74f`, `f667674` (phase 3, one per milestone).

## Measurements (library)
Triangles: human 4,024, Claude 1,212, car 19,700, phone 476, cushion + magic 4,922. Draft render of all rigs 1.0 s, peak 498 MB. Contract test on a copy of the realistic scene: appends 5 collections and 104 actions in 0.12 s, peak 575 MB.

## Honest caveats
- I never saw the motion in real time (frame strips and numbers only); the creator has not yet reviewed the phase 3 reels in detail.
- **Car entry/exit (`HUM_stand_to_sit_car`, `_sit_to_stand_car`) are not fitted to the real door and seat geometry.**
- The magic ring is faint; the puffs and sparkles are barely visible; the dash accent strip bleaches when it glows.
- Human reactions are subtle without a face (body language only, by the creator's decision).
- A mid-phase bug (Claude's parts about 4 cm off his bones after a rig rebuild, caused by stale matrices of hidden lineup copies) is fixed in `04_claude_rig.py`; phase 1-2 Claude stills may show the offset, numbers are unaffected.
- The creator closed the Blender window once before it was saved; phase 3 was rebuilt from the scripts (they reproduce it). The Blender window I reopened is closed now; `anim_work.blend` is saved.

## Open items and the two options for the next part
1. **Integrate into the realistic scene** (recommended): change list in the phase 1 and phase 2 reports (section 7), place Claude at the driver-seat origin (car space 0.42, -0.19, 0.81), key the cushion landing spot to the real seat, fit the car entry/exit to the real door, first sample render and footprint measurement.
2. **Phase 4 extras and open items:** `HUM_turn_in_place`, `HUM_seatbelt_on`, `CAR_drive_path`, `CAR_body_sway`, monitor on/off, thumb symmetry, hoodie poke-through checks.

## How to resume
Scripts are idempotent in `lab/animation-build/scripts/`; the rebuild order is in the phase 3 report (section 5): `04_claude_rig.py` then `42_cushion_rig.py` and `45_magic_rig.py` (04 deletes every Claude-owned object), then the action scripts, then `13_build_library.py` (headless). Launch the work file with `lab/animation-build/launch_blender.sh` (bridge); save it (`bpy.ops.wm.save_mainfile()`) after milestones. Do not rerun `05_car_and_phone.py` once the phone bone exists.
