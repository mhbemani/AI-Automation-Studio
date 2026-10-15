"""Emotions for the faceless guy (see EMOTIONS.md): brow shape keys + one action per emotion.
1. Brow shape keys on HUM_Body (only the brow ridge / lower forehead of the head move):
   brow_up_L/R, brow_down_L/R, brow_inner_up, brow_squeeze. Head frame: up = head bone, forward = face direction,
   brow line at 39 % of the head height; strength fades from the brow line to the eye sockets and up the forehead.
   Each key is driven by a same-named custom property on the rig's "head" pose bone (0..1), so one action can hold
   body pose + brows.
2. Actions EMO_NN_name (fake user, 1 frame): a shared neutral body pose plus the emotion's changes (world-axis bone
   turns, see pose_test.py conventions) and the brow values. L/R = the character's left/right; Claude is on his left.
The file is left in the neutral standing pose (set on the bones, no action assigned).
Run: Blender -b --factory-startup character_selection_lab.blend --python scripts/build_emotions.py  (env OUT=)"""
import bpy, os, math
from mathutils import Vector, Matrix, Euler
o = bpy.data.objects["HUM_Body"]; rig = bpy.data.objects["RIG_Human"]
for ob in (o, rig):
    bpy.context.view_layer.objects.active = ob
    if ob.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
gn = {g.index: g.name for g in o.vertex_groups}
def ss(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)

