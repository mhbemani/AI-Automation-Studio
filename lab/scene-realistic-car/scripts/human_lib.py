# The human, polygon diet (2026-10-09): BlenderKit "Lowpoly Male Standing" (Hyperreality Lowpoly, Royalty Free), a 3K-tri
# faceted scan in a "checking the phone" pose (hands together at the chest), no rig, no colours, no face features.
# Builds 00_LIB objects with the SAME names the scene used for Oscar, so build_characters.py / animate.py keep working:
#   LIB_Human        armature: a lean FK rig with the Rigify CONTROL names the scripts drive (torso, spine_fk..003, neck,
#                    head, shoulder.L/R, upper_arm_fk/forearm_fk/hand_fk.L/R, thigh_fk/shin_fk/foot_fk.L/R, the
#                    thigh_parent/upper_arm_parent.L/R holders with an "IK_FK" property, DEF-hand.R for the phone).
#                    Axis conventions as measured on Oscar: spine/neck/head +X nods forward, thigh -X lifts the leg
#                    forward, shin/forearm +X bends. REST POSE = the scan's pose (arms bent, hands at the chest), not a
#                    T-pose, so pose values differ from Oscar's (re-tuned in build_characters.py).
#   LIB_Human_Mesh   the scan, scaled to 1.75 m, auto-weighted; materials by region (skin, hair, hoodie, joggers, shoes)
#   LIB_Human_Face   mouth + eyelids in one small mesh, bone-parented to "head", shape keys per emotion
#                    (neutral basis + happy, curious, excited, surprised, thoughtful, proud, amused) + MouthOpen + Blink
#   LIB_Human_Eye_L/R small black oval dots, bone-parented to "head"
# Run from import_assets.py (exec) with `lib`, `to_lib`, `A` defined. Palette: PALETTE below (creator: no preference).
import bpy, bmesh, math
from mathutils import Vector, Matrix

SRC = A + "blenderkit/lowpoly_male.blend"
H = 1.75
PALETTE = {"skin": (0.80, 0.56, 0.42), "hair": (0.10, 0.07, 0.05), "hoodie": (0.03, 0.24, 0.27),   # option 1 (recommended):
           "pants": (0.08, 0.09, 0.13), "shoes": (0.88, 0.88, 0.85),                                 # teal hoodie, navy joggers,
           "mouth": (0.015, 0.012, 0.012), "eye": (0.012, 0.010, 0.010)}                             # white sneakers; black dot eyes + mouth

for o in [o for o in bpy.data.objects if o.name.startswith("LIB_Human")]: bpy.data.objects.remove(o)

