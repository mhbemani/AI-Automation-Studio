# animation-build: final report (phases 1-3) for the project lead

Branch `<task branch>`. Detailed per-phase reports: `lab/results/animation-build-phase1.md`, `-phase2.md`, `-phase3.md`; short hand-over: `lab/results/animation-build-session-report.md`. Contract: `lab/animation-library/CONTRACT.md`. Statuses: last column of `lab/animation-library/ANIMATION_LIST.md`. Library: `lab/animation-library/library_v1.blend`.

## 0. Rebuild order and traps (read this first)
**Rebuild the work file `lab/animation-build/anim_work.blend` from nothing** (all scripts are in `lab/animation-build/scripts/`, idempotent; run through the bridge: `python3 lab/animation-build/bridge/bl.py file <script>` from `lab/animation-build`, with Blender opened by `lab/animation-build/launch_blender.sh`). Phase 3 below was re-run from scratch in this session after the window was lost, and reproduced every number. The phase 1 and 2 part of the order is taken from my own reports and was **not re-run from nothing**; treat it as the best-known order.
1. Blender via `launch_blender.sh` on an empty scene; `00_setup_work.py` (appends copies of the lineup and the human rig from `snapshots/`); save as `anim_work.blend`.
2. Phase 1: `01_human_rig.py`, `02_human_materials.py`, `04_claude_rig.py`, `05_car_and_phone.py`, `06_claude_actions.py`, `12_pose_assets.py`, `08_human_actions.py`, `10_car_actions.py`.
3. Phase 2: `20_human_locomotion.py`, then the phone bone `28_phone_edit_setup.py` (creates `phone_hold.R`; needs `phone_lib.py`), `22_human_phone.py` (reads `scripts/phone_hold_pose.json`), `24_phone_chat.py`, `30_human_seated.py` (reads `scripts/seated_hands_pose.json`), `32_car_grips.py`, `04_claude_rig.py` again (reach and grip constraints), `33_claude_driving.py`.
4. Phase 3 (verified this session): `04_claude_rig.py` -> `42_cushion_rig.py` -> `45_magic_rig.py` -> `40_claude_locomotion.py` -> `43_claude_cushion.py` -> `46_magic_actions.py` -> `50_claude_react.py` -> `51_human_react.py` -> `52_human_car_transitions.py`.
5. Checks: `07_`, `09_`, `11_`, `21_`, `23_`, `31_`, `34_`, `41_`, `44_`, `47_`, `53_*_checks.py` (JSON in `lab/animation-build/stills/`). Save the work file. Library: `/Applications/Blender.app/Contents/MacOS/Blender -b lab/animation-build/anim_work.blend --python lab/animation-build/scripts/13_build_library.py`; then `15_measure.py` and `14_contract_test.py` headless.

**Traps**
- **Save the work file.** The creator closed the Blender window and the unsaved phase 3 state was lost (rebuilt from scripts). Save with `bpy.ops.wm.save_mainfile()` through the bridge after each milestone; ask before assuming a window is open.
- **`04_claude_rig.py` deletes every object owned by Claude** (`anim_owner = claude`: parts, `CUS_Cushion`, `MAG_*`): always rerun `42_` and `45_` after it. It reads the hidden lineup copies, so it unhides the source chain and evaluates at frame 1 (otherwise parts end up 4 cm off the bones; fixed this session).
- **Do not rerun `05_car_and_phone.py` once the phone bone exists** (it moves the phone socket back to `DEF-hand.R` and resets `CAR_ctrl`); use `28_phone_edit_setup.py` to recreate `phone_hold.R` if the human rig is regenerated (`01_` wipes it).
- Custom properties must be set as **floats** (an int assignment turns the property into an int and breaks limits and NLA); call `update_tag()` on the rig and related objects (car objects after `steer`; `MAG_*` after aiming) and `view_layer.update()`.
- `hide_viewport` objects are not evaluated (stale matrices, drivers do not run): use `hide_render` or `hide_get()`.
- After assigning an action force a re-evaluation (`frame_set(500)` then the frame). A property that no active NLA strip keys keeps its last value: reset between uses (`cus_show` etc.).
- `id_properties_ui().update(default=..., min=...)` in one call zeroed min/max: use separate calls (default, min/max, soft limits).
- The library file is git-ignored (`.gitignore` rule `lab/animation-library/*.blend`); `anim_work.blend` too.

