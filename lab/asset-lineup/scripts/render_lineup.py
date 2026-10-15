"""Render one camera of the lineup headlessly.
  Blender -b lab/asset-lineup/lineup.blend --python lab/asset-lineup/scripts/render_lineup.py -- \
      --camera LU_CAM_Overview --preset draft|final --light studio|golden --out file.png
Never saves the .blend."""
import bpy, sys, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lineup_lib as L
p = argparse.ArgumentParser()
p.add_argument("--camera", default="LU_CAM_Overview")
p.add_argument("--preset", default="draft", choices=["draft", "final"])
p.add_argument("--light", default=None, choices=["studio", "golden"])
p.add_argument("--out", required=True)
p.add_argument("--isolate", default="auto", choices=["auto", "off"],
               help="auto: per-asset (_Front/_34) cameras show only that asset, Compare cameras only the pair; labels hidden for both (NEW plinths teal-tinted, OLD amber-tinted)")
a = p.parse_args(sys.argv[sys.argv.index("--") + 1:])
sc = bpy.context.scene
cam = bpy.data.objects.get(a.camera) or bpy.data.objects.get("LU_CAM_" + a.camera)
assert cam, "no such camera: " + a.camera
sc.camera = cam
if a.isolate == "auto":
    name = cam.name[len("LU_CAM_"):]
    assets = [c for c in bpy.data.collections["LU_Assets"].children]
    labels = bpy.data.collections.get("LU_Labels")
    show = None
    if name.endswith(("_Front", "_34")):
        key = name.rsplit("_", 1)[0]                       # e.g. NEW_Claude or NEW_Phone5x
        show = {"LU_NEW_Phone_5x" if key == "NEW_Phone5x" else "LU_OLD_Phone_5x" if key == "OLD_Phone5x" else "LU_" + key}
        if labels: labels.hide_render = True
    elif name.startswith("Compare_"):
        k = name.split("_", 1)[1]
        show = {"LU_NEW_Claude", "LU_V3_Claude", "LU_OLD_Claude"} if k == "Claude3" else {"LU_V3_Claude", "LU_V3A_Claude", "LU_V3B_Claude", "LU_V3C_Claude"} if k == "Cute" else {"LU_NEW_" + k, "LU_OLD_" + k}
        if labels: labels.hide_render = True              # placards would cover the small subjects; NEW plinths are teal-tinted, OLD amber-tinted
    if show:
        for c in assets:
            c.hide_render = c.name not in show
        keys = [n[3:] for n in show]                          # plinths of the other assets would peek out behind the subject
        for o in bpy.data.objects:
            if o.name.startswith("LU_Plinth_"):
                o.hide_render = not any(o.name == "LU_Plinth_" + k for k in keys)
if a.light:
    L.apply_light(a.light, sc)
sc.render.resolution_x, sc.render.resolution_y = (960, 540) if a.preset == "draft" else (1920, 1080)
sc.render.resolution_percentage = 100
sc.eevee.taa_render_samples = 16 if a.preset == "draft" else 32
sc.render.filepath = str(Path(a.out).resolve())
sc.render.image_settings.file_format = "PNG"
bpy.ops.render.render(write_still=True)
print("rendered", cam.name, sc["lineup_light"], a.preset, "->", sc.render.filepath)