def mat(name, color, rough=0.7, emit=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; b = m.node_tree.nodes.get("Principled BSDF") or m.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough
    if emit: b.inputs["Emission Color"].default_value = (*color, 1); b.inputs["Emission Strength"].default_value = emit
    m.diffuse_color = (*color, 1); return m
M = {k: mat(f"MAT_Human_{k.capitalize()}", c, 0.3 if k == "eye" else 0.75) for k, c in PALETTE.items()}

# --- mesh: append, scale to H, feet on z=0, centred on x/y
with bpy.data.libraries.load(SRC, link=False) as (src, dst):
    dst.objects = list(src.objects)
body = next(o for o in dst.objects if o and o.type == "MESH"); to_lib([body])
body.name = body.data.name = "LIB_Human_Scan"
me = body.data; me.transform(body.matrix_world); body.matrix_world = Matrix()
vs = [v.co for v in me.vertices]; lo = Vector([min(v[i] for v in vs) for i in range(3)]); hi = Vector([max(v[i] for v in vs) for i in range(3)])
S = H / (hi.z - lo.z)
me.transform(Matrix.Scale(S, 4) @ Matrix.Translation((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z)))
J = lambda x, y, z: Vector((x, y, z)) * S        # joint positions picked on the unscaled scan (ortho views), then scaled

# --- materials by region (the scan is one fused mesh)
me.materials.clear()
for k in ("hoodie", "skin", "hair", "pants", "shoes"): me.materials.append(M[k])
HEAD_C, HANDS_C = J(0, 0.0, 1.78), J(0.04, -0.33, 1.40)
HC = Vector((0.027, 0.052, 1.676))   # head centre (metres, measured on the scaled scan)
def head_fix(c, n, k):   # per-polygon head pass (2026-10-09): short hair above the ears, skin face/ears/jaw, hood stays hood
    d = c - HC; r = d.xy.length; th = abs(math.degrees(math.atan2(d.x, -d.y)))   # th: 0 = front, 180 = back
    if c.z < 1.45 or r > 0.15: return k
    if k == "hoodie": return "hair" if (th > 115 and c.z > 1.61 and r < 0.105) else k   # hood triangles poking into the back hair
    if c.z < 1.53 and n.z > 0.3: return "hoodie"                                       # upward-facing folds of the hood collar
    return "hair" if c.z > (1.70 if th < 50 else 1.65 if th < 115 else 1.61) else "skin"   # hairline: forehead / above ears / nape
for p in me.polygons:
    c = p.center; k = "hoodie"
    if c.z < 0.10 * S: k = "shoes"
    elif c.z < 0.93 * S: k = "pants"
    elif c.z > 1.66 * S and Vector((c.x - HEAD_C.x, c.y - HEAD_C.y)).length < (0.115 if c.z < 1.74 * S else 0.16) * S:   # head (not the hood)
        k = "hair" if (c.z > 1.87 * S or (c.y > 0.03 * S and c.z > 1.72 * S)) else "skin"
    elif (c - HANDS_C).length < 0.13 * S and c.y < -0.22 * S: k = "skin"
    k = head_fix(c, p.normal, k)
    p.material_index = ("hoodie", "skin", "hair", "pants", "shoes").index(k)
me.polygons.foreach_set("use_smooth", [False] * len(me.polygons))   # the faceted scan look stays (game style)

# --- armature: Rigify CONTROL names, joints MEASURED on the scaled scan (slice centroids / point clusters, 2026-10-09);
# every bone lies inside the body; helper bones (torso, *_parent) are short and tucked in; thin stick display.
arm_d = bpy.data.armatures.new("LIB_Human"); rig = bpy.data.objects.new("LIB_Human", arm_d); to_lib([rig])
arm_d.display_type = "STICK"
lc_ = bpy.context.view_layer.layer_collection.children["00_LIB"]; lc_.exclude = False
bpy.context.view_layer.objects.active = rig
with bpy.context.temp_override(active_object=rig, object=rig, selected_objects=[rig]):
    bpy.ops.object.mode_set(mode="EDIT")
eb = arm_d.edit_bones
V = Vector
JT = {  # character's left = +X, forward = -Y (metres, the 1.75 m scan)
    "hips": V((0, 0.10, 0.88)), "sp1": V((0, 0.10, 1.03)), "sp2": V((0, 0.08, 1.19)), "sp3": V((0, 0.09, 1.34)),
    "neck0": V((0, 0.12, 1.47)), "head0": V((0.01, 0.11, 1.56)), "headtop": V((0.02, 0.07, 1.76)),
    "sh.L": V((0.16, 0.10, 1.42)), "el.L": V((0.24, -0.03, 1.27)), "wr.L": V((0.08, -0.20, 1.28)), "ht.L": V((0.01, -0.27, 1.29)),
    "sh.R": V((-0.16, 0.12, 1.41)), "el.R": V((-0.22, 0.01, 1.25)), "wr.R": V((-0.08, -0.19, 1.27)), "ht.R": V((-0.01, -0.27, 1.28)),
    "hip.L": V((0.11, 0.08, 0.86)), "kn.L": V((0.13, 0.07, 0.48)), "an.L": V((0.18, 0.08, 0.10)), "to.L": V((0.19, -0.11, 0.03)),
    "hip.R": V((-0.11, 0.10, 0.86)), "kn.R": V((-0.15, 0.10, 0.47)), "an.R": V((-0.21, 0.14, 0.10)), "to.R": V((-0.26, -0.03, 0.03)),
}
def bone(name, h, t, parent=None, deform=True):
    b = eb.new(name); b.head, b.tail = h, t; b.use_deform = deform
    if parent: b.parent = eb[parent]; b.use_connect = False
    d = (b.tail - b.head).normalized(); z = V((1, 0, 0)).cross(d)       # local X = world +X: X nods / bends forward
    b.align_roll(z if z.length > 0.3 else V((0, 0, 1)))
    return b
J_ = JT
bone("torso", J_["hips"], J_["hips"] + V((0, 0, 0.06)), deform=False)
bone("spine_fk", J_["hips"], J_["sp1"], "torso")
bone("spine_fk.001", J_["sp1"], J_["sp2"], "spine_fk")
bone("spine_fk.002", J_["sp2"], J_["sp3"], "spine_fk.001")
bone("spine_fk.003", J_["sp3"], J_["neck0"], "spine_fk.002")
bone("neck", J_["neck0"], J_["head0"], "spine_fk.003")
bone("head", J_["head0"], J_["headtop"], "neck")
for s in ("L", "R"):
    bone(f"shoulder.{s}", J_["sp3"] + V((0, 0.02, 0.06)), J_[f"sh.{s}"], "spine_fk.003")
    bone(f"upper_arm_parent.{s}", J_[f"sh.{s}"], J_[f"sh.{s}"] + V((0, 0, 0.04)), f"shoulder.{s}", deform=False)
    bone(f"upper_arm_fk.{s}", J_[f"sh.{s}"], J_[f"el.{s}"], f"shoulder.{s}")
    bone(f"forearm_fk.{s}", J_[f"el.{s}"], J_[f"wr.{s}"], f"upper_arm_fk.{s}")
    bone(f"hand_fk.{s}", J_[f"wr.{s}"], J_[f"ht.{s}"], f"forearm_fk.{s}")
    bone(f"thigh_parent.{s}", J_[f"hip.{s}"], J_[f"hip.{s}"] + V((0, 0, 0.04)), "torso", deform=False)
    bone(f"thigh_fk.{s}", J_[f"hip.{s}"], J_[f"kn.{s}"], "torso")
    bone(f"shin_fk.{s}", J_[f"kn.{s}"], J_[f"an.{s}"], f"thigh_fk.{s}")
    bone(f"foot_fk.{s}", J_[f"an.{s}"], J_[f"to.{s}"], f"shin_fk.{s}")
bone("DEF-hand.R", eb["hand_fk.R"].head.copy(), eb["hand_fk.R"].tail.copy(), "hand_fk.R", deform=False)
with bpy.context.temp_override(active_object=rig, object=rig, selected_objects=[rig]):
    bpy.ops.object.mode_set(mode="OBJECT")
for n in ("thigh_parent.L", "thigh_parent.R", "upper_arm_parent.L", "upper_arm_parent.R"): rig.pose.bones[n]["IK_FK"] = 1.0
for pb in rig.pose.bones: pb.rotation_mode = "XYZ"
body.parent = None

# --- face parts (head-local layout from the scan: face front ~ y -0.075, eyes at z ~1.735, mouth ~1.675, unscaled)
dg = bpy.context.evaluated_depsgraph_get()
def front(x, z):   # where the face surface is at (x, z): ray from the front
    hit, loc, n, i = body.ray_cast(Vector((x, -2.0, z)), Vector((0, 1, 0)))
    return loc if hit else Vector((x, -0.07 * S, z))
EYE_Z, MOUTH_Z, EX = 1.805 * S, 1.728 * S, 0.029 * S   # eyes ~1.63 m on the 1.75 m figure
def head_child(name, me_, mats):
    for m in mats: me_.materials.append(m)
    o = bpy.data.objects.new(name, me_); to_lib([o])
    o.parent = rig; o.parent_type = "BONE"; o.parent_bone = "head"
    bpy.context.view_layer.update()
    hb_ = rig.data.bones["head"]   # rest matrix of the head bone, at its tail (bone parenting attaches at the tail)
    o.matrix_parent_inverse = (rig.matrix_world @ hb_.matrix_local @ Matrix.Translation((0, hb_.length, 0))).inverted()
    return o
EW, EH = 0.0075 * S, 0.0105 * S   # eye = small black oval dot (half width / half height), same place as before
for s, sx in (("L", 1), ("R", -1)):
    p = front(sx * EX, EYE_Z) + Vector((0, 0.002 * S, 0))
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=1.0,
                                                matrix=Matrix.Translation(p) @ Matrix.Diagonal((EW, 0.004 * S, EH, 1)))
    for f in bm.faces: f.smooth = True
    em = bpy.data.meshes.new(f"LIB_Human_Eye_{s}"); bm.to_mesh(em); bm.free()
    head_child(f"LIB_Human_Eye_{s}", em, [M["eye"]])

