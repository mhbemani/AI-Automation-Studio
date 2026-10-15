# animation-build, phase 2 (story scenes): report

## 1. Verdict
**Works with caveats.** The story-scene animations of the list's step 2 are built and pass their numeric checks: walking and standing, the phone set on the creator's own pose, the chat reveal, the seated passenger set, and Claude driving with stretching arms. The creator reviewed stills, the walk and the phone videos during the task and approved them "for now". Not verified by me: how the motion feels in real time, and anything inside the real scene (no scene integration yet).

## 2. Decisions and changes made with the creator during phase 2
- **Claude's reach (decision):** a stretch between "cartoon stretch" and "lean in": arms get longer but never thinner, at most **2.3x** their length. Beyond that Claude turns the body and uses one hand, or uses magic (phase 3). Added later: **each hand can slide around its own side wall and each leg around the underside** (properties `arm_y/z_*`, `leg_x/y_*`).
- **The walk looked crooked:** the scan's stance is not symmetric (hip centre x = 0.042 m; the right ankle sits 7 cm behind its hip and the right foot toes out 30 degrees against 6 for the left). Walking and standing now use a symmetric stance (ankles 3 cm outside the hips, both feet 6 degrees toe-out); measured 0.119 m / 0.120 m from the centre line and 6.0 / 6.0 degrees.
- **The phone hold was wrong, so the creator posed it by hand in Blender** (right wrist, every finger joint, the phone, head, arm). I read the pose from the open session and rebuilt every phone action around it; it is stored as `HUM_pose_stand_phone` and in `lab/animation-build/scripts/phone_hold_pose.json`. For that I added the bone `phone_hold.R`, which carries the phone, and switched the phone arm from IK to FK.
- The "phone jumps larger" the creator saw in the raise: the phone's scale never changes (1.0 in every frame of every action); it is the phone turning its face toward the camera while it is lifted (apparent area up to 2x). I staggered the hand 3 frames ahead of the arm, which lowered the worst case a little (area ratio 1.47 to 1.35 over four camera angles), but it cannot be removed completely, only moved around.

- **The seated hands looked wrong, so the creator fixed them by hand in Blender** (both arms, wrists and every finger joint on the seat). I read that pose (`scripts/seated_hands_pose.json`) and rebuilt all seated actions and `HUM_pose_seated` on it; the earlier solver-made hands and the extra finger curl were dropped.

## 3. What was built (all in `lab/animation-library/library_v1.blend`, now 84 actions)
| group | actions |
|---|---|
| standing and walking | `HUM_stand_idle` (96 loop), `HUM_walk_cycle` (24 loop, in place, 1.2 m per cycle), `HUM_stand_to_walk` and `HUM_walk_to_stand` (12), `HUM_stop_from_walk` (18), `HUM_walk_out_building` (72, root motion) |
| phone | `HUM_pose_stand_phone`, `HUM_phone_raise` (20), `HUM_phone_hold_read` (96 loop), `HUM_phone_type` (48 loop), `HUM_phone_lower_pocket` (30), `HUM_phone_show_claude` (24), `HUM_walk_texting` (24 loop), `PHN_chat_reveal` (120), `PHN_screen_glow` (12) |
| seated passenger | `HUM_pass_hands_lap` (96 loop), `HUM_pass_turn_to_claude` (24), `HUM_pass_look_out_window` (120 loop), `HUM_pass_lean_forward` (20), `HUM_talk_hand_gesture_a` (36 loop) |
| Claude driving | `CLA_drive_hold_wheel` (96 loop), `CLA_drive_steer_left/right` (24), `CLA_drive_hands_off` (18), `CLA_talk_arm_wiggle` (36 loop) |

Rig additions: Claude's reach and slide controls, aim bones that can follow the car's wheel grips; the car gets `CAR_WheelGripPivot` and `CAR_WheelGrip_L/R`; the phone gets `phone_visible`, `chat_*` and `screen_glow` properties. `CONTRACT.md` and the status column of `ANIMATION_LIST.md` are updated.

