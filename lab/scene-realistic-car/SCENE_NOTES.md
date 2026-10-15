# Realistic car scene: setup handoff

> **Polygon diet, round 2 (2026-10-09). This section supersedes the asset, budget and measurement details further down.**
> The full report is `lab/results/realistic-scene-diet.md`; the heavy v1 is archived in `backups/scene_v1_heavy_not_renderable.blend`.
>
> **New assets** (BlenderKit Royalty Free, credits in `ASSETS.md`):
> - **Hero car:** low-poly Plymouth (`LIB_Hero_*`), yellow, 7,263 tris exterior + 3,820 interior.
> - **Parked cars:** the JDM Skyline (`LIB_JDM`), 5 linked duplicates at 7,606 tris each, smoothed by shading only (4,413 v / 3,803 f before and after).
> - **The human:** "Lowpoly Male Standing" (`scripts/human_lib.py`), 3,230 tris (3,638 after the rigid-piece rebuild below) with small black dot eyes, a small black mouth line (no brows), skin eyelids and emotion shape keys. The hair/skin/hood colour of every head polygon is set by `head_fix()` (short hair above the ears and nape, skin face/ears/jaw). It uses an FK rig with the **same Rigify control names** (`torso`, `spine_fk…003`, `neck`, `head`, `upper_arm_fk`/`forearm_fk`/`hand_fk`, `thigh_fk`/`shin_fk`/`foot_fk`, `*_parent` with `IK_FK`, `DEF-hand.R` for the phone). Its **rest pose is the scan's phone pose**, so the pose values in `build_characters.py` were re-tuned. The face shape keys are `happy`, `curious`, `excited`, `surprised`, `thoughtful`, `proud`, `amused`, `MouthOpen` and `Blink`, on `CHAR_Human*_Face` (the mesh is shared by the two human objects).
> - **Claude:** 1,656 tris (lower superellipsoid resolution).
> - **Street props:** about 1K each. The city's 2K textures are 1K copies made by `fetch_assets.py`, and the Eevee shadow pool is 256 MB.
>
> **Results** (polycount tool, same cameras and frames as before):
> - in-camera average: city 134.5K (max 315K), everything 152.7K (it was 836.6K);
> - render: draft 0.48–1.30 s and 1080p 1.98–4.09 s per frame;
> - total footprint: **2.10 GB (draft) / 2.48 GB (1080p)**, RSS 0.96 / 1.12 GB.
>
> **Rebuild order (unchanged scripts, new content):** `fetch_assets` (also makes the 1K copies) → `import_assets` (props, the human via `human_lib.py`, `LIB_Hero_*` and `LIB_JDM` once) → `build_city` → `build_car` → `drive_car` → `build_characters` → `build_phone` → `build_cameras` → `build_lighting`.
>
> **Script changes:**
> - `build_car.py`: the hero car, glass by material role, beige back faces, the lighter interior, the JDM parked cars.
> - `build_characters.py`: seat 0.40 / y 0.28, hip 0.86, the new poses, and copied bone-parent inverses (setting `.parent` in Python resets them).
> - `build_lighting.py`: headlight position and the shadow pool.
> - `build_city.py`: 1K textures.
> - `import_assets.py`: the new assets, prop decimation ratios.
>
> For `animate.py`: `WHEEL_R` 0.343 and `WHEELBASE` 2.92 for this car.
>
> **Human rebuilt as rigid pieces** (creator, 2026-10-09). The fused scan is cut into 17 rigid parts: `Mesh` (chest + hood), `Pelvis`, `Belly`, `Neck`, `Head` (whole face down to the jaw), and `UpperArm`, `Forearm`, `Hand`, `Thigh`, `Shin`, `Foot` for `.L`/`.R`. Each cut is capped, so no holes show when a joint bends, and each part is bone-parented (no skinning); the face parts ride on the head bone. The skeleton is re-fitted to joints measured on the mesh: every bone sits inside the body (the first rig had the spine on the front surface and helper bones sticking out), with thin stick display. Same bone and object names. 20 parts, 3,638 tris.
>
> **How the cutting works:**
> 1. Cores are labelled directly: the spine and head axis, tight capsules around the limb bones, the feet.
> 2. The rest grows over the surface (Dijkstra) into five chains: torso, arms and legs.
> 3. Inside each chain, planes through the elbow, wrist, knee and ankle make clean cuts; the torso is cut by height.
> 4. Labels are smoothed, and stray fragments merge into their neighbour.
>
> The seated arms were re-searched for this rig. Stills: `stills/HUMAN_pieces_pose_test.jpg` (a stress pose: no shards, no holes), `HUMAN_skeleton_inside_body.jpg`, `HUMAN_pieces_shots.jpg`.
>
> **Worse than v1:** the human is a faceted scan with sticker-like features, seated hands are awkward, and the cabin has no glass roof. See the diet report, section 6.