# ---------- 1. brow shape keys
hb = rig.data.bones["head"]; H0 = hb.head_local
u = (hb.tail_local - hb.head_local).normalized()
head = [v for v in o.data.vertices if v.groups and gn[max(v.groups, key=lambda g: g.weight).group] == "head"]
f = Vector((0, -1, 0)); f = (f - u * f.dot(u)).normalized()
left = u.cross(f).normalized()
c = sum((v.co for v in head), Vector()) / len(head)
front = sorted(head, key=lambda v: -(v.co - c).dot(f))[:max(3, len(head) // 10)]
xc = sum(((v.co - c).dot(left) for v in front)) / len(front)          # face centre line (sideways)
hmax = max((v.co - H0).dot(u) for v in head); hb_line = 0.39 * hmax
def masks(p):
    dh = (p - H0).dot(u) - hb_line; dx = (p - c).dot(left) - xc
    if (p - c).dot(f) <= 0 or abs(dx) > 0.085: return None
    v = 1.0 if abs(dh) < 0.008 else (max(0, 1 - (-dh - 0.008) / 0.014) if dh < 0 else max(0, 1 - (dh - 0.008) / 0.042))
    return v, dx
if not o.data.shape_keys: o.shape_key_add(name="Basis", from_mix=False)
SK = {}
def key(name, fn):
    k = o.data.shape_keys.key_blocks.get(name) or o.shape_key_add(name=name, from_mix=False)
    for v in o.data.vertices: k.data[v.index].co = v.co
    n = 0
    for v in head:
        m = masks(v.co)
        if not m or m[0] <= 0: continue
        d = fn(m[0], m[1])
        if d.length > 1e-6: k.data[v.index].co = v.co + d; n += 1
    SK[name] = n
L = lambda dx: ss(-0.01, 0.015, dx); R = lambda dx: ss(-0.01, 0.015, -dx)
inner = lambda dx: 1 - ss(0.0, 0.035, abs(dx))
key("brow_up_L", lambda m, dx: u * 0.009 * m * L(dx))
key("brow_up_R", lambda m, dx: u * 0.009 * m * R(dx))
key("brow_down_L", lambda m, dx: (-u * 0.008 + f * 0.002) * m * L(dx))
key("brow_down_R", lambda m, dx: (-u * 0.008 + f * 0.002) * m * R(dx))
key("brow_inner_up", lambda m, dx: u * 0.009 * m * inner(dx))
key("brow_squeeze", lambda m, dx: (-math.copysign(1, dx) * left * 0.004 - u * 0.003) * m * (1 - ss(0.02, 0.06, abs(dx))))
# drivers: shape key value <- head pose bone custom property
hp = rig.pose.bones["head"]
for name in SK:
    hp[name] = 0.0
    ui = hp.id_properties_ui(name); ui.update(min=0.0, max=1.0, soft_min=0.0, soft_max=1.0)
    kb = o.data.shape_keys.key_blocks[name]
    kb.driver_remove("value"); fc = kb.driver_add("value"); dr = fc.driver; dr.type = 'AVERAGE'
    var = dr.variables.new(); var.name = "v"; var.type = 'SINGLE_PROP'
    var.targets[0].id_type = 'OBJECT'; var.targets[0].id = rig; var.targets[0].data_path = f'pose.bones["head"]["{name}"]'

# ---------- 2. poses
def aim(name, d):
    bpy.context.view_layer.update()
    pb = rig.pose.bones[name]; M = pb.matrix.copy(); cur = (M.to_3x3() @ Vector((0, 1, 0))).normalized()
    q = cur.rotation_difference(Vector(d).normalized()); h = M.translation
    pb.matrix = Matrix.Translation(h) @ q.to_matrix().to_4x4() @ Matrix.Translation(-h) @ M
def turn(name, axis, deg):
    bpy.context.view_layer.update()
    pb = rig.pose.bones[name]; M = pb.matrix.copy(); h = M.translation
    pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h) @ M
def curl(prefix_list, deg, sides="LR", spread=0):
    for s in sides:
        for pb in rig.pose.bones:
            if pb.name.endswith("." + s) and pb.name.startswith(tuple(prefix_list)):
                pb.rotation_mode = 'QUATERNION'
                pb.rotation_quaternion = pb.rotation_quaternion @ Euler((math.radians(deg), 0, 0)).to_quaternion()
FING = ("f_index", "f_middle", "f_ring", "f_pinky")
def shoulders(up):   # +up raises both shoulders (degrees)
    turn("shoulder.L", 'Y', -up); turn("shoulder.R", 'Y', up)
NEUTRAL_JSON = os.path.join(os.path.dirname(__file__), "neutral_pose.json")
def neutral():
    """the creator's corrected standing pose (scripts/neutral_pose.json) if saved, else the scripted first version"""
    if os.path.exists(NEUTRAL_JSON):
        import json
        from mathutils import Quaternion
        for name, v in json.load(open(NEUTRAL_JSON)).items():
            pb = rig.pose.bones[name]; pb.rotation_mode = 'QUATERNION'
            pb.rotation_quaternion = Quaternion(v["rot"]); pb.location = v["loc"]
        bpy.context.view_layer.update(); return
    for s, g in (("L", 1), ("R", -1)):
        aim(f"upper_arm.{s}", (0.2 * g, 0.06, -1)); aim(f"forearm.{s}", (0.1 * g, -0.22, -1)); aim(f"hand.{s}", (0.06 * g, -0.12, -1))
    turn("chest", 'X', 6); turn("neck", 'X', 6); turn("head", 'X', 8); shoulders(-3)
    curl(FING, -18); curl(("thumb",), -10)
E = {   # name: (brows, extra ops)
    "neutral": ({}, []),
    "listening": ({}, [("turn", "head", 'Z', 12), ("turn", "head", 'Y', 8)]),
    "curious": ({"brow_up_L": .45, "brow_up_R": .45}, [("turn", "spine", 'X', 6), ("turn", "head", 'Y', 12), ("turn", "head", 'Z', 10), ("turn", "head", 'X', -4)]),
    "surprised": ({"brow_up_L": .95, "brow_up_R": .95}, [("turn", "chest", 'X', -5), ("turn", "head", 'X', -8), ("sh", 7), ("curl", FING, 14)]),
    "confused": ({"brow_up_L": .8, "brow_down_R": .5}, [("turn", "head", 'Y', -14), ("turn", "head", 'Z', -6)]),
    "thoughtful": ({"brow_inner_up": .35, "brow_down_L": .2, "brow_down_R": .2}, [("turn", "head", 'X', 12), ("turn", "head", 'Z', -18)]),
    "annoyed": ({"brow_down_L": .9, "brow_down_R": .9, "brow_squeeze": .8}, [("turn", "head", 'X', 6), ("sh", 5), ("curl", FING, -70), ("curl", ("thumb",), -30)]),
    "sad": ({"brow_inner_up": .9}, [("turn", "chest", 'X', 10), ("turn", "head", 'X', 20), ("sh", -6)]),
    "tired": ({"brow_down_L": .4, "brow_down_R": .4}, [("turn", "chest", 'X', 14), ("turn", "neck", 'X', 10), ("turn", "head", 'X', 22), ("sh", -8)]),
    "amused": ({"brow_up_L": .3, "brow_up_R": .3}, [("turn", "head", 'X', 6), ("turn", "head", 'Z', 10), ("sh", 4)]),
    "happy": ({"brow_up_L": .35, "brow_up_R": .35}, [("turn", "chest", 'X', -6), ("turn", "head", 'X', -8), ("sh", -2)]),
    "awkward": ({"brow_up_L": .4, "brow_up_R": .4, "brow_inner_up": .3}, [("turn", "head", 'Z', -22), ("turn", "head", 'X', 5), ("sh", 8), ("curl1", ("f_index.01", "f_index.02"), -45, "R")]),
    "agreeing": ({}, [("turn", "head", 'X', 15)]),
    "disagreeing": ({"brow_down_L": .3, "brow_down_R": .3}, [("turn", "head", 'Z', -16)]),
    "zoning_out": ({}, [("turn", "chest", 'X', 6), ("turn", "head", 'X', 4), ("sh", -5), ("curl", FING, 10)]),
    "excited": ({"brow_up_L": .75, "brow_up_R": .75}, [("turn", "chest", 'X', -6), ("turn", "spine", 'X', 6), ("turn", "head", 'X', -8), ("turn", "head", 'Z', 10), ("curl", FING, 12)]),
    "proud": ({"brow_down_L": .15, "brow_down_R": .15}, [("turn", "chest", 'X', -9), ("turn", "head", 'X', -14), ("sh", -4)]),
}
def reset():
    for pb in rig.pose.bones:
        pb.matrix_basis.identity(); pb.rotation_mode = 'QUATERNION'
    for n in SK: hp[n] = 0.0
def apply(name):
    reset(); neutral(); brows, ops = E[name]
    for op in ops:
        if op[0] == "turn": turn(op[1], op[2], op[3])
        elif op[0] == "sh": shoulders(op[1])
        elif op[0] == "curl": curl(op[1], op[2])
        elif op[0] == "curl1": curl(op[1], op[2], sides=op[3])
    for n, x in brows.items(): hp[n] = x
    bpy.context.view_layer.update()
if not rig.animation_data: rig.animation_data_create()
names = []
for i, name in enumerate(E, 1):
    an = f"EMO_{i:02d}_{name}"; names.append(an)
    old = bpy.data.actions.get(an)
    if old: bpy.data.actions.remove(old)
    act = bpy.data.actions.new(an); act.use_fake_user = True
    rig.animation_data.action = act
    apply(name)
    for pb in rig.pose.bones:
        pb.keyframe_insert("rotation_quaternion", frame=1); pb.keyframe_insert("location", frame=1)
    for n in SK: hp.keyframe_insert(f'["{n}"]', frame=1)
rig.animation_data.action = None; reset(); neutral(); bpy.context.view_layer.update()   # leave him standing (neutral)
print("EMOTIONS shape keys", SK, "| brow line height %.3f of %.3f m, face centre offset %.3f" % (hb_line, hmax, xc), "| actions", names)
bpy.ops.wm.save_as_mainfile(filepath=os.environ.get("OUT", bpy.data.filepath))