## 1. What was built, per phase
Status words as in `ANIMATION_LIST.md` (done / partial / todo).
- **Phase 1, foundations (done):** silver faceless human (Rigify rig, 1.75 m; creator decision: plain scan, no face, no colours, so `HUM_blink` and `HUM_emoface_*` are dropped, emotions are body language), Claude armature (parts follow bones, `ctrl` properties with drivers: eyes, glints, blush, arms, squash, lean, talk), car controls (wheels, steering, doors), phone attachment. 59 actions: Claude idle/blink/talk/looks/emotions (eyes + body), human seat idle/talk/looks/emotion bodies, car wheel spin/sway/steer/doors.
- **Phase 2, story scenes (done):** `HUM_stand_idle`, `HUM_walk_cycle`, blends, `HUM_walk_out_building`; the phone set on the creator's hand-posed pose (`HUM_phone_raise/hold_read/type/lower_pocket/show_claude`, `HUM_walk_texting`, `PHN_chat_reveal`, `PHN_screen_glow`); the seated set on the creator's hand-fixed seated pose (`HUM_pass_*`, `HUM_talk_hand_gesture_a`); Claude driving (`CLA_drive_hold_wheel/steer_left/steer_right/hands_off`, `CLA_talk_arm_wiggle`) with arms stretching at most 2.3x (never thinner) and sliding around their own side. Total 84 actions.
- **Phase 3, signature moments (done, two rows partial):** Claude `CLA_walk_cycle`, `CLA_run_cycle`, `CLA_idle_to_walk`, `CLA_walk_to_idle`, `CLA_pickup_arrival`; cushion `CLA_cushion_jump/run_carry/hold_to_throw/throw_and_jump/sit/sleep/happy_stand`, `CLA_stand_to_cushion_sit`; magic `MAG_ring_shoot/wrap/fade`, `CLA_magic_cast`, `CAR_self_drive_start`; reactions `CLA_react_proud_puff/oops/giggle`, `HUM_react_startle/laugh/impressed/shake_head`; `HUM_phone_to_seat_idle` (+ `PHN_phone_pocket`). **Partial:** `HUM_stand_to_sit_car`, `HUM_sit_to_stand_car` (plausible choreography, not fitted to the real door and seat). Total 113 actions.
- **Todo (not built):** `HUM_turn_in_place`, `HUM_seatbelt_on`, `CAR_drive_path`, `CAR_body_sway`, monitor on/off, the remaining phase 4 extras of the list, scene integration.

## 2. Numbers
- Library `library_v1.blend`: **4.25 MB**, 104 objects, **113 actions** (fake users, marked as assets), collections HUMAN, CLAUDE, CAR, PHONE, CUSHION, MAGIC (+ hidden REGEN metarig).
- Triangles (evaluated): human **4,024**, Claude **1,212**, car **19,700**, phone **476**, cushion + magic together **4,922**.
- Draft render of all rigs (960x540, Eevee, 16 samples, headless): **1.0 s**, peak memory **498 MB**. Contract test on a copy of the 30 MB realistic scene (appends 5 collections and 104 actions in 0.12 s): peak **575 MB**, about 0.3 s per 640x360 frame. Machine: Apple M2, 8 GB, Blender 4.5.3 LTS.
- Checks (all pass, JSON in `lab/animation-build/stills/`): loops exact (last key equals first); planted-foot drift 0.0 to 0.01 cm (human and Claude, walk, run, car entry); driving hand-to-grip error 0.0 cm, arm stretch at most 2.25x (limit 2.3x); cushion landing exactly on the cushion top; car entry ends 0.7 cm from the seated pose.

