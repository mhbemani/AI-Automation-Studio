# human-rig: a rigged, layered low-poly human built from scratch

## 1. Verdict

**Works.** The new character replaces the old faceted scan in a copy of the realistic car scene.

- **Built from scratch, in layers:** a hidden body, head, eyes, hair, hands, hoodie, hood, pants and shoes, all skinned to one Rigify rig. The rig has finger bones and face bones.
- **The scene contract is kept:** the control names, `DEF-hand.R` for the phone, and the shape-key names are the same. The contract changes are small, listed in section 7, and patched in this lab's own copies of the scene scripts.
- **The clothing does what the brief asks:**
  - the collar and hood stay still when the head turns ±70°;
  - the sleeves and pants bend cleanly at the joints;
  - the hem rides up and the sleeves slide up when the arms rise;
  - the pants cuffs stretch at the bent ankle.
- **The result:**
  - 6,002 tris;
  - the same draft render time as the diet scene;
  - 0 visible skin pixels through the clothes in 15 of 18 stress poses;
  - an IK walk with about 6 mm of foot slide per step.

**Weak spots:** chunky fingertips in the phone close-up, faint subtle emotions at small sizes, and a few known poke-through specks (section 5).

## 2. How I did it (reproducible)

Lab folder: `lab/human-rig/`. Commands and the build order are in `lab/human-rig/README.md`. Commits are on branch `<task branch>`, one per milestone.

### 2.1 Approach

- **Parametric lofting.** Each part is a script that lofts cross-section rings along the Rigify bones, so the joint loops sit where the bones bend.
  - Torso and legs are one watertight underlay. The arms grow out of holes cut in the torso, and the legs out of half-rings plus a crotch vertex.
  - The head is a 17 × 26 parametric grid. Gaussian "feature bumps" shape it, and the mouth slit and eye holes are part of its topology.
  - Hands, hoodie and pants use the same ring loft.
  - Shapes were tuned by looking at a snapshot after every step. Nothing was hand-modelled outside the scripts, so every result is in a script.
- **Skeleton.** Rigify's human metarig, scaled to 1.75 m and put in an A-pose. Its face is replaced by 20 simple deforming face bones (`basic.super_copy`). The thumbs are opened 28° so they don't lie flat along the palm.
- **Weights.**
  - The body, hoodie and pants share one *geometric* weight function (`_weights.py`). Each vertex is projected onto the spine, arm and leg bone chains. Hinge joints blend narrowly and twist joints widely. Special rules cover the shoulders, the hips (gluteal fold) and the crotch, which both legs share.
  - The head, hands and shoes have weights written by script.
  - **The hoodie's weights stop at the chest bone (`DEF-spine.003`).** No hoodie or hood vertex can follow the neck or head.
- **Layer fit.** The garments are pushed outward to a minimum clearance. Then the hidden underlay is pulled inside every garment (12 mm, 34 mm at the hip creases and shoulders). That's what removes the skin slivers between the coarse faces.
- **Correctives (no cloth simulation).**
  - Corrective Smooth on the body, hoodie and pants.
  - Shape keys `CR_hem_up_L/R` and `CR_sleeve_up_L/R` on the hoodie. They are driven by the elbow-to-hip distance, through a simple expression (no Python auto-run). That works for both FK and IK arms.

### 2.2 Milestones

| # | Content | Stills (`lab/human-rig/stills/`) |
|---|---|---|
| 0 | Reference extraction (measurements, palette, sheet, silhouette masks) | `../reference/old_sheet.png` |
| 1 | Rig + body underlay; arm raise, knee flex, spine twist | `M1_*` |
| 2 | Head, eyes, hair, face bones, 9 keys; emotion sheets at two sizes | `M2_*` |
| 3 | Hands, finger presets, phone grip | `M3_*` |
| 4 | Body weights (before/after the automatic weights) | `M4_*` |
| 5 | Shoes | `M5_*` |
| 6 | Hoodie + hood; collar test with head turns | `M6_*` |
| 7 | Pants | `M7_*` |
| 8 | Stress pass, visible-skin metric, correctives | `M8_*` |
| 9 | Action library, walk sliding | `M9_*` |
| 10 | Integration test, renders, polycount, IoU, before/after | `M10_*` |