# mouth (8-segment line) + upper eyelids (skin, closed by "Blink"): one mesh. No brows (creator, 2026-10-09)
fb = bmesh.new(); groups = {}
def strip(tag, pts, half_h, mi, depth=0.004 * S):
    vs_ = []
    for q in pts:
        a = fb.verts.new(q + Vector((0, -depth, half_h))); b_ = fb.verts.new(q + Vector((0, -depth, -half_h))); vs_.append((a, b_))
    for (a1, b1), (a2, b2) in zip(vs_, vs_[1:]):
        f = fb.faces.new((a1, a2, b2, b1)); f.material_index = mi
    groups[tag] = [v for pair in vs_ for v in pair]
for s, sx in (("L", 1), ("R", -1)):
    lid = [front(sx * (EX + (i - 2) * 0.0050 * S), EYE_Z + EH + 0.002 * S) + Vector((0, -0.005 * S, 0)) for i in range(5)]
    strip(f"lid_{s}", lid, 0.0012 * S, 1, depth=0.0)
mouth = [front((i - 4) * 0.0045 * S, MOUTH_Z + (abs(i - 4) * 0.0003) * S) for i in range(9)]
strip("mouth", mouth, 0.0018 * S, 0)
fm = bpy.data.meshes.new("LIB_Human_Face")
fb.verts.index_update(); idx = {k: [v.index for v in vv] for k, vv in groups.items()}
fb.to_mesh(fm); fb.free()
face = head_child("LIB_Human_Face", fm, [M["mouth"], M["skin"]])
for p in fm.polygons: p.use_smooth = True

