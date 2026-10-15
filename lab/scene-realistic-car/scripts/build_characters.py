# Characters: Claude (driver, LEFT front seat = car-local +X), the human Oscar seated in the RIGHT front seat
# (creator's change, 2026-10-09), Oscar standing outside the exit door texting, and the phone prop.
# Re-runnable: rebuilds objects tagged cs_owner in {"claude","human"} unless user_locked. Car-local: forward -Y.
# Oscar = BlenderKit Rigify rig (LIB_Human). Rest pose: T-pose facing -Y, hips at z 0.84. Measured FK axes:
#   upper_arm_fk: Z rotation lowers the arm (L -, R +), +X swings it forward; forearm_fk +X bends the elbow forward;
#   thigh_fk -X lifts the leg forward; shin_fk +X bends the knee; head/neck +X nods down, Y turns, Z tilts.
# Contract mapping (old Quaternius names -> Rigify): Hips->torso, Spine*->spine_fk*, Neck->neck, Head->head,
#   Left/RightArm->upper_arm_fk.L/R, ForeArm->forearm_fk, UpLeg->thigh_fk, Leg->shin_fk, Foot->foot_fk,
#   RightHand->DEF-hand.R (phone parent). Arms/legs are switched to FK (IK_FK = 1).
import bpy, bmesh, math
from mathutils import Vector, Euler, Matrix

for o in [o for o in bpy.data.objects if o.get("cs_owner") in ("claude", "human") and not o.get("user_locked")]:
    bpy.data.objects.remove(o)
for o in [o for o in bpy.data.objects if o.name.startswith("TMP_Rig")]: bpy.data.objects.remove(o)
taken = {o.name for o in bpy.data.objects}
COLL, PROPS = bpy.data.collections["03_CHARACTERS"], bpy.data.collections["06_PROPS"]
car = bpy.data.objects["CAR_Exterior"]
SEAT_TOP = 0.40                         # cushion top (car-local z), see build_car.py
CLAUDE_X, HUMAN_X, SEAT_Y = 0.42, -0.42, 0.28

def mat(name, color, rough=0.5, emit=None, strength=0.0, sss=0.0, coat=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs[0])
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Radius"].default_value = (0.3, 0.12, 0.06)
    b.inputs["Subsurface Scale"].default_value = 0.05; b.inputs["Coat Weight"].default_value = coat
    if emit: b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = strength
    m.diffuse_color = (*color, 1); return m

# Claude re-shaded (creator's choice A): satin orange with a soft warm glow; glossy capsule eyes with a highlight.
ORANGE = mat("MAT_ClaudeOrange", (0.55, 0.12, 0.035), 0.45, emit=(0.9, 0.3, 0.12), strength=0.02, sss=0.0, coat=0.2)
EYE = mat("MAT_ClaudeEye", (0.012, 0.01, 0.01), 0.25, coat=0.3)
GLINT = mat("MAT_ClaudeEyeGlint", (1, 1, 1), 0.2, emit=(1, 1, 1), strength=1.5)
PHONE = mat("MAT_Phone", (0.25, 0.5, 0.75), 0.35)   # light blue case: readable against the dark jacket
SCREEN = mat("MAT_PhoneScreen", (0.6, 0.75, 1.0), 0.2, emit=(0.6, 0.75, 1.0), strength=2.0)

