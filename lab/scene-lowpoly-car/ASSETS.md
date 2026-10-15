# Assets (all CC0, downloaded 2026-10-08, licence checked on the source page before download)

Files live in `lab/scene-lowpoly-car/assets/` (git-ignored). Zips are unpacked next to themselves (`<zip name>/`).
Imported by `scripts/import_assets.py` into the hidden `00_LIB` collection.

| Name | Source page | Download URL | Licence | Size | Local file |
|---|---|---|---|---|---|
| Kenney City Kit (Roads) | https://kenney.nl/assets/city-kit-roads | https://kenney.nl/media/pages/assets/city-kit-roads/74288c9459-1787042796/kenney_city-kit-roads.zip | CC0 1.0 | 2.8 MB | `assets/kenney_city-kit-roads.zip` |
| Kenney City Kit (Commercial) 2.1 | https://kenney.nl/assets/city-kit-commercial | https://kenney.nl/media/pages/assets/city-kit-commercial/a742d900eb-1753115042/kenney_city-kit-commercial_2.1.zip | CC0 1.0 | 4.1 MB | `assets/kenney_city-kit-commercial_2.1.zip` |
| Kenney Car Kit 3.1 | https://kenney.nl/assets/car-kit | https://kenney.nl/media/pages/assets/car-kit/1a312ec241-1775131960/kenney_car-kit.zip | CC0 1.0 | 4.8 MB | `assets/kenney_car-kit.zip` |
| Animated Human Low Poly (Quaternius) | https://opengameart.org/content/animated-human-low-poly | https://opengameart.org/sites/default/files/Animated%20Human%20by%20%40Quaternius_0.zip | CC0 1.0 (also in the zip's License.txt) | 5.0 MB | `assets/quaternius_animated_human.zip` |
| HDRI "Venice Sunset" 1k (Greg Zaal, Poly Haven) | https://polyhaven.com/a/venice_sunset | https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/1k/venice_sunset_1k.hdr | CC0 1.0 | 1.4 MB | `assets/venice_sunset_1k.hdr` |

Re-download: `cd lab/scene-lowpoly-car/assets && curl -fLO <url>` for each row, then `unzip -o <zip> -d <zip without .zip>`.

## Import notes
- Kenney kits are in "kit units": city ×8 (road tile 8 m, building-a 10.3 m), cars ×1.8 (sedan 4.6 m long, 2.7 m wide, 2.1 m tall: chunky toy proportions).
- Kenney orientation: building fronts face +Y, cars face −Y. glTF import sets quaternion rotation mode.
- Quaternius human FBX: Y-up, armature rotated 90° X, 5.26 units tall → scaled to ~1.8 m and applied. 48-bone humanoid rig (Mixamo-style names: Hips, Spine, LeftUpLeg…). Ships animations kept with fake user: Idle, Walk, Run, Jump, Punch, Working, Death.
