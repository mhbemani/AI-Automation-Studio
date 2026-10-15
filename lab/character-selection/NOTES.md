# character-selection: progress notes (pause 2026-10-12)

The creator changed the plan: instead of shortlisting new characters, we are rigging the static BlenderKit
"Lowpoly Male Standing" scan (the one in the scene) step by step, together, in `character_selection_lab.blend`
(git-ignored). The original scan is kept hidden in `REF_static_baseline`; the work is `HUM_Body` + `RIG_Human`
in `STEP1_rig`.

## Done (scripts in `scripts/`, stills in `stills/`)
| Step | What | Script / still |
|---|---|---|
| 1 | 19-bone body rig, automatic weights; creator re-placed the bones by hand | `build_rig.py`, `rebind.py` / `step1_*` |
| 2 | creator cut the head off at the neck and extended the neck; creator cut the palms apart; hand weights cleaned | `check_ring.py`, `fix_hand_weights.py` / `step2_*` |
| 3 | left hand replaced by a mirror of the right (later superseded) | `mirror_hand.py` / `step3_*` |
| 4 | new hands: palm + five finger tubes fitted to the scan hand, relaxed curl, mirrored | `build_hands.py` / `step4_*` |
| - | the forearm pose was made the rest pose (Edit Mode = what you see) | `apply_pose_as_rest.py` |
| 5 | creator adjusted the right fingers; fingers + thumb welded to the palm, round tips, mirrored | `weld_fingers.py` / `step5_*` |
| 6 | hands stitched to the sleeves | `connect_hands.py` / `step6_*` |
| 7 | 30 finger bones (Rigify-style names), ring-based weights; creator re-placed some joints | `add_finger_bones.py`, `finger_pose_test.py` / `step7_*`, `step8_*` |

State on 2026-10-12 00:20: mesh 1,797 verts / 3,586 tris, body + arms + hands one piece, head a separate piece;
rig 49 bones; every vertex weighted; poses (seated, arms up/down, head turn, bend/twist, finger curl/fist/point) work
(`stills/step8_body_check.jpg`, `stills/step8_finger_check.jpg`).

## Left to do (suggested order)
1. **Rebind the body to the moved bones, keeping the hand/finger weights.** The creator moved the pelvis head 89 mm,
   both ankles 45 mm (shin tail / foot head) and the hand tails; the body weights still come from the old positions.
   Needs a rebind script: automatic weights for the body, then restore the hand + finger weights.
2. **Thumb asymmetry:** `thumb.01.R` was moved (6 mm), `thumb.01.L` was not; check both thumbs.
3. **Close the hood opening** at the neck (10 open edges left from the earlier hole filling).
4. **Face:** no face bones or shape keys yet. The scene needs `MouthOpen`, `Blink` and the 8 emotions.
5. **Scene contract:** the scene's scripts drive Rigify control names (`torso`, `spine_fk...`, `neck`, `head`,
   `upper_arm_fk`/`forearm_fk`/`hand_fk.*`, `thigh_fk`/`shin_fk`/`foot_fk.*`, `DEF-hand.R`); this rig uses simple
   names (`pelvis`, `spine`, `chest`, `upper_arm.L`, ...). Either rename/map or generate a Rigify rig.
6. **Size:** the scan is 1.93 m tall; the scene's human is 1.75 m.
7. Optional: one extra ring per finger joint (the fist bends in sharp corners); materials/colours (all grey now).
8. Housekeeping: empty collection `STEP1_rig.001` (the deleted clone); `character_selection_lab_handsA_scan_curl.blend`
   is an old variant; `character_selection_lab.blend1` is Blender's automatic backup.

## Gotchas
- A file saved with the armature or the mesh in Edit Mode: headless scripts must switch to Object Mode first
  (otherwise automatic weights come out empty and poses do not evaluate).
- After editing the file headlessly, the open Blender window needs **File > Revert** (never save the old window over it).
