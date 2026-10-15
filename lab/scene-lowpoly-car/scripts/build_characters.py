# Characters: the Claude creature (driver seat), the seated human (back right), the human outside
# the exit building's door, and the phone prop. Re-runnable: rebuilds objects tagged cs_owner in
# {"claude","human"} unless user_locked. Car-local frame: forward -Y, driver (left) +X.
# Quaternius rig facts (found by inspection): the human faces +X in rest pose, T-pose arms on ±Y;
# leg/arm bones swing forward/down with +X pose rotation (bone X axis points world -Y / -X).
import bpy, math
from mathutils import Vector, Euler

for o in [o for o in bpy.data.objects if o.get("cs_owner") in ("claude", "human") and not o.get("user_locked")]:
    bpy.data.objects.remove(o)
taken = {o.name for o in bpy.data.objects}
COLL, PROPS = bpy.data.collections["03_CHARACTERS"], bpy.data.collections["06_PROPS"]
car = bpy.data.objects["CAR_Exterior"]

def mat(name, color, rough=0.5):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough
    m.diffuse_color = (*color, 1); return m

ORANGE = mat("MAT_ClaudeOrange", (0.69, 0.18, 0.09), 0.6)   # ~#D97757 in linear
EYE = mat("MAT_ClaudeEye", (0.01, 0.01, 0.01), 0.2)
PHONE = mat("MAT_Phone", (0.02, 0.02, 0.025), 0.3)
SCREEN = mat("MAT_PhoneScreen", (0.6, 0.75, 1.0), 0.2)
SCREEN.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (0.6, 0.75, 1.0, 1)
SCREEN.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 2.0

def block(name, size, m, parent, loc, owner, down=False, bevel=0.0):
    """Box; origin at bottom centre, or at the top centre with the box hanging along -Z (limbs: pivot = joint)."""
    if name in taken: return bpy.data.objects[name]
    sx, sy, sz = (s / 2 for s in size)
    zs = (-2 * sz, 0) if down else (0, 2 * sz)
    vs = [(x, y, z) for x in (-sx, sx) for y in (-sy, sy) for z in zs]
    fs = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.materials.append(m)
    o = bpy.data.objects.new(name, me); o["cs_owner"] = owner
    (PROPS if name.startswith("PROP") else COLL).objects.link(o)
    o.parent = parent; o.location = loc
    if bevel:
        b = o.modifiers.new("Bevel", "BEVEL"); b.width = bevel; b.segments = 2
    return o

def aim(o, target):   # point a hanging limb (-Z) at a target in its parent's space
    o.rotation_euler = (Vector(target) - o.location).to_track_quat("-Z", "Y").to_euler()

# --- Claude: squat orange block in the driver seat (seat top at z 0.93, steering wheel at (0.48,-0.55,1.28)).
body = block("CHAR_Claude", (0.6, 0.5, 0.8), ORANGE, car, (0.48, -0.1, 0.93), "claude", bevel=0.07)
for s, x in (("L", 0.13), ("R", -0.13)):   # eyes high on the face so Claude sees over the dash; L/R = Claude's own left/right (its left is car +X)
    block(f"CHAR_Claude_Eye_{s}", (0.07, 0.03, 0.13), EYE, body, (x, -0.255, 0.58), "claude", bevel=0.02)
for s, x in (("L", 1), ("R", -1)):   # two "arms" reaching for the wheel rim
    arm = block(f"CHAR_Claude_Arm_{s}", (0.1, 0.1, 0.3), ORANGE, body, (0.24 * x, -0.18, 0.34), "claude", down=True, bevel=0.03)
    aim(arm, (0.15 * x, -0.47, 0.38))
for i, x in enumerate((-0.21, -0.07, 0.07, 0.21)):   # four stubby legs over the seat edge
    leg = block(f"CHAR_Claude_Leg_{i + 1}", (0.1, 0.1, 0.32), ORANGE, body, (x, -0.17, 0.08), "claude", down=True, bevel=0.03)
    leg.rotation_euler = (math.radians(-55), 0, 0)

# --- Humans: linked copies of the library rig.
def human(name, parent, loc, rot_z):
    if name in taken: return bpy.data.objects[name]
    src = bpy.data.objects["LIB_Human"]; a = src.copy(); a.name = name; a["cs_owner"] = "human"
    COLL.objects.link(a); a.parent = parent; a.location = loc; a.rotation_euler = (0, 0, math.radians(rot_z))
    m = bpy.data.objects["LIB_Human_Mesh"].copy(); m.name = name + "_Mesh"; m["cs_owner"] = "human"
    COLL.objects.link(m); m.parent = a; next(d for d in m.modifiers if d.type == "ARMATURE").object = a
    for b in a.pose.bones: b.rotation_mode = "XYZ"; b.location = (0, 0, 0); b.rotation_euler = (0, 0, 0)
    return a

def pose(a, **rot):   # bone name -> (x, y, z) degrees
    for n, r in rot.items(): a.pose.bones[n].rotation_euler = Euler([math.radians(v) for v in r])

ARMS_DOWN = dict(LeftArm=(72, 0, 0), RightArm=(72, 0, 0))
# Seated in the back right (car -X), rig +X turned to car forward (-Y); thighs on the seat (top z 0.91).
seated = human("CHAR_Human", car, (-0.48, 0.97, 0.12), -90)
pose(seated, LeftUpLeg=(88, 0, 0), RightUpLeg=(88, 0, 0), LeftLeg=(-88, 0, 0), RightLeg=(-88, 0, 0),
     LeftForeArm=(0, 0, 0), RightForeArm=(0, 0, 0), Spine=(0, 0, -6), **ARMS_DOWN)

# Outside the exit building's door (x≈1.5, front face y=-8), facing the street, phone in hand. This is also his state at
# frame 1 of the video (animate.py starts him here, P0 / FINAL_FACE there must match): CAM_PHONE_CU is built from it.
street = human("CHAR_Human_Street", None, (1.5, -7.7, 0), 100)
pose(street, RightForeArm=(0, 0, -90), **ARMS_DOWN)   # forearm across the chest: texting
phone = block("PROP_Phone", (0.075, 0.012, 0.15), PHONE, None, (0, 0, 0), "human", bevel=0.006)
block("PROP_Phone_Screen", (0.066, 0.002, 0.13), SCREEN, phone, (0, -0.007, 0.01), "human")
phone.parent = street; phone.parent_type = "BONE"; phone.parent_bone = "RightHand"
phone.location = (0, 0, 0)   # on the hand; angled toward his face/the close-up camera in build_cameras.py
if "PROP_Phone_Text" not in taken:   # the message bubble on the screen (screen faces the phone's -Y)
    cu = bpy.data.curves.new("PROP_Phone_Text", "FONT"); cu.body = "Claude, I wanna\ngo home."
    cu.size = 0.0085; cu.align_x = "CENTER"; cu.align_y = "CENTER"
    cu.materials.append(mat("MAT_PhoneText", (0.01, 0.01, 0.02), 0.5))
    t = bpy.data.objects.new("PROP_Phone_Text", cu); t["cs_owner"] = "human"; PROPS.objects.link(t)
    t.parent = phone; t.location = (0, -0.0085, 0.085); t.rotation_euler = (math.radians(90), 0, 0)

# Claude's car view (drive scene) needs nothing else; the old staged street human from build_city is replaced.
bpy.data.orphans_purge(do_recursive=True)
result = sorted(o.name for o in bpy.data.objects if o.get("cs_owner") in ("claude", "human"))