- **Rebuild from nothing:** `scripts/build_all.py` in an empty saved file. I tested this on 2026-10-09: every count and measurement came out identical.
- **Integration:**
  ```bash
  Blender -b lab/scene-realistic-car/scene.blend --python lab/human-rig/scripts/integrate_test.py
  ```
  The source scene's md5 was checked before and after every headless run, and it was unchanged.

## 3. How the look was carried over

- **What I took from the old human:**
  - the palette, as its exact linear colours: hoodie `#34858d`, skin `#e6c4ac`, hair `#5a4c41`, joggers `#515565`, shoes `#f1f1ed`;
  - its proportions: 1.75 m tall, neck at about 1.47 m, shoulders at about 1.40 m, knee at 0.48 m;
  - its silhouette elements: a loose hoodie with a big hood, drawstrings, joggers with cuffs, white low-tops, short dark hair, and the faceted flat shading.

  The old human's geometry was not reused.
- **Silhouette IoU.** I rendered orthographic masks of the old and new street human in the scene, with the same cameras (`stills/M10_silhouette_iou.png` and `.json`):

  | View | Raw IoU | Centroid-aligned | New area / old |
  |---|---|---|---|
  | front | 0.60 | 0.60 | 0.96 |
  | side | 0.43 | 0.72 | 0.83 |
  | back | 0.60 | 0.60 | 0.96 |
  | 3/4 | 0.56 | 0.59 | 0.95 |

  The side view's low raw number is placement, not shape: the old rig's origin sat about 10 cm in front of its body.
- **Deliberate deviations:**
  - He texts one-handed: the left arm hangs and the phone is in the right hand. The old scan held the phone with both hands.
  - He stands with a normal stance; the scan's feet were wide apart.
  - The hoodie is slightly slimmer and less crumpled, a clean faceted shell instead of scan noise.
  - There's a separate, smaller hood and a kangaroo pocket.
  - The face has real eye openings, lids, lips and a mouth interior instead of stickers.

  Side by side: `stills/M10_reference_old_top_new_bottom.png`.

## 4. Skeleton and naming map

**Rig size:** `LIB_Human` has 461 bones (Rigify controls, MCH and ORG bones), 90 of them deforming.

**Deforming bones:**

| Region | DEF bones |
|---|---|
| Spine and neck | `spine`, `spine.001`–`.003` (spine), `spine.004`/`.005` (neck), `spine.006` (head) |
| Each side | `pelvis`, `shoulder`, `upper_arm` + `.001` (twist), `forearm` + `.001` (twist), `hand`, `palm.01–.04` |
| Fingers | 3 bones each for `thumb`, `f_index`, `f_middle`, `f_ring`, `f_pinky` |
| Legs | `thigh` + `.001`, `shin` + `.001`, `foot`, `toe` |
| Face | `jaw`, `lip.T`, `lip.B`, `lips.L/R`, `eye.L/R`, `lid.T/B.L/R`, `brow.L/R.001–.003`, `cheek.L/R` |

**Controls the scene drives keep their exact names:** `torso`, `spine_fk…003`, `neck`, `head`, `shoulder.*`, `upper_arm_fk`/`forearm_fk`/`hand_fk.*`, `thigh_fk`/`shin_fk`/`foot_fk.*`, `*_parent` with `IK_FK`, `DEF-hand.R`.

**Axis conventions are unchanged:** +X nods/bends, Y turns, upper_arm Z raises.

**New controls:** IK limbs (`hand_ik`, `foot_ik`, poles), toe controls, `f_*.01_master` finger curls, and the face controls.

## 5. Triangles, stress poses and poke-through

**Triangles** (`lab/tools/polycount.py` agrees: `human_street` 6,002):

| Part | Tris | Target |
|---|---|---|
| Body underlay | 890 | 1,500–2,000 (more wasn't needed; it's hidden) |
| Head (with brows, lips, mouth bag, teeth, ears) | 1,014 | about 1,000 |
| Eyes | 2 × 140 | a few hundred |
| Hair | 390 | a few hundred |
| Hands | 2 × 426 | 400–600 each |
| Hoodie (with pocket and drawstrings) | 1,092 | about 2,000 |
| Hood | 236 | |
| Pants | 856 | about 1,200 |
| Shoes | 2 × 196 | about 300 each |
| **Total** | **6,002** | 6–9K (old: 3,610) |

