"""Build "Facet": faceted low-poly gem character + rigid-part rig + action library.
Run via build.sh (blender -b --factory-startup -P build_character.py -P build_stage.py).
Idempotent: starts from an empty scene every time. Z up, character faces -Y, screen-right = +X.
Pose values are WORLD-aligned degrees/units (converted to bone-local per bone), keyed every frame.
"""
import bpy, bmesh, math, random, os, sys
from math import radians as rad
from mathutils import Vector, Euler, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from palette import PAL as P, srgb

bpy.ops.wm.read_factory_settings(use_empty=True)
rng = random.Random(7)

# ---------------------------------------------------------------- materials (3)
def mat(name, rough, clear=0.0, emit=None, spec=0.5):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    attr = nt.nodes.new("ShaderNodeAttribute"); attr.attribute_name = "col"; attr.attribute_type = 'GEOMETRY'
    nt.links.new(attr.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = spec
    b.inputs["Coat Weight"].default_value = clear
    b.inputs["Coat Roughness"].default_value = 0.22
    if emit:
        nt.links.new(attr.outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = emit
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    return m

M_CRYSTAL = mat("crystal", 0.18, clear=0.35, spec=0.5)   # head, crown, hands: cut-stone look
M_BODY = mat("body", 0.55, clear=0.15, spec=0.4)        # torso, arms, legs, mouth: matte stone
M_ACC = mat("accent", 0.32, clear=0.25, spec=0.45)    # crown, chest gem, ears
M_EYE = mat("eye", 0.9, emit=0.35, spec=0.0)             # eyes only: subtle emissive

# ---------------------------------------------------------------- mesh helpers
def make_obj(name, verts, faces, colors, material, jitter=0.0):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    vs = [bm.verts.new(v + Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * jitter) for v in verts]
    for f in faces:
        try: bm.faces.new([vs[i] for i in f])
        except ValueError: pass
    bm.normal_update(); bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    layer = bm.loops.layers.color.new("col")
    for i, f in enumerate(bm.faces):
        base = srgb(colors[i % len(colors)]); k = rng.uniform(0.8, 1.12)   # per-facet value jitter = gem look
        c = (min(base[0] * k, 1), min(base[1] * k, 1), min(base[2] * k, 1), 1)
        for l in f.loops: l[layer] = c
        f.smooth = False
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = False
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    o.data.materials.append(material)
    return o

def lathe(name, rings, n, colors, material, apex_top=None, apex_bot=None, jitter=0.0):
    """rings: [(z, rx, ry, cx, cy, rot_deg)] top->bottom; half-step rot between rings gives gem triangle strips."""
    verts, idx = [], []
    for z, rx, ry, cx, cy, rot in rings:
        ids = []
        for j in range(n):
            a = rad(rot) + 2 * math.pi * j / n
            ids.append(len(verts)); verts.append(Vector((cx + rx * math.cos(a), cy + ry * math.sin(a), z)))
        idx.append(ids)
    faces = []
    for A, B in zip(idx, idx[1:]):
        for j in range(n):
            j1 = (j + 1) % n
            faces.append((A[j], A[j1], B[j])); faces.append((A[j1], B[j1], B[j]))
    if apex_top is None: faces.append(tuple(idx[0]))
    else:
        t = len(verts); verts.append(Vector(apex_top)); faces += [(idx[0][j], idx[0][(j + 1) % n], t) for j in range(n)]
    if apex_bot is None: faces.append(tuple(idx[-1]))
    else:
        t = len(verts); verts.append(Vector(apex_bot)); faces += [(idx[-1][j], idx[-1][(j + 1) % n], t) for j in range(n)]
    return make_obj(name, verts, faces, colors, material, jitter)

def diamond(name, c, rx, ry, rz, n, colors, material, rot=0, tilt=(0, 0, 0)):
    o = lathe(name, [(0, rx, ry, 0, 0, rot)], n, colors, material, apex_top=(0, 0, rz), apex_bot=(0, 0, -rz))
    o.data.transform(Euler([rad(a) for a in tilt]).to_matrix().to_4x4())
    o.data.transform(Matrix.Translation(c)); return o

def flat_shape(name, pts, colors, material):
    verts = [Vector((x, 0, z)) for x, z in pts] + [Vector((0, 0, 0))]
    c = len(pts)
    return make_obj(name, verts, [(i, (i + 1) % c, c) for i in range(c)], colors, material)

# (3 + accent = 4 materials)
# ---------------------------------------------------------------- geometry (rest pose, world coords)
SH_X, SH_Z = 0.6, 1.0
parts = {}
def add(bone, o): parts.setdefault(bone, []).append(o); return o

head = add("head", lathe("head", [
    (2.02, 0.30, 0.28, 0.0, 0.0, 22.5),
    (1.86, 0.60, 0.56, 0.0, 0.0, 0.0),
    (1.62, 0.66, 0.62, 0.0, 0.0, 22.5),
    (1.40, 0.52, 0.50, 0.0, 0.0, 0.0),
], 8, [P["head"], P["head2"], P["head"], P["head3"]], M_CRYSTAL, apex_bot=(0, -0.02, 1.2), jitter=0.0))
add("torso", lathe("torso", [
    (1.24, 0.24, 0.22, 0, 0, 30),
    (1.08, 0.44, 0.34, 0, 0, 0),
    (0.78, 0.40, 0.32, 0, 0, 30),
    (0.52, 0.22, 0.2, 0, 0, 0),
], 6, [P["body"], P["body2"], P["body"], P["body3"]], M_BODY, apex_bot=(0, 0, 0.36), jitter=0.01))
add("torso", diamond("chest_gem", (0, -0.31, 0.88), 0.11, 0.06, 0.15, 4, [P["accent"], P["accent2"]], M_ACC))

for side, sx in (("L", -1), ("R", 1)):
    ax = sx * SH_X
    add("arm_" + side, lathe("arm_" + side, [
        (SH_Z + 0.08, 0.07, 0.07, ax, 0, 0),
        (SH_Z - 0.10, 0.13, 0.12, ax, 0, 30),
        (SH_Z - 0.34, 0.10, 0.09, ax, 0, 0),
    ], 6, [P["limb"], P["limb2"], P["limb"]], M_BODY, apex_bot=(ax, 0, SH_Z - 0.50), jitter=0.006))
    add("hand_" + side, diamond("hand_" + side, (ax, 0, 0.33), 0.14, 0.12, 0.23, 5, [P["hand"], P["hand2"]], M_CRYSTAL, rot=18))
    lx = sx * 0.22
    add("leg_" + side, lathe("leg_" + side, [
        (0.40, 0.11, 0.11, lx, 0, 0),
        (0.30, 0.16, 0.15, lx, 0, 36),
        (0.06, 0.17, 0.24, lx, -0.06, 0),
        (0.0, 0.14, 0.2, lx, -0.06, 36),
    ], 5, [P["foot"], P["foot2"]], M_BODY, jitter=0.006))

for i, (x, h, t) in enumerate(((0, 0.34, (0, 0, 0)), (-0.17, 0.22, (0, -22, 0)), (0.17, 0.22, (0, 22, 0)))):
    add("crown", diamond("crown%d" % i, (x, 0, 2.02 + h * 0.9), 0.07, 0.07, h, 4, [P["accent"], P["accent2"]], M_ACC, rot=45, tilt=t))
for sx in (-1, 1):
    add("head", diamond("ear", (sx * 0.71, 0, 1.62), 0.07, 0.07, 0.17, 4, [P["accent"], P["accent2"]], M_ACC, rot=45, tilt=(0, sx * 90, 0)))

# ---------------------------------------------------------------- armature
arm_data = bpy.data.armatures.new("FacetRig")
rig = bpy.data.objects.new("FacetRig", arm_data); bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig; rig.select_set(True)

bpy.context.view_layer.update()
def front_hit(x, z):   # eyes/mouth sit exactly ON the head surface
    ok, loc, nor, _ = head.ray_cast(Vector((x, -3, z)), Vector((0, 1, 0)))
    assert ok, "raycast missed head"
    return loc, nor
EYE_X, EYE_Z, MOUTH_Z = 0.21, 1.74, 1.47
anchors = {"eye_L": front_hit(-EYE_X, EYE_Z), "eye_R": front_hit(EYE_X, EYE_Z), "mouth": front_hit(0, MOUTH_Z)}

BONES = {  # name: (parent, head, tail)
    "root": (None, (0, 0, 0), (0, 0, 0.2)),
    "torso": ("root", (0, 0, 0.6), (0, 0, 1.0)),
    "head": ("torso", (0, 0, 1.3), (0, 0, 1.9)),
    "crown": ("head", (0, 0, 2.0), (0, 0, 2.3)),
    "eye_L": ("head", None, None), "eye_R": ("head", None, None), "mouth": ("head", None, None),
    "arm_L": ("torso", (-SH_X, 0, SH_Z), (-SH_X, 0, 0.55)),
    "arm_R": ("torso", (SH_X, 0, SH_Z), (SH_X, 0, 0.55)),
    "hand_L": ("arm_L", (-SH_X, 0, 0.56), (-SH_X, 0, 0.1)),
    "hand_R": ("arm_R", (SH_X, 0, 0.56), (SH_X, 0, 0.1)),
    "leg_L": ("root", (-0.22, 0, 0.4), (-0.22, 0, 0.0)),
    "leg_R": ("root", (0.22, 0, 0.4), (0.22, 0, 0.0)),
}
bpy.ops.object.mode_set(mode='EDIT')
for n, (par, h, t) in BONES.items():
    b = arm_data.edit_bones.new(n)
    if n in anchors:
        h = anchors[n][0] + anchors[n][1] * 0.03; t = h + Vector((0, 0, 0.1))
    b.head = Vector(h); b.tail = Vector(t)
for n, (par, h, t) in BONES.items():
    if par: arm_data.edit_bones[n].parent = arm_data.edit_bones[par]
bpy.ops.object.mode_set(mode='OBJECT')

eye_pts = [(0, 0.12), (0.07, 0.04), (0.07, -0.08), (0, -0.12), (-0.07, -0.08), (-0.07, 0.04)]
for n in ("eye_L", "eye_R"):
    loc, nor = anchors[n]
    nor = (nor * 0.5 + Vector((0, -1, 0)) * 0.5).normalized(); qm = nor.to_track_quat('-Y', 'Z').to_matrix().to_4x4()
    o = flat_shape(n, eye_pts, [P["eye"]], M_EYE)
    o.data.transform(qm); o.data.transform(Matrix.Translation(loc + nor * 0.03)); add(n, o)
    hl = flat_shape(n + "_hl", [(0, 0.04), (0.025, 0.0), (0, -0.04), (-0.025, 0.0)], [P["eyehl"]], M_EYE)
    hl.data.transform(Matrix.Translation((-0.025, 0, 0.05))); hl.data.transform(qm); hl.data.transform(Matrix.Translation(loc + nor * 0.038)); add(n, hl)
loc, nor = anchors["mouth"]; nor = (nor * 0.6 + Vector((0, -1, 0)) * 0.4).normalized()
mo = flat_shape("mouth", [(-0.19, 0.02), (-0.10, 0.09), (0.10, 0.09), (0.19, 0.02), (0.10, -0.09), (-0.10, -0.09)], [P["mouth"]], M_EYE)
mo.data.transform(nor.to_track_quat('-Y', 'Z').to_matrix().to_4x4()); mo.data.transform(Matrix.Translation(loc + nor * 0.03)); add("mouth", mo)

bpy.context.view_layer.update()
for bn, objs in parts.items():          # rigid parenting: no weights, rest world pose unchanged
    pb = arm_data.bones[bn]
    for o in objs:
        o.parent = rig; o.parent_type = 'BONE'; o.parent_bone = bn
        o.matrix_parent_inverse = (rig.matrix_world @ pb.matrix_local @ Matrix.Translation((0, pb.length, 0))).inverted()

BN = list(BONES)
CONV = {n: arm_data.bones[n].matrix_local.to_3x3() for n in BN}   # bone-local -> world basis at rest
def to_local_q(n, qw): m = CONV[n]; return (m.inverted() @ qw.to_matrix() @ m).to_quaternion()
def to_local_v(n, v): return CONV[n].inverted() @ Vector(v)

# ---------------------------------------------------------------- animation library (procedural poses, baked to Actions)
FPS = 30
def ease(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def lerp(a, b, k): return a + (b - a) * k
def vl(a, b, k): return tuple(lerp(x, y, k) for x, y in zip(a, b))
def sine(t, period, ph=0): return math.sin(2 * math.pi * (t / period + ph))
def blink(t, times, dur=0.16):
    for b in times:
        if b <= t <= b + dur: return 1 - 0.88 * math.sin(math.pi * (t - b) / dur)
    return 1.0

def pose(**kw):
    p = {n: {"r": (0, 0, 0), "l": (0, 0, 0), "s": (1, 1, 1)} for n in BN}
    p["arm_L"]["r"] = (0, 14, 0); p["arm_R"]["r"] = (0, -14, 0)
    p["hand_L"]["r"] = (0, 6, 0); p["hand_R"]["r"] = (0, -6, 0)
    p["mouth"]["s"] = (1, 1, 0.16)
    for k, v in kw.items():
        if k == "mouth_open": p["mouth"]["s"] = (1, 1, max(v, 0.05)); continue
        bone, ch = k.rsplit("_", 1); p[bone][ch] = tuple(v)
    return p
def blend(pa, pb, k): return {n: {ch: vl(pa[n][ch], pb[n][ch], k) for ch in ("r", "l", "s")} for n in pa}
def add_(p, bone, ch, v): p[bone][ch] = tuple(a + b for a, b in zip(p[bone][ch], v))
def eyes(p, z):
    for e in ("eye_L", "eye_R"): p[e]["s"] = (1, 1, z)

def a_idle(t):
    p = pose(arm_L_r=(0, 12, 0), arm_R_r=(0, -12, 0))
    add_(p, "root", "l", (0, 0, 0.025 * sine(t, 2.0)))
    add_(p, "torso", "s", (0, 0, 0.012 * sine(t, 2.0)))
    add_(p, "head", "r", (2 * sine(t, 2.0, 0.1), 0, 5 * sine(t, 2.0)))
    add_(p, "arm_L", "r", (0, 2 * sine(t, 2, .2), 0)); add_(p, "arm_R", "r", (0, -2 * sine(t, 2, .2), 0))
    eyes(p, blink(t, (0.6, 1.5))); return p

def a_talk(t):
    p = pose()
    bounce = abs(sine(t, 2.0, 0))          # 2 bounces per 2 s loop
    add_(p, "root", "l", (0, 0, 0.035 * bounce)); add_(p, "torso", "s", (0, 0, -0.015 * bounce))
    add_(p, "head", "r", (4 * sine(t, 1.0, 0.3), 0, 6 * sine(t, 2.0)))
    g1 = ease(1 - abs(t - 0.6) / 0.55); g2 = ease(1 - abs(t - 1.4) / 0.55)
    p["arm_R"]["r"] = (-30 * g1, -22 - 25 * g1, 0); p["hand_R"]["r"] = (-20 * g1, -10 + 5 * sine(t, 0.5) * g1, 0)
    p["arm_L"]["r"] = (-30 * g2, 22 + 25 * g2, 0); p["hand_L"]["r"] = (-20 * g2, 10 - 5 * sine(t, 0.5) * g2, 0)
    eyes(p, blink(t, (1.1,))); return p

def point(side):
    sx = 1 if side == "right" else -1
    arm, hand = ("arm_R", "hand_R") if sx == 1 else ("arm_L", "hand_L")
    def f(t):
        base = a_talk(0.2)
        up = pose(**{arm + "_r": (-12, -sx * 88, 0), hand + "_r": (0, -sx * 4, 0),
                     "head_r": (-3, 0, sx * 22), "torso_r": (0, 0, sx * 8), "mouth_open": 0.3, "eye_L_l": (sx * 0.03, 0, 0), "eye_R_l": (sx * 0.03, 0, 0)})
        k = ease(t / 0.35) * (1 - ease((t - 0.85) / 0.35))
        p = blend(base, up, k)
        add_(p, "root", "l", (0, 0, 0.03 * math.sin(math.pi * min(1, t / 0.45)))); eyes(p, 1); return p
    return f

def a_wave(t):
    k = ease(t / 0.4) * (1 - ease((t - 1.6) / 0.4))
    up = pose(arm_R_r=(0, -132, 0), head_r=(0, 0, -8), mouth_open=0.35, torso_r=(0, 0, -4))
    p = blend(a_talk(0.2), up, k); w = sine(t, 0.5) * k
    p["hand_R"]["r"] = (0, -15, 28 * w); add_(p, "arm_R", "r", (0, 0, 10 * w))
    add_(p, "root", "l", (0, 0, 0.02 * abs(sine(t, 1.0)) * k)); eyes(p, 1); return p

def a_celebrate(t):
    jump = math.sin(math.pi * t / 0.9) if t < 0.9 else 0
    k = ease(t / 0.25) * (1 - ease((t - 1.2) / 0.3))
    up = pose(arm_L_r=(0, 155, 0), arm_R_r=(0, -155, 0), hand_L_r=(0, 10, 0), hand_R_r=(0, -10, 0), head_r=(-8, 0, 0), mouth_open=0.85)
    p = blend(a_talk(0.2), up, k)
    add_(p, "root", "l", (0, 0, 0.3 * jump))
    sq = 0.88 if t < 0.12 else 1 + 0.06 * jump
    p["root"]["s"] = (1 / math.sqrt(sq), 1 / math.sqrt(sq), sq)
    add_(p, "root", "r", (0, 0, 12 * sine(t, 0.6) * k))
    add_(p, "arm_L", "r", (0, 8 * sine(t, 0.3) * k, 0)); add_(p, "arm_R", "r", (0, -8 * sine(t, 0.3) * k, 0))
    eyes(p, 0.45 if 0.2 < t < 1.2 else 1); return p

def a_think(t):
    k = ease(t / 0.6)
    up = pose(arm_R_r=(-128, -22, 0), hand_R_r=(-40, -30, 0), head_r=(-8, 0, -14), eye_L_l=(0, 0, 0.04), eye_R_l=(0, 0, 0.04), torso_r=(0, 0, 4), mouth_open=0.08)
    p = blend(a_talk(0.2), up, k)
    add_(p, "head", "r", (0, 0, 2 * sine(t, 2.4) * k)); add_(p, "root", "l", (0, 0, 0.012 * sine(t, 2.4)))
    eyes(p, blink(t, (1.4,))); return p

def a_enter(t):
    u = ease(t / 0.9); hop = abs(math.sin(math.pi * 2 * u)) * 0.22 * (1 - u)
    p = a_talk(0.2); p["root"]["l"] = (4.6 * (1 - u), 0, hop); p["root"]["r"] = (0, 0, 10 * (1 - u)); return p
def a_exit(t):
    u = ease(t / 0.9); hop = abs(math.sin(math.pi * 2 * u)) * 0.22 * (1 - u * 0.4)
    p = a_talk(0.2); p["root"]["l"] = (-4.8 * u, 0, hop); p["root"]["r"] = (0, 0, -10 * u)
    add_(p, "arm_R", "r", (0, -40 * math.sin(math.pi * min(1, u * 1.2)), 0)); return p

ACTIONS = {  # name: (fn, seconds, loop)
    "idle": (a_idle, 2.0, True), "talk": (a_talk, 2.0, True),
    "point_left": (point("left"), 1.2, False), "point_right": (point("right"), 1.2, False),
    "wave": (a_wave, 2.0, False), "celebrate": (a_celebrate, 1.5, False),
    "think": (a_think, 2.4, True), "enter": (a_enter, 1.0, False), "exit": (a_exit, 1.0, False),
}

def crown_lag(frames):   # secondary motion: low-pass of head yaw + body vertical velocity
    out, st, last = [], [0.0, 0.0], None
    for p in frames:
        z = p["root"]["l"][2]; vz = 0 if last is None else z - last; last = z
        tgt = (-1.1 * p["head"]["r"][2] - 0.5 * p["root"]["r"][2], -vz * 900)
        for i in range(2): st[i] += (tgt[i] - st[i]) * 0.22
        out.append((st[0] * 0.8, st[1]))
    return out

def bake_action(name, fn, dur, loop):
    N = int(round(dur * FPS)) + 1
    frames = [fn(f / FPS) for f in range(N)]
    lag = crown_lag(frames + frames)[-N:] if loop else crown_lag(frames)
    for p, (a, b) in zip(frames, lag): p["crown"]["r"] = (b, 0, a)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    rig.animation_data_create(); rig.animation_data.action = act
    for bn in BN:
        pb = rig.pose.bones[bn]; pb.rotation_mode = 'QUATERNION'
        for f, p in enumerate(frames):
            ql = to_local_q(bn, Euler([rad(a) for a in p[bn]["r"]], 'XYZ').to_quaternion())
            pb.rotation_quaternion = ql; pb.location = to_local_v(bn, p[bn]["l"])
            pb.scale = Vector([abs(x) for x in (CONV[bn].inverted() @ Vector(p[bn]["s"]))])
            for path in ("rotation_quaternion", "location", "scale"): pb.keyframe_insert(path, frame=f + 1)
    act["loop"] = loop; act["frames"] = N
    return act

for n, (fn, dur, loop) in ACTIONS.items(): bake_action(n, fn, dur, loop)
for pb in rig.pose.bones:
    pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
rig.animation_data.action = bpy.data.actions["idle"]
rig["facet"] = True
tris = sum(len(o.data.polygons) for v in parts.values() for o in v)
print("TRIS", tris, "OBJECTS", sum(len(v) for v in parts.values()))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "facet.blend"), compress=True)