def rbox(name, size, m, parent, loc, owner, down=False, radius=0.0, seg=3, coll=COLL, power=None, res=(10, 6)):
    """Rounded box (superellipsoid: smooth, squarish, any proportions); origin at the bottom centre, or at the top
    centre hanging along -Z (limbs: pivot = joint). `power` sets the squareness (higher = boxier); default from radius."""
    if name in taken: return bpy.data.objects[name]
    sx, sy, sz = (v / 2 for v in size); z0 = -2 * sz if down else 0.0
    n = power or max(2.5, min(10.0, 2.0 * min(size) / max(radius, 1e-3) / 1.6))
    e = 2.0 / n
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=res[0], v_segments=res[1], radius=1.0)   # diet: low res, smooth shading
    sg = lambda c: math.copysign(abs(c) ** e, c)
    for v in bm.verts:
        x, y, z = v.co.normalized(); v.co = Vector((sg(x) * sx, sg(y) * sy, sg(z) * sz + z0 + sz))
    for f in bm.faces: f.smooth = True
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(m)
    o = bpy.data.objects.new(name, me); o["cs_owner"] = owner; coll.objects.link(o)
    o.parent = parent; o.matrix_parent_inverse = Matrix(); o.location = loc
    return o

def aim(o, target):   # point a hanging limb (-Z) at a target in its parent's space
    o.rotation_euler = (Vector(target) - o.location).to_track_quat("-Z", "Y").to_euler()

# --- Claude: rounded orange block on the driver seat; front faces car -Y. L/R = Claude's own left/right (left = +X).
body = rbox("CHAR_Claude", (0.56, 0.46, 0.74), ORANGE, car, (CLAUDE_X, SEAT_Y - 0.02, SEAT_TOP), "claude", power=7, res=(24, 14))
for s, x in (("L", 0.12), ("R", -0.12)):
    eye = rbox(f"CHAR_Claude_Eye_{s}", (0.075, 0.04, 0.14), EYE, body, (x, -0.215, 0.47), "claude", power=3, res=(12, 8))
    rbox(f"CHAR_Claude_Eye_{s}_Glint", (0.024, 0.01, 0.026), GLINT, eye, (0.014, -0.019, 0.085), "claude", power=2, res=(8, 4))
for s, x in (("L", 1), ("R", -1)):   # arms reach for the wheel rim (wheel centre (0.42,-0.40,0.80) car-local)
    arm = rbox(f"CHAR_Claude_Arm_{s}", (0.09, 0.09, 0.30), ORANGE, body, (0.24 * x, -0.12, 0.34), "claude", down=True, power=3)
    aim(arm, (0.16 * x, -0.42, 0.22))   # down-forward to the lower half of the rim
for i, x in enumerate((-0.19, -0.065, 0.065, 0.19)):   # four stubby legs over the seat edge
    leg = rbox(f"CHAR_Claude_Leg_{i + 1}", (0.09, 0.09, 0.22), ORANGE, body, (x, -0.16, 0.07), "claude", down=True, power=3)
    leg.rotation_euler = (math.radians(-60), 0, 0)

# --- Oscar: linked copies of the library rig (shared meshes), posed with FK.
def human(name, parent, loc, rot_z):
    if name in taken: return bpy.data.objects[name]
    src = bpy.data.objects["LIB_Human"]; a = src.copy(); a.name = name; a["cs_owner"] = "human"
    COLL.objects.link(a); a.parent = parent; a.matrix_parent_inverse = Matrix(); a.location = loc
    a.rotation_mode = "XYZ"; a.rotation_euler = (0, 0, math.radians(rot_z))
    for ch in src.children:
        if ch.hide_render: continue   # the trophy
        part = ch.name[len("LIB_Human_"):]   # Mesh (chest), Pelvis, Belly, Neck, Head, UpperArm.L, ..., Face, Eye_L/R
        m = ch.copy(); m.name = name + "_" + part; m["cs_owner"] = "human"
        COLL.objects.link(m); m.parent = a; m.matrix_parent_inverse = ch.matrix_parent_inverse.copy()   # setting .parent resets it
        for d in m.modifiers:
            if d.type == "ARMATURE": d.object = a
    for pb in a.pose.bones:
        pb.rotation_mode = "XYZ"; pb.rotation_euler = (0, 0, 0); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
    for n in ("thigh_parent.L", "thigh_parent.R", "upper_arm_parent.L", "upper_arm_parent.R"): a.pose.bones[n]["IK_FK"] = 1.0
    bpy.context.view_layer.update()   # bone-parented parts (hair, eyes, teeth): re-anchor the hair in the rest pose
    for ch, m in zip([c for c in src.children if not c.hide_render], [c for c in a.children]):
        if m.parent_type == "BONE" and m.parent_bone == "ORG-spine.006": m.matrix_world = a.matrix_world @ src.matrix_world.inverted() @ ch.matrix_world   # hair only (eyes/teeth are fine)
    return a

