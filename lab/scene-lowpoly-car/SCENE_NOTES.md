# Car scene: initial 3D set-up (handoff)

**Verdict:** works, with caveats. The full scene is set up and every camera is verified: city block, car with interior, the Claude character, the human (seated and standing), the phone, a working rear-view mirror in both interior shots, golden-hour lighting and shot markers. Blender 4.5.3 LTS with Eevee, on an Apple M2 with 8 GB RAM. Spend: $0, with only CC0 assets (see `ASSETS.md`).

## Files
- `scene.blend` is the working file (23 MB). It is **not committed** because it exceeds the size rule; rebuild it with the scripts below. Backups go in `backups/` and previews in `previews/`; both are git-ignored.
- `stills/*.jpg` are the committed draft renders: each camera at 960×540, `*_1080p` for both interior shots, `*_9x16` for the vertical versions, `RING_*` views of the city (top, straight, corner), `LAP_*` interior frames around the lap.
- `scripts/` holds the build scripts. Each one rebuilds only the objects tagged with its `cs_owner`, and skips anything with `user_locked = True`.

## Rebuild from scratch
1. Download the assets listed in `ASSETS.md` into `assets/` and unzip them.
2. Run `launch_blender.sh scene.blend`. On a fresh start, save an empty file as `scene.blend` first; the scripts find `assets/` relative to the .blend file.
3. Run the scripts in this order: `python3 bridge/bl.py file scripts/<name>.py` with `import_assets` → `build_city` → `build_car` → `build_characters` → `build_cameras` → `build_lighting` → `drive_car`.

After editing characters or the car, re-run **`build_car` → `build_cameras` → `build_lighting`**. `build_car` resets the car's material slots and removes the mirror probe; the other two scripts restore them. **`build_city` recreates `CAR_Exterior`** (it owns the staging), so after it always run the whole chain down to `drive_car`.

## Collections and objects
| Collection | Contents |
|---|---|
| `00_LIB` (excluded) | One clean, real-scale copy of every imported model (`LIB_*`). Scene objects are linked duplicates of these. |
| `01_CITY` | A **closed ring road** (see City layout): `CITY_Road_<edge>_<i>`, `CITY_Road_Curve_<edge>`, `CITY_CornerFill_<edge>_Outer/Inner`, `CITY_Sidewalk_<edge>O/I_<i>`, `CITY_ExitBuilding` (x=0, south side, door at x≈1.5, y=−8), `CITY_Bldg_<edge>O/I_<i>` and `CITY_Bldg_Corner_*`, `CITY_StreetLight_<edge>O/I_<i>` (every 16 m), `CITY_Tree_*`, `CITY_ParkedCar_A…F`, background `CITY_BG_*` (`_In_` inner block, `_Far_` far skyline), `CITY_Park`, `CITY_Ground` (1.6 km), and **`CITY_DrivePath`** (closed lane path, see Driving). Edges: 0 = south (pickup street), 1 = east, 2 = north, 3 = west. |
| `02_CAR` | `CAR_Exterior` (the Kenney sedan, its body mesh `CAR_Body`; faces +X in the world, −Y in its own space) plus `CAR_Wheel_*` (pivots at the wheel centres). Interior parts: `CAR_Seat_FL` (driver), `CAR_Seat_FR`, `CAR_Seat_Rear` (each seat has `_Back` and `_Headrest`), `CAR_Dashboard`, `CAR_SteeringWheel` (with its column), `CAR_Int_Floor`, `CAR_RearViewMirror` (`_Glass`, `_Stem`) and `CAR_MirrorProbe`. Everything is parented to `CAR_Exterior`. |
| `03_CHARACTERS` | `CHAR_Claude` (in the driver seat) with `_Eye_L/R`, `_Arm_L/R` and `_Leg_1…4`. `CHAR_Human` (back right seat, seated pose) and `CHAR_Human_Street` (at the exit door, texting pose); each has a `_Mesh`. |
| `04_CAMERAS` | `CAM_EST_Street`, `CAM_PHONE_CU`, `CAM_HUMAN_POV`, `CAM_CLAUDE_POV`, and working views `CAM_WORK_Overview` and `CAM_WORK_Top` (orthographic, whole ring). |
| `05_LIGHTS` | `LIGHT_Sun`, `LIGHT_Street_*` with `LIGHT_Bulb_*`, `LIGHT_CarHead_L/R`, `LIGHT_CarFill`, `LIGHT_CarRim`, `LIGHT_ClaudeFace`. The car lights are parented to the car. |
| `06_PROPS` | `PROP_Phone` (parented to the RightHand bone of `CHAR_Human_Street`) with `_Screen` and `_Text` ("Claude, I wanna go home."). |

