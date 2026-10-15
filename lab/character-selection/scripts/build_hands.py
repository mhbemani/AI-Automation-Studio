"""Step 4: rebuild both hands with a real palm and separate fingers, fitted to the scan's right hand.
The right hand is lofted in the scan hand's own frame (u = length toward the knuckles, v = width toward the thumb,
w = thickness toward the palm; measured by PCA of the old hand): a palm of 8-sided rings from inside the cuff to the
knuckles, and five 6-sided finger tubes (knuckle, middle joint, last joint, tip) whose joints sit on the scan's knuckle
ridges and curled fingertips. Fingers are separate pieces pushed into the palm (no welding), flat side on the back.
The left hand is the same mesh mirrored through the hand bones (as in mirror_hand.py).
Old hands (strongest weight hand.R / hand.L) are deleted, loose vertices removed, the new wrist opening closed.
Weights: cuff ring forearm 1, wrist ring forearm/hand 0.5/0.5, everything else hand 1 (finger bones come later).
Run: Blender -b --factory-startup character_selection_lab.blend --python scripts/build_hands.py"""
import bpy, bmesh, math
from mathutils import Vector, Matrix
o = bpy.data.objects["HUM_Body"]; rig = bpy.data.objects["RIG_Human"]
for ob in (o, rig):
    bpy.context.view_layer.objects.active = ob
    if ob.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
gi = {g.name: g.index for g in o.vertex_groups}; gn = {i: n for n, i in gi.items()}
bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table(); dl = bm.verts.layers.deform.active
dom = lambda v: gn[max(v[dl].keys(), key=lambda k: v[dl][k])] if v[dl] else None

# --- scan hand frame (PCA of the old right hand, same as hand_closeup.py)
H = [v for v in bm.verts if dom(v) == "hand.R"]
F = {f for v in H for f in v.link_faces}; P = [v.co.copy() for v in {v for f in F for v in f.verts}]
c = sum(P, Vector()) / len(P)
C = Matrix(((0.0,) * 3,) * 3)
for p in P:
    d = p - c
    for i in range(3):
        for j in range(3): C[i][j] += d[i] * d[j]
ax = []
for _ in range(3):
    a = Vector((1, .3, .2))
    for _ in range(100):
        a = C @ a
        for b in ax: a -= b * a.dot(b)
        a.normalize()
    ax.append(a)
U, V, W = ax
if sum((p - c).dot(U) for p in [v.co for v in H]) < 0: U = -U          # u toward the fingers
# thumb side = +v; palm side = +w (checked on the scan: thumb tip v +0.08, curled fingertips w +0.03)
print("FRAME u", tuple(round(x, 3) for x in U), "v", tuple(round(x, 3) for x in V), "w", tuple(round(x, 3) for x in W))
X = lambda u, v, w: c + U * u + V * v + W * w

# --- delete the old hands
before = {e for e in bm.edges if e.is_boundary}
old = [v for v in bm.verts if dom(v) in ("hand.R", "hand.L")]
bmesh.ops.delete(bm, geom=old, context='VERTS')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
rim = [e for e in bm.edges if e.is_boundary and e not in before]
bmesh.ops.holes_fill(bm, edges=rim, sides=0)

# --- builders (in u, v, w)
def ring(center, d, side, rx, ry, n, phase=0.0):
    """n points around center in the plane normal to d; rx along 'side', ry along the other axis"""
    d = d.normalized(); s = (side - d * side.dot(d)).normalized(); t = d.cross(s)
    return [center + s * (rx * math.cos(phase + 2 * math.pi * k / n)) + t * (ry * math.sin(phase + 2 * math.pi * k / n)) for k in range(n)]
new = []  # (BMVert, {group: weight})
def loft(rings, weights, apex=None, close_start=True):
    vs = [[bm.verts.new(p) for p in r] for r in rings]
    for r, wt in zip(vs, weights): new.extend((v, wt) for v in r)
    n = len(rings[0])
    for a, b in zip(vs, vs[1:]):
        for k in range(n): bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
    if apex is not None:
        t = bm.verts.new(apex); new.append((t, weights[-1]))
        for k in range(n): bm.faces.new((vs[-1][k], vs[-1][(k + 1) % n], t))
    else: bm.faces.new(vs[-1])
    if close_start: bm.faces.new(list(reversed(vs[0])))
HAND = {"hand.R": 1.0}; WRIST = {"hand.R": .5, "forearm.R": .5}; CUFF = {"forearm.R": 1.0}
side_v = Vector((0, 1, 0))  # (u,v,w) space vectors are converted below
def UVW(u, v, w): return Vector((u, v, w))
def to_world(p): return X(p.x, p.y, p.z)