## Round 1 notes (milestones 0-9; assets, budgets and measurements superseded above)

**Verdict:** works, with caveats. The full scene is set up, lit and camera-ready:
- a game-style downtown ring road;
- a yellow coupe with a built interior;
- Claude re-shaded, and the human (Oscar) seated and texting;
- a chat-app phone screen;
- golden-hour lighting;
- 17 shot markers from a voiced 71.8 s timeline.

The stylised scene's `drive_car.py` runs unchanged; its `animate.py` runs after small fixes (see Contract test). Blender 4.5.3 LTS, Eevee, on an Apple M2 with 8 GB RAM.

Look agreed with the creator: stylised-realistic, "like a game / animated film", not photoreal. Assets: CC0, plus two BlenderKit Royalty Free assets (the human and the car) that the creator chose; see `ASSETS.md`.

## Decisions taken with the creator (2026-10-08/09)

| Topic | Decision |
|---|---|
| City | Generic modern mid-rise downtown |
| Time of day | Golden hour, look A: warm and friendly, not dark |
| Street | 13 m curb to curb: parking, lane, lane, parking; 4 m sidewalks |
| Look | Game-style |
| Asset policy | Hybrid: CC0, except two BlenderKit assets the creator logged in for |
| Car | BlenderKit "Vulcar Hachura" yellow coupe instead of my scripted sedan; my interior inside it |
| Seating (**big change**) | The human sits in the **front passenger seat** beside Claude, not in the back. The faces are seen directly, so **no rear-view-mirror shots** and no planar probe. The mirror stays as a plain prop. |
| Claude | Look A: rounded satin-orange block, capsule eyes with a highlight |
| Phone | Chat UI in the style of the Claude app (typing, sent bubble, reply); no real logos |
| Dialogue | `production/dialogue_v2.json`: v1 topic rewritten as natural speech, 14 lines |
| Voices | Local Kokoro TTS: Claude `af_heart`, human `am_michael`. ElevenLabs was dropped: its free plan is non-commercial and needs attribution. |

## Files

- `scene.blend` (84 MB, not in git; texture paths are relative to it, assets under `assets/`).
- Backups are in `backups/`; quick previews go to `previews/`. Both are git-ignored.
- `stills/`: committed JPGs:
  - `CITY_*`, `CAR_*`, `CHAR_*`, `PHONE_ui_states`;
  - `CAMS_16x9` and `CAMS_9x16`;
  - `LOOK_*`;
  - `FINAL_*` (1080p, 32 samples);
  - `DRAFT_9frames_lap` (960×540, 16 samples, four interior frames along the drive);
  - `LAP_claude_pov_10` (full lap, milestone 3);
  - `CONTRACT_animate_sheet` (the animated copy).
- `production/`: dialogue v2, the Kokoro + Whisper pipeline copied from the stylised scene (`run.sh`), `timeline.json`, `envelope_*.json`, `checks.txt` (all pass) and `samples.py` (candidate voices). Generated audio (`out/`, `work/`, `samples/`) and `.venv/` (209 MB) are git-ignored.

## Rebuild from scratch

1. Get the assets: `python3 scripts/fetch_assets.py` (CC0, 88.8 MB). For the two BlenderKit files, see `ASSETS.md`.
2. Start Blender: `./launch_blender.sh scene.blend`.
   - On a fresh start, first save an empty file as `scene.blend` in this folder.
   - The scripts find `assets/` and `production/` next to the .blend.
3. Run the build scripts in order, each with `python3 bridge/bl.py file scripts/<name>.py`:
   `import_assets` → `build_city` → `build_car` → `build_characters` → `build_phone` → `drive_car` → `build_cameras` → `build_lighting`.