# shape keys (offsets in the face mesh's own space = scan space): emotions + MouthOpen + Blink
face.shape_key_add(name="Basis", from_mix=False)
def key(name, fn):
    k = face.shape_key_add(name=name, from_mix=False)
    for tag, ids in idx.items():
        n = len(ids) // 2
        for j, vi in enumerate(ids):
            col = j // 2; u = (col / max(1, n - 1)) * 2 - 1                # -1..1 along the strip
            k.data[vi].co = fm.vertices[vi].co + Vector(fn(tag, u, j % 2)) * S
    return k
U = 0.002   # expression strength (the mouth is a small black line now; offsets are mouth/lid moves, no brows)
M_ = lambda f: (lambda t, u, b: (0, 0, f(u, b) * U) if t == "mouth" else (0, 0, 0))
key("happy",      M_(lambda u, b: 4 * u * u - 1.5))
key("curious",    lambda t, u, b: (0, 0, -0.8 * U * u) if t == "mouth" else ((0, 0, 1.5 * U) if t == "lid_L" else (0, 0, 0)))
key("excited",    M_(lambda u, b: 5 * u * u - 2.5 - (3 if b else 0)))
key("surprised",  lambda t, u, b: (0, 0, -6 * U * (1 - u * u)) if (t == "mouth" and b) else ((0, 0, 2 * U) if t.startswith("lid") else (0, 0, 0)))
key("thoughtful", lambda t, u, b: (0, 0, -1.0 * U * (1 - u * u)) if t == "mouth" else (0, 0, -1.5 * U))
key("proud",      lambda t, u, b: (0, 0, (2.5 * u * u - 0.8) * U) if t == "mouth" else (0, 0, -1.0 * U))
key("amused",     M_(lambda u, b: 3.0 * max(u, 0) ** 2 - 0.5))
key("MouthOpen",  M_(lambda u, b: -5 * (1 - u * u) if b else 0))
key("Blink",      lambda t, u, b: (0, 0, -(2 * EH / S + 0.004) if b == 1 else -0.002) if t.startswith("lid") else (0, 0, 0))   # the lid's lower edge drops over the eye
# --- the body as RIGID PIECES (creator, 2026-10-09: "break the character into pieces"). The scan is one fused shell
# (the arms touch the chest), so: 1) CORES are labelled directly (spine/head axis, tight capsules around the limb bones,
# the feet); 2) the rest is filled by growing over the surface from the cores (Dijkstra), giving five chains (torso,
# arm.L/R, leg.L/R); 3) inside a chain the pieces are split by PLANES through the joints (clean straight cuts); the
# torso by heights, the hood stays with the chest; 4) labels are smoothed and stray fragments merged, so every piece is
# one chunk; 5) cuts are capped and each piece is bone-parented (rigid).
import heapq, collections as _c
PARENT = {"Mesh": "spine_fk.003", "Pelvis": "spine_fk", "Belly": "spine_fk.001", "Neck": "neck", "Head": "head",
          **{f"{n}.{s}": f"{b}.{s}" for s in ("L", "R") for n, b in (("UpperArm", "upper_arm_fk"), ("Forearm", "forearm_fk"),
             ("Hand", "hand_fk"), ("Thigh", "thigh_fk"), ("Shin", "shin_fk"), ("Foot", "foot_fk"))}}
