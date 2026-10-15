"""Day 2: copy the finished right hand (mesh + finger bones + weights) to the left side.
0. repair: a fingertip that is broken (a 6-sided face capping the last-joint ring from inside) is rebuilt
   along its .03 bone (tip ring + dome, last bone 100 %)
1. the left hand (vertices >= 50 % on hand.L / finger .L bones) is deleted; this re-opens the left sleeve rim
2. the right hand (same rule, .R) is duplicated and moved with  M = hand.L @ mirrorX @ hand.R^-1  (rest matrices),
   faces flipped, weights renamed .R -> .L, and its open wrist ring is stitched to the left sleeve rim
3. every finger bone .L is replaced by the mirrored .R bone (head, tail, roll), parent hand.L / previous bone
Run: Blender -b --factory-startup character_selection_lab.blend --python scripts/mirror_right_hand.py  (env OUT=)"""
import bpy, bmesh, os, math
from mathutils import Vector, Matrix
o = bpy.data.objects["HUM_Body"]; rig = bpy.data.objects["RIG_Human"]
for ob in (o, rig):
    bpy.context.view_layer.objects.active = ob
    if ob.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
gi = {g.name: g.index for g in o.vertex_groups}; gn = {i: n for n, i in gi.items()}
bm = bmesh.new(); bm.from_mesh(o.data); dl = bm.verts.layers.deform.active
cen = lambda vs: sum((v.co for v in vs), Vector()) / len(vs)
isdigit = lambda n: n.startswith(("f_", "thumb"))
def handw(v, s):
    return sum(w for k, w in v[dl].items() if gn[k].endswith("." + s) and (gn[k].startswith("hand") or isdigit(gn[k])))
def frame(n):
    a = Vector((1, 0, 0)) if abs(n.x) < .9 else Vector((0, 1, 0))
    a = (a - n * a.dot(n)).normalized(); return a, n.cross(a)
def walk(loop):
    ls = set(loop); out = [loop[0]]
    while len(out) < len(loop):
        out.append(next(e.other_vert(out[-1]) for e in out[-1].link_edges
                        if e.other_vert(out[-1]) in ls and e.other_vert(out[-1]) not in out[-2:]))
    return out
def zipper(A, B, c, n):
    A, B = walk(A), walk(B)
    sense = lambda L: sum((L[k].co - c).cross(L[(k + 1) % len(L)].co - c).dot(n) for k in range(len(L)))
    if (sense(A) > 0) != (sense(B) > 0): B.reverse()
    a, b = frame(n); ang = lambda v: math.atan2((v.co - c).dot(b), (v.co - c).dot(a))
    j0 = min(range(len(B)), key=lambda j: abs(math.remainder(ang(B[j]) - ang(A[0]), 2 * math.pi))); B = B[j0:] + B[:j0]
    def frac(L):
        d = [0.0]
        for k in range(len(L)): d.append(d[-1] + (L[(k + 1) % len(L)].co - L[k].co).length)
        return [x / d[-1] for x in d]
    fA, fB = frac(A), frac(B); out, i, j = [], 0, 0
    while i < len(A) or j < len(B):
        if j == len(B) or (i < len(A) and fA[i + 1] <= fB[j + 1]):
            out.append(bm.faces.new((A[i % len(A)], A[(i + 1) % len(A)], B[j % len(B)]))); i += 1
        else:
            out.append(bm.faces.new((A[i % len(A)], B[(j + 1) % len(B)], B[j % len(B)]))); j += 1
    return out

# ---- 0. repair broken fingertips on the right hand
# A broken tip = a 6-sided face capping a last-joint ring (.02/.03 50/50) from the inside. Everything beyond that ring
# is removed and the last segment is rebuilt along the .03 bone: tip ring (78 % radius, 7 mm before the bone's tail)
# + dome (ring at 80 % radius, top at 0.62 x radius), all 100 % on the .03 bone.
repaired = []
for f in list(bm.faces):
    if not f.is_valid or len(f.verts) != 6: continue
    names = [{gn[k] for k in v[dl].keys()} for v in f.verts]
    j03 = {n for ns in names for n in ns if n.endswith(".03.R")}
    if not (len(j03) == 1 and all(len(ns) == 2 and any(n.endswith(".02.R") for n in ns) for ns in names)): continue
    bone = j03.pop(); ring = list(f.verts)
    back = {x for v in ring for e in v.link_edges for x in [e.other_vert(v)] if any(gn[k].endswith(".01.R") for k in x[dl].keys())}
    blob, st = set(), [x for v in ring for x in (e.other_vert(v) for e in v.link_edges) if x not in ring and x not in back]
    while st:
        x = st.pop()
        if x in blob or x in ring or x in back: continue
        blob.add(x); st.extend(e.other_vert(x) for e in x.link_edges)
    if len(blob) > 40: continue                                        # safety: not a fingertip
    bb = rig.data.bones[bone]; head, tail = bb.head_local, bb.tail_local; dr = (tail - head).normalized()
    c = cen(ring)
    bmesh.ops.delete(bm, geom=[f], context='FACES_ONLY')
    bmesh.ops.delete(bm, geom=list(blob), context='VERTS')
    R6 = walk(ring)
    ct = tail - dr * 0.007
    P6 = [bm.verts.new(ct + ((v.co - c) - dr * (v.co - c).dot(dr)) * 0.78) for v in R6]
    r = sum((v.co - ct).length for v in P6) / 6
    Q = [bm.verts.new(ct + dr * (0.4 * r) + (v.co - ct) * 0.8) for v in P6]; top = bm.verts.new(ct + dr * (0.62 * r))
    for q in P6 + Q + [top]: q[dl][gi[bone]] = 1.0
    for k in range(6):
        k1 = (k + 1) % 6
        bm.faces.new((R6[k], R6[k1], P6[k1], P6[k])); bm.faces.new((P6[k], P6[k1], Q[k1], Q[k])); bm.faces.new((Q[k], Q[k1], top))
    bmesh.ops.recalc_face_normals(bm, faces=list({fa for v in R6 + P6 + Q + [top] for fa in v.link_faces}))
    repaired.append((bone, len(blob)))
