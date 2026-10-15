# Animation library contract (library_v1.blend, phases 1-3)

How a scene uses the rigs and actions in `lab/animation-library/library_v1.blend`. Built by the scripts in `lab/animation-build/scripts/` (numbered `01_` ... `15_`); checked numerically (`lab/animation-build/stills/*_checks.json`) and by a contract test on a copy of the realistic scene (`lab/animation-build/scripts/14_contract_test.py`).

## General
- 1 unit = 1 m, +Z up, 24 fps. **Every character and the car face -Y.** For the human and the car "left" (L) is **+X** (the car's driver side is +X); for Claude the lineup naming is kept: his `*_L` parts are on **-X**.
- Each rig's root object origin is on the ground between the feet (Claude, human) or the car root (wheels touch z = 0, no rotation). Place a rig in a scene by moving/rotating the **armature object** (`RIG_Human`, `RIG_Claude`) or `CAR_Exterior`.
- Collections (also marked as assets): `HUMAN`, `CLAUDE`, `CAR`, `PHONE`, `CUSHION` (phase 3), `MAGIC` (phase 3). `REGEN` holds the hidden Rigify metarig `META_Human` (only needed to regenerate the human rig).
- All actions have fake users and are marked as assets (tags: Claude/Human/Car, loop/one-shot/pose). Append with `bpy.data.libraries.load(path, link=False)` (objects, collections and actions) or the Asset Browser.
- **Scripts reading evaluated data (viewport depsgraph) need the rig objects visible in the viewport:** objects with `hide_viewport = True` are not evaluated there, so drivers do not update (final renders use the render depsgraph and are not affected). Prefer `hide_render` or `hide_get()` for visibility keys.
- **Set custom properties as floats** (`ctrl["squash"] = 0.3`, not `0`): an int assignment turns the property into an int and breaks limits and animation. After changing a property from a script call `rig.update_tag()` (then read evaluated data).

### Playing and layering actions (NLA recipe)
Actions only key control properties/bones. Put one base action on the bottom NLA track (blend `REPLACE`) and layer the rest with `COMBINE` (adds Euler/float values; absolute base poses are the exception, see the human):
```python
def nla(rig, strips):               # strips = [(action_name, start_frame, blend)]
    ad = rig.animation_data_create(); ad.action = None
    for i, (name, start, blend) in enumerate(strips):
        tr = ad.nla_tracks.new(); s = tr.strips.new(name, start, bpy.data.actions[name])
        s.blend_type = blend; s.extrapolation = "HOLD" if i == 0 else "NOTHING"
nla(bpy.data.objects["RIG_Claude"], [("CLA_idle", 1, "REPLACE"), ("CLA_emoeyes_happy", 20, "COMBINE"), ("CLA_emobody_happy", 20, "COMBINE"), ("CLA_blink", 40, "COMBINE")])
```
- **Pose actions** (`*_emoeyes_*`, `*_emobody_*`, `*_look_*`): frame 1 = neutral, the last frame = the held pose. Play forward to blend in; to blend out play the action reversed (NLA `use_reverse`) or key the default values. A held emotion = `s.extrapolation = "HOLD_FORWARD"`.
- **Loops** (`CLA_idle`, `CLA_talk_pulse`, `HUM_seat_idle`, `HUM_talk_small`, `CAR_wheel_spin`, `CAR_steering_sway`): the **last key equals the first**; the loop length is the key range minus one (96, 12, 96, 48, 12, 96 frames). They carry a Cycles modifier, so a strip with `repeat = n` tiles perfectly.

## Claude: `RIG_Claude` (+ parts `CLA_*`)
- **Parts** (rigid, one full-weight vertex group each; his look is exactly the lineup's V3-A): `CLA_Body`, `CLA_Arm_L/R`, `CLA_Eye_L/R`, `CLA_Glint_L/R`, `CLA_Leg_1..4`, `CLA_Blush_L/R` (blush from the V3B variant, scaled to ~0 when `blush` = 0). Eyes, glints and blush have rounded corners. About 1,200 triangles in all.
- **Bones:** `root` (ground, move/rotate/scale him as a whole), `squash` (pivot at the ground), `body` (pivot at the bottom centre of the body), `eye_L/R`, `glint_L/R`, `arm_L/R` (pivot at the shoulder on the body wall), `leg_1..4` (pivot at the hip), `blush_L/R`, `ctrl` (the control panel, no deformation). Legs/arms/eyes are children of `body`; `body` is a child of `squash`.
- **Controls = custom properties of the pose bone `ctrl`** (`rig.pose.bones["ctrl"]["name"]`), all floats, driven onto the bones by drivers. Do not key the driven bone channels, key these:

| property | range (default) | effect |
|---|---|---|
| `eye_open` | 0..1.4 (1) | eye height multiplier, 0 = closed (blink) |
| `eye_h_L`, `eye_h_R` | 0.1..2 (1) | per-eye height scale (L = -X) |
| `eye_w` | 0.4..1.8 (1) | eye width scale |
| `eye_y` | -0.06..0.06 m (0) | both eyes up/down |
| `look_x`, `look_y` | -0.05..0.05 m (0) | eyes (and glints) shift, + = viewer's right / up |
| `eye_roll` | -35..35 deg (0) | eye tilt, + = tops lean outward (droopy), - = inward (stern) |
| `glint` | 0..2 (1) | glint size |
| `blush` | 0..1 (0) | cheeks |
| `arm_L`, `arm_R` | -70..120 deg (0) | arm raise, + = up (the arm also moves out of the wall) |
| `arm_fwd_L`, `arm_fwd_R` | -90..90 deg (0) | arm swing, + = forward (-Y) |
| `squash` | -1..1 (0) | +1 short and wide, -1 tall and thin, volume kept, pivot at the ground |
| `lean` / `nod` / `turn` | +-25 / +-25 / +-60 deg (0) | body roll (+ = toward +X), pitch (+ = forward), yaw (+ = face toward +X) about the bottom centre |
| `bob` | -0.05..0.1 m (0) | body up/down |
| `talk` | 0..1 (0) | voice envelope: stretches up (squash -0.22), bobs 12 mm, eyes +8% taller, glints +25% |

- **Emotions:** eight, `neutral, happy, curious, excited, surprised, thoughtful, proud, amused`. Eyes and body are separate: `CLA_emoeyes_<e>` (8 frames, eye/glint/blush properties) and `CLA_emobody_<e>` (16 frames, body properties). `CLA_pose_<e>` are single-frame absolute poses with both (Asset Browser pose assets). Values live in `lab/animation-build/scripts/claude_presets.py`.
- **Other actions:** `CLA_idle` (96 loop), `CLA_blink` (6, layer it), `CLA_talk_pulse` (12 loop, demo of the `talk` property), `CLA_look_left/right/up/down/camera` (6, eyes only), `CLA_look_around` (60).
- **Speech:** the live way is to key/drive `ctrl["talk"]` from the audio envelope; `lab/animation-build/scripts/claude_talk.py: bake_talk(rig, envelope, start_frame, fps, env_rate)` bakes one key per frame (tested: 0-frame lag, 0 error against the formula).
- Not in phase 1: walk/run/sit poses, the cushion `LU_V3A_Cushion` and the magic ring (they stay in the lineup file).

## Human: `RIG_Human` + `HUM_Body` (+ phone)
- **Look:** the original scan, one silver-grey material `HUM_silver`, no face, no eyes, no mouth (creator decision). 4,024 triangles, 1.75 m tall, hood closed. The 6 old brow shape keys are still on `HUM_Body` and unused.
- **Rig:** Rigify (generated from `META_Human`), 358 bones, `HUM_Body` is skinned to the `DEF-*` bones (spine, shoulder, upper_arm, forearm, hand, five fingers x3, thigh, shin, foot, toe) plus the old groups as `OLD_*` (read by the `HUM_Contact` geometry-nodes modifier; they deform nothing). Segments = 1 (no twist bones).
- **Scene control names (Rigify):** `root`, `torso`, `hips`, `chest`, `spine_fk`, `spine_fk.001/.002/.003`, `neck`, `head`, `shoulder.L/R`, `upper_arm_fk.L/R`, `forearm_fk.L/R`, `hand_fk.L/R`, `thigh_fk.L/R`, `shin_fk.L/R`, `foot_fk.L/R`, `toe_fk.L/R`; IK: `hand_ik.*`, `foot_ik.*`, `upper_arm_ik_target.*`, `thigh_ik_target.*`; fingers: `f_<index|middle|ring|pinky>.01-.03.L/R`, `thumb.01-.03.L/R` plus master controls `f_index.01_master.L` etc.; limb switch `upper_arm_parent.L/R` and `thigh_parent.L/R` with custom property **`IK_FK` (1 = FK, 0 = IK; the library is saved in FK)**. `DEF-hand.R` is the deforming hand bone (phone).
- **Rotation modes:** the FK controls the actions use (`spine_fk*`, `neck`, `head`, `shoulder.*`, limb FK, fingers, finger masters, `torso`, `hips`) are **Euler XYZ** so layers add.
- **Axes when authoring poses** (world, rest): X + = nod forward, Y + = tilt toward his left (+X), Z + = turn toward his left. Claude (the driver) sits on his left.
- **Base poses (absolute, bottom layer):** `HUM_pose_neutral` (the creator's standing pose; also stored in `rig["neutral_pose"]`), `HUM_pose_seated` (an extra: legs, torso and hands resting on the thighs, for a seat of about 0.45 m).
- **Deltas (layer on a base with COMBINE):** `HUM_seat_idle` (96 loop), `HUM_emobody_<e>` (16, the 8 emotions as head/neck/spine/shoulder/finger body language), `HUM_talk_small` (48 loop), `HUM_talk_nod` (14), `HUM_look_at_<phone|claude|road|window|monitor>` (10). Dropped from the list because there is no face: `HUM_blink`, `HUM_emoface_*`, mouth/`MouthOpen`, eye looks.
- **Phone:** `PHN_Phone` (real size 74 x 9 x 150 mm, screen faces its local -Y, long axis +Z) with its UI objects `PHN_Phone_Screen`, `PHN_UI_*` (the typed-text objects `PHN_UI_Typed_01..24` are all visible by default; they get visibility keys in the chat-reveal action of phase 2). It is parented to `HUM_PhoneSocket`, an empty on the bone `DEF-hand.R` (back of the phone on the palm, long axis along the fingers). Hide or unparent it when not needed.

## Car: `CAR_Exterior` (root) + `CAR_*` parts, control `CAR_ctrl`
- **Pivots:** root at the origin, no rotation, wheels touch z = 0, front = -Y, driver side (left, steering wheel) = +X. Wheel hubs are the object origins (spin about local X, `rotation_mode` XYZ, **+X rotation = rolling forward**), wheel radius 0.335 m. `CAR_SteeringWheel` is `ZYX` Euler: its own axis is Z. `CAR_Door_L` (+X) and `CAR_Door_R` (-X) hinge at their origins and rotate about local Z (L negative, R positive, limit 0..65 deg; the old `DoorSwing` limit constraints and the L door's `StickToAnchor` stay). 19.7K triangles (seats use subdivision).
- **Controls = custom properties of the empty `CAR_ctrl`** (`ctrl["distance"]`, floats), drivers do the rest:

| property | range | effect |
|---|---|---|
| `distance` | m | wheel angle = (distance + speed * frame / 24) / 0.335 on all four wheels |
| `speed` | m/s | automatic rolling: adds `speed * frame / 24` to the distance (leave 0 when `distance` is keyed from a path) |
| `steer` | -1..1 | + = right; steering wheel +-450 deg, front wheels +-28 deg (about the local Z of the wheel parent) |
| `door_L`, `door_R` | 0..1 | door angle 0..65 deg (linear; the easing is in the actions) |

- **Actions:** `CAR_wheel_spin` (12 loop = exactly one revolution, 30 deg/frame, `distance` counts up through a Cycles `REPEAT_OFFSET`; change the speed by scaling the NLA strip; above 36 deg/frame the 5 spokes alias), `CAR_steering_sway` (96 loop), `CAR_steering_turn_left/right` (24, ends at 0.6), `CAR_door_open_L/R`, `CAR_door_close_L/R` (24, eased).
- Not in phase 1: drive path, body sway, monitor on/off, self-drive start.


## Phase 2 additions (2026-10-14)
### Human: walking, phone, seated
- **Locomotion** (absolute full-body actions, legs in IK mode: `thigh_parent.L/R["IK_FK"]` = 0 inside them, keyed): `HUM_stand_idle` (96 loop), `HUM_walk_cycle` (24 loop, in place: the scene moves him **1.2 m per cycle**, i.e. 0.05 m per frame; planted-foot drift 0.01 cm), `HUM_stand_to_walk` (12, ends exactly at walk phase 0 = frame 1 of the cycle), `HUM_walk_to_stand` (12, starts at phase 0), `HUM_stop_from_walk` (18), `HUM_walk_out_building` (72, accelerates, **root motion on the `root` bone** along -Y). Walking and standing use a symmetric stance (the scan's own stance is not symmetric: ankles 3 cm outside the hip joints, both feet toe out 6 deg). The Rigify IK controls (`foot_ik.*`, `toe_ik.*`, `hand_ik.*`) are keyed in these actions.
- **Phone in hand:** the arm is **FK** (`upper_arm_parent.R["IK_FK"] = 1`). The phone sits on the bone **`phone_hold.R`** (child of `DEF-hand.R`, collection "Phone"); `HUM_PhoneSocket` hangs on it. Pose the phone in the hand by moving/rotating that bone. The creator's hand-edited pose is `HUM_pose_stand_phone` (single-frame pose asset; source data `lab/animation-build/scripts/phone_hold_pose.json`). Actions built on it: `HUM_phone_raise` (20), `HUM_phone_hold_read` (96 loop), `HUM_phone_type` (48 loop), `HUM_phone_lower_pocket` (30), `HUM_phone_show_claude` (24, ends with the screen turned to the driver), `HUM_walk_texting` (24 loop). The phone is 0.40 m from his eyes with the screen about 26 deg off his eye line (the creator's pose).
- **Phone object properties** (custom properties of `PHN_Phone`, all float): `phone_visible` (0/1, hides the whole phone), `chat_greeting` (1 before typing), `chat_typed` (0..24 characters), `chat_sent` (0/1), `chat_reply` (0/1), `screen_glow` (0..1.5). Drivers set the UI objects' visibility. `PHN_chat_reveal` (120 frames: greeting to frame 9, typing from 12 at one character per 2 frames, send at 66, reply at 102; constant interpolation) and `PHN_screen_glow` (12 frames) are actions on `PHN_Phone`. The scene's own message length differs: key `chat_typed` yourself for other texts.
- **Seated** (absolute, legs and arms FK, hips about 0.52 m, hands on the thighs; seat height 0.45 m): `HUM_pass_hands_lap` (96 loop), `HUM_pass_turn_to_claude` (24, ends turned to his left), `HUM_pass_look_out_window` (120 loop, looks out of his right window), `HUM_pass_lean_forward` (20), `HUM_talk_hand_gesture_a` (36 loop, right hand). `HUM_pose_seated` is the matching single pose.

### Claude: reaching, sliding, driving
- **Reach:** `arm_aim_L/R` (0..1) make the arm aim at the bone `aim_L/R` and stretch toward it (Stretch To, no volume change, **limit 2.3x its length**, he never gets thinner). Beyond the limit use `scripts/claude_reach.py: plan_reach()` (pure python): it says `stretch`, `turn` (turn/lean the body and use one hand) or `magic` (phase 3).
- **Sliding:** each arm's pivot slides on its side wall (`arm_y_L/R` -0.09..0.09, `arm_z_L/R` -0.10..0.15 m) and each leg slides under the body (`leg_x_1..4` +-0.12, `leg_y_1..4` +-0.10 m). Sliding combines with aim.
- **Hands on the wheel:** `aim_follow_L/R` = 1 makes the aim bones stick to the car's grips `CAR_WheelGrip_R` (for `arm_L`, -X side) and `CAR_WheelGrip_L` (for `arm_R`); the constraints exist only while the car is in the file. **Convention: `RIG_Claude`'s origin sits at the driver seat, car space (0.42, -0.19, 0.81).** The grips hang on `CAR_WheelGripPivot`, a child of the steering wheel that turns only 15 percent as far as the wheel (hand-over-hand cheat), at +-0.133 m from the wheel centre.
- **Actions:** `CLA_drive_hold_wheel` (96 loop, plays with `CAR_steering_sway`), `CLA_drive_steer_left` / `_right` (24, play with `CAR_steering_turn_left/right`, lean into the turn, eyes follow), `CLA_drive_hands_off` (18, arms release and open), `CLA_talk_arm_wiggle` (36 loop). Checked in play: hand-to-grip error 0.0 cm, stretch at most 2.25x.
- All still on the `ctrl` properties (floats). **After changing the car's `steer` from a script, `update_tag()` the car objects too** (`CAR_ctrl`, `CAR_SteeringWheel`, `CAR_WheelGripPivot`), otherwise the grips lag one evaluation.

### Car additions
- `CAR_WheelGripPivot`, `CAR_WheelGrip_L` (+X), `CAR_WheelGrip_R` (-X) on the steering wheel (see above).

## Phase 3 additions (2026-10-14)
### Claude: movement, root controls, cushion
- **New `ctrl` properties (floats):** `leg_len_1..4` (0.2..2.2, leg length), `leg_rot_1..4` (+-60 deg, swing about the hip, + = foot forward), `leg_y_n` now +-0.14; `arm_len_L/R` (1..2.3, 0.5 minimum, arm length, driven onto the arm bone, never thinner); `hop` (root height in m), `jump_t` (0..1, root travels to the cushion's resting place), `move_x` / `move_y` (root travel in m, +Y = backwards), `yaw` (whole-body turn about the vertical axis in deg, **+ = turns toward his own right, i.e. -X while he faces -Y**), `cus_*` (below).
- **Walk and run (in place, the scene moves the rig):** `CLA_walk_cycle` (24 loop, **0.40 m per cycle**, trot with legs 1+4 against 2+3), `CLA_run_cycle` (16 loop, **0.571 m per cycle**, with a flight phase), `CLA_idle_to_walk` and `CLA_walk_to_idle` (10 each; the first frame of the cycle is the end pose / start pose). Planted-foot drift 0.0 / 0.002 cm, feet never below the ground (`stills/claude_locomotion_checks.json`). `CLA_pickup_arrival` (72) travels itself: `move_y` runs him 1.46 m toward -Y, he brakes and turns 90 deg with `yaw`.
- **Cushion:** `CUS_Cushion` (collection `CUSHION`, child of `RIG_Claude`, driven by `ctrl`): `cus_show` (default **0**: shrunk to nothing; every cushion action keys 1), `cus_held` (1 = hugged upright in front of him), `cus_toss` (0..1: flies to `cus_dx/cus_dy/cus_dz`, default (-0.9, 0, 0.78), rig-local, `cus_dz` = height of the cushion's origin), `cus_arc` (extra height during the throw), `cus_tumble` (deg), `cus_squash` (manual squash). Resting on the ground (cushion bottom at z = 0) the cushion is 0.215 m high: **while he stands or sits on it, the root height is `hop` = 0.215** (the actions include that). The Squash shape key follows how deep his feet sink in (root height against the cushion top). `CLA_cushion_throw_and_jump` ends with the root at `cus_dz + 0.116` (checked: exactly on the cushion top, squash back at 0).
- **Cushion actions:** `CLA_cushion_jump` (60 loop), `CLA_cushion_run_carry` (16 loop), `CLA_cushion_hold_to_throw` (18), `CLA_cushion_throw_and_jump` (72), `CLA_cushion_sit` / `_sleep` / `_happy_stand` (96 loops), `CLA_stand_to_cushion_sit` (24).
- **Reactions:** `CLA_react_proud_puff` (24), `CLA_react_oops` (20), `CLA_react_giggle` (24 loop).
- **Layering:** a property that no active strip keys keeps its **last value** (an NLA `COMBINE`/`REPLACE` only touches keyed channels). When switching actions, put the properties back to their defaults (for example `cus_show = 0`); see `14_contract_test.py`.

### Magic: `MAG_Root` and the ring (collection `MAGIC`)
- `MAG_Root` (empty, child of `RIG_Claude`, at rig-local (0, -0.30, 0.38) = in front of his hands, **its -Y axis is the shot direction**) carries the float properties `fade` (0..1 visibility, drives the material's FADE node), `shot` (0..1, ring position along -Y), `dist` (m to the target, default 1.2), `size`, `wrap` (0..1) and `wrap_to` (scale at wrap = 1, default 0.7), `spin_rate`, `puff` (smoke puffs 0..1), `sparkle` (sparkle orbit 0..1). Children: `MAG_Ring` (+ `_Main`, `_Inner`, `_Wisp`), `MAG_Puff_1..3`, `MAG_Orbit` + `MAG_Sparkles`; materials `MAG_MAT_Magic` / `MAG_MAT_MagicSmoke`; the objects cast no shadows.
- **Aim:** `scripts/magic_lib.py: aim_magic(target_rig_local)` turns `MAG_Root` toward the target and sets `dist` (it needs `update_tag()` on the `MAG_*` objects, done inside). `plan_reach()` returns `mode = "magic"` for a target beyond the 2.3x reach and body turn: play `CLA_magic_cast` and the ring actions then.
- **Actions** (on `MAG_Root`): `MAG_ring_shoot` (24), `MAG_ring_wrap` (30, starts where shoot ends: shot = 1, fade = 1), `MAG_ring_fade` (18, starts where wrap ends). Recipe (the sequence in `claude_magic_f21.png`): `CLA_magic_cast` strip at 1, `MAG_ring_shoot` at 8, `MAG_ring_wrap` at 31, `MAG_ring_fade` at 61. `CLA_magic_cast` (24): wind-up, both arms push forward (1.6x), body leans in.

### Car: self-drive
- **New property** `CAR_ctrl["dash_glow"]` (0..1): brightens the dash screen, the monitor and the accent strip (drivers on the materials' emission strength). `CAR_self_drive_start` (48) keys `dash_glow` 0 to 1, a steering pulse (`steer` +-0.07, back to 0) and `distance` from rest to 1.0 m (2 m/s at the end). Do not also key `speed` over the same frames (it adds to `distance`); continue the roll with `speed = 2` afterwards. The drive path is the scene's job.

### Human: reactions and transitions
- **Seated reactions** (absolute, on the creator's seated pose, so play them as the base strip, not `COMBINE` over another `HUM_pass_*`): `HUM_react_startle` (16), `HUM_react_laugh` (36), `HUM_react_impressed` (30), `HUM_react_shake_head` (18). Body language only (no face, no brows). They return to the seated pose (end minus start 0 except startle: 0.06 deg).
- **`HUM_phone_to_seat_idle`** (36): the phone arm eases from `HUM_pose_stand_phone`'s pose into the seated hands (ends within 1 cm of `HUM_pose_seated`). `PHN_phone_pocket` (36, on `PHN_Phone`) sets `phone_visible` 1 to 0 at frame 30 (constant).
- **Car transitions** (absolute, in the **seat frame**: the rig origin is where `HUM_pose_seated` has him; passenger door on his right = **-X**): `HUM_stand_to_sit_car` (72): starts standing beside the door at pelvis (-0.80, -0.05) facing +X, ducks, right foot then left foot step in, he turns to face -Y and sits; ends on `HUM_pose_seated` (0.7 cm). `HUM_sit_to_stand_car` (72): the same plan backwards with a deeper duck. Legs are IK (keyed) until the last 8 frames, which crossfade `thigh_parent.L/R["IK_FK"]` to 1 (the seated FK legs). Checked: planted ankle drift 0.01 cm, hip-to-ankle at most 0.792 m (leg 0.818). **Not fitted to the real door and seat geometry**: place the rig so the step-in lands on the car's floor and key `CAR_ctrl["door_R"]` open with `CAR_door_open_R`.

### Rebuild order (scripts)
`04_claude_rig.py` deletes every object owned by `anim_owner = claude` (Claude parts, cushion, magic): after it run `42_cushion_rig.py` and `45_magic_rig.py`. Actions: `40_`, `43_`, `46_`, `50_` (Claude), `51_`, `52_` (human), checks `41_`, `44_`, `47_`, `53_`. `04` reads the lineup copies at frame 1 with the source chain unhidden (their world matrices are stale otherwise).

## Integration notes for the realistic scene (see the report for the full change list)
- The new car uses the same object names the scene scripts already know (`CAR_Exterior`, `CAR_Wheel_front-left`, `CAR_SteeringWheel`, `CAR_Door_L`...), but the wheel and steering rotations are now **driven**: key `CAR_ctrl["distance"]` and `["steer"]` instead of the wheel/steering objects.
- The human has the Rigify FK names the scene scripts expect (`spine_fk.001-.003`, `neck`, `head`) but no face keys (`Blink`, `MouthOpen`, emotions).
- Claude is an armature now: key the `ctrl` properties (or use the actions) instead of moving `CHAR_Claude`, the eyes and the arms as objects.
