"""Rule check: how far do chest/back vertices move when only the arms move?
Chest/back = vertices between 1.05 m and 1.5 m height whose x is within 12 cm of the body centre line (well away
from the sleeves). Prints mean / max movement per pose. Run: Blender -b <blend> --python scripts/measure_chest_drag.py -- <pose> ..."""
import bpy, sys, os
poses = sys.argv[sys.argv.index("--") + 1:]
o = bpy.data.objects["HUM_Body"]
src = open(os.path.join(os.path.dirname(__file__), "pose_test.py")).read()
setup = src.split("for op, name, *v in P[pose]:")[0]
xc = bpy.data.objects["RIG_Human"].data.bones["chest"].head_local.x
def evaluated():
    dg = bpy.context.evaluated_depsgraph_get(); me = o.evaluated_get(dg).to_mesh()
    co = [v.co.copy() for v in me.vertices]; o.evaluated_get(dg).to_mesh_clear(); return co
for pose in poses:
    exec(setup.replace("pose = args[1]", f"pose = {pose!r}"))
    for pb in rig.pose.bones: pb.matrix_basis.identity()
    bpy.context.view_layer.update(); rest = evaluated()
    idx = [i for i, p in enumerate(rest) if 1.05 < p.z < 1.5 and abs(p.x - xc) < 0.12]
    for op, name, *v in P[pose]:
        {"aim": lambda: aim(name, v[0]), "turn": lambda: turn(name, v[0], v[1]), "move": lambda: move(name, v[0])}[op]()
    bpy.context.view_layer.update(); posed = evaluated()
    d = sorted((posed[i] - rest[i]).length for i in idx)
    print("DRAG %-10s chest/back vertices %d: mean %.1f mm, 90%% %.1f mm, max %.1f mm" % (pose, len(d), sum(d) / len(d) * 1000, d[int(.9 * len(d))] * 1000, d[-1] * 1000))
