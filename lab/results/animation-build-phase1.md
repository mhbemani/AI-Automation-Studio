# animation-build, phase 1 (foundations): report

## 1. Verdict
**Works with caveats.** The three rigs (silver human, Claude, car) are finished and controllable, 59 actions are built and pass numeric checks, and a contract test shows a scene can use the library. Not verified by me: how the motion *feels* (I cannot watch video in real time) and anything in the real scene's composition. The creator reviewed stills and emotion sheets during the task, not yet the final preview videos' feel.

## 2. Decisions that changed during the task
- Human: Rigify rig fitted to the creator's scan skeleton, scaled to 1.75 m (approved at milestone 0).
- A face (decal mesh, 9 shape keys, eye and jaw bones) and two colour palettes were built and shown (milestone 1-2), then **the creator decided the human stays the plain scan, silver-grey, no face, no colours.** The face scripts are archived in `lab/animation-build/scripts/_archive_face/`. Consequences: `HUM_blink` and `HUM_emoface_*` dropped, human emotions are body language only.
- Claude's emotion presets were retuned for cuteness on the creator's feedback (bigger glints, lower and rounder eyes, blush on or off, no stern tilts), and the eyes, glints and blush got rounded corners.

## 3. What I did (reproduce from scratch)
Work file `lab/animation-build/anim_work.blend` (not in git), opened with `launch_blender.sh` (live bridge). Scripts, in order, all idempotent, run via `python3 lab/animation-build/bridge/bl.py file <script>` from `lab/animation-build`:

| step | script | what |
|---|---|---|
| 0 | `00_setup_work.py` | append copies of the lineup (V3-A Claude, car, phone) and the human rig into `anim_work.blend` (sources snapshotted in `snapshots/`) |
| 1 | `01_human_rig.py` | scale to 1.75 m, close the hood, fit metarig, Rigify generate, move weights to `DEF-*` (chest/neck/foot split), smooth weights, copy the neutral pose |
| 2 | `02_human_materials.py` | one silver-grey material |
| 3 | `04_claude_rig.py` | Claude armature, rigid parts, rounded eyes/glints/blush, `ctrl` properties and drivers |
| 4 | `05_car_and_phone.py` | car renamed `CAR_*`, grounded at the origin, `CAR_ctrl` and drivers; phone at real size, `HUM_PhoneSocket` on `DEF-hand.R` |
| 5 | `06_claude_actions.py`, `12_pose_assets.py` | Claude actions and single-frame pose assets |
| 6 | `08_human_actions.py` | human base poses and actions |
| 7 | `10_car_actions.py` | car actions |
| checks | `07_`, `09_`, `11_*_checks.py`, `stress_human.py`, `stress_claude.py` | numeric checks, stress sheets |
| reels | `render_reel_claude.py`, `render_reel_human.py`, `render_reel_car.py` | preview videos (Eevee draft 960x540, 24 fps) |
| 8 | `13_build_library.py` (headless), `14_contract_test.py`, `15_measure.py` | library file, contract test, measurements |

(`03_*` face scripts: archived, not used.) Commits on branch `<task branch>`, one per milestone.

## 4. Outputs
- **Library:** `lab/animation-library/library_v1.blend` (3.16 MB; also copied to `lab/animation-library/library_v1.blend`). 90 objects, 59 actions with fake users, marked as assets: 33 `CLA_*` (incl. 8 pose assets), 18 `HUM_*`, 8 `CAR_*`. Collections `HUMAN`, `CLAUDE`, `CAR`, `PHONE` (+ hidden `REGEN` with the metarig).
- **Contract:** `lab/animation-library/CONTRACT.md`. **Statuses:** last column of every table in `lab/animation-library/ANIMATION_LIST.md` (15 rows done, 2 partial/dropped groups noted, 52 todo for later phases).
- **Preview videos** (`lab/animation-build/previews/`, 30-120 KB each): `reel_claude_emotions.mp4` (eyes + body + blink), `reel_claude_emoeyes.mp4`, `reel_claude_emobody.mp4`, `reel_claude_basics.mp4` (idle + blinks, talk), `reel_claude_looks.mp4`, `reel_human_emobody.mp4`, `reel_human_basics.mp4`, `reel_human_looks.mp4`, `reel_car.mp4`.
- **Stills** (`lab/animation-build/stills/`): `human_stress_sheet.jpg`, `claude_stress_sheet.jpg`, `claude_cute_v5.jpg` and earlier versions, `claude_emotions_*`, `human_emobody_v4.jpg`, `car_controls_sheet.jpg`, `contract_test_sheet.jpg`, frame strips `*_strip_*.jpg`, `library_draft_render.png`, check files `*_checks.json`, `polycount_library.json`.