4. Voices and timeline: `production/run.sh`.

Gotchas:
- `build_city` recreates `CITY_DrivePath`, so always re-run `drive_car` and `build_cameras` after it.
- `build_characters` must be followed by `build_phone` (the UI is parented to the phone screen) and by `build_cameras` (the cameras read the eye positions).
- `import_assets` appends the Vulcar into `00_LIB` only once. Its materials ship with fake users, which are cleared on import. Delete `LIB_Vulcar_*` to re-import.
- Every script rebuilds only the objects tagged with its `cs_owner` and skips anything with `user_locked = True`.

## Collections and objects

| Collection | Contents |
|---|---|
| `00_LIB` (excluded) | Poly Haven props: `LIB_Bench`, `LIB_TrashCan`, `LIB_Hydrant`, `LIB_UtilityBox`, `LIB_Manhole` (and an unused `LIB_StreetLamp`, a wall lantern). Oscar: `LIB_Human` (Rigify) and its meshes. The Vulcar parts: `LIB_Vulcar_*`, scaled 6%, with `LIB_Vulcar_Wheel_*` centred and decimated. |
| `01_CITY` | See the City table below. |
| `02_CAR` | `CAR_Exterior`: the root, an empty mesh, faces local −Y, carries the Follow Path constraint. Its children: the Vulcar parts (`CAR_Ext_*`, `CAR_Wheel_front-left/-right`, `CAR_Wheel_back-left/-right`, `CAR_Brake_*`) and the interior (`CAR_Int_Floor`, `CAR_Int_DoorCards`, `CAR_Dashboard`, `CAR_Seat_FL`/`FR` with `_Back`/`_Headrest`, `CAR_SteeringWheel` and `CAR_SteeringColumn`, `CAR_RearViewMirror` with `_Glass`/`_Stem`). |
| `03_CHARACTERS` | `CHAR_Claude` with `_Eye_L/R` (and `_Glint`), `_Arm_L/R` and `_Leg_1..4`. `CHAR_Human` (seated, front right) and `CHAR_Human_Street` (at the exit door), each with `_Mesh`, `_Jacket`, `_Hair`, `_Eye_l/r` and `_Tooths_*`. |
| `04_CAMERAS` | `CAM_EST_Street`, `CAM_PHONE_CU`, `CAM_HUMAN_POV`, `CAM_CLAUDE_POV`, `CAM_INT_TwoShot`, plus the working views `CAM_WORK_Top` and `CAM_WORK_Overview`. |
| `05_LIGHTS` | `LIGHT_Sun`, `LIGHT_Lamp_*` (one per lamp post), `LIGHT_CarHead_L/R`, `LIGHT_CarFill`, `LIGHT_KeyClaude`, `LIGHT_KeyHuman`, `LIGHT_CarRim` (the car lights are children of the car). |
| `06_PROPS` | `PROP_Phone` (bone-parented to `DEF-hand.R` of the street human) and `PROP_Phone_Screen`, which carries the chat UI `PROP_UI_*`. |

### City

The ring's centreline runs x −172…188, y 0…216 (360 × 216 m), with corner radius R = 16. The car drives counter-clockwise in the outer lane, 2 m from the centreline (lane radius 18 m on the corners). The pickup stop is at (5, −2), heading +X, 167 m before the first corner. The exit door is at x = 1.5, on the facade line y = −10.5.

| Objects | What they are |
|---|---|
| `CITY_Road`, `CITY_RoadMarkings` | Road and painted markings: dashed centre line, parking-lane lines, 6 signalised zebra crosswalks with stop lines |
| `CITY_Sidewalk_Outer/Inner`, `CITY_Apron_Outer`, `CITY_InnerBlock`, `CITY_Ground` | Sidewalks with 0.15 m curb walls, plazas, ground |
| `CITY_Bldg_*`, `CITY_Bldg_Corner_*`, `CITY_ExitBuilding` | Rows of 10 shared building designs (glass, office, brick, concrete, white render with ribbon windows and wood slats; shopfront glass at street level), corner glass towers, and the exit building (white, glass lobby, canopy, door at x = 1.5) |
| `CITY_Lamp_*`, `CITY_Tree_*`, `CITY_Signal_*`, `CITY_Bench_*`, `CITY_Bin_*`, `CITY_Hydrant_*`, `CITY_UtilBox_*`, `CITY_Manhole_*` | Street furniture. The pickup area x −8…14 on the south sidewalk is kept clear. |
| `CITY_BG_*`, `CITY_BGFar_*`, `CITY_BG_In_*` | Background: a second ring of buildings, a far skyline and the inner block. They cast no shadows. |
| `CITY_ParkedCar_00..10` | Parked cars: one baked, shared Vulcar mesh, recoloured per object |
| `CITY_DrivePath` | The lane path: closed, 1137.1 m, stored in `length_m` |
| `CITY_ExitDoor` | Empty that marks the door |

