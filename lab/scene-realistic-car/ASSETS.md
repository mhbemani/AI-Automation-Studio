# Assets (realistic-leaning / game-style car scene)

Files live in `assets/` (git-ignored; in this worktree it is a symlink to the base checkout's `lab/scene-realistic-car/assets/`).
Re-download the CC0 part with `python3 scripts/fetch_assets.py`. Downloaded 2026-10-09. `fetch_assets.py` also makes 1K copies (`*_1k.jpg`, `*_1K-JPG_*`) of the 2K texture sets locally with `sips` (memory diet).

**Look agreed with the creator:** stylised-realistic, like an animated film or a modern game (not photoreal).
**Licence decision (creator, 2026-10-09):** hybrid. Everything is CC0, **except the human and the car**, which come from BlenderKit (the creator lifted the brief's BlenderKit ban for these two assets and logged in themselves). The car's interior, the buildings and Claude are built by script.

## BlenderKit (Royalty Free, NOT CC0)
Polygon diet (2026-10-09, creator's DIET_SPEC.md): the first three rows are the assets in use; Oscar and the Vulcar below them were the heavy v1 assets (replaced; files kept in assets/ for reference, not used by the scene).
| Asset | Author | Licence | Local file | Size | Notes |
|---|---|---|---|---|---|
| [Low poly plymouth car](https://www.blenderkit.com/asset-gallery-detail/bdc55ac4-0696-4304-b616-4f91ac40808f/) (base id `62804a83-6bfd-45d9-865a-7b19b2ac1ddd`) | Rohit Gupta | BlenderKit Royalty Free (free) | `blenderkit/plymouth_lowpoly.blend` | 0.46 MB | Hero car. Listed "7,545" = faces of the half mesh; mirrored it is 31.3K tris. We scale 1.06, split the wheels, decimate wheels and grille, planar-dissolve the body: 7,263 tris. Recoloured yellow (creator), window materials -> glass. Credit: "Low poly Plymouth car by Rohit Gupta (BlenderKit)". |
| [Low Poly JDM Sports Car (Skyline)](https://www.blenderkit.com/asset-gallery-detail/b20a329f-ba0e-43d7-8fbf-303627c6a8dc/) (base id `ab0b231a-8351-422f-b55f-108faa77641d`) | Sachin H | BlenderKit Royalty Free (free) | `blenderkit/jdm_skyline_lowpoly.blend` | 0.33 MB (1K) | Parked cars (5 linked duplicates). 7,606 tris incl. wheels and interior (listed 3,803 = faces). Smoothed by shading only, 4,413 verts / 3,803 faces before and after. Credit: "Low Poly JDM Sports Car (Skyline) by Sachin H (BlenderKit)". |
| [Lowpoly Male Standing](https://www.blenderkit.com/asset-gallery-detail/28322be2-8331-4f54-a614-2a014f5efcec/) (base id `ead8da9e-6788-44f8-9366-870cc3d76a32`) | Hyperreality Lowpoly | BlenderKit Royalty Free (free) | `blenderkit/lowpoly_male.blend` | 0.14 MB | The human. 3,010-tri faceted scan in a phone pose, no rig/colours/face; we add an FK rig (Rigify control names), materials, black dot eyes, a mouth line, emotion shape keys (3,230 tris total). Credit: "Lowpoly Male Standing by Hyperreality Lowpoly (BlenderKit)". |
| [Oscar Character Rigged](https://www.blenderkit.com/asset-gallery-detail/349ee3b5-f082-4faf-a47d-3e6819badbcf/) (base id `cb6c4200-fe88-4d95-99f9-fac4a5c2d3bb`) | Rex Mun | BlenderKit Royalty Free | `blenderkit/oscar_1K.blend` | 2.8 MB | 1K texture variant, textures packed. Rigify rig with face controls (lips, jaw, brows, lids), 1.75 m, about 32k tris. Comes holding a trophy (`statue`), which we hide. |
| [Vulcar Hachura](https://www.blenderkit.com/asset-gallery-detail/a35fe290-c737-4e46-a5ed-8f99ac6fc9df/) (base id `4e37c6e3-de00-46c8-b13d-7cdb0f9359f4`) | m awais | BlenderKit Royalty Free | `blenderkit/vulcar_hachura_2K.blend` | 8.9 MB | Claude's car (creator's pick, 2026-10-09). 2-door coupe, no interior (opaque window panels). Saved by Blender 5.0 (opens in 4.5 with a version warning). We scale it 6%, turn the window panels into glass, decimate the wheels (67k -> 8k tris each) and build the interior. Credit: "Vulcar Hachura car by m awais (BlenderKit)". |

How it was fetched (both): the BlenderKit add-on (installed and logged in by the creator) downloaded the 1K file into `~/blenderkit_data/models/oscar-character-_349ee3b5-.../`; the add-on's own append step stalled, so the file was copied into `assets/blenderkit/` and the textures packed. Royalty Free allows use in our rendered videos; the raw asset must not be redistributed (it is git-ignored). Credit line for the video: "Oscar character by Rex Mun (BlenderKit)".

## Poly Haven (CC0, https://polyhaven.com/license)
| Asset | Type | Res | Authors | Local path |
|---|---|---|---|---|
| sunset_jhbcentral | HDRI | 2k (6 MB) | Greg Zaal, Dimitrios Savva | `polyhaven/hdri/` |
| asphalt_02 | texture | 2k | Rob Tuytel | `polyhaven/textures/asphalt_02/` |
| concrete_pavement | texture | 2k | Charlotte Baglioni | `polyhaven/textures/concrete_pavement/` |
| brushed_concrete | texture | 1k | Dario Barresi, Dimitrios Savva | `polyhaven/textures/brushed_concrete/` |
| brown_leather | texture | 1k | Rob Tuytel | `polyhaven/textures/brown_leather/` |
| beige_wall_001 | texture | 1k | Dimitrios Savva, Rico Cilliers | `polyhaven/textures/beige_wall_001/` |
| street_lamp_02 | model glTF | 1k | Josh Dean | `polyhaven/models/street_lamp_02/` (20k tris) |
| fire_hydrant | model glTF | 1k | Gonçalo Felício | `polyhaven/models/fire_hydrant/` (86k tris: decimate on import) |
| metal_trash_can | model glTF | 1k | GurJas Studios | `polyhaven/models/metal_trash_can/` (14k) |
| modular_street_seating | model glTF | 1k | Stuart Attenborrow | `polyhaven/models/modular_street_seating/` (25k) |
| utility_box_01 | model glTF | 1k | James Ray Cock | `polyhaven/models/utility_box_01/` (4k) |
| water_manhole_cover | model glTF | 1k | Raunox | `polyhaven/models/water_manhole_cover/` (6k) |

## ambientCG (CC0, https://ambientcg.com/license)
| Asset | Res | Use | Local path |
|---|---|---|---|
| Facade001 | 2K-JPG (5.5 MB zip) | glass curtain-wall tower | `ambientcg/Facade001/` |
| Facade006 | 2K-JPG (5.8 MB) | white office grid | `ambientcg/Facade006/` |
| Facade017 | 1K-JPG (6.7 MB) | concrete grid, lit windows | `ambientcg/Facade017/` |
| Facade020A | 1K-JPG (7.3 MB) | brick mid-rise | `ambientcg/Facade020A/` |

Total CC0 download: 88.8 MB.

## Rejected (and why)
- Khronos CarConcept (CC-BY): a 2-seat supercar, no back seat.
- Kiln "Generic sedan": AI-generated (not allowed), no interior.
- Quaternius Downtown City MegaKit / Universal Base Characters (CC0): itch.io is behind a Cloudflare check I may not click; also old-NYC brick, while the creator's references are modern.
- Poly Haven trees: 0.3-4.6 M polys, up to 213 MB each, too heavy for 8 GB. Trees will be built light (leaf cards).
- BlenderKit "Restaurant": only a vibe reference, not downloaded.
- My scripted 4-door sedan (M4 first try): replaced by the Vulcar at the creator's request; code in git history.