## 3. Honest flaws and what I could not verify
- **I never saw any motion in real time**: judged from numbers and frame strips only. The creator reviewed phase 1 and 2 stills/videos and said "good for now" about phase 3, without a detailed review of the phase 3 reels.
- **Car entry and exit are not fitted to the real door, sill, legroom and seat**; `HUM_sit_to_stand_car` is the entry played backwards with a deeper duck (checked numerically, not as a sheet).
- Magic ring faint and thin at medium distance (the creator's original material), puffs and sparkles barely visible; the dash accent strip bleaches to white-violet when it glows.
- Human has no face, so laugh, impressed and shake_head are subtle at two-shot size; human deformation at extremes (arms up, crouch) shows stretch and foldovers (phase 1 stress numbers); hoodie poke-through and thumb symmetry were never checked.
- Claude's driver-seat origin convention (car space 0.42, -0.19, 0.81) was not checked against the real scene; the hand-over-hand wheel cheat (grips turn 15 percent as far as the wheel) was not tested with the creator.
- Claude walk/run is a trot of my own design: planting exact, body motion plausible, not tuned against reference. Phone raise shows a perspective size change near the front camera (the phone's scale never changes).
- Phase 1/2 Claude stills (`claude_cute_v5.jpg`, emotion sheets, `claude_drive_sheet.jpg`) were made before a fix of a 4 cm mesh offset (his eyes, arms and legs sat 4 cm low vs his bones in some rebuilds); the library and all phase 3 renders are after the fix; check numbers are bone-based and unaffected.
- The contract test scene shows magenta city materials (its CC0 textures are not next to the copy), so it renders on a grey stage.

## 4. What the creator should watch (`lab/animation-build/previews/`, 24 fps, labelled on screen)
- `reel_claude3_signature.mp4` (23.7 s): 0-3.4 `CLA_cushion_throw_and_jump`; 3.4-6.1 `CLA_cushion_jump`; 6.1-7.6 `CLA_cushion_run_carry`; 7.6-11.8 `CLA_cushion_sit`; 11.8-13.1 `CLA_react_proud_puff`; 13.1-14.3 `CLA_react_oops`; 14.3-16.4 `CLA_react_giggle`; 16.4-19.9 `CLA_pickup_arrival`; **19.9-23.7 `CLA_magic_cast` with the ring (shoot, wrap, fade): judge the ring's visibility here.**
- `reel_human3_react.mp4` (14.5 s): 0-1.1 startle; 1.1-2.9 laugh; 2.9-4.5 impressed; 4.5-5.6 shake head; 5.6-7.5 phone to seat; **7.5-11.0 `HUM_stand_to_sit_car` and 11.0-14.5 `HUM_sit_to_stand_car` (the entry choreography: decide if the idea works).**
- `reel_claude2_locomotion.mp4` (7.3 s): 0-3.2 walk, 3.2-6.0 run, 6.0-7.3 the two blends.
- Phase 2 reels (creator saw them): `reel_human2_locomotion.mp4` (13.2 s), `reel_human2_phone.mp4` (15.6 s: raise 0-1.2, read 1.2-5.3, type 5.3-9.5, show Claude 9.5-10.9, pocket 10.9-12.4, walk texting 12.4-15.6), `reel_human2_seated.mp4` (15.4 s), `reel_claude_driving.mp4` (11.6 s), `reel_car.mp4` (13.3 s). Phase 1 reels: `reel_claude_*.mp4` and `reel_human_*.mp4` (5-12 s each: emotions, basics, looks).
- Stills: `stills/contract_test_sheet.jpg` (library used in a scene copy, with the cushion and the ring), `stills/human3_enter_sheet.jpg`, `stills/magic_cast_sheet.jpg`, `stills/claude3_*_sheet.jpg`.

## 5. What is left and what I recommend next
1. **Creator review** of the three phase 3 reels (feel, ring visibility, entry choreography).
2. **Integrate into the realistic scene** (recommended next): change list in `animation-build-phase1.md` and `-phase2.md` section 7 (replace the object animation of Claude and the car by the rigs/actions; key `CAR_ctrl["distance"/"steer"]`; Claude at the driver-seat origin; key the cushion landing `cus_dx/dy/dz` to the real seat; fit and key the car entry/exit with `CAR_door_open_R`; `phone_visible`/`PHN_phone_pocket`), then a first sample render and the footprint with city, car and both rigs.
3. **Phase 4 extras and open items:** `HUM_turn_in_place`, `HUM_seatbelt_on`, `CAR_drive_path`, `CAR_body_sway`, monitor, thumb symmetry, hoodie poke-through, plus whatever the list holds for phase 4 (not read yet).

## 6. Decisions needed from the creator
- Next step: scene integration first, or phase 4 extras first (I recommend integration).
- The magic ring: keep the faint original look, or make it brighter and thicker?
- Whether the car entry/exit idea (step in sideways, turn, sit) is what they want before it is fitted to the real car.