## Cameras and shots

The 17 timeline markers come from `production/timeline.json`; each one binds its camera.

| Camera | Shots | Framing (verified with renders) | 9:16 `v916` |
|---|---|---|---|
| `CAM_EST_Street` | intro, pickup | 95 mm from 28 m down the street. The human at the door is **155 px tall at 960×540**, and the car arrives head-on with the whole car in frame. Depth of field f/2.8 on the human. | 130 mm, shift_x −0.40: the human is about 210 px; the car enters on the right |
| `CAM_PHONE_CU` | phone | From his eyes, 20 cm onto the screen; the full chat UI is readable. Parented to `CHAR_Human_Street`. | 40 mm |
| `CAM_HUMAN_POV` | Claude speaks | From the passenger side, ahead of Claude's face: Claude in 3/4 view at **25% of the frame width**, with the city in the driver window. The human's shoulder edges the frame. | 22 mm |
| `CAM_CLAUDE_POV` | the human speaks | The human's face in 3/4 view, the right window and the street behind him | 22 mm |
| `CAM_INT_TwoShot` | optional reactions | From the dashboard: both side by side | 11 mm |

`scripts/set_aspect.py` switches the render aspect. Set it first with `bl.py exec 'ASPECT="9:16"'`, then run the script; switch back to 16:9 before 16:9 renders.

## Lighting and look (`build_lighting.py`)

- **World:** the `sunset_jhbcentral` HDRI lights the scene at 0.55 and shows in reflections. Camera rays see a painted sky (peach horizon, soft blue zenith).
- **Sun:** 4.4, elevation 28°, from the east, straight down the pickup street. From the north-east the buildings put the street in shade.
- **City lights:** lamp LEDs at emission 6, each with a shadowless 90 W point light. Shopfront glass glows warm at 0.35; red signals glow.
- **Car lights:** the Vulcar's LED tubes (heads 8, tails 5), plus two 120 W spots.
- **Interior:** a 5 W roof fill, a 2.5 W key on each face, a 3 W cool rim.
- **Materials:** car glass alpha 0.22 with a dark tint; phone text darkened.
- **Colour and Eevee:** AgX, Medium High Contrast. Eevee: 32 render samples, screen-trace ray tracing at half resolution, 1 shadow ray, 4 steps, light threshold 0.005. The light threshold is from the stylised tuning; 0.05 made lamps drop out.

## Measurements (headless `blender -b`, `scripts/measure_renders.py`, warm-up discarded; the GUI Blender stayed open)

| Shot | 960×540, 16 samples | 1920×1080, 32 samples | Stylised scene |
|---|---|---|---|
| `CAM_EST_Street` | 2.25 s | 4.82 s | 2.27 / 7.5 s |
| `CAM_PHONE_CU` | 1.12 s | 2.81 s | 0.81 / 4.2 s |
| `CAM_HUMAN_POV` | 1.84–1.88 s (f360, 600, 1200) | 5.04 s | 1.96 / 8.0 s |
| `CAM_CLAUDE_POV` | 1.77–2.22 s (f450, 900, 1700) | 5.01 s | 1.76 / 7.3 s |
| `CAM_INT_TwoShot` | 1.87 s | 5.18 s | — |