In the scene, the average in-camera total drops from 146.9K to 137.4K tris. The difference is mostly animation visibility and city props, not the human.

**Stress poses** (`stills/M8_stress_sheet.png`): arms high, elbows at 120°, shoulder rotation, arms back and forward, head ±70°, neck tilt both ways, spine twist, seated, crouch, 90° knee lift, ankle up and down, fist, relaxed fingers, texting. Nothing collapses or breaks.

**Poke-through, as visible skin pixels** (`scripts/visible_check.py`). The covered skin is rendered red and everything else black, from 7 orthographic views at about 5 mm per pixel:

| Result | Poses |
|---|---|
| 0 px | 15 of 18 poses, including **seated**, the pose the car uses |
| 2 px | arms up high (armpit) |
| 5 px | texting (back of the armpit) |
| 13 px | 90° knee lift (hip crease, one side view; not used by the scene) |

The older raycast and face-overlap counts are in `stills/M8_numbers.json`. They overstate the problem, because most crossings sit inside folds no camera can see.

## 6. What the clothing does (before/after)

`stills/M10_before_after_clothing.jpg` shows the old and new street human with the same control values, from the front-3/4 and the side.

| Test | Old scan | New character |
|---|---|---|
| Head turn 70° | The head barely turns, and the whole upper body is one surface | The head turns inside a collar that stays still (`M6_collar_head_turns.png`) |
| Arm raise | Barely moves the arm | The sleeve follows; the shoulder deforms cleanly; with the arms high the hem rises up to 5 cm and the cuffs slide 3.5 cm up the forearm (`M8_correctives_hem_sleeve.png`) |
| Knee lift | The pants tear apart at the knee | Clean bend |
| Ankle bend | — | The pants cuff stretches over the joint while the leg above stays still (`M7_pants_stress.png`) |

## 7. Action library and integration

**Actions** (with fake users; the single-frame poses are pose-library assets):

| Kind | Actions |
|---|---|
| Idle loops | `HUM_SeatedIdle` (96 frames), `HUM_StandTexting` (96 frames) |
| Walk | `HUM_Walk` (24 frames, in place, 1.6 m per cycle = 1.6 m/s at 24 fps, IK feet) |
| Talking loops (48 frames) | `HUM_Talk_Explain`, `HUM_Talk_BothHands`, `HUM_Talk_Point` |
| Head looks | `HUM_Look_Left/Right/Up/Down` |
| Finger presets | `HUM_Hand_Open/Relaxed/Fist/Point/Phone/Typing` |
| Emotions | `HUM_Emo_<emotion>` (body language) and `HUM_EmoFace_<emotion>` (face keys), for all 8 emotions |

**Walk foot sliding** (`scripts/measure_walk.py`), measured on the shoe mesh while the object moves at 1.6 m/s over two cycles:

| Measure | Result |
|---|---|
| Mean slide while in contact | 0.29 mm per frame |
| Largest slide in one frame | 2.1 mm |
| Heels | 1.4 mm in total |
| Balls of the feet | 11–12.5 mm in total (about 6 mm per step) |
| Lowest point of the sole | 3 mm below the ground |

**Integration test** (`scene_test.blend`, a copy):

- **Worked unchanged:** the scene's `build_phone.py`, `build_cameras.py` (it reads the new eye positions), the 17 shot markers, and the timeline-driven sections of `animate.py` for car, Claude, camera drift and visibility. The seated head motion (`HEMO`) needed no change, because the control names are Rigify's.
- **Needed changes** (patched copies in `lab/human-rig/integration/`, listed in the README):

  | Change | Detail |
  |---|---|
  | Part names | `_Body` instead of `_Mesh`; face keys on `_Head` |
  | Per-character copies | `_Head` and `_Hoodie` meshes, with the hoodie drivers re-pointed |
  | A-pose rest | Poses re-tuned: seated legs solved onto the car floor (about 3 cm residual), hands onto the thighs |
  | Phone | Placed by a grip offset in `DEF-hand.R` |
  | Walk | From `HUM_Walk`/`HUM_StandTexting` (4.04 m in 60 frames, 1.62 m/s); height at the sidewalk (z 0.15) |
  | Face | A new block keys the seated human's face: 29 emotion keys, a speech-driven `MouthOpen`, 20 blinks |

