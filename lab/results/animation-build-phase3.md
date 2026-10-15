# animation-build, phase 3 (signature moments): report

## 1. Verdict
**Works with caveats.** Everything on the phase 3 list is built and passes its numeric checks: Claude's walk and run, the cushion set, the magic ring, `CLA_magic_cast`, `CAR_self_drive_start`, the reactions, and the transitions. Not verified by me: how the motion *feels* (I cannot watch video in real time; I judged from numbers and frame strips), and anything inside the real scene. The car entry and exit are plausible but **not fitted to the real door and seat geometry**.

## 2. Decisions and changes made during phase 3
- The creator's earlier decisions still apply: the human is a plain silver faceless scan (reactions are body language only), Claude stays cute, arms stretch at most 2.3x.
- The "out of reach" fallback from phase 2 is now real: `plan_reach()` returns `magic` for far targets and `scripts/magic_lib.py: aim_magic()` points the ring at the target.
- The cushion is **hidden by default** (`cus_show = 0`, shrunk to nothing). Every cushion action keys it to 1. Reason: the cushion rests on the ground at Claude's origin, so any ordinary pose showed him standing inside it.
- Root controls added to Claude: `move_x`, `move_y`, `yaw` (so an action can travel and turn, used by `CLA_pickup_arrival`).
- Added beyond the list: `CLA_walk_cycle`, `CLA_run_cycle` (Claude's gait, needed for the pickup and the carry run), `PHN_phone_pocket` (hides the phone at the end of `HUM_phone_to_seat_idle`).

## 3. What was built (all in `lab/animation-library/library_v1.blend`, now 113 actions)
| group | actions |
|---|---|
| Claude locomotion | `CLA_walk_cycle` (24 loop, 0.40 m per cycle), `CLA_run_cycle` (16 loop, 0.571 m per cycle), `CLA_idle_to_walk`, `CLA_walk_to_idle` (10 each), `CLA_pickup_arrival` (72, travels 1.46 m, brakes, turns 90 deg) |
| cushion (`CUS_Cushion`) | `CLA_cushion_jump` (60 loop), `CLA_cushion_run_carry` (16 loop), `CLA_cushion_hold_to_throw` (18), `CLA_cushion_throw_and_jump` (72), `CLA_cushion_sit`, `_sleep`, `_happy_stand` (96 loops), `CLA_stand_to_cushion_sit` (24) |
| magic | `MAG_ring_shoot` (24), `MAG_ring_wrap` (30), `MAG_ring_fade` (18), `CLA_magic_cast` (24), `CAR_self_drive_start` (48) |
| Claude reactions | `CLA_react_proud_puff` (24), `CLA_react_oops` (20), `CLA_react_giggle` (24 loop) |
| human (seated) | `HUM_react_startle` (16), `_laugh` (36), `_impressed` (30), `_shake_head` (18), `HUM_phone_to_seat_idle` (36), `PHN_phone_pocket` (36) |
| car entry and exit | `HUM_stand_to_sit_car` (72), `HUM_sit_to_stand_car` (72) |

New objects: `CUS_Cushion` (collection `CUSHION`), `MAG_Root` with the ring, puffs and sparkle orbit (collection `MAGIC`). New properties: Claude `ctrl` (`leg_len_n`, `leg_rot_n`, `arm_len_L/R`, `hop`, `jump_t`, `move_x/y`, `yaw`, `cus_*`), `CAR_ctrl["dash_glow"]`, the `MAG_Root` properties. Full list and recipes: `lab/animation-library/CONTRACT.md` (phase 3 section). Statuses: `ANIMATION_LIST.md` (23 rows updated).

## 4. Numbers and checks (all pass; JSON files in `lab/animation-build/stills/`)
- **Claude locomotion** (`claude_locomotion_checks.json`): planted-foot drift 0.0 cm (walk) and 0.002 cm (run) in stance, feet never below the ground, 15 / 7 stance frames per leg, loops exact. The blends start exactly at the idle pose and end exactly at walk frame 1 (difference 0.0).
- **Cushion** (`claude_cushion_checks.json`): frame counts as listed (loops have one extra key, the last equals the first: 0.0 difference); in the throw the root ends exactly on the cushion top (root minus cushion z = 0.116 m) and the squash is back at 0.
- **Magic** (`magic_checks.json`): shoot ends 1.2 m out at scale 1, wrap ends at 0.70 of the size, fade ends at 0, sparkle 0; `CLA_magic_cast` arm stretch 1.6x (limit 2.3x), first and last pose equal; `CAR_self_drive_start` ends with the car rolled 1.0 m, `dash_glow` 1, `steer` back to 0. `aim_magic` puts the ring exactly on a test target.
- **Reactions and transitions** (`react_checks.json`): counts as listed; one-shots return to their start (largest difference 0.08 deg/value); `HUM_phone_to_seat_idle` ends 1.0 cm from `HUM_pose_seated`; `HUM_stand_to_sit_car` ends 0.7 cm from it, planted ankles drift 0.01 cm, hip-to-ankle distance at most 0.792 m (leg length 0.818), the pelvis was lowered at most 2 cm to keep legs from overstretching; `CLA_pickup_arrival` travels 1.463 m, ends yaw -90 deg (toward his own right), planted feet move at most 0.37 cm per frame during the braking blend.
- **Library:** 4.25 MB, 104 objects, 113 actions. Triangles: human 4,024, Claude 1,212, car 19,700, phone 476, cushion and magic together 4,922. Draft render of all rigs (960x540, Eevee, 16 samples, headless): 1.0 s, peak memory 498 MB. Contract test on a copy of the realistic scene (appends the five collections and 104 actions in 0.12 s): peak 575 MB, about 0.3 s per 640x360 frame (`stills/contract_test_sheet.jpg`, now with the hugged cushion and the magic ring).
- **Reels** (`lab/animation-build/previews/`): `reel_claude2_locomotion.mp4` (walk, run, blends), `reel_claude3_signature.mp4` (cushion throw/jump/carry/sit, reactions, pickup, magic), `reel_human3_react.mp4` (reactions, phone to seat, car entry and exit). Stills: `claude2_strip_walk.jpg`, `claude2_strip_run.jpg`, `claude3_cushion_sheet2.jpg`, `claude3_react_sheet.jpg`, `claude3_pickup_sheet.jpg`, `magic_cast_sheet.jpg`, `magic_rig_test.jpg`, `car_self_drive_sheet.jpg`, `car_dash_glow.jpg`, `human3_react_sheet.jpg`, `human3_enter_sheet.jpg`.

## 5. How to reproduce (scripts in `lab/animation-build/scripts/`, run via the bridge, in this order)
`04_claude_rig.py` (rerun: new props and root drivers; **it deletes every object owned by Claude, so rerun** `42_cushion_rig.py` and `45_magic_rig.py` after it), `40_claude_locomotion.py`, `43_claude_cushion.py`, `46_magic_actions.py`, `50_claude_react.py`, `51_human_react.py`, `52_human_car_transitions.py`; checks `41_`, `44_`, `47_`, `53_`; reels `render_reel_claude2.py`, `render_reel_m3.py human|claude`; sheets `claude_sheet2.py`, `magic_sheet.py`, `action_sheet.py`; then `13_build_library.py` (headless), `14_contract_test.py`, `15_measure.py`. Do not rerun `05_car_and_phone.py` after the phone bone exists (see phase 2).

## 6. Problems, honest flaws and what I could not verify
- **Motion feel unverified by me** (frame strips and numbers only): the creator has not seen the phase 3 reels yet.
- **Car entry and exit are a plausible choreography, not fitted to the real car**: the door position, the sill height, the legroom and the seat are not checked against the scene. The preview chair block stands in for the seat, and the sheet shows him passing through it. `HUM_sit_to_stand_car` is the entry plan played backwards with a deeper duck; I checked it numerically (it starts on the seated pose) but did not look at it as a sheet. Both need a pass in the real scene (and `CAR_door_open_R` keyed with them).
- **Human reactions are subtle without a face**: startle reads clearly (hands come up); laugh, impressed and shake_head are body and head only (measured: shake about +-10 deg of head turn, nod about 13 deg, laugh head back about 9 deg) and are hard to see at two-shot size.
- **Magic look:** the ring is the creator's original ring material, faint and thin at medium distance; the smoke puffs and the sparkle orbit are barely visible in my frames. The dash accent strip bleaches to white-violet when it glows (I did not tune the colour). Nothing here has been judged by the creator.
- **`CAR_self_drive_start`** has no drive path (the scene's job) and the steering pulse was not compared with a reference.
- **Walk and run gait** are a trot (legs 1+4 against 2+3) of my own design; foot planting is exact, but the body motion is plausible, not tuned against reference.
- **Mesh offset found and fixed (mid-phase):** after a rebuild with `04` I found Claude's eyes, arms and legs sitting about 4 cm lower than his bones (legs 4 cm under the ground) because the script read the hidden lineup copies with stale or animated world matrices. The script now unhides the source chain and evaluates at frame 1. The library, the contract test, the Claude reels, and the phase 3 Claude stills (walk and run strips, cushion, reaction, pickup and magic sheets) were re-rendered after the fix. Claude stills from phases 1 and 2 (for example `claude_cute_v5.jpg`, the emotion sheets and `claude_drive_sheet.jpg`) were made before it and may show the 4 cm offset; the numbers behind all checks are bone-based and unaffected.
- **Props that no active strip keys keep their last value** (documented in the contract): when switching actions on Claude put `cus_show`, `move_*`, `yaw` etc. back to their defaults.
- The old phase 1 and 2 open items remain: `HUM_turn_in_place`, `HUM_seatbelt_on`, thumb symmetry and hoodie poke-through checks, the driver-seat origin against the real scene, `CAR_drive_path`/`CAR_body_sway`/monitor.
- My Blender window was closed by the creator mid-phase; the work file had lost the unsaved phase 3 state, so I rebuilt everything from the scripts (which proves they reproduce it) and saved `anim_work.blend`.

## 7. Recommendation
1. **Creator review** of the three new reels (feel, the ring's visibility, the entry choreography).
2. **Integrate into the realistic scene** (change list in phase 1 section 7 and phase 2 section 7), then place the human and the car door for the entry, key the cushion's landing spot (`cus_dx/dy/dz`) to the real seat, and render a first sample with city, car and both rigs.
3. **Phase 4 (extras)** from the list, plus the open items above.
