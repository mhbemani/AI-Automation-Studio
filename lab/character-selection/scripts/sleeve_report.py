"""Sleeve health around the elbows at REST: radius profile along the arm and self-intersections.
For each arm, sleeve vertices (strongest weight upper_arm/forearm) are sliced every 2 cm along the arm (shoulder ->
wrist, elbow = 0): mean / min radius from the bone line. Self-intersections: triangle pairs of the sleeve that cross
each other (not sharing a vertex). Run: Blender -b <blend> --python scripts/sleeve_report.py"""
import bpy, bmesh, collections
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import intersect_point_line
o = bpy.data.objects["HUM_Body"]; B = bpy.data.objects["RIG_Human"].data.bones
gn = {g.index: g.name for g in o.vertex_groups}
bm = bmesh.new(); bm.from_mesh(o.data); dl = bm.verts.layers.deform.active
bm.verts.ensure_lookup_table()
dom = lambda v: gn[max(v[dl].keys(), key=lambda k: v[dl][k])] if v[dl] else ""
for s in "LR":
    S, E, W = B[f"upper_arm.{s}"].head_local, B[f"forearm.{s}"].head_local, B[f"forearm.{s}"].tail_local
    sv = [v for v in bm.verts if dom(v) in (f"upper_arm.{s}", f"forearm.{s}")]
    prof = collections.defaultdict(list)
    for v in sv:
        best = None
        for a, b, sign in ((S, E, -1), (E, W, 1)):
            q, t = intersect_point_line(v.co, a, b)
            if 0 <= t <= 1:
                d = (v.co - q).length; along = (q - E).length * sign
                if best is None or d < best[0]: best = (d, along, v.co - q)
        if best: prof[round(best[1] / 0.02) * 2].append(best)
    line = " ".join(f"{k:+d}:{sum(x[0] for x in r)/len(r)*100:.1f}/{min(x[0] for x in r)*100:.1f}" for k, r in sorted(prof.items()) if -16 <= k <= 16)
    off = " ".join(f"{k:+d}:{(sum((x[2] for x in r), Vector())/len(r)).length*100:.1f}" for k, r in sorted(prof.items()) if -16 <= k <= 16)
    print(f"SLEEVE {s} radius cm (along arm cm: mean/min) {line}")
    print(f"SLEEVE {s} bone off-centre cm (slice centroid to bone) {off}")
    faces = [f for f in bm.faces if all(dom(v) in (f"upper_arm.{s}", f"forearm.{s}") for v in f.verts) and
             min((v.co - E).length for v in f.verts) < 0.15]
    tris = []
    for f in faces:
        vs = [v.index for v in f.verts]
        for k in range(1, len(vs) - 1): tris.append((vs[0], vs[k], vs[k + 1]))
    bvh = BVHTree.FromPolygons([v.co for v in bm.verts], tris, all_triangles=True)
    pairs = [(a, b) for a, b in bvh.overlap(bvh) if a < b and not set(tris[a]) & set(tris[b])]
    print(f"SLEEVE {s} elbow-zone triangles {len(tris)}, crossing pairs {len(pairs)}")
