"""Download the CC0 assets listed in ASSETS.md into assets/ (skips files already there).
Usage: python3 scripts/fetch_assets.py   (plain Python, no Blender needed)
The BlenderKit human (assets/blenderkit/oscar_1K.blend) is fetched by hand through the add-on, see ASSETS.md."""
import json, os, sys, urllib.request, zipfile, io

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
UA = {"User-Agent": "studio-lab/1.0"}

# Poly Haven: (asset, resolution). Textures: diffuse/normal(GL)/roughness/AO JPGs. Models: glTF + textures.
PH_HDRI = [("sunset_jhbcentral", "2k")]
PH_TEX = [("asphalt_02", "2k"), ("concrete_pavement", "2k"), ("brushed_concrete", "1k"),
          ("brown_leather", "1k"), ("beige_wall_001", "1k")]
PH_MODELS = [("street_lamp_02", "1k"), ("fire_hydrant", "1k"), ("metal_trash_can", "1k"),
             ("modular_street_seating", "1k"), ("utility_box_01", "1k"), ("water_manhole_cover", "1k")]
# ambientCG facade sets: (asset, zip attribute)
ACG = [("Facade001", "2K-JPG"), ("Facade006", "2K-JPG"), ("Facade017", "1K-JPG"), ("Facade020A", "1K-JPG")]
TEX_MAPS = {"Diffuse": "diff", "nor_gl": "nor_gl", "Rough": "rough", "AO": "ao"}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA)).read()


def save(url, path):
    if os.path.exists(path):
        return 0
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = get(url)
    with open(path, "wb") as f:
        f.write(data)
    print(f"  {len(data)/1e6:6.1f} MB  {os.path.relpath(path, ROOT)}")
    return len(data)


def main():
    total = 0
    for a, r in PH_HDRI:
        f = json.loads(get(f"https://api.polyhaven.com/files/{a}"))["hdri"][r]["hdr"]
        total += save(f["url"], f"{ROOT}/polyhaven/hdri/{a}_{r}.hdr")
    for a, r in PH_TEX:
        files = json.loads(get(f"https://api.polyhaven.com/files/{a}"))
        for key, short in TEX_MAPS.items():
            if key in files:
                f = files[key][r]["jpg"]
                total += save(f["url"], f"{ROOT}/polyhaven/textures/{a}/{a}_{short}_{r}.jpg")
    for a, r in PH_MODELS:
        g = json.loads(get(f"https://api.polyhaven.com/files/{a}"))["gltf"][r]["gltf"]
        d = f"{ROOT}/polyhaven/models/{a}"
        total += save(g["url"], f"{d}/{os.path.basename(g['url'])}")
        for rel, inc in g.get("include", {}).items():
            total += save(inc["url"], f"{d}/{rel}")
    for a, attr in ACG:
        d = f"{ROOT}/ambientcg/{a}"
        if os.path.isdir(d):
            continue
        data = get(f"https://ambientcg.com/get?file={a}_{attr}.zip")
        zipfile.ZipFile(io.BytesIO(data)).extractall(d)
        total += len(data)
        print(f"  {len(data)/1e6:6.1f} MB  ambientcg/{a} ({attr})")
    print(f"downloaded {total/1e6:.1f} MB")
    # polygon/memory diet: 1K copies of the 2K texture sets (2K textures were the main GPU-memory driver), made locally
    import glob, subprocess
    for f in glob.glob(f"{ROOT}/polyhaven/textures/*/*_2k.jpg") + glob.glob(f"{ROOT}/ambientcg/*/*_2K-JPG_*.jpg"):
        o = f.replace("_2k.jpg", "_1k.jpg").replace("_2K-JPG_", "_1K-JPG_")
        if not os.path.exists(o): subprocess.run(["sips", "-Z", "1024", f, "--out", o], check=True, capture_output=True)


if __name__ == "__main__":
    sys.exit(main())
