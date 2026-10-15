"""Human face (milestone 2): HUM_Face = thin decal mesh on the scan's face (eyes, lids, lashes, brows, mouth) with the
shape keys the scene expects (Blink, MouthOpen, happy, curious, excited, surprised, thoughtful, proud, amused) and eye bones.
Also weights the chin of HUM_Body to the jaw bone. Idempotent; run after 01 and 02 (bridge, cwd lab/animation-build)."""
import bpy, math, os
from mathutils import Vector as V
ROOT = os.environ.get("ANIM_ROOT") or os.path.dirname(os.path.abspath(__import__("bpy").data.filepath))
exec(open(os.path.join(ROOT, "scripts", "face_spec.py")).read())
S = SPEC
OFF = dict(sclera=0.0030, iris=0.0036, glint=0.0042, lid=0.0046, lash=0.0050, brow=0.0042, mouth=0.0034)
MATS = dict(sclera=("HUM_eyewhite", "f4f1ea", .5), iris=("HUM_iris", "231e2a", .25), glint=("HUM_eyewhite", None, 0), lid=("HUM_skin", None, 0),
            lash=("HUM_lash", "231b17", .2), brow=("HUM_brow", "3a2d26", .1), mouth=("HUM_mouth", "6a2a2e", .25))
def lin(c): return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def getmat(name, hexc, emit=0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True
    if hexc:
        c = [lin(int(hexc[i:i + 2], 16) / 255) for i in (0, 2, 4)]
        b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'); b.inputs["Base Color"].default_value = (*c, 1); b.inputs["Roughness"].default_value = 0.6
        m.diffuse_color = (*c, 1)
        if emit:
            b.inputs["Emission Color"].default_value = (*c, 1); b.inputs["Emission Strength"].default_value = emit
    return m

# ---- parametric vertices: (feature, side, x, z) + role data; key deltas are functions of those
class P:  # a decal vertex
    def __init__(s, feat, side, x, z, **kw): s.feat, s.side, s.x, s.z, s.kw = feat, side, x, z, kw
verts, faces, fmat = [], [], []
def add(feat, side, x, z, **kw): verts.append(P(feat, side, x, z, **kw)); return len(verts) - 1
def tri(a, b, c, feat): faces.append((a, b, c)); fmat.append(feat)
def quad(a, b, c, d, feat): tri(a, b, c, feat); tri(a, c, d, feat)

NCOL = 7
for side, sx in (("L", 1), ("R", -1)):
    ex, ez, a, b = S["cx"] + sx * S["eye_dx"], S["eye_z"], S["eye_a"], S["eye_b"]
    # sclera: fan of 12
    c = add("sclera", side, ex, ez, role="c"); ring = [add("sclera", side, ex + a * math.cos(k * math.pi / 6), ez + b * math.sin(k * math.pi / 6), role="ring", ang=k * 30) for k in range(12)]
    for k in range(12): tri(c, ring[k], ring[(k + 1) % 12], "sclera")
    # iris: fan of 10 (moves with the eye bone), glint
    c = add("iris", side, ex, ez, role="c"); rr = 0.0072
    ring = [add("iris", side, ex + rr * math.cos(k * 2 * math.pi / 10), ez + rr * math.sin(k * 2 * math.pi / 10), role="ring") for k in range(10)]
    for k in range(10): tri(c, ring[k], ring[(k + 1) % 10], "iris")
    gx, gz, gs = ex - sx * 0.0025, ez + 0.0030, 0.0018
    g = [add("glint", side, gx + dx, gz + dz, role="g") for dx, dz in ((-gs, -gs), (gs, -gs), (gs, gs), (-gs, gs))]
    quad(*g, "glint")
    # upper lid (skin) + lash line: columns across the eye. top row above the eye, bottom row = lid edge
    cols = [-1 + 2 * i / (NCOL - 1) for i in range(NCOL)]
    lt = [add("lid", side, ex + u * (a + 0.001), ez + b * math.sqrt(max(1 - u * u, 0)) + 0.0045, role="lidtop", u=u) for u in cols]
    lb = [add("lid", side, ex + u * (a + 0.001), ez + b * math.sqrt(max(1 - u * u, 0)), role="lidbot", u=u) for u in cols]
    for i in range(NCOL - 1): quad(lt[i], lt[i + 1], lb[i + 1], lb[i], "lid")
    lk = [add("lash", side, ex + u * (a + 0.001), ez + b * math.sqrt(max(1 - u * u, 0)) - 0.0016, role="lash", u=u) for u in cols]
    for i in range(NCOL - 1): quad(lb[i], lb[i + 1], lk[i + 1], lk[i], "lash")
    # lower lid (skin): bottom row fixed at the eye's lower edge, top row rises on squint
    ub = [add("lid", side, ex + u * (a + 0.001), ez - b * math.sqrt(max(1 - u * u, 0)) - 0.0045, role="lowbot", u=u) for u in cols]
    ut = [add("lid", side, ex + u * (a + 0.001), ez - b * math.sqrt(max(1 - u * u, 0)), role="lowtop", u=u) for u in cols]
    for i in range(NCOL - 1): quad(ub[i], ub[i + 1], ut[i + 1], ut[i], "lid")
    # brow: 6 columns inner -> outer, two rows
    BC = 6
    top, bot = [], []
    for j in range(BC):
        t = j / (BC - 1); x = S["cx"] + sx * (S["brow_dx_in"] + t * (S["brow_dx_out"] - S["brow_dx_in"]))
        zc = S["brow_z"] + 0.004 * math.sin(t * math.pi * 0.9) - 0.004 * t * t
        th = 0.0085 * (1 - 0.35 * t)
        top.append(add("brow", side, x, zc + th / 2, role="browtop", t=t)); bot.append(add("brow", side, x, zc - th / 2, role="browbot", t=t))
    for j in range(BC - 1): quad(top[j], top[j + 1], bot[j + 1], bot[j], "brow")
# mouth: columns across, top and bottom lip rows
MC = 9; mt, mbm = [], []
for i in range(MC):
    u = -1 + 2 * i / (MC - 1)
    mt.append(add("mouth", None, S["cx"] + u * S["mouth_hw"], S["mouth_z"], role="mtop", u=u)); mbm.append(add("mouth", None, S["cx"] + u * S["mouth_hw"], S["mouth_z"] - 0.0025 * (1 - 0.3 * abs(u)), role="mbot", u=u))
for i in range(MC - 1): quad(mt[i], mt[i + 1], mbm[i + 1], mbm[i], "mouth")

# ---- shape-key parameters. eye: (sv scale, fT upper lid lowered 0..1, fB lower lid raised 0..1); brow: (inner dz, outer dz, dx_in); mouth dict
KEYS = {
 "Blink":      dict(eyeL=(1, 1, .1), eyeR=(1, 1, .1), brL=(-.002, -.002), brR=(-.002, -.002)),
 "MouthOpen":  dict(mouth=dict(open=.016, w=.9)),
 "happy":      dict(eyeL=(1, .10, .5), eyeR=(1, .10, .5), brL=(.005, .006), brR=(.005, .006), mouth=dict(smile=.011, w=1.15)),
 "curious":    dict(eyeL=(1.3, 0, 0), eyeR=(.85, .3, 0), brL=(.022, .016), brR=(-.003, -.006), mouth=dict(smile=-.001, asym=.003, w=.7, open=.004, shift=.004)),
 "excited":    dict(eyeL=(1.25, 0, 0), eyeR=(1.25, 0, 0), brL=(.014, .015), brR=(.014, .015), mouth=dict(smile=.011, w=1.2, open=.016)),
 "surprised":  dict(eyeL=(1.4, 0, 0), eyeR=(1.4, 0, 0), brL=(.019, .019), brR=(.019, .019), mouth=dict(w=.5, open=.019)),
 "thoughtful": dict(eyeL=(1, .38, 0), eyeR=(1, .38, 0), brL=(.011, -.001), brR=(.005, -.005), mouth=dict(smile=-.002, w=.7, shift=-.006)),
 "proud":      dict(eyeL=(1, .38, .05), eyeR=(1, .38, .05), brL=(-.003, .001), brR=(-.003, .001), mouth=dict(smile=.006, w=1.0)),
 "amused":     dict(eyeL=(1, .12, .75), eyeR=(1, .2, .25), brL=(.012, .010), brR=(-.004, -.004), mouth=dict(smile=.002, asym=.013, w=1.05, open=.003)),
}
def eye_xz(p, e):
    """position of an eye decal vertex under eye params e=(sv,fT,fB)."""
    sv, fT, fB = e
    ex, ez = S["cx"] + (1 if p.side == "L" else -1) * S["eye_dx"], S["eye_z"]
    a, b = S["eye_a"], S["eye_b"]
    x, z = p.x, ez + (p.z - ez) * sv if p.feat in ("sclera", "iris", "glint") else p.z
    r = p.kw.get("role"); u = p.kw.get("u", 0)
    top = ez + b * sv * math.sqrt(max(1 - u * u, 0)); close = ez - b * sv * math.sqrt(max(1 - u * u, 0)) - 0.0006
    low_edge = close + 0.0006
    if r == "lidtop": z = top + 0.0045
    elif r == "lidbot": z = top + (close - top) * fT
    elif r == "lash": z = top + (close - top) * fT - 0.0016
    elif r == "lowbot": z = low_edge - 0.0045
    elif r == "lowtop": z = low_edge + (top - low_edge) * 0.55 * fB
    return x, z
def mouth_xz(p, m):
    u = p.kw["u"]; r = p.kw["role"]
    w = m.get("w", 1.0); x = S["cx"] + m.get("shift", 0) + u * S["mouth_hw"] * w
    side = max(u, 0) ** 2 * m.get("asym", 0)
    lift = m.get("smile", 0) * u * u + side
    zt = S["mouth_z"] + lift
    if r == "mtop": return x, zt + 0.0004 * m.get("open", 0) / .014
    return x, zt - 0.0025 * (1 - 0.3 * abs(u)) - m.get("open", 0) * max(1 - u * u, 0) ** 0.8
def brow_xz(p, kd, side):
    t = p.kw["t"]; dz = kd[0] + (kd[1] - kd[0]) * t
    return p.x, p.z + dz
_planes = {}
def eye_plane(side):
    """flat 'sticker' plane for one eye: least-squares plane through the skin there, moved forward so ~90% of the skin is behind it."""
    import numpy as np
    if side in _planes: return _planes[side]
    ex, ez = S["cx"] + (1 if side == "L" else -1) * S["eye_dx"], S["eye_z"]
    pts = []
    for i in range(-3, 4):
        for j in range(-3, 4):
            x, z = ex + i * 0.0065, ez + j * 0.0055
            l, n = hit(x, z)
            if l is not None: pts.append((x - ex, z - ez, l.y))
    A = np.array([[1, p[0], p[1]] for p in pts]); y = np.array([p[2] for p in pts])
    c = np.linalg.lstsq(A, y, rcond=None)[0]
    resid = y - A @ c
    c[0] += np.percentile(resid, 5) - 0.0005   # forward = smaller y
    _planes[side] = (ex, ez, c); return _planes[side]
def plane_pos(side, x, z, off):
    ex, ez, c = eye_plane(side)
    y = c[0] + c[1] * (x - ex) + c[2] * (z - ez)
    n = V((-c[1], -1.0, -c[2])).normalized() * -1.0  # normal toward -Y
    n = V((c[1], -1.0, c[2])).normalized()
    return V((x, y, z)) + n * off
def position(p, key):
    k = KEYS.get(key, {}); x, z = p.x, p.z
    if p.feat in ("sclera", "iris", "glint", "lid", "lash"):
        e = k.get("eye" + p.side, (1, 0, 0)); x, z = eye_xz(p, e)
    elif p.feat == "brow": x, z = brow_xz(p, k.get("br" + p.side, (0, 0)), p.side)
    elif p.feat == "mouth": x, z = mouth_xz(p, k.get("mouth", {}))
    if p.feat in ("sclera", "iris", "glint", "lid", "lash"): return plane_pos(p.side, x, z, OFF[p.feat] - 0.0010)
    return surface(x, z, OFF[p.feat])

def build():
    _planes.clear()
    for n in ("HUM_Face",):
        o = bpy.data.objects.get(n)
        if o: bpy.data.objects.remove(o)
    me = bpy.data.meshes.get("HUM_Face")
    if me: bpy.data.meshes.remove(me)
    rig = bpy.data.objects["RIG_Human"]; body = bpy.data.objects["HUM_Body"]
    base = [position(p, None) for p in verts]
    me = bpy.data.meshes.new("HUM_Face"); me.from_pydata([tuple(v) for v in base], [], faces)
    o = bpy.data.objects.new("HUM_Face", me); o["anim_owner"] = "human"
    bpy.data.collections["HUMAN"].objects.link(o)
    # materials
    order = []
    for f in fmat:
        if f not in order: order.append(f)
    for f in order: me.materials.append(getmat(*MATS[f]))
    for pl, f in zip(me.polygons, fmat): pl.material_index = order.index(f)
    me.shade_flat() if hasattr(me, "shade_flat") else None
    # vertex groups: everything to the head, irises + glints to the eye bones
    gh = o.vertex_groups.new(name="DEF-spine.006"); ge = {s: o.vertex_groups.new(name=f"DEF-eye.{s}") for s in "LR"}
    for i, p in enumerate(verts):
        if p.feat in ("iris", "glint"): ge[p.side].add([i], 1.0, 'REPLACE')
        else: gh.add([i], 1.0, 'REPLACE')
    # shape keys
    o.shape_key_add(name="Basis", from_mix=False)
    for kname in KEYS:
        sk = o.shape_key_add(name=kname, from_mix=False)
        for i, p in enumerate(verts): sk.data[i].co = position(p, kname)
        sk.slider_min, sk.slider_max = 0.0, 1.0
    me.update()
    mod = o.modifiers.new("Armature", 'ARMATURE'); mod.object = rig
    o.parent = rig
    return len(me.polygons)

def jaw_weights(body):
    """chin/lower-face skin -> DEF-jaw (smooth falloff); idempotent."""
    skin = [i for i, m in enumerate(body.data.materials) if m and m.name == "HUM_skin"]
    jg = body.vertex_groups.get("DEF-jaw")
    head = body.vertex_groups.get("DEF-spine.006")
    if jg:
        for v in body.data.vertices:
            try: wj = jg.weight(v.index)
            except RuntimeError: continue
            head.add([v.index], min(1, (dict((g.group, g.weight) for g in v.groups).get(head.index, 0)) + wj), 'REPLACE')
        body.vertex_groups.remove(jg)
    jg = body.vertex_groups.new(name="DEF-jaw")
    face_v = set()
    for p in body.data.polygons:
        if p.material_index in skin and p.center.z > 1.45:
            face_v.update(p.vertices)
    ymid = 0.075
    n = 0
    for vi in face_v:
        v = body.data.vertices[vi]
        if v.co.y > ymid: continue
        t = (S["mouth_z"] + 0.012 - v.co.z) / 0.045
        wj = max(0.0, min(1.0, t)); wj = wj * wj * (3 - 2 * wj) * 0.9
        if wj < 0.02: continue
        cur = {g.group: g.weight for g in v.groups}
        keep = 1 - wj
        for gi, w in cur.items():
            if body.vertex_groups[gi].name.startswith("DEF-") and body.vertex_groups[gi].name != "DEF-jaw":
                body.vertex_groups[gi].add([vi], w * keep, 'REPLACE')
        jg.add([vi], wj, 'REPLACE'); n += 1
    return n

def jaw_driver(rig):
    pb = rig.pose.bones["jaw"]; pb.rotation_mode = 'XYZ'
    for fc in list(rig.animation_data.drivers if rig.animation_data else []):
        if fc.data_path == 'pose.bones["jaw"].rotation_euler': rig.animation_data.drivers.remove(fc)
    fc = pb.driver_add("rotation_euler", 0); d = fc.driver; d.type = 'SCRIPTED'
    v = d.variables.new(); v.name = "mo"; v.type = 'SINGLE_PROP'; v.targets[0].id_type = 'KEY'
    v.targets[0].id = bpy.data.objects["HUM_Face"].data.shape_keys; v.targets[0].data_path = 'key_blocks["MouthOpen"].value'
    d.expression = "mo * 0.17"

def eye_limits(rig):
    """keep the irises inside the sclera: pitch +-12 deg, yaw +-22 deg (local axes of the eye controls)."""
    for side in "LR":
        pb = rig.pose.bones[f"eye.{side}"]; pb.rotation_mode = 'XYZ'
        for c in list(pb.constraints):
            if c.name == "EYE_LIMIT": pb.constraints.remove(c)
        c = pb.constraints.new('LIMIT_ROTATION'); c.name = "EYE_LIMIT"; c.owner_space = 'LOCAL'
        c.use_limit_x = c.use_limit_z = True
        c.min_x, c.max_x = math.radians(-12), math.radians(12); c.min_z, c.max_z = math.radians(-22), math.radians(22)

body = bpy.data.objects["HUM_Body"]
tris = build(); nj = jaw_weights(body); jaw_driver(bpy.data.objects["RIG_Human"]); eye_limits(bpy.data.objects["RIG_Human"])
result = (tris, nj)
