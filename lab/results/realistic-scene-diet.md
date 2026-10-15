# realistic-car-scene, polygon diet (round 2)

## 1. Verdict

**Works: every budget in `DIET_SPEC.md` is met**, with the same scene system (object names, pivots, parents, cameras, markers, the timeline v2, bone names). The cost is a **visible quality step down**, mainly on the human (see section 6).

| Measure | Heavy v1 | After the diet | Budget |
|---|---|---|---|
| Everything in frame, average | 836,551 tris | **152,730** | — |
| City in camera, average | 589,529 | **134,524** | ≤300K |
| City in camera, maximum | 1,580K | **315,498** | ≤600K |
| Total footprint at 1080p | 4.2 GB | **2.48 GB** | ≤2.5 GB |
| 1080p frame time | 2.8–5.2 s | **2.0–4.1 s** | — |

The 1080p numbers are the `/usr/bin/time` total peak including GPU buffers, measured with the GUI Blender open.

## 2. What I did

Branch `<task branch>`. The heavy file is archived as `backups/scene_v1_heavy_not_renderable.blend`.

- **Assets.** Downloaded through the creator's logged-in BlenderKit add-on (the add-on's own import stalls, so the files are copied from `~/blenderkit_data/models`). All three are free, BlenderKit Royalty Free: usable in modified, monetised videos, not redistributable. Credits are in `ASSETS.md`.
  - Hero car: "Low poly plymouth car" (Rohit Gupta).
  - Parked cars: "Low Poly JDM Sports Car (Skyline)" (Sachin H).
  - Human: "Lowpoly Male Standing" (Hyperreality Lowpoly).
  - **The listings count faces, not triangles.** The Plymouth is 31.3K tris once mirrored (listed as 7,545); the JDM is 7,606 tris (listed as 3,803).
- **A, hero car (`import_assets.py` + `build_car.py`).**
  - Imported once as `LIB_Hero_*` and scaled 1.06; mirror and "smooth by angle" applied.
  - The four wheels are split out **by face**: inside the wheel circle, on the outer side, not paint. Pivots sit at the wheel centres. Each wheel is decimated to 12% (about 390 tris).
  - The grille (1,845 faces) is split off and decimated to 12%. The rest of the body gets a **planar dissolve at 11°**, which only merges flat faces, so the shape is unchanged.
  - The paint is recoloured to the creator's yellow; the black vinyl roof stays.
  - Seven window materials become glass (`.067`–`.069`/`.042` are the side windows). Back faces of the paint and roof show a beige headliner.
  - Interior rebuilt for the measured cabin (floor z 0.255, roof inside z 1.32, windshield y −0.93 to −0.35) with 1–2 bevel segments.
  - Totals: **exterior 7,263 + interior 3,820 = 11,083 tris**. Contract names are kept; for `animate.py`, `WHEEL_R` is 0.343 and `WHEELBASE` 2.92.
- **B, parked cars.** 5 linked duplicates of one mesh (`LIB_JDM`), each with an object-level paint copy.
  - Smoothing uses **shading only**: smooth faces, sharp edges only above 60°, weighted normals (face area, keep sharp).
  - **4,413 verts / 3,803 faces before and after**, asserted in the script.
  - A first try with sharp edges at 35° looked *more* faceted than the shipped asset, so 60° it is.
  - Still: `stills/DIET_parked_car_smoothing_before_after.jpg`.
- **C, human (`scripts/human_lib.py`, called by `import_assets.py`).**
  - The scan is scaled to 1.75 m.
  - **A lean FK rig with the Rigify control names the scripts use:** `torso`, `spine_fk…003`, `neck`, `head`, `shoulder.*`, `upper_arm_fk`/`forearm_fk`/`hand_fk`, `thigh_fk`/`shin_fk`/`foot_fk`, the `*_parent` bones with `IK_FK`, and `DEF-hand.R` for the phone. Same axis conventions as Oscar.
  - **The rest pose is the scan's phone pose**, so the pose values in `build_characters.py` were re-tuned (the seated arms by a small search).
  - Skinned with automatic weights (1,499/1,499 vertices).
  - Materials by region: skin, hair, hoodie, joggers, shoes. Palette option 1 (teal hoodie, navy joggers, white sneakers) is recommended and used; option 2 (rust/grey) is in `stills/DIET_human_palettes.jpg`.
  - Face parts: 8×6 eyeballs with an iris disc, brows, a mouth and upper lids, bone-parented to `head`.
  - **Shape keys:** happy, curious, excited, surprised, thoughtful, proud, amused, MouthOpen and Blink (basis = neutral).
  - **Whole character: 3,230 tris.**
