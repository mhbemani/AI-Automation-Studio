"""Re-append the human from the selection lab's saved file and put it back on its plinth; nothing else in the lineup changes
(except the human's label text and the two LU_CAM_NEW_Human_* cameras, which are refitted).
Close the lineup in any Blender window first (this script writes lineup.blend), then run:
  Blender -b lab/asset-lineup/lineup.blend --python lab/asset-lineup/scripts/refresh_human.py [-- --no-copy]
--no-copy: reuse snapshots/human_snapshot.blend instead of copying the selection lab file again.
The selection lab file is only read (copied), never opened in place or written."""
import bpy, sys, shutil, math
from pathlib import Path
from mathutils import Vector, Matrix
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lineup_lib as L

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if "--no-copy" not in ARGS:
    if L.SNAP.exists():
        shutil.copy2(L.SNAP, L.SNAP.with_name("human_snapshot_prev.blend"))
    shutil.copy2(L.SRC_HUMAN, L.SNAP)
sc = bpy.context.scene
coll = bpy.data.collections["LU_NEW_Human"]
for o in list(coll.objects):
    bpy.data.objects.remove(o)
rig, objs = L.append_human(L.SNAP, coll)
L.settle()
x, y = 15.5, L.ROW_Y["NEW"]   # same slot as in build_lineup.py (COL_X["Human"])
L.put_on_plinth(rig, objs, (x, y))
lo, hi = L.world_bbox(objs)
tris = L.tri_count(objs)
dims = tuple(round(v, 3) for v in (hi - lo))
rig["lineup_source"] = {"file": str(L.SRC_HUMAN), "object": "RIG_Human + HUM_Body", "git": f"snapshot sha1 {L.sha1(L.SNAP)}"}
rig["lineup_tris"] = tris; rig["lineup_objects"] = len(objs); rig["lineup_dims_m"] = list(dims)
t = bpy.data.objects.get("LU_Label_NEW_Human_info")
if t:
    t.data.body = f"{tris:,} tris   {' x '.join(f'{v:.2f}' for v in dims)} m"
for suffix, az, el in (("Front", -90, 8), ("34", -50, 18)):
    cam = bpy.data.objects[f"LU_CAM_NEW_Human_{suffix}"]
    L.fit_camera(cam, lo, hi, az, el, margin=0.10, lens=70)
sc.camera = bpy.data.objects["LU_CAM_Overview"]
bpy.data.orphans_purge(do_recursive=True)
try:
    bpy.ops.file.pack_all()
except Exception as e:
    print("pack_all:", e)
bpy.ops.wm.save_mainfile()
print("human refreshed:", tris, "tris", dims, "m")