# palm: (u, width, thickness, centre v, centre w)
PALM = [(-0.075, .052, .034, -.004, -.004, CUFF), (-0.050, .060, .032, -.004, -.006, WRIST),
        (-0.012, .086, .032, -.010, -.008, HAND), (0.022, .090, .026, -.010, -.011, HAND)]
palm_rings = [[to_world(p) for p in ring(UVW(u, cv, cw), UVW(1, 0, 0), UVW(0, 1, 0), wd / 2, th / 2, 8, math.pi / 8)]
              for u, wd, th, cv, cw, _ in PALM]
cap = to_world(UVW(0.030, -.010, -.011))
loft(palm_rings, [p[5] for p in PALM], apex=cap)

# fingers: joints (u, v, w) from the scan: knuckle ridge -> middle joint (top of the bend) -> last joint -> tip
FINGERS = {  # name: (joints, radius at knuckle)
    "index":  ([(.012, .026, -.012), (.064, .030, -.008), (.079, .031, .006), (.073, .033, .021)], .0108),
    "middle": ([(.014, .004, -.013), (.068, .002, -.005), (.066, .000, .016), (.053, -.002, .025)], .0112),
    "ring":   ([(.012, -.019, -.012), (.062, -.022, -.005), (.059, -.021, .014), (.047, -.020, .023)], .0105),
    "pinky":  ([(.008, -.042, -.010), (.048, -.047, -.004), (.047, -.048, .010), (.037, -.050, .017)], .0090),
    "thumb":  ([(-.034, .020, .002), (-.006, .044, .010), (.011, .064, .016), (.023, .079, .020)], .0130),
}
import os
CURL = float(os.environ.get("CURL", "1"))  # 1 = the scan's curl; 0 = every segment straight along the first one
for name, (J, r0) in FINGERS.items():
    J = [UVW(*j) for j in J]
    if CURL < 1:  # keep segment lengths, blend each segment's direction toward the first segment's direction
        d0 = (J[1] - J[0]).normalized(); K = [J[0], J[1]]
        for k in (1, 2):
            seg = J[k + 1] - J[k]; d = d0.slerp(seg.normalized(), CURL)
            K.append(K[-1] + d * seg.length)
        J = K
    rings_, wts = [], []
    radii = [r0, r0 * .9, r0 * .8, r0 * .62]
    side = UVW(0, 1, 0) if name != "thumb" else UVW(0, 0, 1)
    for k, (p, r) in enumerate(zip(J[:3], radii)):
        dprev = (J[k] - J[k - 1]) if k else (J[1] - J[0])
        d = dprev.normalized() + (J[k + 1] - J[k]).normalized()
        rings_.append([to_world(q) for q in ring(p, d, side, r, r * .8, 6)])
        wts.append(HAND)
    dt = (J[3] - J[2]).normalized()
    rings_.append([to_world(q) for q in ring(J[3] - dt * .007, dt, side, radii[3], radii[3] * .8, 6)])
    wts.append(HAND)
    loft(rings_, wts, apex=to_world(J[3] + dt * .002))

# --- weights for the new right hand
for v, wt in new:
    for g, w in wt.items(): v[dl][gi[g]] = w
right = [v for v, _ in new]
# --- left hand = mirrored copy through the hand bones (same transform as mirror_hand.py)
rf = list({f for v in right for f in v.link_faces})
dup = bmesh.ops.duplicate(bm, geom=rf)
nv = [g for g in dup["geom"] if isinstance(g, bmesh.types.BMVert)]
nf = [g for g in dup["geom"] if isinstance(g, bmesh.types.BMFace)]
B = rig.data.bones
bmesh.ops.transform(bm, matrix=B["hand.L"].matrix_local @ Matrix.Scale(-1, 4, (1, 0, 0)) @ B["hand.R"].matrix_local.inverted(), verts=nv)
bmesh.ops.reverse_faces(bm, faces=nf)
swap = {gi[n]: gi[n[:-2] + ".L"] for n in gi if n.endswith(".R")}
for v in nv:
    d = v[dl]; old_w = dict(d); d.clear()
    for k, w in old_w.items(): d[swap.get(k, k)] = w
bm.normal_update(); bm.to_mesh(o.data); o.data.update()
print("HANDS old verts removed", len(old), "| new verts per hand", len(right), "faces", len(rf),
      "tris", sum(len(f.verts) - 2 for f in rf), "| total verts", len(o.data.vertices))
bpy.ops.wm.save_as_mainfile(filepath=os.environ.get("OUT", bpy.data.filepath))
