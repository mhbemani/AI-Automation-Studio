"""Step 5: weld the right hand's fingers and thumb to the palm, round the fingertips, mirror the result to the left.
Fingers: the palm's knuckle ring + cap are removed; each finger's base cap is removed and its base ring slid along the
  finger onto the old knuckle plane. The new knuckle edge is the outline (convex hull) of the 4 finger rings, so the
  palm narrows/widens to exactly fit the fingers; the palm's previous ring is stitched to that outline (zipper
  triangles), and the small valleys between neighbouring fingers are filled and triangulated.
Thumb: its base ring is pressed onto the nearest palm faces (projected along the palm normal), those faces are
  opened (grown until the ring fits inside) and the opening is stitched to the ring.
Tips: the sharp 6-triangle cone becomes a dome (one extra ring at 80 % radius, apex at 0.62 x radius, smoothed once).
Left hand: deleted and replaced by a mirrored copy of the right (bone rest matrices, .R -> .L weights).
Run: Blender -b --factory-startup character_selection_lab.blend --python scripts/weld_fingers.py   (env OUT=path to save elsewhere)"""
import bpy, bmesh, os, math
from mathutils import Vector, Matrix
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
side_islands = lambda s: [i for i in islands() if sum(dom(v) == f"hand.{s}" for v in i) > len(i) / 2]

def frame(n):
    a = Vector((1, 0, 0)) if abs(n.x) < .9 else Vector((0, 1, 0))
    a = (a - n * a.dot(n)).normalized(); return a, n.cross(a)
def angle(p, c, n, a, b):
    d = p - c; return math.atan2(d.dot(b), d.dot(a))
def zipper(A, B, c, n):
    """stitch two closed loops (lists of BMVerts) around centre c / axis n with triangles"""
    a, b = frame(n)
    A = sorted(A, key=lambda v: angle(v.co, c, n, a, b)); B = sorted(B, key=lambda v: angle(v.co, c, n, a, b))
    ang = lambda v: angle(v.co, c, n, a, b)
    j0 = min(range(len(B)), key=lambda j: abs(math.remainder(ang(B[j]) - ang(A[0]), 2 * math.pi)))
    B = B[j0:] + B[:j0]
    out, i, j = [], 0, 0
    unwrap = lambda v, base: base + (math.remainder(ang(v) - base, 2 * math.pi) % (2 * math.pi))
    a0 = ang(A[0])
    while i < len(A) or j < len(B):
        ta = unwrap(A[(i + 1) % len(A)], a0) if i < len(A) else 9e9
        tb = unwrap(B[(j + 1) % len(B)], a0) if j < len(B) else 9e9
        if i == len(A) - 1: ta = 2 * math.pi + a0 if i < len(A) else ta
        if j == len(B) - 1: tb = 2 * math.pi + a0 if j < len(B) else tb
        if ta <= tb: out.append(bm.faces.new((A[i % len(A)], A[(i + 1) % len(A)], B[j % len(B)]))); i += 1
        else: out.append(bm.faces.new((A[i % len(A)], B[(j + 1) % len(B)], B[j % len(B)]))); j += 1
    return out