## 5. Measurements
- **Triangles** (evaluated, `15_measure.py`): human 4,024 (budget 12K), Claude 1,212 (parts 76-108 each; was 750 before the rounded corners), car 19,700 (body 5,028; seats use subdivision), phone 476.
- **Library file:** 3.16 MB compressed.
- **Draft render of all three rigs** (960x540, Eevee, 16 samples, headless): 1.15 s, peak memory 443 MB. Contract test on a copy of the realistic scene (30 MB file): 0.4 s per 640x360 frame, peak 500-780 MB. Well inside the 2.5 GB footprint.
- **Machine:** Apple M2, 8 GB; Blender 4.5.3 LTS.

## 6. Checks
- **Rig stress, human** (`human_stress_numbers.json`, edge stretch vs rest / foldover faces): neutral 2.4x / 2 faces; head turn +-70 deg unchanged; spine twist 4.1x; elbows 120 deg 4.0x / 66; seated 6.4x / 64; crouch 9.0x / 120; arms raised 8.5x / 55 (66 over-stretched edges, the armpit). Nothing explodes (feet stay at z >= 0, no runaway vertices). A weight-smoothing pass cut the bad edges by about 35 percent.
- **Rig stress, Claude** (`claude_stress_numbers.json`): squash and stretch keep volume at 1.00; eyes, glints and blush stay on the front face at every extreme; arms were found to sink into the wall at large angles, so the slider range is -70..120 deg and the arm lifts away from the wall while it swings.
- **Animation checks** (all pass, `claude_action_checks.json`, `human_action_checks.json`, `car_action_checks.json`): frame counts match the list; loops: first and last key equal (max difference 0.0) and a second cycle equals the first; no value outside its slider range or bone limit (head 75, neck 45, spine 35, shoulders 25 deg); blink = 6 frames with 2 closed frames; **`CLA_talk_pulse`/`talk` follows a test envelope with 0 frames of lag and 0 error**; wheel spin = 360 deg per 12-frame loop (30 deg/frame, below the 36 deg alias limit of the 5 spokes); door and steer values within range.
- **Contract test** (`14_contract_test.py`, copy of `scene.blend` in `lab/animation-build/contract_test/`, original untouched): appended `CLAUDE` + `HUMAN` and 51 actions in 0.04 s, layered idle + `CLA_emoeyes_happy` + `CLA_emobody_happy` + `CLA_blink` + a baked talk pulse on Claude, and seated base + idle + `HUM_emobody_curious` + `HUM_look_at_claude` + `HUM_talk_small` on the human; rendered 5 stills (`contract_test_sheet.jpg`).