- **Phone fix found here:** the first phone close-up showed the fingers wrapping over the screen. The grip was reworked: fingers on the left edge, the thumb at the lower right, the phone held lower. Now the chat UI and the typed text are fully readable.
- **Still to change in the scene:** `animate.py` walks him to the old **rear**-right door (`P1`). Since he now sits in front, it should be the front-right door.
- **Stills:** `stills/M10_old_vs_new.jpg` shows `CAM_EST_Street` f40 and f300, `CAM_PHONE_CU` f160, `CAM_INT_TwoShot` f600, `CAM_CLAUDE_POV` f450 and `CAM_HUMAN_POV` f700. The old images come from the source scene, which is static (not animated); the new ones from the animated copy.

## 8. Render time and memory

Apple M2, 8 GB, Blender 4.5.3 LTS. Headless `measure_renders.py` at 960×540, 16 samples, with the GUI Blender open.

| Shot | Old | New |
|---|---|---|
| EST f40 | 0.80 s | 0.98 s |
| EST f300 | 0.98 s | 1.04 s |
| PHONE_CU f160 | 0.48 s | 0.58 s |
| TwoShot f600 | 1.20 s | 1.24 s |
| CLAUDE_POV f450 | 1.01 s | 1.03 s |
| HUMAN_POV f700 | 1.08 s | 1.13 s |

- **Time:** 0.48–1.24 s per draft frame, within the diet scene's 0.48–1.30 s.
- **Memory:** peak footprint (`/usr/bin/time -l`) 2.22 GB new vs 2.12 GB old; resident memory 0.99 vs 1.11 GB.
- **Files:** `human.blend` is 7.0 MB.

## 9. Honest flaws

- **Fingers:** they're tubes pushed into the palm, not welded. Fingertips look chunky in the phone close-up.
- **Faceted head:** the lips read a little blocky at close range.
- **Emotions at small sizes:**
  - At about 70 px faces (two-shot), happy, excited and surprised read; curious, thoughtful, proud and amused are faint. You chose to keep the strengths.
  - At the 155 px full figure of the opening shot, the face doesn't read at all, so the body language has to carry it.
- **Gestures and walk:**
  - The talking gestures lift the hands to about chin and chest height, a bit high.
  - The walk is a brisk "game walk" with slightly bent knees, because 1.6 m per cycle is a long stride for this leg length.
  - The gestures aren't wired into `animate.py` yet.
- **Body underlay:** coarse (890 tris) and pulled inside the cloth, so it's only suitable as a hidden layer.
- **Hood:** a simple swept shape with no visible opening or inside.
- **Poke-through specks:** a few remain (section 5).
- **Copying the character:** the corrective drivers point at `LIB_Human`, so every character copy needs the mesh copy and re-pointing that the patched `build_characters.py` does.
- **Rigify:** the add-on is enabled in your Blender preferences. It's only needed to regenerate the rig; the generated rig plays without it. You can turn it off under Preferences > Add-ons.

## 10. What I couldn't verify

- Motion in real time: I saw stills and sampled frames only, never a playback.
- The lip sync against the actual audio: `MouthOpen` follows the envelope numerically, but I didn't watch it with sound.
- 1080p and 9:16 renders, and a full-sequence render.
- How the seated legs look in the footwell (hidden in all shots).
- How the street shot looks when he walks to the corrected front door.

## 11. Recommendations

1. In the scene:
   - adopt the patched `build_characters.py` and `animate.py`;
   - move `P1` to the front-right door, and add a "get in" beat or keep the cut.
2. Wire the talking loops into `animate.py`, driven by the human's lines (`HUM_Talk_*` blended on the arms while he speaks).
3. More fidelity, in order of payoff:
   - welded fingers with one more ring per joint, and a slightly denser hand (about 700 tris);
   - a 30-column head with a mouth corner loop, so emotions read at small sizes;
   - smooth shading with sharp edges on the clothes;
   - a hood opening.
4. Add a second corrective pair for the pants (knee and hip crease), driven like the hoodie's. It would clear the last 13 px in the 90° knee lift.
