"""Step 6: connect each hand to its sleeve.
The sleeve's wrist cap (the face that closed the opening when the old hand was removed) is found by casting a ray
from the hand's wrist ring toward the elbow; it is removed, which re-opens the sleeve rim. The hand's cuff ring
(the stub hidden inside the sleeve) and its cap are removed, which opens the hand's wrist ring. Rim and wrist ring
are stitched with triangles (zipper), so the sleeve hem now runs into the wrist.
Run: Blender -b --factory-startup character_selection_lab.blend --python scripts/connect_hands.py   (env OUT=, DRY=1)"""
import bpy, bmesh, os, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
o = bpy.data.objects["HUM_Body"]; rig = bpy.data.objects["RIG_Human"]
for ob in (o, rig):
    bpy.context.view_layer.objects.active = ob
    if ob.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
gi = {g.name: g.index for g in o.vertex_groups}; gn = {i: n for n, i in gi.items()}
bm = bmesh.new(); bm.from_mesh(o.data); dl = bm.verts.layers.deform.active
dom = lambda v: gn[max(v[dl].keys(), key=lambda k: v[dl][k])] if v[dl] else None
cen = lambda vs: sum((v.co for v in vs), Vector()) / len(vs)
def islands():
    seen, out = set(), []
    for v in bm.verts:
        if v in seen: continue
        st, c = [v], []; seen.add(v)
        while st:
            a = st.pop(); c.append(a)
            for e in a.link_edges:
                b = e.other_vert(a)
                if b not in seen: seen.add(b); st.append(b)
        out.append(c)
    return out
def frame(n):
    a = Vector((1, 0, 0)) if abs(n.x) < .9 else Vector((0, 1, 0))
    a = (a - n * a.dot(n)).normalized(); return a, n.cross(a)
def walk(loop):
    """order a closed loop of vertices by following the edges between them (works for uneven, concave rims)"""
    ls = set(loop); out = [loop[0]]
    while len(out) < len(loop):
        out.append(next(e.other_vert(out[-1]) for e in out[-1].link_edges
                        if e.other_vert(out[-1]) in ls and e.other_vert(out[-1]) not in out[-2:]))
    return out
def zipper(A, B, c, n):
    """stitch two closed loops with triangles, matching them by arc length (not by angle)"""
    A, B = walk(A), walk(B)
    sense = lambda L: sum((L[k].co - c).cross(L[(k + 1) % len(L)].co - c).dot(n) for k in range(len(L)))
    if (sense(A) > 0) != (sense(B) > 0): B.reverse()
    a, b = frame(n); ang = lambda v: math.atan2((v.co - c).dot(b), (v.co - c).dot(a))
    j0 = min(range(len(B)), key=lambda j: abs(math.remainder(ang(B[j]) - ang(A[0]), 2 * math.pi))); B = B[j0:] + B[:j0]
    def frac(L):
        d = [0.0]
        for k in range(len(L)): d.append(d[-1] + (L[(k + 1) % len(L)].co - L[k].co).length)
        return [x / d[-1] for x in d]
    fA, fB = frac(A), frac(B)
    out, i, j = [], 0, 0
    while i < len(A) or j < len(B):
        if j == len(B) or (i < len(A) and fA[i + 1] <= fB[j + 1]):
            out.append(bm.faces.new((A[i % len(A)], A[(i + 1) % len(A)], B[j % len(B)]))); i += 1
        else:
            out.append(bm.faces.new((A[i % len(A)], B[(j + 1) % len(B)], B[j % len(B)]))); j += 1
    return out
report = []
for s in "RL":
    isl = islands()
    hand = next(i for i in isl if sum(dom(v) == f"hand.{s}" for v in i) > len(i) / 2)
    body = max(isl, key=len)
    r0 = [v for v in hand if dom(v) == f"forearm.{s}"]
    cap0 = next(f for f in {f for v in r0 for f in v.link_faces} if all(v in r0 for v in f.verts))
    r1 = list({e.other_vert(v) for v in r0 for e in v.link_edges} - set(r0))
    axis = (cen(r0) - cen(r1)).normalized()               # from the wrist toward the elbow
    bf = list({f for v in body for f in v.link_faces})
    bvh = BVHTree.FromPolygons([v.co for v in body], [[body.index(v) for v in f.verts] for f in bf]) if False else None
    vi = {v: k for k, v in enumerate(body)}
    bvh = BVHTree.FromPolygons([v.co for v in body], [[vi[v] for v in f.verts] for f in bf])
    loc, nor, fi, dist = bvh.ray_cast(cen(r1), axis, 0.25)
    cap = bf[fi]
    report.append(f"{s}: sleeve cap {len(cap.verts)}-sided, {dist*1000:.0f} mm from the wrist ring; hand cuff ring {len(r0)}, wrist ring {len(r1)}")
    if os.environ.get("DRY") == "1": continue
    rim = list(cap.verts)
    if os.environ.get("DBG"):
        ax_ = (cen(r1) - cen(rim)).normalized(); fa, fb = frame(ax_); cc = (cen(rim) + cen(r1)) / 2
        for nm_, L_ in (("rim", rim), ("wrist", r1)):
            print("DBG", s, nm_, sorted((round(math.degrees(math.atan2((v.co - cc).dot(fb), (v.co - cc).dot(fa)))), round((v.co - cc - ax_ * (v.co - cc).dot(ax_)).length * 1000)) for v in L_))
    bmesh.ops.delete(bm, geom=[cap], context='FACES_ONLY')
    bmesh.ops.delete(bm, geom=r0, context='VERTS')       # removes the cuff ring, its cap and the cuff->wrist band
    c = (cen(rim) + cen(r1)) / 2
    zf = zipper(rim, r1, c, (cen(r1) - cen(rim)).normalized())   # sort around the line joining the two rings
    bmesh.ops.recalc_face_normals(bm, faces=list({f for v in rim + r1 for f in v.link_faces}))
    report.append(f"   stitched with {len(zf)} triangles; open edges near this wrist: {sum(e.is_boundary for v in rim + r1 for e in v.link_edges)}")
print("CONNECT", " | ".join(report))
if os.environ.get("DRY") == "1": raise SystemExit
allf = list(bm.faces)
print("CONNECT islands", sorted(map(len, islands()), reverse=True)[:6], "| non-manifold edges", sum(not e.is_manifold for e in bm.edges),
      "| degenerate", sum(f.calc_area() < 1e-7 for f in allf))
bm.normal_update(); bm.to_mesh(o.data); o.data.update()
bpy.ops.wm.save_as_mainfile(filepath=os.environ.get("OUT", bpy.data.filepath))
