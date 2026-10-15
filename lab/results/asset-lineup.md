# Asset lineup (all assets, new and old, side by side)

One Blender file, `lab/asset-lineup/lineup.blend`, holds every asset at real-world scale under the same light so their vibe can be compared and each can be reviewed one at a time (Claude, car, phone next). Assembly only: nothing was redesigned. Built 2026-10-12 with Blender 4.5.3 LTS (Eevee Next, AgX / Medium High Contrast, as in the realistic scene).

## What is in the file
Row NEW (back, y = +4.3 m, teal-tinted plinths) and row OLD (front, y = -4.3 m, amber-tinted plinths), left to right: Claude, car, phone, parked car, human. Every asset has its own collection under `LU_Assets`, a plinth, a tilted placard (name, source scene, triangles, bounding box in metres) and a colour strip (teal NEW / amber OLD).

| Collection | Source (read-only) | Object | Notes |
|---|---|---|---|
| `LU_NEW_Claude` | `lab/scene-realistic-car/scene.blend` | `CHAR_Claude` + 10 parts | detached from the car seat |
| `LU_NEW_Car` | same | `CAR_Exterior` + 19 parts | no Follow Path, no occupants |
| `LU_NEW_Phone` (+ `LU_NEW_Phone_5x`) | same | `PROP_Phone` + screen + UI + 24 hidden typing texts | detached from the hand bone; on a small easel, leaning 15 deg |
| `LU_NEW_ParkedCar` | same | `CITY_ParkedCar_00` | the smoothed JDM car; nose to +X found from the lamp / tail-light faces |
| `LU_OLD_Claude` | `lab/scene-lowpoly-car/scene.blend` | `CHAR_Claude` + parts | arms still Track-To two grip empties (copies kept with Claude, see below) |
| `LU_OLD_Car` | same | `CAR_Exterior` + parts (+ wheel grips, mirror probe) | no Follow Path, no lights/occupants |
| `LU_OLD_Phone` (+ `LU_OLD_Phone_5x`) | same | `PROP_Phone` + screen + bubble + texts | |
| `LU_OLD_Human` | same | `CHAR_Human_Street` + mesh | optional reference; walk pose baked at source frame 200 |
| `LU_NEW_Human` | snapshot of `character_selection_lab.blend` (`snapshots/human_snapshot.blend`, sha1 recorded on the root) | `HUM_Body` + `RIG_Human` | rest pose (all pose bones cleared), grey; `REF_static_baseline` not included |

Object names are the originals with `LU_NEW_` / `LU_OLD_` in front (the two scenes reuse names). The root of each asset carries custom properties `lineup_source` (file, original object name, git info), `lineup_tris`, `lineup_objects`, `lineup_dims_m`. The source scene files are not tracked by git (gitignored), so `git` says "untracked" plus the file's modification time.

## Per-asset table
Triangles: evaluated, render-visible meshes, same method as `lab/tools/polycount.py` (modifiers applied, text objects not counted). Size: bounding box (x, y, z) in metres as placed (cars run along x).

| Asset | Tris | Objects | Size (m) | Textures (image maps) | Source object |
|---|---:|---:|---|---|---|
| NEW Claude | 1,656 | 11 | 0.57 x 0.65 x 0.82 | none (procedural materials) | `CHAR_Claude` |
| NEW Hero car | 11,083 | 20 | 5.03 x 2.02 x 1.34 | 3 x 1024 (brown leather diff / rough / normal) | `CAR_Exterior` |
| NEW Phone | 430 | 38 | 0.07 x 0.05 x 0.15 | none | `PROP_Phone` |
| NEW Parked car | 7,606 | 1 | 4.87 x 2.06 x 1.45 | 1536 x 1024 plate | `CITY_ParkedCar_00` |
| NEW Human (scan, rigged) | 4,016 | 2 (mesh + armature, 49 bones) | 1.21 x 0.45 x 1.91 (A-pose arms make it 1.21 wide) | none (grey `hle_grey`) | `HUM_Body`, `RIG_Human` |
| OLD Claude | 972 | 11 | 0.60 x 0.75 x 0.96 | none | `CHAR_Claude` |
| OLD Car | 2,440 | 23 | 4.59 x 2.70 x 2.56 | 512 x 512 colormap | `CAR_Exterior` |
| OLD Phone | 122 | 29 | 0.08 x 0.05 x 0.15 | none | `PROP_Phone` |
| OLD Human (reference) | 1,578 | 2 | 0.75 x 0.80 x 1.84 | 32 x 32 skin | `CHAR_Human_Street` |

The two 5x phone copies are linked duplicates (same mesh/curve data, scaled 5 on the root) and are not counted. The numbers match the earlier reports (Claude about 1.7K / 0.97K, car about 11K, parked car 7.6K per the diet report; the brief said "about 4K" for the parked car, the file says 7,606).
`asset_table.json` next to the file has the same data.