There are about 1,440 objects and about 490k visible triangles (buildings are linked duplicates, so memory stays low).

## Cameras and shot markers (24 fps, placeholder timing)
| Frame | Marker | Camera | Framing |
|---|---|---|---|
| 1 | SHOT01 | CAM_EST_Street | Across the street: the exit door, the human waiting, the car at the curb. 24 mm. |
| 73 | SHOT02 | CAM_PHONE_CU | The human's POV onto the phone screen. 40 mm. |
| 121 | SHOT03 | CAM_EST_Street | The pickup. |
| 193 / 337 | SHOT04/06 | CAM_HUMAN_POV | Beside the human's head (0.35 m to his right, under the roof): Claude's right side/back on the left third, Claude's eyes in the mirror upper centre, the road through the windshield. 33 mm. |
| 265 / 409 | SHOT05/07 | CAM_CLAUDE_POV | The road through the windshield, the wheel, and the human's face in the mirror. 24 mm, clip_start 0.45. |

The interior cameras are parented to the car. Speaker cuts: when Claude speaks, use HUMAN_POV; when the human speaks, use CLAUDE_POV. Move markers with G in the Timeline; bind a camera with Ctrl+B. **Whenever you add a cut, also keyframe the mirror** to `CAR_RearViewMirror["aim_<camera>"]` with constant interpolation, as `build_cameras.py` does.

## City layout (round 2: endless ring)
- **Ring:** a rounded rectangle, centreline x −176…184, y 0…216 (360 × 216 m), 8 m roads, 4 m sidewalks. Corners are the Kenney curve tile (centreline radius 12 m); the sidewalk tiles leave bare ground at the curve's outer corner and inner quarter, so `CITY_CornerFill_*` (sidewalk texel of the same colormap) fill them.
- **Driving direction:** counter-clockwise, right lane = the outer lane, so the car's corners have **radius 14 m**. Straights: 336 m (south/north) and 192 m (east/west) along the lane, i.e. 40 s and 23 s at 8.5 m/s; a corner every 23-40 s.
- **Pickup:** unchanged, on the south straight: exit building at x=0, car at the curb at (5, −2) heading +X, 167 m before the first corner. `CAM_EST_Street` is unchanged.
- **Buildings:** both sides of every edge, random kit buildings from a fixed seed (`random.Random(7)`), rows spaced so they end flush at the corners; a tower on each outer corner and a block on each inner corner. Inner block: low blocks on a 28 m grid around a small park with trees. Outside: a ring of towers/blocks 34-44 m out and a far skyline of big low-detail blocks ~120-160 m out on a 1.6 km ground, so the horizon never shows the void. Background objects don't cast shadows.
- **Street lights** every 16 m on both sides, staggered (132 lamps; each gets a shadowless point light and an emissive bulb from `build_lighting`). **Trees:** one shared low-poly mesh (`CITY_Tree`), every 48 m on the inner sidewalk plus the park. **Parked cars:** six, on the inner (oncoming) lane's curb, away from corners; none in the drive lane.
- **9:16:** `scripts/set_aspect.py` (set `ASPECT`) switches the resolution and applies each camera's `v916` = (lens, shift_x, shift_y): CAM_HUMAN_POV 56 mm, shift −0.06/0.01 (at 33 mm the tall frame shows the roof lining and headrest); CAM_CLAUDE_POV 24 mm, shift_x 0.07 (brings the mirror in from the right edge). Switch back to 16:9 before 16:9 renders.