def hull2d(pts):  # monotone chain; pts = [(x, y, item)]
    pts = sorted(pts, key=lambda p: (p[0], p[1]))
    cross = lambda o_, a_, b_: (a_[0] - o_[0]) * (b_[1] - o_[1]) - (a_[1] - o_[1]) * (b_[0] - o_[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return [p[2] for p in lo[:-1] + up[:-1]]

R = side_islands("R"); palm = max(R, key=len); digits = [i for i in R if i is not palm]
assert len(digits) == 5 and len(palm) == 33, [len(i) for i in R]
apex = next(v for v in palm if len(v.link_faces) == 8 and all(len(f.verts) == 3 for f in v.link_faces))
K = [e.other_vert(apex) for e in apex.link_edges]
M = list({e.other_vert(k) for k in K for e in k.link_edges} - set(K) - {apex})
assert len(M) == 8
wrist = [v for v in palm if dom(v) == "forearm.R"]
n = (apex.co - cen(wrist)).normalized(); pc = cen(K)
def digit(isl):
    base = next(f for f in {f for v in isl for f in v.link_faces} if len(f.verts) == 6)
    tip = next(v for v in isl if len(v.link_faces) == 6 and all(len(f.verts) == 3 for f in v.link_faces))
    ring = list(base.verts)
    nxt = [e.other_vert(v) for v in ring for e in v.link_edges if e.other_vert(v) not in ring]
    return dict(base=base, ring=ring, d=(cen(nxt) - cen(ring)).normalized(), tip=tip)
P = {id(i): digit(i) for i in digits}
thumb = max(digits, key=lambda i: (cen(P[id(i)]["ring"]) - pc).dot(-n))   # deepest base along the palm axis
fingers = [i for i in digits if i is not thumb]

# ---- fingers
for isl in fingers:
    p = P[id(isl)]
    for v in p["ring"]: v.co = v.co + p["d"] * ((pc - v.co).dot(n) / p["d"].dot(n))
    bmesh.ops.delete(bm, geom=[p["base"]], context='FACES_ONLY')
bmesh.ops.delete(bm, geom=[apex], context='VERTS')
a, b = frame(n)
ring_vs = [v for isl in fingers for v in P[id(isl)]["ring"]]
H = hull2d([((v.co - pc).dot(a), (v.co - pc).dot(b), v) for v in ring_vs])
# knuckle band: the palm's last ring takes the finger outline's shape, BAND below the fingers
BAND = 0.008
hp = [((v.co - pc).dot(a), (v.co - pc).dot(b)) for v in H]
for k in K:
    t = math.atan2((k.co - pc).dot(b), (k.co - pc).dot(a)); dx, dy = math.cos(t), math.sin(t)
    best = None
    for (x1, y1), (x2, y2) in zip(hp, hp[1:] + hp[:1]):   # ray from the centre to the outline
        den = dx * (y2 - y1) - dy * (x2 - x1)
        if abs(den) < 1e-12: continue
        r_ = (x1 * (y2 - y1) - y1 * (x2 - x1)) / den; u_ = (x1 * dy - y1 * dx) / den
        if r_ > 0 and -1e-9 <= u_ <= 1 + 1e-9 and (best is None or r_ < best): best = r_
    k.co = pc + a * (dx * best) + b * (dy * best) - n * BAND
M = K
zf = zipper(M, H, pc, n)
valley_edges = [e for e in bm.edges if len(e.link_faces) == 1 and all(v in ring_vs for v in e.verts)]
vf = bmesh.ops.holes_fill(bm, edges=valley_edges, sides=0)["faces"]
vt = bmesh.ops.triangulate(bm, faces=vf, quad_method='BEAUTY', ngon_method='BEAUTY')["faces"]

# ---- thumb
p = P[id(thumb)]
palm_now = [f for f in {f for v in M for f in v.link_faces} | {f for v in palm if v.is_valid for f in v.link_faces}
            if all(v.is_valid for v in f.verts) and not any(v in ring_vs for v in f.verts)]
palm_now = [f for f in palm_now if f.is_valid]
pv = list({v for f in palm_now for v in f.verts}); pi = {v: i for i, v in enumerate(pv)}
bvh = BVHTree.FromPolygons([v.co for v in pv], [[pi[v] for v in f.verts] for f in palm_now])
tc = cen(p["ring"]); s, ns, fi, _ = bvh.find_nearest(tc)
F0 = palm_now[fi]; ns = F0.normal.copy(); loop = list(F0.verts)
print("WELD thumb: base centre %.1f mm from palm, palm face %s mm, ring radius %.1f mm" % ((tc - s).length * 1000, [round(e.calc_length() * 1000) for e in F0.edges], sum((v.co - tc).length for v in p["ring"]) / 6 * 1000))
fa, fb = frame(ns); to2 = lambda q: ((q - s).dot(fa), (q - s).dot(fb))
poly = [to2(v.co) for v in loop]
def inside(pt, m=0.002):
    x, y = pt; c = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1): c = not c
    if not c: return False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):  # margin from every side
        ex, ey = x2 - x1, y2 - y1; L = math.hypot(ex, ey)
        if abs((x - x1) * ey - (y - y1) * ex) / L < m: return False
    return True
if min(e.calc_length() for e in F0.edges) < 2.2 * (sum((v.co - tc).length for v in p["ring"]) / 6):
    longE = sorted(F0.edges, key=lambda e: e.calc_length())[-2:]
    nb = [f for e in longE for f in e.link_faces if f is not F0 and f in palm_now]
    hole_faces = [F0] + nb
    ns = sum((f.normal for f in hole_faces), Vector()).normalized(); fa, fb = frame(ns)
    hv = {v for f in hole_faces for v in f.verts}
    bnd = [e for f in hole_faces for e in f.edges if sum(lf in hole_faces for lf in e.link_faces) == 1]
    loop = [bnd[0].verts[0]]
    while len(loop) < len(bnd):
        loop.append(next(e.other_vert(loop[-1]) for e in bnd if loop[-1] in e.verts and e.other_vert(loop[-1]) not in loop[-2:]))
    poly = [to2(v.co) for v in loop]
else: hole_faces = [F0]
proj = {v: v.co - ns * (v.co - s).dot(ns) for v in p["ring"]}
shrink = 1.0
while not all(inside(to2(q)) for q in proj.values()) and shrink > 0.3:
    proj = {v: s + (q - s) * 0.95 for v, q in proj.items()}; shrink *= 0.95