## Render cost (one draft overview, 960 x 540, 16 samples, studio light)
`/usr/bin/time -l`: Blender reports render 0.90 s, wall 1.39 s, **peak resident memory about 600 MB** (golden light: 0.80 s render, 1.28 s wall, about 730 MB). 1920 x 1080 / 32 samples golden: 2.9 s render, 3.4 s wall, about 680 MB. Eevee runs on the Mac GPU here; these figures say nothing about a CPU-only render. The file is 23 MB (packed textures and the 2k HDRI); memory in the Blender window is higher than these headless figures and was not measured.

## How to use it
**Open:** `/Applications/Blender.app/Contents/MacOS/Blender lab/asset-lineup/lineup.blend` (the repo copy, or `lab/asset-lineup/lineup.blend`). Images are packed, so it does not depend on the asset folders.
**Rebuild from scratch** (idempotent, overwrites `lineup.blend`; sources are only read):
```
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python lab/asset-lineup/scripts/build_lineup.py
```
**Switch lighting:** two presets, `studio` (soft sun key, big shadowless soft-box fill, rim sun, grey world) and `golden` (the realistic scene's world: sunset HDRI + painted sky at 0.55 and its sun, 4.4 W/m2 warm, same 28 deg elevation, azimuth turned to the front-right so the camera side is lit). In Blender: Text editor, open `LU_light_studio.py` or `LU_light_golden.py`, Run Script (Alt+P). It toggles the `LU_LIGHT_Studio` / `LU_LIGHT_Golden` collections and the scene world and sets `scene["lineup_light"]`. Headless: `--light studio|golden` below.
**Render a camera** (never saves the .blend):
```
/Applications/Blender.app/Contents/MacOS/Blender -b lab/asset-lineup/lineup.blend --python lab/asset-lineup/scripts/render_lineup.py -- --camera LU_CAM_Compare_Car --preset draft --light golden --out out.png
```
`--preset draft` = 960 x 540 / 16 samples, `final` = 1920 x 1080 / 32. Per-asset cameras (`_Front`, `_34`) render with only that asset (other assets and the placards hidden, plinths and floor stay); the two `Compare` cameras show only the NEW + OLD pair of that asset without placards (the plinth tint tells NEW teal from OLD amber); everything else shows all. `--isolate off` renders everything. `scripts/render_many.sh studio|golden draft|final CAM ...` renders several into `previews/`.
**Cameras** (collection `LU_Cameras`): `LU_CAM_Overview`, `LU_CAM_NEW_Row`, `LU_CAM_OLD_Row`, `LU_CAM_Compare_Claude`, `LU_CAM_Compare_Car`, and for every asset `LU_CAM_<NEW|OLD>_<Claude|Car|Phone|ParkedCar|Human>_Front` and `_34` (cars: Front = from the nose side, +X; others from -Y), plus `LU_CAM_NEW_Phone5x_*`, `LU_CAM_OLD_Phone5x_*` for the enlarged phones. Each is fitted with a bounding-box search so the subject fills the frame.
**Refresh the human** after the selection lab changes it (close the lineup in any Blender window first, the script writes the file):
```
/Applications/Blender.app/Contents/MacOS/Blender -b lab/asset-lineup/lineup.blend --python lab/asset-lineup/scripts/refresh_human.py
```
It copies the selection lab's saved file to `snapshots/human_snapshot.blend` (previous snapshot kept as `human_snapshot_prev.blend`), re-appends `HUM_Body` + `RIG_Human` into `LU_NEW_Human`, puts it back on its plinth, updates its label numbers and the two human cameras, and touches nothing else. `-- --no-copy` reuses the existing snapshot. (Tested on a copy of the lineup: 4,016 tris, 1.21 x 0.45 x 1.91 m, same as before.) The selection lab file is only copied, never opened in place or written.
**Check:** `scripts/check_lineup.py` translates every asset's root and confirms all parts follow (11 collections OK), no constraint targets outside an asset, no missing images, no object outside a collection. Result: OK.

## Changes made to assemble (not redesigns)
- **Follow Path** (car, both scenes) removed; the drive-path curve was not included. Cars sit nose to +X on their plinths.
- **Claude** (both) is parented to the car in the sources: detached keeping its pose. **Phones** are parented to the street human's hand bone in the sources: detached and stood on an easel (my own two-box stand, `LU_Stand_*`, not part of the asset), screen facing the camera, tilted 15 degrees.
- **Old Claude's arms** are Track-To constraints on two grip empties on the old steering wheel. The car and Claude are on different plinths, so the lineup carries copies of the two grips (`LU_OLD_..._ClaudeCopy`) parented to Claude at the same relative place. The poses are the source poses.
- **Old scene animation:** the old assets are keyframed (Claude, eyes, wheels, steering wheel, mirror, human walk, phone visibility). Evaluated at source frame 200 (phone bubble and sent text visible, Claude neutral), then the actions were unhooked (kept in the file with a fake user) so placement is not overridden. The new scene has no object animation. The 24 hidden "typing" texts on both phones stay hidden as in the sources.
- **Left out:** car lights, cameras and probes parented to the car except the old mirror's planar probe (kept); seated human and its parts; the street human of the realistic scene (1.75 m, not asked for); all city, props and lights.
- **Human:** pose bones all reset to rest (the saved selection file had 41 posed bones); face shape keys left as saved.
- **Look settings:** the realistic scene's Eevee settings (ray tracing screen, fast GI, 256 MB shadow pool, 1K textures). One deviation: shadow resolution scale 0.5 instead of 1.0, because close cameras overflowed the 256 MB pool ("shadow buffer full" for the old car front camera); the fill light has no shadows. The golden-hour sun azimuth was turned toward the camera (the scene's sun comes from +X, which would leave the side facing the camera in shadow); the HDRI is unchanged, so the bright spot of the HDRI in reflections and the sun lamp do not agree in direction.