- **D, the rest.**
  - **Claude:** superellipsoid resolution cut from 32×20 to 24×14 on the body, 10–12×6–8 on the parts: 13,376 → **1,656 tris**, same look.
  - **City:** props were about 80% of the triangles. Hydrant 10.4K → about 1K, bench 8.7K → about 1K, bin 3.2K → 1K, utility box 4.4K → 1.1K, manhole 6.3K → about 160. City in camera went from 276K to 135K on average.
  - **Memory, bisected at 1080p:**
    - 2K textures were the main driver (−0.51 GB at 1K);
    - the shadow pool was next (−0.27 GB at 256 MB; shadows off saved 0.43 GB);
    - ray tracing −0.11, the HDRI −0.09, the lamps' 63 point lights 0.
    - Fix: local 1K copies of the six 2K texture sets (made with `sips`, no download), plus a 256 MB shadow pool.

## 3. Output

- `lab/scene-realistic-car/scene.blend` (not in git), copied to the base checkout. `backups/scene_v1_heavy_not_renderable.blend` is the heavy v1.
- Stills:
  - `stills/DIET_FINAL_*` (1080p, one per camera);
  - `DIET_DRAFT_9frames_lap` (960×540, all cameras plus four lap positions);
  - `DIET_parked_car_smoothing_before_after`;
  - `DIET_human_emotions` (the 8 emotions + MouthOpen + Blink);
  - `DIET_human_face2`, `DIET_human_palettes`;
  - `DIET_CONTRACT_animate_sheet`;
  - `polycount_after_diet.json` (the tool's raw output).

## 4. Measurements

`lab/tools/polycount.py`, same cameras and frames as the baseline:

| | Heavy v1 | After the diet |
|---|---|---|
| Human (whole) | 66,180 tris / 33,088 faces | **3,230 / 3,132** |
| Claude | 13,376 / 7,040 | **1,656 / 952** |
| Hero car (exterior + interior + wheels) | 205,604 / 112,221 | **11,083 / 5,951** |
| One parked car | 141,692 (11 copies) | **7,606** (5 copies of one mesh) |
| City, whole scene | 2,605,693 (573 objects) | **504,128** (567 objects) |
| In camera: city average | 589,529 (27K–1,580K) | **134,524** (29.8K–315K) |
| In camera: car / Claude / human seated / human street | 136,299 / 8,715 / 53,937 / 43,048 | **8,755 / 1,189 / 2,692 / 1,848** |
| **In camera: everything, average (max)** | **836,551 (1,805,187)** | **152,730 (331,084)** |

Per camera (city / total average): EST 480K/840K → **101K/126K**; PHONE 27K/100K → 72K/82K; HUMAN_POV 1,271K/1,516K → **250K/268K**; CLAUDE_POV 165K/419K → **57K/74K**. The phone shot's city count rose because the close-up now looks down at more paving and props. It's an upper bound (no occlusion), the same as the baseline.

Render: headless `blender -b`, `scripts/measure_renders.py`, warm-up frame discarded, the GUI Blender **open**, same shots as before.

| | Heavy v1 | After the diet |
|---|---|---|
| Draft 960×540, 16 samples | 1.1–2.3 s/frame | **0.48–1.30 s** (EST 1.02, PHONE 0.48, interiors 1.01–1.30, 9 frames over the lap) |
| Final 1080p, 32 samples | 2.8–5.2 s | **1.98–4.09 s** (EST 3.69, PHONE 1.98, HUMAN 3.73, CLAUDE 3.63, TwoShot 4.09) |
| Blender RSS (draft / final) | 1.26 / 1.91 GB | **0.96 / 1.12 GB** |
| Total footprint incl. GPU (draft / final) | 3.8 / 4.2 GB | **2.10 / 2.48 GB** |

## 5. Contract test

The adapted `animate.py` runs on the diet scene unchanged since the heavy round:
- The visibility swap at frame 337 covers the face parts.
- The seated human's head is keyed on top of the build pose (turn about 12–15°, small nods and tilts) in action `ANIM_HumanSeated`.
- The phone UI states and the car still work; `stills/DIET_CONTRACT_animate_sheet.jpg` shows them.
- `drive_car.py` is unchanged and works on the new car.
- `verify_animation.py` is still written for timeline v1 (unchanged from round 1).

## 6. What got worse, and what I could not verify

**Worse:**
- **The human is far cruder than Oscar.** He's a faceted low-poly scan: the face is a few big triangles, the features are flat stickers (eyes, brows, mouth), there are no fingers and the hood edge shows a couple of skin-coloured triangles.
- **His expressions are readable only in close-up:** excited, surprised and mouth-open read clearly; happy, curious, thoughtful, proud and amused are subtle. The lids cover the eyes on Blink, but the iris can peek out at some angles.
- **Seated, his hands sit awkwardly at the lap**, and the light-teal hoodie reads bright under the cabin keys.
- **The hero car** is a 1970s muscle car now: no glass roof, so the cabin is darker (the beige headliner fixes most of that). Its planar-dissolved body is smooth in our shots, but I didn't check it closer than the street shot.
- **The street props** are coarse at about 1K, invisible at shot distance.
- **The 1K city textures** are slightly softer on the asphalt close to the camera.

**Not verified:**
- audio;
- motion: the expressions and the rig were checked only as stills, and the walk isn't written;
- the creator's viewport responsiveness on this Mac;
- the head-turn and tilt sign conventions of the new rig against `animate.py`'s emotion tables (the motion is small and looks plausible in stills).

## 6b. Follow-up: the human as rigid pieces (creator request, same day)

The creator saw bones sticking out of the body and a statue-like, solidly skinned character, and asked to rebuild him as separate moving parts with the same look.

- **Skeleton:** re-fitted to joints measured on the mesh (slice centroids and point clusters). Every bone sits inside the body; display is now "Stick".
- **The scan is cut into 17 rigid parts, capped and bone-parented**, in four steps: core labels, then growing over the surface, then planes through the joints, then label smoothing and fragment merging.
- **A stress pose holds:** leg lifted and knee bent, an arm raised, the head turned, the torso bent. No shards and no holes, the hood stays on the chest. (`stills/HUMAN_pieces_pose_test.jpg`)
- **Totals:** 20 parts, 3,638 tris.
- **Contract test passes:** the visibility swap and the seated head keys.
- **Poses:** the seated hands were re-searched.
- **Phone:** the screen is no longer covered by the sleeve.
- **Limits:** rigid joints show a visible seam or overlap at strong bends (knees in the seated pose). That's the usual puppet look, and acceptable for this faceted style.

## 7. Recommendation

Use the diet scene for the animation step: it fits the 8 GB Mac with headroom (2.5 GB total at 1080p).

If the creator finds the human too crude, there are two options:
1. Spend the remaining budget (about 6.8K tris) on him: a smoother head (a subdivided head region only) plus real fingers.
2. A better base character within 10K.

Either way, write the walk and getting-in for the FK rig next.

## 6c. Follow-up: head colours and face (creator request, same day)

- **Every head polygon checked.** The old head rule measured from a point 9 cm in front of the skull, so hair ran down over the cheeks and ears, hood triangles cut into the back hair, and skin triangles showed on the hood collar. The new rule (`head_fix()` in `human_lib.py`) works around the real head centre: short hair above the forehead, ears and nape, skin on the face, ears and jaw, and the upward-facing collar folds stay hoodie.
- **Face:** the eyes are now small black oval dots (1.4 × 1.9 cm) and the mouth is a short black line (3.6 cm), both in the same places as before. The brows are gone. The skin eyelids stay for `Blink`. The expressions now move only the mouth and the lids. Still: `stills/HUMAN_head_colours_face.jpg`.