hole = set(hole_faces)
bmesh.ops.delete(bm, geom=[p["base"]], context='FACES_ONLY')
bmesh.ops.delete(bm, geom=list(hole), context='FACES_ONLY')
bmesh.ops.delete(bm, geom=[e for e in bm.edges if not e.link_faces], context='EDGES')
for v, q in proj.items(): v.co = q
zt = zipper(loop, p["ring"], s, ns)
hole_loop = loop
bmesh.ops.smooth_vert(bm, verts=list(set(loop) | set(p["ring"])), factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
print("WELD thumb base fitted into", len(hole), "palm faces, base ring scaled to %.0f %%" % (shrink * 100))

# ---- fingertips
for isl in digits:
    t = P[id(isl)]["tip"]; R6 = [e.other_vert(t) for e in t.link_edges]
    c = cen(R6); prev = list({e.other_vert(v) for v in R6 for e in v.link_edges} - set(R6) - {t})
    ax = (c - cen(prev)).normalized(); r = sum((v.co - c).length for v in R6) / 6
    ordered = [R6[0]]  # walk the tip ring by its edges (angle sorting fails on a twisted ring)
    while len(ordered) < 6:
        ordered.append(next(e.other_vert(ordered[-1]) for e in ordered[-1].link_edges
                            if e.other_vert(ordered[-1]) in R6 and e.other_vert(ordered[-1]) not in ordered[-2:]))
    R6 = ordered
    w = dict(t[dl]); bmesh.ops.delete(bm, geom=[t], context='VERTS')
    Q = [bm.verts.new(c + ax * (0.4 * r) + (v.co - c) * 0.8) for v in R6]; top = bm.verts.new(c + ax * (0.62 * r))
    for q in Q + [top]:
        for k, x in w.items(): q[dl][k] = x
    for k in range(6):
        bm.faces.new((R6[k], R6[(k + 1) % 6], Q[(k + 1) % 6], Q[k])); bm.faces.new((Q[k], Q[(k + 1) % 6], top))
    bmesh.ops.smooth_vert(bm, verts=Q + [top], factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)  # evens out twisted tips

right = [v for i in side_islands("R") for v in i]
# safety: close any small gap left between the stitched parts (no degenerate-dissolve: it collapsed a narrow fingertip)
gaps = bmesh.ops.holes_fill(bm, edges=list({e for v in right for e in v.link_edges if e.is_boundary}), sides=12)["faces"]
bmesh.ops.triangulate(bm, faces=gaps, quad_method='BEAUTY', ngon_method='BEAUTY')
right_isl = side_islands("R"); right = [v for i in right_isl for v in i]
rf = list({f for v in right for f in v.link_faces})
bmesh.ops.recalc_face_normals(bm, faces=rf)
bad = sum(not e.is_manifold for f in rf for e in f.edges) // 1
deg = sum(f.calc_area() < 1e-7 for f in rf)
print("WELD knuckle outline", len(H), "verts; zipper", len(zf), "valleys", len(vf), "-> tris", len(vt),
      "| thumb opening", len(hole), "faces, loop", len(hole_loop), "zipper", len(zt),
      "| right hand pieces", len(right_isl), "verts", len(right), "tris", sum(len(f.verts) - 2 for f in rf),
      "| non-manifold edge refs", bad, "degenerate faces", deg, "| gaps closed", len(gaps))

# ---- mirror to the left
oldL = [v for i in side_islands("L") for v in i]
bmesh.ops.delete(bm, geom=oldL, context='VERTS')
dup = bmesh.ops.duplicate(bm, geom=rf)
nv = [g for g in dup["geom"] if isinstance(g, bmesh.types.BMVert)]
nf = [g for g in dup["geom"] if isinstance(g, bmesh.types.BMFace)]
B = rig.data.bones
bmesh.ops.transform(bm, matrix=B["hand.L"].matrix_local @ Matrix.Scale(-1, 4, (1, 0, 0)) @ B["hand.R"].matrix_local.inverted(), verts=nv)
bmesh.ops.reverse_faces(bm, faces=nf)
swap = {gi[k]: gi[k[:-2] + ".L"] for k in gi if k.endswith(".R")}
for v in nv:
    dd = v[dl]; ow = dict(dd); dd.clear()
    for k, x in ow.items(): dd[swap.get(k, k)] = x
bm.normal_update(); bm.to_mesh(o.data); o.data.update()
print("WELD left hand: removed", len(oldL), "added", len(nv))
bpy.ops.wm.save_as_mainfile(filepath=os.environ.get("OUT", bpy.data.filepath))
