# Facet: style guide ("low-poly gem")

Goal: later characters/props must look like they live in the same world as **Facet**.

## Shape language
- Hard facets only. **Flat shading everywhere, no subdivision, no bevel, no smooth normals.**
- Everything is a *lathe gem*: an n-gon ring stack (n = 5-8) where consecutive rings are rotated by half a step, which gives the triangle-strip look of a cut stone. Caps are a flat table (top) or a point (bottom).
- Bodies are rigid pieces with small gaps between them (floating shoulders, floating torso over feet). Gaps are intentional, not a bug.
- Silhouette accents are small amber bipyramids (crown spikes, ear gems, chest gem).
- Eyes/mouth are flat hexagon facets placed ON the head surface (raycast to the surface, +0.03 offset), never spheres.
- Budget: Facet is ~340 triangles / 19 meshes. Limit for a character: ~2,000 triangles. Per-vertex jitter of up to ~0.01 on torso/limbs makes facets look hand-cut; the head is kept exactly symmetric.

## Proportions (units, Z up, character faces -Y, screen-right = +X)
| part | size |
|---|---|
| total height (crown tip) | ~2.7, body ~2.4 |
| head | 1.32 wide x 0.8 tall (1.2..2.02), 8-sided, flat table, wider than the torso (big-head cute ratio) |
| torso | 0.88 wide x 0.8 tall, 6-sided elongated crystal, floats 0.1 above the feet |
| arms | shoulder pivot at x = +-0.6, z = 1.0; upper arm 0.5 long, hand gem 0.46 long, 0.05 gap |
| legs | 0.4 tall stubs with a flat toe-forward foot |
| eyes | 0.14 x 0.24 hexagon at x = +-0.21, z = 1.74 |

## Palette (sRGB hex; kept in `palette.py`)
| role | hex | use |
|---|---|---|
| aqua-teal | `#2EC4B6` (+ `#1FA39A` dark, `#6FE3D4` light) | head crystal |
| indigo | `#5B5BD6` (+ `#4747B8`, `#7A7AEA`) | torso, upper arms |
| coral | `#FF6B6B` (+ `#E64A5A`) | hands, feet |
| amber (accent) | `#FFC93C` (+ `#FFAE1A`) | crown, ears, chest gem |
| eye / mouth | `#141C5C` / `#2A0F2E`, highlight `#E8FAFF` | face |

Each facet gets a random value jitter (x0.8 .. x1.12) baked in a colour attribute `col`, so a handful of base colours reads as many facets. Reads on dark navy `#0b1020` and on light backgrounds (checked on `#0b1020` and `#e9edf5`).

## Materials (4, Principled BSDF, colour comes from the `col` attribute, no images)
| name | roughness | extras | used on |
|---|---|---|---|
| crystal | 0.18 | coat 0.35, specular 0.5 | head, hands |
| body | 0.55 | coat 0.15 | torso, arms, legs |
| accent | 0.32 | coat 0.25 | crown, ears, chest gem |
| eye | 0.9 | emission 0.35, specular 0 | eyes, mouth (only emissive material) |

## Lighting / render recipe
- Eevee (`BLENDER_EEVEE_NEXT`), **Standard** view transform, film transparent, RGBA PNG. 16 samples draft / 32 final.
- Key: warm soft area light, camera-left, high (850 W). Fill: cool blue area, low, camera-right (220 W). Rim: strong pink-magenta area from behind-right (340 W). Rim 2: cool cyan from behind-left (500 W). Very low world (0.35 blue-grey, never visible: background is transparent).
- Contact shadow: a procedural soft blob (transparent material, dark navy, radial falloff) parented to the root bone. Eevee Next has no working shadow catcher, so this is the substitute.
- Camera: 50 mm, 24 deg three-quarter azimuth, 9 deg elevation.