## 7. What `animate.py` (realistic scene) would need to change (not done: integration is a later task)
1. **Claude:** replace the object animation of `CHAR_Claude`, `CHAR_Claude_Eye_L/R`, `CHAR_Claude_Arm_L/R` by `RIG_Claude`: map `pitch`->`nod`, `roll`->`lean`, `yaw`->`turn`, `lift`+bounce->`bob`, `stretch`->`-squash`, `eye_sz`->`eye_h_L/R` (asym split), `eye_sx`->`eye_w`, `eye_tilt`->`eye_roll`, `eye_dx/dy`->`look_x/look_y`, the random blink array->`eye_open` keys or `CLA_blink` strips, the speech envelope->`ctrl["talk"]` (`claude_talk.bake_talk`). Car lean/pitch and the scene-level move go on the `root` bone or the armature object. The mirror-aim code that reads Claude's per-frame object transform must read the evaluated rig instead.
2. **Car:** stop keying wheel/steering rotations on the objects (they are driven now); key `CAR_ctrl["distance"]` (= `DIST`, wheel radius is 0.335 here vs 0.357 in the script) and `["steer"]` (= `STEER / 28 deg`, steering ratio comes from the driver: 450 deg wheel per 1.0). The library car has its root at the origin facing -Y, the scene's follow-path setup (`CITY_DrivePath`) must be reapplied to the new `CAR_Exterior`.
3. **Human:** the Rigify FK names (`spine_fk.001-.003`, `neck`, `head`) and the Euler keys of section 5 still fit, but the scene human is replaced by `RIG_Human` + `HUM_pose_seated` + the library actions; the face keys (`Blink`, `MouthOpen`, the 8 emotions) and their keying code are removed; the phone parents to `HUM_PhoneSocket` instead of `DEF-hand.R` directly.
4. **Visibility keys** use `hide_viewport` + `hide_render` on the whole hierarchy: fine for rendering, but do not rely on viewport-evaluated data for hidden rigs.
5. `new_action(...)` in `_anim_util.py` writes object-level slots; library actions are on pose-bone/ctrl-property paths, so a scene mixing both should use the NLA recipe in `CONTRACT.md`.

## 8. Problems, honest flaws and caveats
- **Motion feel is unverified by me.** I judged from numbers and frame strips only. The creator should watch the nine reels and give a verdict on timing, bounce and the amount of idle.
- **Human emotions are subtle** without a face, even after raising the amplitudes: curious, thoughtful, surprised and proud read; happy, excited and amused are the weakest. At two-shot size the human is about 300 px tall.
- **Human deformation** is not clean at extremes: stretch up to 8-9x and 55-120 foldover faces in arms-up, seated and crouch poses. Poke-through of the hoodie against itself was **not measured** (only foldover count). The old `HUM_Contact` geometry-nodes modifier is kept; its effect with the new weights was not measured.
- **Thumb symmetry** (the two thumb pivots differ by a few mm because the creator moved one) was **not checked or fixed.**
- **`HUM_pose_seated`** is an approximation made against a preview seat (hands near the thighs); it was not fitted to the car seat or the steering geometry. `HUM_look_at_*` targets are plausible angles, not computed from the car.
- **Claude:** the blink closes to a thin line (his original eyes squashed); the surprised look is the most "stare-y"; arm raise is limited to -70..120 deg (a stub arm pivoting at the body wall), so "hands to the steering wheel" will need a dedicated solution (phase 2).
- **Car:** body sway, drive path, monitor on/off and self-drive start are not built; the car was not tested with Claude and the human seated in it. Wheel spin above 36 deg/frame aliases (5 spokes).
- **Phone:** attached, but the typed-text objects are all visible by default; no phone actions yet.
- **Library quirks to know:** custom properties must be set as floats (an int turns the property into an int and breaks limits and animation); the human FK controls are Euler XYZ; Claude's `*_L` parts are on -X (lineup naming) while the human's and car's L is +X.
- The contract-test scene copy shows magenta city materials because its CC0 textures are not next to the copy; the stills therefore use a grey test stage. Not a library problem.
- A second Blender window (the creator's `lineup.blend`) was open; I did not touch or close it. My own window (bridge) is still open for the creator.

## 9. Recommendation
1. **Creator review of the reels and the contract**, then fix what feels wrong (amplitudes, idle, door speed).
2. **Phase 2 (story scenes):** the walk cycle and walk-texting first (needs the IK/foot-contact pass, plus checking foot sliding numerically), the phone actions and the chat reveal (`PHN_chat_reveal`), `HUM_phone_*`, then `CLA_drive_hold_wheel` (decide how a stub-armed Claude reaches the wheel) and the `HUM_pass_*` set on the car seat.
3. **Integrate into the realistic scene** following section 7 and re-render a first sample; measure the footprint again with the car, city and both rigs.
4. Smaller follow-ups: fix thumb symmetry, a poke-through check for the hoodie, a seat-fitted seated pose, `CAR_body_sway`, and a decision on whether the human should get any face later (the archived face scripts are ready).