- **Time:** draft frames take 1.1–2.3 s, the same range as the stylised scene. 1080p frames take 2.8–5.2 s, below the brief's 8–10 s target. The stylised final preset also used 2 shadow rays and 6 steps; mine uses 1 ray and 4 steps.
- **Memory:**
  - Blender's own peak (RSS): **1.26 GB** at draft, **1.91 GB** at 1080p.
  - Total peak including GPU buffers (`/usr/bin/time -l`): **3.8 GB** at draft, **4.2 GB** at 1080p. That's over the brief's roughly 2.5 GB.
  - What I tried at 1080p, measured on two frames:
    - render subdivision capped at 1: −0.4 GB;
    - plus all textures at 1K: −0.7 GB in total (3.5 GB);
    - a smaller shadow pool: no real gain;
    - hiding the parked cars: no gain (they share one mesh).
  - I did not find the main driver. Recommendation: keep the GUI closed for long renders, and use the subdivision cap plus 1K textures if memory gets tight. I didn't compare their visual cost side by side.

## Contract test (stylised `drive_car.py` / `animate.py` on this scene)

- **`drive_car.py`: unchanged, works.** Full lap from `CAM_CLAUDE_POV` (`stills/LAP_claude_pov_10.jpg`), with exact headings on every side. It is re-keyed from the new timeline: arrival at frame 241, stop at 313, departure at 337.
- **`animate.py`: section by section**

| Section | Result | What I changed (in `scripts/animate.py`, the copy for this scene) |
|---|---|---|
| 1 Markers | Unchanged, works | — |
| 2 Car (wheel roll and steer, steering wheel, Claude's grip points) | Unchanged, works | `WHEEL_R` 0.357, `WHEELBASE` 2.91 for this car |
| 3 Street-human walk | **Fails** | Needs the Quaternius "Walk" clip. Oscar's rig has none, so the walk is skipped and he stands at the door. A walk needs a Rigify-compatible clip or hand keys. |
| 3 Phone | **Fails** | Targeted `PROP_Phone_Text`. Rewritten to key the chat UI states: greeting, `PROP_UI_Typed_NN`, bubble at `sendFrame`, Claude's reply 1.5 s later. |
| 4 Claude (emotions, blink, speech pulse) | Unchanged, works | Same part names and pivots. His grip arms can point at `CAM_HUMAN_POV` like a short beak in some frames; cosmetic. |
| Mirror | **Fails** | Needs `M_local`. Now skipped: no mirror shots. |
| 5 Seated human | **Fails** | Used Quaternius bone names. Now mapped (Spine*→`spine_fk.00x`, Neck→`neck`, Head→`head`), with the offsets **added** to the build pose. Axis signs: nod is +X as before; turn and tilt signs are not verified. |
| 6 Camera drift | Unchanged, works | — |
| 7 Visibility | **Fails** | Hid only the armature and mesh, while the hair, jacket and eyes are separate objects. Now all children are covered. |

- **`verify_animation.py`:** not adapted. It hard-codes the v1 timeline (frames 253–277), the back door and the mirror keys, so it needs a rewrite for timeline v2.
- **Animated copy:** the cut sheet `stills/CONTRACT_animate_sheet.jpg` shows the phone states, the arrival and five interior frames. The animated copy was not kept; `scene.blend` itself is not animated.

## What the animation step must change

- Write a walk for Oscar (Rigify): from the door to the curb, then getting into the **front right** door.
- Facial expressions on Oscar's Rigify face controls (`jaw_master`, `lips.L/R`, `brow.*`, `lid.*`) driven by `envelope_human.json` and the emotion keys. The face rig is there but untested.
- Glances from `dialogue_v2.json` "look" (at Claude, the road, the right window).
- Adapt `verify_animation.py` to timeline v2.
- Decide whether `CAM_INT_TwoShot` takes some reaction beats (the timeline's cut rule allows it; `build.py` currently cuts only between the two POVs).

## Known issues

- 3.5–4.2 GB total peak memory (see Measurements).
- Dark streaks on the passenger seat back in the two-shot (a shadow artefact).
- The side windows read beige and foggy from inside.
- Oscar's eyes look a bit flat.
- Oscar's pose at the door has an open left hand ("presenting"). The phone sits in front of his fingers rather than in a real grip; it reads in the close-up.
- Outer corner plazas are bare. A few Poly Haven props (galvanised bin, hydrant) are more photo-real than the rest.
- The BlenderKit add-on is installed in the creator's Blender preferences, so every Blender start loads it. At quit it throws a harmless `unregister_class` error.
- Two ignored props: the `LIB_StreetLamp` asset (a wall lantern) is unused, as is `CAM_WORK_Overview`.
