"""Penetration metric: pose the rig (pose_test.py poses), evaluate the mesh with and without HUM_Contact, and count
shin/foot vertices that are inside the thigh surface (and vice versa) and the deepest one, per leg.
Run: Blender -b --factory-startup <blend> --python scripts/measure_contact.py -- <pose> [<pose> ...]"""
import bpy, sys, os, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
poses = sys.argv[sys.argv.index("--") + 1:]
o = bpy.data.objects["HUM_Body"]; gi = {g.name: g.index for g in o.vertex_groups}
src = open(os.path.join(os.path.dirname(__file__), "pose_test.py")).read()
setup = src.split("for op, name, *v in P[pose]:")[0].replace("pose = args[1]", "pose = None")
def w(v, names): return sum(g.weight for g in v.groups if g.group in [gi[n] for n in names])
def measure():
    dg = bpy.context.evaluated_depsgraph_get(); me = o.evaluated_get(dg).to_mesh()
    res = []
    for s in "LR":
        A = [i for i, v in enumerate(o.data.vertices) if w(v, [f"thigh.{s}"]) > 0.5]
        Bv = [i for i, v in enumerate(o.data.vertices) if w(v, [f"shin.{s}", f"foot.{s}"]) > 0.5]
        for P_, Q_ in ((A, Bv), (Bv, A)):
            Ps = set(P_)
            faces = [list(p.vertices) for p in me.polygons if all(i in Ps for i in p.vertices)]
            bvh = BVHTree.FromPolygons([v.co for v in me.vertices], faces)
            n_in, deep = 0, 0.0
            for i in Q_:
                p = me.vertices[i].co; loc, nor, fi, dist = bvh.find_nearest(p)
                if loc is not None and dist < 0.04 and (loc - p).dot(nor) > 0.002: n_in += 1; deep = max(deep, dist)
            res.append((n_in, deep))
    o.evaluated_get(dg).to_mesh_clear()
    return [(a[0] + b[0], max(a[1], b[1])) for a, b in (res[0:2], res[2:4])]
for pose in poses:
    exec(setup.replace("pose = None", f"pose = {pose!r}"))
    for op, name, *v in P[pose]:
        {"aim": lambda: aim(name, v[0]), "turn": lambda: turn(name, v[0], v[1]), "move": lambda: move(name, v[0])}[op]()
    bpy.context.view_layer.update()
    m = o.modifiers.get("HUM_Contact"); out = {}
    for state in (False, True):
        if m: m.show_viewport = state
        if not m and state: break
        out["with" if state else "without"] = measure()
    print("MEASURE", pose, {k: [f"L {a} verts inside, deepest {b*1000:.0f} mm" if i == 0 else f"R {a} verts inside, deepest {b*1000:.0f} mm" for i, (a, b) in enumerate(v)] for k, v in out.items()})
    for pb in rig.pose.bones: pb.matrix_basis.identity()