def seg_dist(p, a_, b_):
    ab = b_ - a_; t = max(0.0, min(1.0, (p - a_).dot(ab) / ab.length_squared)); return (p - (a_ + ab * t)).length
bmw = bmesh.new(); bmw.from_mesh(me); bmw.verts.ensure_lookup_table(); bmw.faces.ensure_lookup_table()
NV = len(bmw.verts); chain = [None] * NV
axis = [(J_["hips"], J_["neck0"]), (J_["neck0"], J_["headtop"])]
for v in bmw.verts:
    p = v.co
    if 0.80 < p.z < 1.47 and abs(p.x) < 0.12 and p.y > -0.02: chain[v.index] = "torso"
    if p.z > 1.43 and seg_dist(p, *axis[1]) < 0.13: chain[v.index] = "torso"
    for s in ("L", "R"):
        if seg_dist(p, J_[f"sh.{s}"], J_[f"el.{s}"]) < 0.05 or seg_dist(p, J_[f"el.{s}"], J_[f"wr.{s}"]) < 0.045 \
           or seg_dist(p, J_[f"wr.{s}"], J_[f"ht.{s}"]) < 0.045: chain[v.index] = f"arm.{s}"
        if (p.z < 0.80 and seg_dist(p, J_[f"hip.{s}"], J_[f"an.{s}"]) < 0.09) or (p.z < 0.14 and (p.x > 0) == (s == "L")):
            chain[v.index] = f"leg.{s}"
dist = [0.0 if c else float("inf") for c in chain]; heap = [(0.0, i) for i, c in enumerate(chain) if c]; heapq.heapify(heap)
while heap:
    d0, i = heapq.heappop(heap)
    if d0 > dist[i]: continue
    for e in bmw.verts[i].link_edges:
        j = e.other_vert(bmw.verts[i]).index; nd = d0 + e.calc_length()
        if nd < dist[j]: dist[j] = nd; chain[j] = chain[i]; heapq.heappush(heap, (nd, j))
def side(p, joint, d1, d2):   # >0: beyond the joint plane (normal = mean direction of the two bones)
    n = ((d1).normalized() + (d2).normalized()).normalized(); return (p - joint).dot(n)