def pose(a, **rot):   # bone name (dots as __) -> (x, y, z) degrees
    for n, r in rot.items(): a.pose.bones[n.replace("__", ".")].rotation_euler = Euler([math.radians(v) for v in r])

# Seated in the passenger seat facing forward (-Y, like the rest pose): hips ~0.10 above the cushion.
HIP_REST = Vector((0, 0.10, 0.88))   # hip joint of the rest pose (human_lib.py rig, measured)
seated = human("CHAR_Human", car, Vector((HUMAN_X, SEAT_Y + 0.04, SEAT_TOP + 0.04)) - HIP_REST, 0)
pose(seated, thigh_fk__L=(-84, 0, 3), thigh_fk__R=(-84, 0, -3), shin_fk__L=(84, 0, 0), shin_fk__R=(84, 0, 0),
     foot_fk__L=(-6, 0, 0), foot_fk__R=(-6, 0, 0),
     spine_fk__001=(-8, 0, 0), neck=(4, 0, 0), head=(0, 12, 0))   # slight lean back, head turned a little toward Claude
pose(seated, upper_arm_fk__L=(20, 0, 10), upper_arm_fk__R=(10, 0, -10), forearm_fk__L=(50, 0, -30), forearm_fk__R=(60, 0, 30))   # hands on the thighs (searched, rigid-piece rig)

# Outside the exit door (door centre x 1.5, facade y -10.5, sidewalk z 0.15), facing the street (+Y), texting.
street = human("CHAR_Human_Street", None, Vector((1.5, -9.7, 0.15)), 180)
pose(street, neck=(4, 0, 0), head=(8, 0, 0))   # the scan already holds a phone at the chest; a slight look down, face still readable
phone = rbox("PROP_Phone", (0.075, 0.009, 0.15), PHONE, None, (0, 0, 0), "human", power=10, coll=PROPS)
rbox("PROP_Phone_Screen", (0.068, 0.002, 0.138), SCREEN, phone, (0, -0.0045, 0.006), "human", power=12, coll=PROPS)
bpy.context.view_layer.update()
phone.parent = street; phone.parent_type = "BONE"; phone.parent_bone = "DEF-hand.R"
bpy.context.view_layer.update()
PB = street.pose.bones
hand = street.matrix_world @ ((PB["DEF-hand.R"].head.lerp(PB["DEF-hand.R"].tail, 0.5) + PB["hand_fk.L"].head.lerp(PB["hand_fk.L"].tail, 0.5)) / 2)
eyes = street.matrix_world @ PB["head"].head.lerp(PB["head"].tail, 0.35)
look = (eyes - hand).normalized()                                                  # the screen (phone -Y) faces his eyes
q = look.to_track_quat("-Y", "Z"); up = q @ Vector((0, 0, 1))
phone.matrix_world = Matrix.Translation(hand + look * 0.09 + up * 0.02) @ q.to_matrix().to_4x4()   # held at its lower edge: the hands do not cover the input bar
# the chat UI on the screen is built by build_phone.py (run it after this script)

bpy.data.orphans_purge(do_recursive=True); bpy.context.view_layer.update()
def head_pos(a): return [round(v, 2) for v in (a.matrix_world @ a.pose.bones["head"].tail)]
result = {"objects": sorted(o.name for o in bpy.data.objects if o.get("cs_owner") in ("claude", "human")),
          "seated_head_top": head_pos(seated), "street_head_top": head_pos(street)}
