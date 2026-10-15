# Animation library: what to prebuild

Written from the asset lineup (`lab/asset-lineup/lineup.blend`, the creator's working file) and from the story scenes: a human walks out of a building, texts, rides in the front passenger seat of a car and talks, while Claude drives and talks. Everything is at 24 fps. The scene timeline drives 8 emotions: neutral, happy, curious, excited, surprised, thoughtful, proud, amused. Claude has eye and body emotions only, no mouth.

Naming: `HUM_` human, `CLA_` Claude, `CAR_` car, `PHN_` phone, `MAG_` Claude's magic ring. Durations are rough, in frames. "Loop" means it must tile perfectly. Priority is **must** or **nice**. Use frequency is **very often**, **often** or **rare**. "Drives" lists what mainly moves.

## 0. Rig status (what is done, what is missing)

> **Updated after phase 1:** the human (Rigify, silver, faceless), Claude (armature + sliders) and the car (controls) are finished and in `library_v1.blend`; the "Missing" items below that concern these are done unless listed in the report. The text below is the state **before** phase 1, kept for the record.

### Human
- **Current human in the lineup:** `LU_NEW_RIG_Human` (armature) + `LU_NEW_HUM_Body` (the grey scan, about 4,000 tris). In `lab/asset-lineup/lineup.blend` (copy at `lab/asset-lineup/lineup.blend`). A seated copy `LU_NEW_RIG_Human_InCar` is in the car (the creator re-posed and rescaled it). The selection lab file it came from is `lab/character-selection/character_selection_lab.blend` in the `optimistic-wilson-150cb0` worktree.
- **Done:** 49 bones: `pelvis`, `spine`, `chest`, `neck`, `head`, `shoulder.L/R`, `upper_arm`, `forearm`, `hand`, five finger chains per hand (`f_index/middle/ring/pinky.01-03`, `thumb.01-03`), `thigh`, `shin`, `foot`. Skinned, with corrective smooth on the knees and arms. Seated pose with two-bone IK was built by script (`lab/asset-lineup/scripts/place_occupants.py`), including hands on the steering wheel.
- **Missing for animating:** no IK/FK controls (pose bones directly, or add IK); no toe bones; **no face at all**: no eyes, no jaw, no `MouthOpen`, no `Blink`; only 6 brow shape keys (`brow_up_L/R`, `brow_down_L/R`, `brow_inner_up`, `brow_squeeze`). It is grey (no colours or clothes yet). The scene scripts expect the **Rigify control names** (`torso`, `spine_fk…003`, `neck`, `head`, `upper_arm_fk`, `forearm_fk`, `hand_fk`, `thigh_fk`, `shin_fk`, `foot_fk`, `*_parent` with `IK_FK`, `DEF-hand.R` for the phone) and the face keys `happy`, `curious`, `excited`, `surprised`, `thoughtful`, `proud`, `amused`, `MouthOpen`, `Blink`. The lineup human has none of these.
- **Older human with those names:** the realistic scene's `CHAR_Human*` in `lab/scene-realistic-car/scene.blend` (Rigify-named FK rig, 8 emotion face keys, `MouthOpen`, `Blink`, phone on `DEF-hand.R`). It is the only human the existing scene animation scripts (`lab/scene-realistic-car/scripts/animate.py`) drive today.

### Claude (main, V3-A)
- **Where:** `LU_V3A_CHAR_Claude` and parts in `lab/asset-lineup/lineup.blend`, under the empty `LU_V3A_Set` (carry empty) with his cushion `LU_V3A_Cushion`. Variants `V3` (plain), `V3B` (blush), `V3C` (big eyes + blush) are reference faces.
- **Done:** 11 separate parts, no armature: body root (origin on the ground), `Arm_L/R` (pivot at the shoulder), `Eye_L/R` (+ white glints), `Leg_1-4` (pivot at the hip). A jump loop (`Claude_Jump_on_Cushion`, 60 frames) with squash and stretch, and the cushion `Squash` shape key driven by his feet, plus `squash_manual`. Magic ring `LU_V3A_Magic_Ring` with `fade` and `spin`. Three custom Claude and cushion variants made by the creator (running, sitting, sleeping, happy standing) exist as separate objects and are not tidied yet.
- **Missing:** an armature or control empties for the parts; eye and body emotion presets (eye scale and height, glint, arm angle, body squash; V3B/V3C show the blush look but it is not a toggle); blink; mouth-free talk pulse; walk, run and sit poses; the in-car Claude is a loose copy and not parented to the car.
- **Older Claude with working emotion/talk code:** the realistic scene's `CHAR_Claude` (rounded block, body + arms + eyes + legs), driven by `animate.py` (emotions, blink, speech pulse). The new block Claude uses different part names and pivots, so those scripts need a mapping.

### Car (new hero coupe)
- **Where:** `LU_NEW_CAR_*` in `lab/asset-lineup/lineup.blend`.
- **Done:** root `LU_NEW_CAR_Exterior`; separate wheels (round, 5 spokes, spin about their local X); steering wheel; two doors `Door_L` (+x, driver side) and `Door_R`, with hinge anchor on `Door_L`, rotate about Z with limits 0 to 65 degrees (`Door_L` negative, `Door_R` positive); door panels; dash monitor with a `VIDEO_TEXTURE` slot; seat bases.
- **Missing:** a drive path and follow-path setup in this file (the scene has `CITY_DrivePath`); steering linked to the front wheels; a wheel-spin driver tied to speed; the right door anchor; door open/close actions.

### Phone
- **Where:** `LU_NEW_PROP_Phone` (+ 5x copy) in the lineup; the scene phone is `PROP_Phone` with `PROP_UI_*` in the realistic scene.
- **Done:** screen, UI, typing text objects (visibility keyed in the scene). **Missing:** hand attachment (scene parents it to `DEF-hand.R`), the lineup copy has none.

## Phase 3 result (2026-10-14)
Signature moments, built on phases 1 and 2 (same file): Claude's walk and run cycles (in place, planted feet do not slide), the cushion (`CUS_Cushion` in collection `CUSHION`, driven by `ctrl`) with eight `CLA_cushion_*` / `CLA_stand_to_cushion_sit` actions, the magic ring (`MAG_Root` and children in collection `MAGIC`) with `MAG_ring_shoot/wrap/fade`, `CLA_magic_cast` and `CAR_self_drive_start` (dash glow), Claude's reactions, `CLA_pickup_arrival` (new root props `move_x/move_y/yaw`), the seated human reactions, `HUM_phone_to_seat_idle` and the car entry/exit transitions. See `lab/results/animation-build-phase3.md` and `CONTRACT.md`. Still todo: `HUM_turn_in_place`, `HUM_seatbelt_on`, `CAR_drive_path`/`CAR_body_sway`/monitor, scene integration.

## Phase 2 result (2026-10-14)
Story-scene animations built on top of phase 1 (same file, `library_v1.blend`): standing and walking with IK legs and a symmetric stance, the phone set built on the creator's own holding-phone pose (FK arm, `phone_hold.R` bone), the chat reveal on the phone, the seated passenger set, and Claude driving with stretching, sliding arms that follow the wheel grips. See `lab/results/animation-build-phase2.md` and `CONTRACT.md`. Still todo: `HUM_turn_in_place`, `HUM_seatbelt_on`, `HUM_phone_to_seat_idle`, the transitions into and out of the car, reactions, the cushion, magic ring and self-drive set (phase 3), `CAR_drive_path`/`CAR_body_sway`/monitor.

## Phase 1 result (2026-10-13)
Built by the animation-build task: `library_v1.blend` + `CONTRACT.md` in this folder, report `lab/results/animation-build-phase1.md`. Status per row is in the last column of every table below (done / partial / dropped / todo). Decisions that changed the list: **the human is a plain silver scan with no face**, so `HUM_blink` and `HUM_emoface_*` are dropped and his emotions are body language only; added: `CLA_idle` (96 loop), `CLA_pose_<emotion>` (single-frame pose assets), `HUM_pose_neutral` and `HUM_pose_seated` (absolute base poses). The phone is attached to the hand (`HUM_PhoneSocket` on `DEF-hand.R`), the car and Claude have their controls.

## 1. Seated and passenger

| name | purpose | shots | loop? | frames | priority | use | drives | fingers / face | status (phase 1) |
|---|---|---|---|---|---|---|---|---|---|
| `HUM_seat_idle` | seated, breathing, tiny weight shifts, slight lean | INT two-shot, HUMAN_POV | loop | 96 | must | very often | `pelvis`, `spine`, `chest`, `head`, `shoulder.*` | no / blink if a face exists | done |
| `HUM_pass_hands_lap` | passenger hands resting on the lap | INT two-shot | loop | 96 | must | very often | `upper_arm`, `forearm`, `hand`, fingers | fingers relaxed | done (phase 2; seated, hands on the thighs) |
| `HUM_pass_look_out_window` | looks out of the side window, small head motion | cutaways | loop | 120 | nice | often | `neck`, `head`, eyes | face | done (phase 2; head/neck/spine only, no eyes) |
| `HUM_pass_turn_to_claude` | turns head and shoulders to Claude to listen | INT two-shot | one-shot | 24 | must | very often | `spine`, `neck`, `head` | eyes | done (phase 2; head, neck, chest turn to his left) |
| `HUM_pass_lean_forward` | leans toward the dash or screen | monitor shots | one-shot | 20 | nice | rare | `spine`, `chest`, `head` | no | done (phase 2) |
| `HUM_seatbelt_on` | pulls the belt across and clicks it | arrival | one-shot | 40 | nice | rare | `shoulder`, `upper_arm`, `hand`, fingers | fingers | todo |

## 2. Standing and walking

| name | purpose | shots | loop? | frames | priority | use | drives | fingers / face | status (phase 1) |
|---|---|---|---|---|---|---|---|---|---|
| `HUM_walk_cycle` | normal walk, phone-compatible arms | EST street | loop | 24 (1 step pair) | must | very often | `pelvis`, legs, `spine`, arms | no | done (phase 2; 24 frames in place, 1.2 m per cycle, IK feet, symmetric stance) |
| `HUM_walk_out_building` | exits the door, steps onto the pavement | opening | one-shot | 72 | must | often | whole body, door | no | done (phase 2; with root motion, no door) |
| `HUM_walk_texting` | walks while looking at the phone, head down | PHONE_CU | loop | 24 | must | often | walk + `head`, right arm up | fingers on the phone | done (phase 2; built on the creator's holding-phone pose) |
| `HUM_stand_idle` | standing breathing, weight shift | before the car | loop | 96 | must | very often | `pelvis`, `spine`, `head` | no | done (phase 2) |
| `HUM_stop_from_walk` | decelerates to a stop | arrival | one-shot | 18 | must | often | legs, `spine` | no | done (phase 2) |
| `HUM_turn_in_place` | turns toward the car or Claude | arrival | one-shot | 24 | nice | often | `pelvis`, `spine`, legs | no | todo |

## 3. Phone use

| name | purpose | shots | loop? | frames | priority | use | drives | fingers / face | status (phase 1) |
|---|---|---|---|---|---|---|---|---|---|
| `HUM_phone_hold_read` | holds the phone at chest height, reading | PHONE_CU | loop | 96 | must | very often | right/left arm, `hand`, head | fingers | done (phase 2; creator's pose) |
| `HUM_phone_type` | thumbs typing | PHONE_CU | loop | 48 | must | very often | thumbs `thumb.*`, `hand` | fingers | done (phase 2; thumb taps) |
| `HUM_phone_raise` | raises the phone from the side to reading height | PHONE_CU | one-shot | 20 | must | often | arm chain | fingers | done (phase 2) |
| `HUM_phone_lower_pocket` | lowers and pockets it | arrival | one-shot | 30 | nice | often | arm chain | fingers | done (phase 2) |
| `HUM_phone_show_claude` | holds the phone out toward Claude | INT two-shot | one-shot | 24 | nice | rare | arm chain | fingers | done (phase 2) |
| `PHN_chat_reveal` | messages appear on the screen (typing then send) | PHONE_CU | one-shot | 120 | must | very often | visibility keys of `PROP_UI_*` / typing objects | no | done (phase 2; properties + drivers on PHN_Phone) |
| `PHN_screen_glow` | screen wakes and dims | PHONE_CU | one-shot | 12 | nice | often | screen emission | no | done (phase 2) |

## 4. Talking gestures

| name | purpose | shots | loop? | frames | priority | use | drives | fingers / face | status (phase 1) |
|---|---|---|---|---|---|---|---|---|---|
| `HUM_talk_small` | head bob and shoulders while speaking, seated | INT two-shot | loop | 48 | must | very often | `head`, `neck`, `chest`, brows | face (`MouthOpen`) | done (no mouth: head, neck, chest, shoulders) |
| `HUM_talk_hand_gesture_a` | one hand opens while talking | INT two-shot | loop | 36 | nice | often | arm chain | fingers | done (phase 2; seated, right hand) |
| `HUM_talk_nod` | small nods to emphasise | any | one-shot | 14 | must | very often | `head`, `neck` | no | done |
| `CLA_talk_pulse` | body squash pulse to the voice (no mouth) | all Claude shots | loop (envelope driven) | 12 | must | very often | body scale Z, eyes | no | done (live `talk` property + `bake_talk`) |
| `CLA_talk_arm_wiggle` | arms move a little while he speaks | INT two-shot | loop | 36 | nice | often | `Arm_L/R` | no | done (phase 2) |

## 5. Emotions and expressions

Eight emotions: neutral, happy, curious, excited, surprised, thoughtful, proud, amused. Human face keys are shape keys; body language is pose; Claude uses eyes, glints, blush and body.

| name | purpose | shots | loop? | frames | priority | use | drives | fingers / face | status (phase 1) |
|---|---|---|---|---|---|---|---|---|---|
| `HUM_emoface_<emotion>` (x8) | face pose for each emotion; blended in and out | all human close-ups | pose (blend 8-12) | 12 | must | very often | face shape keys: `happy`, `curious`, `excited`, `surprised`, `thoughtful`, `proud`, `amused`, neutral; brows | **face needed** | dropped: the human has no face (creator decision) |
| `HUM_emobody_<emotion>` (x8) | small posture change per emotion | seated + standing | pose (blend 12) | 16 | must | very often | `chest`, `head`, shoulders, hands | no | done (body language only) |
| `HUM_blink` | blink, random spacing | all human shots | one-shot (layer) | 6 | must | very often | `Blink` shape key / lids | **face needed** | dropped: no face |
| `CLA_emoeyes_<emotion>` (x8) | eye shape, height and glint per emotion (neutral, happy, curious, excited, surprised, thoughtful, proud, amused) | all Claude shots | pose (blend 8) | 8 | must | very often | `Eye_L/R` scale and position, glints, blush objects | no | done |
| `CLA_emobody_<emotion>` (x8) | body language per emotion (bounce, lean, arms) | all Claude shots | pose (blend 12) | 16 | must | very often | body root, `Arm_L/R`, legs | no | done |
| `CLA_blink` | quick blink (eyes squash flat) | all Claude shots | one-shot (layer) | 6 | must | very often | `Eye_L/R` scale Z | no | done |

## 6. Head and eye looks

| name | purpose | shots | loop? | frames | priority | use | drives | fingers / face | status (phase 1) |
|---|---|---|---|---|---|---|---|---|---|
| `HUM_look_at_<target>` (phone, claude, road, window, monitor) | head and eyes toward a target, eased | all | pose (blend 10) | 10 | must | very often | `neck`, `head`, eyes | eyes | done (phone, claude, road, window, monitor; head and neck only) |
| `CLA_look_<dir>` (left, right, up, down, camera) | eyes shift toward a point | all | pose (blend 6) | 6 | must | very often | `Eye_L/R` offset, glints | no | done (left, right, up, down, camera) |
| `CLA_look_around` | curious scanning of the scene | establishing | one-shot | 60 | nice | often | eyes, body turn | no | done |
| `HUM_look_around_idle` | idle head scanning | standing | loop | 120 | nice | often | head | eyes | todo |

## 7. Reactions

| name | purpose | shots | loop? | frames | priority | use | drives | fingers / face | status (phase 1) |
|---|---|---|---|---|---|---|---|---|---|
| `HUM_react_startle` | flinch when something surprising happens (the car drives itself, the magic ring) | magic / self-drive | one-shot | 16 | must | often | whole upper body, hands | face | done (phase 3; seated, body language only: hands come up, chin up) |
| `HUM_react_laugh` | laughs at Claude | INT two-shot | one-shot | 36 | nice | often | shoulders, head | face | done (phase 3; seated, shoulders and head) |
| `HUM_react_impressed` | eyebrows up, slow nod | self-drive | one-shot | 30 | nice | often | head, brows | face | done (phase 3; seated, lean back and slow nod, no brows) |
| `HUM_react_shake_head` | gentle no | any | one-shot | 18 | nice | rare | head | no | done (phase 3; seated) |
| `CLA_react_proud_puff` | stretches taller, chest out | after the magic | one-shot | 24 | must | often | body scale, arms | no | done (phase 3) |
| `CLA_react_oops` | squash and wobble when something goes wrong | rare scenes | one-shot | 20 | nice | rare | body, eyes | no | done (phase 3) |
| `CLA_react_giggle` | quick bounces in place | happy moments | loop (short) | 24 | nice | often | body, legs | no | done (phase 3; 24 loop, key range 25) |

## 8. Driving, steering, wheel spin, mirror

| name | purpose | shots | loop? | frames | priority | use | drives | fingers / face | status (phase 1) |
|---|---|---|---|---|---|---|---|---|---|
| `CLA_drive_hold_wheel` | Claude stands on his cushion, both arms to the wheel | CLAUDE_POV, INT two-shot | loop | 96 | must | very often | `Arm_L/R`, body, cushion squash | no | done (phase 2; needs Claude at the driver seat origin, see CONTRACT) |
| `CLA_drive_steer_left` / `_right` | lean and arm movement with steering | driving shots | one-shot | 24 | must | very often | `Arm_L/R`, body lean | no | done (phase 2; left and right) |
| `CLA_drive_hands_off` | arms drop and open when the car drives itself | self-drive | one-shot | 18 | must | often | `Arm_L/R` | no | done (phase 2) |
| `CLA_mirror_check` | looks up at the mirror and back to the road | driving | one-shot | 36 | nice | often | eyes, body | no | todo |
| `CAR_steering_sway` | steering wheel gentle sway | driving | loop | 96 | must | very often | `LU_NEW_CAR_SteeringWheel` rotation | no | done |
| `CAR_steering_turn_<dir>` | steering wheel turn, front wheels follow | driving | one-shot | 24 | must | very often | steering wheel rotation, front wheel steering | no | done (left, right) |
| `CAR_wheel_spin` | all four wheels spin at a chosen speed | any moving car shot | loop (speed driven) | 12 | must | very often | wheel local X rotation | no | done (also driven by `speed` / `distance`) |
| `CAR_drive_path` | car follows the road with matched wheels | EST street | one-shot | variable | must | very often | root path, wheels, body sway | no | todo |
| `CAR_body_sway` | small body roll and pitch on turns and bumps | driving | loop | 48 | nice | often | root | no | todo |
| `CAR_door_open_L` / `_R` and `CAR_door_close_L` / `_R` | doors open and close with an ease | getting in, pick-up | one-shot | 24 | must | very often | `Door_L/R` rotation Z (limits 0..65) | no | done (open and close, L and R) |
| `CAR_monitor_video_play` / `_stop` | dash monitor switches between standby and a video | any dash shot | one-shot | 12 | nice | rare | `NEW_MAT_CarMonitor` emission, `VIDEO_TEXTURE` | no | todo |

## 9. Claude's cushion and magic

| name | purpose | shots | loop? | frames | priority | use | drives | fingers / face | status (phase 1) |
|---|---|---|---|---|---|---|---|---|---|
| `CLA_cushion_jump` | the jump loop on the cushion (already built, `Claude_Jump_on_Cushion`) | playful moments | loop | 60 | must | often | body height and scale, cushion `Squash` | no | done (phase 3; rebuilt on the CUS_Cushion rig, key cus_show = 1) |
| `CLA_cushion_run_carry` | runs holding the cushion | arrival, pick-up | loop | 16 | must | often | legs, arms, cushion follows `LU_V3A_Set` | no | done (phase 3; hugs CUS_Cushion in front of him) |
| `CLA_cushion_sit` / `_sleep` / `_happy_stand` | his cushion ways (the creator's variants) | quiet moments | loop | 96 | nice | often | body, eyes, cushion | no | done (phase 3; `_sleep`, `_happy_stand` too; he stands on the cushion at root height 0.215) |
| `CLA_cushion_throw_and_jump` | throws the cushion on the seat, jumps on it | getting in | one-shot | 72 | must | often | arms, cushion arc, body | no | done (phase 3; the cushion lands at cus_dx/dy/dz, he jumps on it, squash while he lands) |
| `MAG_ring_shoot` | the ring appears at his hand and flies to the target | magic | one-shot | 24 | must | often | `LU_V3A_Magic_Ring` position, scale, `fade` | no | done (phase 3; MAG_Root props: fade, shot, dist, size) |
| `MAG_ring_wrap` | ring tightens around the target (steering wheel) | magic | one-shot | 30 | must | often | ring scale, `spin`, `fade` | no | done (phase 3; wrap, wrap_to) |
| `MAG_ring_fade` | ring dissolves into sparkles | magic | one-shot | 18 | must | often | `fade`, sparkles | no | done (phase 3; sparkle orbit) |
| `CLA_magic_cast` | points both or one arm, little body push | magic | one-shot | 24 | must | often | `Arm_L/R`, body, eyes | no | done (phase 3; both arms, 1.6x stretch) |
| `CAR_self_drive_start` | wheel pulse, dash glow, the car starts rolling | magic | one-shot | 48 | must | often | wheels, dash emission, drive path | no | done (phase 3; dash_glow, steering pulse, rolls to 2 m/s; the drive path is the scene's) |

## 10. Transitions between poses

| name | purpose | shots | loop? | frames | priority | use | drives | fingers / face | status (phase 1) |
|---|---|---|---|---|---|---|---|---|---|
| `HUM_stand_to_sit_car` | gets into the car and sits | arrival | one-shot | 72 | must | often | whole body, door | face | partial (phase 3; plausible choreography, not fitted to the real door and seat geometry) |
| `HUM_sit_to_stand_car` | gets out | end | one-shot | 72 | nice | rare | whole body | no | partial (phase 3; the entry plan played backwards with a deeper duck, not fitted to the real car) |
| `HUM_walk_to_stand` / `HUM_stand_to_walk` | blends between standing and walking | EST street | one-shot | 12 | must | very often | legs, pelvis | no | done (phase 2; both directions) |
| `HUM_phone_to_seat_idle` | pockets the phone and settles into the seat | arrival | one-shot | 36 | nice | often | arms, spine | fingers | done (phase 3; use `PHN_phone_pocket` to hide the phone at frame 30) |
| `CLA_stand_to_cushion_sit` | blend from standing to sitting on the cushion | quiet moments | one-shot | 24 | nice | often | legs, body | no | done (phase 3) |
| `CLA_idle_to_walk` / `CLA_walk_to_idle` | blends | any | one-shot | 10 | must | very often | legs, body | no | done (phase 3; with `CLA_walk_cycle` 24 loop and `CLA_run_cycle` 16 loop, in place, not in the list) |
| `CLA_cushion_hold_to_throw` | hold to throw | getting in | one-shot | 18 | must | often | arms | no | done (phase 3) |
| `CLA_pickup_arrival` | Claude runs up to pick the human up, stops, turns | arrival | one-shot | 72 | must | often | whole body | no | done (phase 3; move_y / yaw root props, runs 1.46 m and turns 90 deg) |

## Build order suggestion

1. **Foundations:** `CLA_idle`, `CLA_blink`, `CLA_emoeyes_*`, `CLA_emobody_*`, `CLA_talk_pulse`, `HUM_seat_idle`, `HUM_blink`, `HUM_emoface_*` (needs the face first), `CAR_wheel_spin`, `CAR_steering_sway`, `CAR_door_*`.
2. **Story scenes:** `HUM_walk_cycle`, `HUM_walk_texting`, `HUM_phone_*`, `PHN_chat_reveal`, `HUM_talk_*`, `HUM_look_at_*`, `CLA_drive_hold_wheel`, `HUM_pass_*`.
3. **Signature moments:** `CLA_cushion_*`, `CLA_magic_cast`, `MAG_ring_*`, `CAR_self_drive_start`, `HUM_react_*`.
4. **Extras:** the rest of the rare and nice-to-have items.

## Open questions for the creator
- Which human do the story scenes use: the lineup scan (needs a face and Rigify-style controls), or the older scene human?
- Should Claude get a small armature (recommended) or stay as separate parts with control empties?
