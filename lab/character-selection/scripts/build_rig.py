"""Step 1: bones + skin binding for the static reference mesh.
Copies 'Lowpoly Male Standing' to HUM_Body (original untouched), builds RIG_Human at the mesh's own joints,
binds with Blender's automatic (heat) weights, saves the file.
Run: Blender -b --factory-startup character_selection_lab.blend --python scripts/build_rig.py
Joint guesses are read off the ortho front/side stills (+X = character's left, -Y = front);
limb joints are then snapped to the local vertex centroid so they sit inside the limb."""
import bpy
from mathutils import Vector
SRC = "Lowpoly Male Standing"
J = {  # name: (x, y, z) guesses
    "pelvis": (0.05, 0.09, 0.92), "spine": (0.05, 0.10, 1.10), "chest": (0.05, 0.10, 1.30),
    "neck": (0.06, 0.12, 1.56), "head": (0.08, 0.04, 1.66), "head_top": (0.08, -0.01, 1.92),
    "clavicle.R": (0.01, 0.10, 1.50), "shoulder.R": (-0.14, 0.09, 1.47), "elbow.R": (-0.21, 0.0, 1.30),
    "wrist.R": (-0.04, -0.22, 1.39), "hand_end.R": (0.03, -0.31, 1.42),
    "clavicle.L": (0.11, 0.10, 1.50), "shoulder.L": (0.25, 0.09, 1.47), "elbow.L": (0.30, 0.0, 1.32),
    "wrist.L": (0.14, -0.22, 1.40), "hand_end.L": (0.06, -0.31, 1.42),
    "hip.R": (-0.04, 0.09, 0.88), "knee.R": (-0.11, 0.05, 0.53), "ankle.R": (-0.20, 0.10, 0.12), "toe.R": (-0.22, -0.13, 0.03),
    "hip.L": (0.14, 0.09, 0.88), "knee.L": (0.17, 0.05, 0.53), "ankle.L": (0.23, 0.10, 0.12), "toe.L": (0.25, -0.13, 0.03),
}
SNAP = {"elbow.R": .07, "elbow.L": .07, "wrist.R": .05, "wrist.L": .05, "knee.R": .09, "knee.L": .09, "ankle.R": .08, "ankle.L": .08}
BONES = [  # name, head, tail, parent, connected
    ("pelvis", "pelvis", "spine", None, False), ("spine", "spine", "chest", "pelvis", True),
    ("chest", "chest", "neck", "spine", True), ("neck", "neck", "head", "chest", True),
    ("head", "head", "head_top", "neck", True),
]
for s in "LR":
    BONES += [(f"shoulder.{s}", f"clavicle.{s}", f"shoulder.{s}", "chest", False),
              (f"upper_arm.{s}", f"shoulder.{s}", f"elbow.{s}", f"shoulder.{s}", True),
              (f"forearm.{s}", f"elbow.{s}", f"wrist.{s}", f"upper_arm.{s}", True),
              (f"hand.{s}", f"wrist.{s}", f"hand_end.{s}", f"forearm.{s}", True),
              (f"thigh.{s}", f"hip.{s}", f"knee.{s}", "pelvis", False),
              (f"shin.{s}", f"knee.{s}", f"ankle.{s}", f"thigh.{s}", True),
              (f"foot.{s}", f"ankle.{s}", f"toe.{s}", f"shin.{s}", True)]

src = bpy.data.objects[SRC]
for n in ("HUM_Body", "RIG_Human"):
    if n in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[n])
col = bpy.data.collections.get("STEP1_rig") or bpy.data.collections.new("STEP1_rig")
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
body = src.copy(); body.data = src.data.copy(); body.name = body.data.name = "HUM_Body"; col.objects.link(body)
src.hide_set(True); src.hide_render = True

verts = [body.matrix_world @ v.co for v in body.data.vertices]
J = {k: Vector(v) for k, v in J.items()}
for k, r in SNAP.items():  # pull the joint to the centre of the nearby surface ring
    for _ in range(3):
        near = [p for p in verts if (p - J[k]).length < r]
        if near: J[k] = sum(near, Vector()) / len(near)

ad = bpy.data.armatures.new("RIG_Human"); rig = bpy.data.objects.new("RIG_Human", ad); col.objects.link(rig)
ad.display_type = 'STICK'; rig.show_in_front = True
bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT')
for name, h, t, parent, conn in BONES:
    b = ad.edit_bones.new(name); b.head = J[h]; b.tail = J[t]
    if parent: b.parent = ad.edit_bones[parent]; b.use_connect = conn
for b in ad.edit_bones:  # roll so local X points to the character's side
    b.align_roll(Vector((0, -1, 0)) if b.name.split('.')[0] in ("thigh", "shin", "pelvis", "spine", "chest", "neck", "head") else Vector((0, 0, 1)))
bpy.ops.object.mode_set(mode='OBJECT')

bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
empty = [g.name for g in body.vertex_groups if not any(g.index in [x.group for x in v.groups] for v in body.data.vertices)]
unweighted = sum(1 for v in body.data.vertices if not v.groups)
print("JOINTS", {k: tuple(round(c, 3) for c in v) for k, v in J.items()})
print("BIND", len(ad.bones), "bones;", len(body.vertex_groups), "groups; empty groups", empty, "; unweighted verts", unweighted)
bpy.ops.wm.save_mainfile()