def piece_of(c, p):
    if c == "torso":
        if p.z > 1.50 and seg_dist(p, *axis[1]) < 0.12: return "Head"        # down to the jaw: the whole face turns
        if p.z > 1.43 and seg_dist(p, *axis[1]) < 0.085: return "Neck"       # the hood around it stays with the chest
        if p.z < J_["sp1"].z: return "Pelvis"
        if p.z < J_["sp2"].z: return "Belly"
        return "Mesh"
    s = c[-1]
    if c.startswith("arm"):
        u, f_, h = J_[f"el.{s}"] - J_[f"sh.{s}"], J_[f"wr.{s}"] - J_[f"el.{s}"], J_[f"ht.{s}"] - J_[f"wr.{s}"]
        if side(p, J_[f"wr.{s}"], f_, h) > 0: return f"Hand.{s}"
        if side(p, J_[f"el.{s}"], u, f_) > 0: return f"Forearm.{s}"
        return f"UpperArm.{s}"
    t_, sh_, ft = J_[f"kn.{s}"] - J_[f"hip.{s}"], J_[f"an.{s}"] - J_[f"kn.{s}"], J_[f"to.{s}"] - J_[f"an.{s}"]
    if p.z < J_[f"an.{s}"].z + 0.03: return f"Foot.{s}"
    if side(p, J_[f"kn.{s}"], t_, sh_) > 0: return f"Shin.{s}"
    return f"Thigh.{s}"
face_lab = [piece_of(_c.Counter(chain[v.index] for v in f.verts).most_common(1)[0][0], f.calc_center_median()) for f in bmw.faces]
adj = [[g.index for e in f.edges for g in e.link_faces if g is not f] for f in bmw.faces]
for _ in range(3):   # majority smoothing of the labels (removes saw-tooth borders)
    new_lab = face_lab[:]
    for i, nb in enumerate(adj):
        cnt = _c.Counter(face_lab[j] for j in nb)
        top, n_ = cnt.most_common(1)[0]
        if top != face_lab[i] and n_ >= 2: new_lab[i] = top
    face_lab = new_lab
for _ in range(4):   # every piece = its largest connected chunk; smaller fragments join their neighbours
    changed = False
    for piece in set(face_lab):
        ids = {i for i, l in enumerate(face_lab) if l == piece}; comps = []
        while ids:
            st_ = [ids.pop()]; comp = set(st_)
            while st_:
                i = st_.pop()
                for j in adj[i]:
                    if j in ids: ids.remove(j); comp.add(j); st_.append(j)
            comps.append(comp)
        comps.sort(key=len, reverse=True)
        for comp in comps[1:]:
            nbl = _c.Counter(face_lab[j] for i in comp for j in adj[i] if j not in comp)
            if nbl:
                tgt = nbl.most_common(1)[0][0]
                for i in comp: face_lab[i] = tgt
                changed = True
    if not changed: break
bmw.free()
PIECES = PARENT
pieces_made = {}
for piece in PIECES:
    ids = {i for i, l in enumerate(face_lab) if l == piece}
    if not ids: continue
    pm = me.copy(); pm.name = "LIB_Human_" + piece
    bm = bmesh.new(); bm.from_mesh(pm); bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in ids], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    border = [e for e in bm.edges if e.is_boundary]
    near = _c.Counter(f.material_index for e in border for f in e.link_faces)
    cap = bmesh.ops.holes_fill(bm, edges=border, sides=0)["faces"]
    for f in cap: f.material_index = near.most_common(1)[0][0] if near else 0
    if cap: bmesh.ops.triangulate(bm, faces=cap)
    bm.to_mesh(pm); bm.free()
    for p_ in pm.polygons: p_.use_smooth = False
    o = bpy.data.objects.new("LIB_Human_" + piece, pm); to_lib([o])
    o.parent = rig; o.parent_type = "BONE"; o.parent_bone = PARENT[piece]
    bb = arm_d.bones[PARENT[piece]]
    o.matrix_parent_inverse = (rig.matrix_world @ bb.matrix_local @ Matrix.Translation((0, bb.length, 0))).inverted()
    pieces_made[piece] = len(pm.polygons)
old_me = body.data; bpy.data.objects.remove(body); bpy.data.meshes.remove(old_me)
weighted = f"rigid pieces: {pieces_made}"
tris = lambda o: sum(len(p.vertices) - 2 for p in o.data.polygons)
human_report = {"scale": round(S, 4), "pieces": weighted,
                "tris": {o.name: tris(o) for o in bpy.data.objects if o.name.startswith("LIB_Human") and o.type == "MESH"}}
