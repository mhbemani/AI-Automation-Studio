"""Rig test helpers (run inside Blender). exec(open(...).read()) then call functions."""
import bpy, json, math, mathutils
from mathutils import Matrix, Vector

def reset_pose(rig, neutral=True):
    for pb in rig.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    if neutral and "neutral_pose" in rig:
        for n, m in json.loads(rig["neutral_pose"]).items():
            if n in rig.pose.bones: rig.pose.bones[n].matrix_basis = Matrix(m)
    bpy.context.view_layer.update()

def rot_world(rig, bone, axis, deg):
    """rotate a pose bone about a world axis through its head."""
    pb = rig.pose.bones[bone]
    M = pb.matrix.copy(); h = M.translation.copy()
    R = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h)
    pb.matrix = R @ M
    bpy.context.view_layer.update()

def move_world(rig, bone, vec):
    pb = rig.pose.bones[bone]; M = pb.matrix.copy(); M.translation += Vector(vec); pb.matrix = M
    bpy.context.view_layer.update()

def rest_edges(me):
    return [(e.vertices[0], e.vertices[1]) for e in me.edges]

_REST = {}
def metrics(body):
    """stretch/foldover numbers of the evaluated mesh against the rest mesh."""
    dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); me = ev.to_mesh()
    base = body.data
    if "e" not in _REST or _REST["n"] != len(base.vertices):
        _REST["n"] = len(base.vertices); _REST["e"] = rest_edges(base)
        _REST["len"] = [(base.vertices[a].co - base.vertices[b].co).length for a, b in _REST["e"]]
        _REST["fn"] = [p.normal.copy() for p in base.polygons]
    worst, bad = 0.0, 0
    for (a, b), l0 in zip(_REST["e"], _REST["len"]):
        l = (me.vertices[a].co - me.vertices[b].co).length
        r = l / max(l0, 1e-4)
        worst = max(worst, r, 1 / max(r, 1e-3) if l0 > 0.01 else 0)
        if (r > 2.0 or r < 0.4) and l0 > 0.01: bad += 1
    flipped = sum(1 for p, n0 in zip(me.polygons, _REST["fn"]) if p.normal.dot(n0) < -0.5)
    zs = [v.co.z for v in me.vertices]
    out = dict(max_stretch=round(worst, 2), bad_edges=bad, flipped_faces=flipped, zmin=round(min(zs), 3), zmax=round(max(zs), 3),
               xspan=round(max(v.co.x for v in me.vertices) - min(v.co.x for v in me.vertices), 3))
    ev.to_mesh_clear()
    return out
