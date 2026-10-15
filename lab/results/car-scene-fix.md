# car-scene round 2: scene-fix (HUMAN_POV + endless ring road)

**Verdict:** done. CAM_HUMAN_POV now matches the brief, and the city is a closed ring the car can lap forever. All four cameras are re-verified, and performance is within budget. Branch `<task branch>` (worktree `optimistic-wilson-150cb0`), 2026-10-08, Blender 4.5.3, Apple M2 8 GB. Details are in `lab/scene-lowpoly-car/SCENE_NOTES.md`; images are in `lab/scene-lowpoly-car/stills/`.

## Task 1: CAM_HUMAN_POV
- **Problem:** at the human's eyes, the camera sat 1 m behind Claude, so Claude filled half the frame.
- **Fix:** the camera now sits beside his head (car-local (−0.8, 0.92, 2.02): 0.35 m to his right, just under the roof), aimed at (0.12, −0.6, 1.72), with a 33 mm lens. I tested six positions and lenses (28-35 mm): two sat inside the human's head, and the front passenger headrest blocked one.
- **Result** (`stills/HUMAN.jpg`, `HUMAN_1080p.jpg`):
  - Claude's right side and back take about 37% of the width, on the left third.
  - The mirror sits upper centre and shows both of Claude's black eyes on the orange face. The eye pair is about 80-100 px at 960 px width, and the mirror about 140 px.
  - The road, a parked SUV and the city show through the windshield.
  - No clipping. The front passenger headrest fills the bottom centre, and the orange inner shell shows as roof and pillar bars at the top left.
- **Rebuild:** `build_cameras.py` owns the position, and the per-shot mirror aim is recomputed from it.
- **9:16:** new `scripts/set_aspect.py` switches the resolution and applies each camera's stored `v916` (lens, shift):
  - HUMAN_POV uses 56 mm with shift −0.06. At 33 mm the tall frame was a third roof lining.
  - CLAUDE_POV uses shift_x 0.07, which fixes the mirror cut-off from round 1.
  - Both are checked (`*_9x16.jpg`).
- **Re-verified after the ring was built:**
  - CLAUDE_POV: the human's face still reads in the mirror.
  - EST_Street: unchanged framing; the human is at the door and the car at the curb.
  - PHONE_CU: unchanged.

## Task 2: ring road + drive path
- **Ring:** a rounded rectangle, centreline 360 × 216 m. The Kenney curve tiles give a 12 m centreline radius. The car drives counter-clockwise in the right lane (the outer lane), so its corners have a **14 m radius**.
- **Lap:** 1,144 m. Long straights of 336 m and 192 m, i.e. 40 s and 23 s at 8.5 m/s.
- **Pickup and opening shot:** the pickup curb and exit building are unchanged on the south straight, 167 m from the first corner. The opening shot is unchanged.
- **Corner fills:** the bare corners of the curve tiles are filled with sidewalk-coloured meshes, so there are no seams (`RING_corner*.jpg`).
- **Buildings:**
  - Both sides of the whole ring are seeded random kit buildings (`random.Random(7)`), all linked duplicates. Rows end flush at the corners, with a tower on each outer corner and a block on each inner corner.
  - The inner block holds low blocks and a small park. Outside are a background ring and a far skyline on a 1.6 km ground.
- **Street furniture:** 132 street lights every 16 m (with lights and bulbs from `build_lighting`), sparse trees from one shared mesh (the kit has no tree), and six parked cars on the oncoming lane's curb.
- **`scripts/build_city.py`** is rewritten. It keeps the `cs_owner` and `user_locked` rules, and the run order is unchanged plus a final `drive_car`.
- **`scripts/drive_car.py`:**
  - Puts a Follow Path constraint on `CAR_Exterior` (forward −Y) along the closed `CITY_DrivePath` (cyclic, starting at the pickup point).
  - A driver on the path's `eval_time` (a simple expression, so no Python auto-run is needed) sets `SPEED` = 8.5 m/s, `DEPART_FRAME` = 193 and `START_M` = 0. The car waits at the curb until frame 193 (EST and pickup shots are intact), then laps forever without keyframes.
  - **Proof:** I rendered 10 frames from CAM_CLAUDE_POV around the full lap, including each corner midpoint and the frame just past the closure (`LAP_claude_pov_10frames.jpg`). The car stays in its lane, the interior, characters, cameras and car lights ride along, the heading is exact on the straights, and nothing jumps at the closure.
  - HUMAN_POV is also checked mid-lap with its mirror aim (`LAP_human_pov_f1300.jpg`). No test keyframes were added; the constraint and driver are left in place.

## Numbers (Eevee, 32 samples)
| Shot | Before | After |
|---|---|---|
| CAM_CLAUDE_POV 960×540 | 3.4 s | 3.8 s (+11%) |
| CAM_CLAUDE_POV 1080p | 6.3 s | 6.5 s (+3%) |
| CAM_HUMAN_POV 960×540 | 3.4 s | 3.7 s (+9%) |
| CAM_HUMAN_POV 1080p | n/a | 6.9 s |
| CAM_EST_Street 960×540 / 1080p | 4.3 / 6.4 s | 3.9 / 5.8 s |

- Visible triangles went from 73k to about 490k; objects from 257 to about 1,440.
- Blender's peak RSS while rendering is about 460 MB. macOS physical footprint (`top` MEM, including GPU) is 1.2-1.3 GB, under the 2 GB budget.
- The `.blend` file grew from 20.7 MB to 23 MB.

## What I could not verify
- I didn't render a full-length video; the lap was checked with sampled frames only.
- There are no real-time playback numbers for the viewport.
- The `top` memory figure is one sample after the renders, not a true peak.

## For the animation step
- After `build_city`, always run the chain `build_car` → `build_characters` → `build_cameras` → `build_lighting` → `drive_car`. `build_city` recreates the car, which drops the constraint.
- The departure is an instant 0 → 8.5 m/s at frame 193; add easing when animating. Wheels are not spinning yet.
- At each new interior cut, keyframe the mirror to `aim_<camera>`. A frame outside an interior shot shows the mirror aimed for the other camera, which is expected.
- For Shorts, run `set_aspect.py` with `ASPECT = "9:16"`, and set it back to `"16:9"` afterwards.

## Files and handoff
- **Commits on the branch:** `build_cameras.py`, new `set_aspect.py`, `build_city.py`, new `drive_car.py`, `SCENE_NOTES.md`, and 14 stills (1 MB).
- **`scene.blend`** (23 MB, not committed) is copied to `lab/scene-lowpoly-car/scene.blend`. The previous file is kept as `backups/scene_v200_before_fix.blend` there and in the worktree.
- **Blender:** the window I launched (from the worktree file) is still open for the creator; I did not close it.