## 4. Numbers and checks (all pass; JSON files in `lab/animation-build/stills/`)
- **Locomotion** (`locomotion_checks.json`): foot drift while a foot is planted 0.008 cm (both feet, in place) and 0.007 cm (walk out of the building, with root motion); ankles never below 0.076 m (the flat-foot height); leg length 0.68-0.81 m (rest 0.82, no overstretch); loop exact; the blends match walk frame 1 exactly (0.0 difference).
- **Phone** (`phone_checks.json`): frame counts, loops exact, phone 0.40-0.41 m from the eyes during reading and typing, screen 23-29 degrees off the eye line (the creator's chosen pose), steady within 5 mm. Chat reveal verified on stills at frames 1, 20, 40, 70 and 105 (`phone_chat_strip.jpg`).
- **Seated** (`seated_checks.json`): counts, loops exact, no rotation over its limit, ankles 0.075-0.10 m (feet flat on the floor).
- **Driving** (`driving_checks.json`): hand-to-grip error **0.0 cm** in all three wheel actions, arm stretch at most 2.25x (limit 2.3), the arm's thickness is constant; the grip-follow check also found and fixed a depsgraph staleness bug in my solver (car objects must be update-tagged after changing `steer` from a script).
- **Library:** 3.66 MB, 93 objects, 84 actions. Triangles: human 4,024, Claude 1,212, car 19,700, phone 476. Draft render of all rigs (960x540, Eevee, 16 samples, headless): 1.6 s, peak memory 428 MB. Contract test on a copy of the realistic scene (30 MB): peak 466 MB, 0.25 s per frame.
- **Reels** (`lab/animation-build/previews/`): `reel_human2_locomotion.mp4`, `reel_human2_phone.mp4`, `reel_human2_seated.mp4`, `reel_claude_driving.mp4`. Frame strips and sheets: `human2_strip_walk.jpg`, `human2_walk_front_strip.jpg`, `human2_strips_phone_all.jpg`, `human2_seated_sheet.jpg`, `claude_drive_sheet.jpg`, `phone_pose_creator.jpg`, `contract_test_sheet.jpg`.

## 5. How to reproduce (scripts in `lab/animation-build/scripts/`, run via the bridge, in this order)
`20_human_locomotion.py` (stand/walk), `phone_lib.py` and `25-28_*` (edit helpers used with the creator), `22_human_phone.py` (reads `phone_hold_pose.json`), `24_phone_chat.py`, `30_human_seated.py`, `32_car_grips.py`, `04_claude_rig.py` (rerun: reach, slide, grips constraints), `33_claude_driving.py`; checks `21_`, `23_`, `31_`, `34_`; reels `render_reel_human2.py`, `render_reel_drive.py`; then `13_build_library.py` (headless), `14_contract_test.py`, `15_measure.py`. Do not rerun `05_car_and_phone.py` after the phone bone exists: it would put the phone socket back on `DEF-hand.R` (re-create the bone with `28_phone_edit_setup.py` if the rig is regenerated).

## 6. Problems, honest flaws and what I could not verify
- **Motion feel unverified by me** (frame strips and numbers only); the creator saw the walk and phone videos and called them fine for now, the seated and driving videos are new.
- **Perspective flash in the phone raise/lower** remains for cameras near the front (see section 2).
- **Claude's driving placement is a convention**: the origin must be at car-space (0.42, -0.19, 0.81) (driver seat, cushion height). I chose it from the car's geometry; it was not checked against the real scene's seat and cushion. If the scene places him elsewhere, the sliding and stretch keys no longer fit and the action must be rebuilt (`33_claude_driving.py` takes the seat position as one constant). The hand-over-hand cheat (the grips turn only 15 percent as far as the wheel) is a choice, not tested with the creator.
- Claude's driving pose needs a 10-16 degree forward lean to stay under the 2.3x stretch; the steer actions pick lean/turn per action by a small search.
- **Seated pose**: the hands are the creator's own pose on a preview seat (0.45 m); the rest is an approximation, not fitted to the car's seat or the steering geometry; `HUM_pass_*` look targets (window, Claude) are plausible angles, not computed from the car. `HUM_pass_look_out_window` and the other human actions move head, neck, spine and shoulders only (no face).
- **Walk:** body motion is plausible but not tuned against reference footage; cadence 2 steps per second at 1.2 m per cycle; legs have no knee/foot polish beyond the heel-toe roll; no turning gait (`HUM_turn_in_place` not built); `HUM_walk_out_building` has no door and no head/phone detail.
- **Blends to and from the scan's own neutral pose are not provided** (standing now uses the symmetric stance, so a cut from `HUM_pose_neutral` to a standing action shifts the feet).
- The old thumb-symmetry and hoodie poke-through checks from phase 1 are still open.
- **Rig regeneration** (re-running `01_human_rig.py`) wipes the hand-built `phone_hold.R` bone; scripts exist to restore it.

## 7. Recommendation
1. **Creator review** of the new seated and driving reels (feel, amounts, the seat convention).
2. **Integrate into the realistic scene** (change list in `animation-build-phase1.md` section 7, plus: place Claude at the driver-seat origin, key `CAR_ctrl["steer"]` and the car's wheel actions together with the Claude driving actions, key `PHN_Phone["chat_typed"]` for the scene's message, and use `phone_visible` to hide the phone outside the street shot). Then render a first sample and measure the footprint with city, car and both rigs.
3. **Phase 3 (signature moments):** the cushion actions, `MAG_ring_*`, `CLA_magic_cast` (also the "out of reach" fallback from the reach planner), `CAR_self_drive_start`, `HUM_react_*`, then the car entry/exit transitions (`HUM_stand_to_sit_car`, `CLA_pickup_arrival`).