if not repaired: print("MIRROR no broken tip found")

# ---- 1. delete the left hand
before = {e for e in bm.edges if e.is_boundary}
HL = [v for v in bm.verts if handw(v, "L") >= 0.5]
bmesh.ops.delete(bm, geom=HL, context='VERTS')
rimL = list({v for e in bm.edges if e.is_boundary and e not in before for v in e.verts})

# ---- 2. copy the right hand
HR = {v for v in bm.verts if handw(v, "R") >= 0.5}
FR = [f for f in bm.faces if all(v in HR for v in f.verts)]
B = rig.data.bones
M = B["hand.L"].matrix_local @ Matrix.Scale(-1, 4, (1, 0, 0)) @ B["hand.R"].matrix_local.inverted()
dup = bmesh.ops.duplicate(bm, geom=FR)
nv = [g for g in dup["geom"] if isinstance(g, bmesh.types.BMVert)]
nf = [g for g in dup["geom"] if isinstance(g, bmesh.types.BMFace)]
bmesh.ops.transform(bm, matrix=M, verts=nv)
bmesh.ops.reverse_faces(bm, faces=nf)
for name in list(gi):
    if name.endswith(".R") and name[:-2] + ".L" not in gi: gi[name[:-2] + ".L"] = o.vertex_groups.new(name=name[:-2] + ".L").index
gn = {i: n for n, i in gi.items()}
swap = {gi[k]: gi[k[:-2] + ".L"] for k in gi if k.endswith(".R")}
for v in nv:
    d = v[dl]; ow = dict(d); d.clear()
    for k, x in ow.items(): d[swap.get(k, k)] = x
wristL = [v for v in nv if any(e.is_boundary for e in v.link_edges)]
zf = zipper(rimL, wristL, (cen(rimL) + cen(wristL)) / 2, (cen(wristL) - cen(rimL)).normalized())
bmesh.ops.recalc_face_normals(bm, faces=list({f for v in rimL + wristL for f in v.link_faces}))

# ---- 3. mirror the finger bones
bpy.context.view_layer.objects.active = rig
bm.normal_update(); bm.to_mesh(o.data); o.data.update()
bpy.ops.object.mode_set(mode='EDIT'); eb = rig.data.edit_bones
M3 = M.to_3x3()
src = {b.name: (b.head.copy(), b.tail.copy(), b.z_axis.copy(), b.parent.name, b.use_connect) for b in eb if b.name.endswith(".R") and isdigit(b.name)}
for name in [b.name for b in eb if b.name.endswith(".L") and isdigit(b.name)]: eb.remove(eb[name])
for name in sorted(src, key=lambda n: n[-4:]):  # .01 before .02 before .03
    h, t, z, par, con = src[name]; nb = eb.new(name[:-2] + ".L")
    nb.head = M @ h; nb.tail = M @ t; nb.align_roll(M3 @ z)
    nb.parent = eb[par[:-2] + ".L"]; nb.use_connect = con
bpy.ops.object.mode_set(mode='OBJECT')
bm2 = bmesh.new(); bm2.from_mesh(o.data)
print("MIRROR repaired tips", repaired, "| left removed", len(HL), "copied", len(nv), "verts", len(nf), "faces | wrist stitched", len(zf),
      "| open edges", sum(e.is_boundary for e in bm2.edges), "non-manifold", sum(not e.is_manifold for e in bm2.edges), "| finger bones mirrored", len(src))
bpy.ops.wm.save_as_mainfile(filepath=os.environ.get("OUT", bpy.data.filepath))