## Decisions
- **Assets:** Kenney City Kit (Roads, Commercial) and Car Kit, the Quaternius Animated Human, and the Poly Haven `venice_sunset` 1k HDRI. All are CC0.
- **Car:** the Kenney sedan, kept at its toy proportions (4.6 × 2.7 × 2.1 m). The roomy cabin fits the interior cameras. The windows are see-through (found by their colour in the texture) and the interior is built from boxes. The car has no rear side windows (stylised).
- **Claude:** a rounded orange block 0.6 × 0.5 × 0.8 m (colour about #D97757) with two black eyes, two "arms" on the steering wheel and four stubby legs. Every part has its pivot at the joint. Note for the creator: it resembles Anthropic's mascot, so check that the use is acceptable if the videos are monetised.
- **Rear-view mirror: Eevee planar light probe** (`CAR_MirrorProbe`). Tested 2026-10-08 against screen-space ray tracing alone:
  - Screen-space tracing can only reflect what is already on screen. In both shots the face sits behind the camera, so the mirror showed the blurry HDRI instead. It is not usable.
  - The planar probe renders a true mirrored view. The face is crisp in the mirror.
  - Requirements: ray tracing ON, method "Screen-Trace", resolution scale 1 (scale 2 blurs the face); the probe sits just in front of the glass; the mirror housing, glass and stem have `hide_probe_plane = True`, otherwise the probe captures the back of the mirror.
  - **Per-shot mirror angle (film cheat):** one angle cannot serve both shots, because CAM_CLAUDE_POV sits 0.4 m behind Claude's eyes (at the eyes, the short cabin cannot fit the mirror in frame). `build_cameras.py` computes one angle per camera from the characters' current eye positions and keyframes it at each marker.
  - The mirror is lower, further forward, nearer the driver and bigger (0.36 m) than in a real car. At roof height it only saw the top of Claude's head.
- **Lighting:** the sunset HDRI provides light and reflections, while camera rays see a painted gradient sky (the HDRI photo used to show through the skyline). A low, warm sun comes from the west. Street lamps are emissive bulbs plus shadowless point lights. Window glass in the building texture glows on about 60% of buildings, chosen at random per building. The car has emissive head and tail lights plus two spots. Inside there is a roof fill, a rim light and a small light on Claude's face. View transform: AgX, Medium High Contrast.
- **Eevee:** 32 render samples, 1 shadow ray, 4 shadow steps, no volumetrics.

## Measurements (Apple M2, 8 GB, Eevee, 32 samples)
Round 2 (ring city, 2026-10-08), round 1 in brackets:
| Shot | 960×540 | 1920×1080 |
|---|---|---|
| CAM_EST_Street | 3.9 s (4.3) | 5.8 s (6.4) |
| CAM_PHONE_CU | 1.4 s (1.4) | n/a |
| CAM_HUMAN_POV | 3.7 s (3.4) | 6.9 s |
| CAM_CLAUDE_POV (with mirror probe) | 3.8 s (3.4) | 6.5 s (6.3) |

Blender's peak RSS while rendering: about 460 MB (round 1: 614 MB peak over the session). macOS `top` "MEM" (physical footprint, including GPU buffers): 1.2-1.3 GB. The first render after opening the file is about 1 s slower (shader compile).

## Known issues
- There is slight shadow grain on building walls at 32 samples. Use 64 samples for finals, which roughly doubles render time.
- The windshield shows a faint dashboard reflection in CAM_CLAUDE_POV.
- 9:16 needs `set_aspect.py` (see City layout); without it, CAM_CLAUDE_POV cuts the mirror and CAM_HUMAN_POV shows a lot of roof lining and headrest.
- CAM_HUMAN_POV: the car's inner shell is orange, so the roof edge and A-pillar show as orange bars at the top left; the front passenger headrest fills the bottom centre. Both read as "inside a car".
- The mirror holds one angle per shot (keyframed at the markers). A test frame outside an interior shot shows the mirror aimed for the *other* camera; that's expected, not a bug.
- No street lights on the corner curves themselves (only along the straights).
- Background towers can intersect each other at the four far corners of the background ring (not visible from the road).
- `CAM_EST_Street` has a street light in the foreground at frame left. That's intentional, for depth, but easy to remove by moving the camera.
- The phone floats beside the fingers rather than being gripped; tune the hand pose when animating.
- Seated pose: the human's hands hang at his sides, and his knees are close to the front seat back. Claude's eyes sit high on its body so it can see over the dashboard.
- The human mesh and armature are shared between `CHAR_Human` and `CHAR_Human_Street` (linked data), so any mesh edit changes both.
- The Kenney car interior shows the orange body colour on the inside of the shell.

## What the animation step needs
- **Driving (ready):** `scripts/drive_car.py` puts a Follow Path constraint ("Drive", forward −Y, up Z) on `CAR_Exterior` targeting `CITY_DrivePath`, a closed (cyclic) poly curve of 1,144 m along the right lane, starting at the pickup point, corners as 1° arcs, a point every ≤8 m on the straights. A driver on the path's `eval_time` (a simple expression, no Python auto-run needed) moves the car at `SPEED` (8.5 m/s, one lap = 134.6 s = 3,230 frames) from `DEPART_FRAME` (193, the first interior shot), starting `START_M` metres along the path; before that the car waits at the curb. It loops forever with no keyframes. Tested over a full lap (10 frames from CAM_CLAUDE_POV, `stills/LAP_*`): it stays in the lane, everything parented to the car rides along, heading is exact on the straights, no jump at the closure. The start is an instant 0 → 8.5 m/s; ease it (keyframe the driver's speed, or replace the driver with eval_time keys) when animating the departure. Wheels: rotate `CAR_Wheel_*` about their local X (8.5 m/s ÷ wheel radius).
- **Claude rig:** separate objects, no armature. Pivots: body at the bottom centre, arms at the shoulders, legs at the hips, eyes at the bottom centre (scale Z to blink). Parent order: body → eyes/arms/legs. Steering: rotate `CAR_SteeringWheel` together with the arms.
- **Human rig:** a 48-bone humanoid (Mixamo-style names). Shipped actions are kept with fake users: Idle, Walk, Run, Jump, Punch, Working, Death. They can be used for walking out of the building. The seated and texting poses are plain bone rotations in `build_characters.py` (Euler XYZ; thigh/arm +X = forward/down).
- **Sound and cuts:** move the markers to the dialogue timing, and keyframe the mirror at each new interior cut (see Cameras).
- **9:16 variants:** apply `shift_x` on CAM_CLAUDE_POV.

## Animation and render (round 3, see `lab/results/car-render.md`)
Chain: `build_city -> build_car -> build_characters -> build_cameras -> build_lighting -> drive_car -> animate` then `verify_animation.py`. `drive_car.py` now keys the path (approach, stop 253-277, smooth departure); `animate.py` builds everything else from `production/timeline.json`. Render: `blender -b scene.blend -P scripts/render_sequence.py -- --preset draft|final [--range a b|--shots S05|--frames ..]`, then FFmpeg with `production/out/audio_mix.wav`. Draft = 960x540, 16 samples (2 s/frame); final = 1920x1080, 32 samples + 2 shadow rays (7.3 s/frame). Keep `light_threshold` at 0.005 (the old 0.05 made the street lamps drop out).
