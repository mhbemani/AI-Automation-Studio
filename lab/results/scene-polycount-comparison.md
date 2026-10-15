# Scene comparison: stylised low-poly vs realistic (heavy v1) — polygon budgets

Measured 2026-10-09 with `lab/tools/polycount.py` (headless Blender 4.5.3; evaluated render-visible meshes with modifiers at viewport subdivision levels; linked duplicates/instances counted per instance; `in-camera` = objects whose bounding box overlaps the camera frustum at 12 sample frames over the four cameras, **no occlusion culling**, so it is an upper bound, equally for both scenes). Sources: `lab/scene-lowpoly-car/scene.blend` (saved 2026-10-08) and `lab/scene-realistic-car/scene.blend` as of 2026-10-09 11:57, now archived as `lab/scene-realistic-car/backups/scene_v1_heavy_not_renderable.blend` (git-ignored).

## Per asset (whole scene)
| Asset | Stylised low-poly | Realistic v1 (heavy) | Ratio |
|---|---|---|---|
| Human | 1,578 tris / 1,578 faces | **66,180 tris / 33,088 faces** | 42x |
| Claude | 972 tris / 486 faces | 13,376 tris / 7,040 faces | 14x |
| Hero car (exterior + interior + wheels) | 2,440 tris / 2,236 faces | **205,604 tris / 112,221 faces** | 84x |
| One parked car | (kit cars, small) | **141,692 tris** each (6+ copies, about 0.85M) | n/a |
| City, whole scene | 481,093 tris (1,088 objects) | **2,605,693 tris** (573 objects) | 5.4x |

## In camera (average over the 12 sample frames)
| | Stylised | Realistic v1 |
|---|---|---|
| City | 86,236 (29K-169K) | **589,529** (27K-1,580K) |
| Car | 1,320 | 136,299 |
| Human | 658 (street) / 394 (seated, avg) | 43,048 / 53,937 |
| Claude | 342 | 8,715 |
| **Everything in frame** | **89,334** (max 171,683) | **836,551** (max 1,805,187) |

Per camera (city avg / total avg): EST 65K/69K vs 480K/840K; PHONE 29K/32K vs 27K/100K; HUMAN_POV 116K/120K vs **1,271K/1,516K**; CLAUDE_POV 105K/107K vs 165K/419K. Overall about 9x the triangle load in frame.

## Measured render cost of the realistic v1 (from its own report, `lab/results/realistic-scene.md`)
Apple M2, 8 GB, headless Eevee, GUI Blender open at the same time: draft 960x540 at 16 samples 1.1-2.3 s/frame (stylised 1.8-2.0 s); 1080p at 32 samples 2.8-5.2 s/frame (stylised 7.3-8.0 s with 2 shadow rays). **Memory is the problem:** Blender RSS 1.26 GB (draft) / 1.91 GB (final) and **total footprint including GPU buffers 3.8 GB (draft) / 4.2 GB (final)** versus about 1.65-1.94 GB for the stylised scene; the driver was not identified (render subdivision 1, 1K textures, a smaller shadow pool and hiding the parked cars did not fix it). On an 8 GB machine that leaves almost nothing for the OS and the GUI, and it makes the viewport and every interactive step heavy. Creator verdict: not usable on this device as it is.

## Biggest offenders (realistic v1)
1. Human at 66K tris (Oscar, BlenderKit): a detailed film-quality mesh.
2. Parked cars: 141,692 tris each, six or more copies (about 0.85M of the 2.6M total).
3. The hero car at 205K tris.
4. The buildings and props along the ring (about 1.05M instanced tris in the draw per the agent): need their own budget once the cars and human are replaced.

## Budgets agreed for the diet (next round)
Human <= 10K tris including eyes/mouth; hero car <= 7K exterior + <= 5K interior; parked cars 4K each (a few, linked duplicates); Claude <= 4K; city in camera average <= 300K (max <= 600K); total footprint during render <= 2.5 GB. The same script and the same cameras/frames are re-run after the diet for a fair before/after.