## Looks side by side (honest, factual)
Seen in `stills/`. The rows are in different styles by design; these are the visible differences.

**Claude.** NEW: smooth, rounded orange box with glossy highlights, round black eyes with a white glint, short stubby arms and four small leg nubs; 0.57 x 0.65 x 0.82 m. OLD: flat-shaded, chamfered box in a lighter salmon-orange, tall rectangular black eyes, long finger-like legs sticking forward (seated pose), arms stretched toward the (now absent) steering wheel; 0.60 x 0.75 x 0.96 m, so about 17 percent taller and 15 percent deeper. Colour differs visibly (NEW is deeper and more red-orange). Eyes differ most. Visible problems: old Claude's arms and legs point at things that are not there (steering wheel, seat) because the pose was made for the car; new Claude's glints sit high in the eyes; both have no feet, mouth or ground contact other than the leg nubs.

**Car.** NEW hero car: 1970s coupe in mustard yellow with black vinyl roof, rear spoiler, hood scoop, glass, textured leather seats visible inside; low (1.34 m) and long (5.03 m); looks "real" next to the OLD one. OLD car: Kenney-style sedan in saturated red-orange with dark blue-grey bumpers, big rounded wheels, flat colours, 4.59 x 2.70 x 2.56 m: almost twice as tall and 35 percent wider than the hero car for a similar length, so it reads as a toy-proportion car. Clashes: proportion and scale (toy vs realistic), colour saturation, level of detail (2.4K vs 11K triangles, procedural paint vs colormap). Visible problems: hero car wheels read as dark flat discs with little rim detail from the 3/4 view; the old car's interior is a dark box without visible seats from the front camera; the parked JDM car is a plain white, faceted body (hard edges around the hood and bumpers).

**Phone.** NEW: pale blue case, soft-grey screen with a chat UI (title "Claude", a grey bubble "Claude, I wanna go home.", an orange avatar, the reply text, a reply bar with an orange send button); text readable at 5x and just readable at 1x on the 960 px renders. OLD: near-black case with a white screen and one saturated blue bubble with white text "Claude, I wanna go home."; 122 triangles; flat. Different sizes in the UI: the old screen has only one element. Visible problems: new phone UI text is thin and low-contrast (grey on grey); old phone bubble is much stronger than anything else on its screen; both are 15 cm tall, the sizes agree.

**Human.** NEW (scan): grey faceted hoodie-and-trousers figure, A-pose, face and hands readable at 1.91 m, no colours yet (4,016 triangles); the 1.21 m width comes from the A-pose arms. OLD: flat-colour low-poly man (teal shirt, blue trousers, brown hair, skin tones, bare feet), thinner, 1.84 m, mid-gesture arm. Visible differences: the scan is 7 cm taller than the old figure (and 16 cm taller than the realistic scene's 1.75 m human), much more detail but uncoloured; the old figure's palette fits the old Claude and car, the scan has no palette yet and sits visually apart from both rows.

**Overall.** The NEW row mixes a glossy rounded Claude, a realistic car and a faceted grey scan; the OLD row is consistently flat-shaded and saturated. In the golden-hour set the NEW car and parked car pick up warm reflections and long shadows; the old car and Claude stay flat. The biggest cross-row mismatches are scale (old car vs hero car), saturation (old = saturated, new = muted) and detail level (Claude and the human against the hero car).

## What I could not verify
- Whether the old human's pose and the old Claude/car poses at frame 200 are the ones the creator would pick; I chose frame 200 for the phone visibility.
- The planar probe on the old car's mirror: kept, but I did not look at the mirror reflection in a render.
- Memory in the Blender window while the creator edits (only headless render peaks were measured).
- That the refresh script still places the human correctly if the selection lab renames `HUM_Body` / `RIG_Human` (it looks the objects up by name).
- That the HDRI sun and the golden-hour sun lamp agree (they do not, see above).
- Final-quality (1920 x 1080, 32 samples) renders were made only for the two overviews; the other stills are 960 x 540 drafts.

## Files
`lab/asset-lineup/`: `scripts/` (`lineup_lib.py`, `build_lineup.py`, `render_lineup.py`, `render_many.sh`, `refresh_human.py`, `check_lineup.py`), `asset_table.json`, `stills/` (small JPEGs: overviews in both lights, NEW/OLD rows, Claude and car comparisons in both lights, enlarged phones, human). Not in git (see `.gitignore`): `lineup.blend`, `snapshots/`, `previews/`.
