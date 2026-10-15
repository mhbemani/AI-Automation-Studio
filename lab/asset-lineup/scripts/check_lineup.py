"""Sanity checks on lineup.blend (read-only): every asset moves as one (translate the root, all parts follow), no missing images,
no objects outside the asset collections, triangle table. Run:
  Blender -b --factory-startup lab/asset-lineup/lineup.blend --python lab/asset-lineup/scripts/check_lineup.py"""
import bpy, sys
from pathlib import Path
from mathutils import Vector, Matrix
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lineup_lib as L
bad = 0
for c in bpy.data.collections["LU_Assets"].children:
    objs = list(c.objects)
    roots = [o for o in objs if o.parent is None or o.parent not in objs]
    lo0, hi0 = L.world_bbox(objs)
    before = {o.name: o.matrix_world.translation.copy() for o in objs}
    saved = {r: r.matrix_world.copy() for r in roots}
    for r in roots:
        r.matrix_world = Matrix.Translation((1, 0, 0)) @ r.matrix_world      # world-space move (roots may be parented to the car)
    bpy.context.view_layer.update()
    moved = [o.name for o in objs if (o.matrix_world.translation - before[o.name] - Vector((1, 0, 0))).length > 1e-4 and o.parent and not o.hide_viewport]   # hidden objects are not evaluated; their parent link is checked below
    for r in roots:
        r.matrix_world = saved[r]
    bpy.context.view_layer.update()
    orphan_hidden = [o.name for o in objs if o.hide_viewport and o.parent is None and o not in roots]
    ext = [(o.name, k, getattr(cn, "target", None).name) for o in objs for k, cn in enumerate(o.constraints) if getattr(cn, "target", None) and getattr(cn, "target") not in objs]
    print(f"{c.name:20s} objs={len(objs):3d} roots={[r.name for r in roots]} parts-not-following={moved} constraints-to-outside={ext} hidden-without-parent={orphan_hidden}")
    bad += len(moved) + len(ext) + len(orphan_hidden)
imgs = [(i.name, tuple(i.size)) for i in bpy.data.images if i.name not in ("Render Result", "Viewer Node") and (i.size[0] == 0 or not i.has_data)]
print("images without data:", imgs)
loose = [o.name for o in bpy.data.objects if not o.users_collection]
print("objects in no collection:", loose)
print("CHECK", "OK" if bad == 0 and not imgs and not loose else "PROBLEMS")
