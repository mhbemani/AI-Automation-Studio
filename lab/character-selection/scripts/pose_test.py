"""Pose RIG_Human into a named test pose (not saved), then render the ortho stills via views.py.
Run: Blender -b --factory-startup character_selection_lab.blend --python scripts/pose_test.py -- <out_prefix> <pose> [views.py flags]
Poses aim bones at world directions (parents first), or rotate them about world axes."""
import bpy, sys, os, math
from mathutils import Vector, Matrix, Quaternion
args = sys.argv[sys.argv.index("--")+1:]
pose = args[1]
rig = bpy.data.objects["RIG_Human"]
for ob in (rig, bpy.data.objects["HUM_Body"]):  # files saved in Edit Mode do not evaluate poses
    bpy.context.view_layer.objects.active = ob
    if ob.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
def aim(name, d):
    bpy.context.view_layer.update()
    pb = rig.pose.bones[name]; M = pb.matrix.copy()
    cur = (M.to_3x3() @ Vector((0, 1, 0))).normalized()
    q = cur.rotation_difference(Vector(d).normalized())
    h = M.translation
    pb.matrix = Matrix.Translation(h) @ q.to_matrix().to_4x4() @ Matrix.Translation(-h) @ M
def turn(name, axis, deg):
    bpy.context.view_layer.update()
    pb = rig.pose.bones[name]; M = pb.matrix.copy(); h = M.translation
    pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-h) @ M
P = {
    "rest": [],
    "arms_down": [("aim", "upper_arm.L", (0.2, 0.05, -1)), ("aim", "forearm.L", (0.12, -0.15, -1)), ("aim", "hand.L", (0.1, -0.1, -1)),
                  ("aim", "upper_arm.R", (-0.2, 0.05, -1)), ("aim", "forearm.R", (-0.12, -0.15, -1)), ("aim", "hand.R", (-0.1, -0.1, -1))],
    "arms_up": [("aim", "upper_arm.L", (1, 0, 0.6)), ("aim", "forearm.L", (0.6, 0, 1)), ("aim", "hand.L", (0.4, 0, 1)),
                ("aim", "upper_arm.R", (-1, 0, 0.6)), ("aim", "forearm.R", (-0.6, 0, 1)), ("aim", "hand.R", (-0.4, 0, 1))],
    "seated": [("aim", "thigh.L", (0.05, -1, -0.05)), ("aim", "shin.L", (0.02, -0.1, -1)), ("aim", "foot.L", (0, -1, -0.2)),
               ("aim", "thigh.R", (-0.05, -1, -0.05)), ("aim", "shin.R", (-0.02, -0.1, -1)), ("aim", "foot.R", (0, -1, -0.2))],
    "head_turn": [("turn", "neck", 'Z', 20), ("turn", "head", 'Z', 40), ("turn", "head", 'X', 10)],
    "bend_twist": [("turn", "spine", 'X', 15), ("turn", "chest", 'X', 15), ("turn", "chest", 'Z', 25)],
    # legs (world axes at the joint): knee flex = shin about +X, hip flex = thigh about -X, toes up = foot about -X,
    # leg out to the side = thigh.L about -Y / thigh.R about +Y
    "knee45": [("turn", f"shin.{s}", 'X', 45) for s in "LR"],
    "knee90": [("turn", f"shin.{s}", 'X', 90) for s in "LR"],
    "knee130": [("turn", f"shin.{s}", 'X', 130) for s in "LR"],
    "ankle_up": [("turn", f"foot.{s}", 'X', -20) for s in "LR"],
    "ankle_down": [("turn", f"foot.{s}", 'X', 35) for s in "LR"],
    "hip_fwd": [("turn", "thigh.L", 'X', -70), ("turn", "thigh.R", 'X', -30)],
    "hip_side": [("turn", "thigh.L", 'Y', -35), ("turn", "thigh.R", 'Y', 35)],
    "hip_back": [("turn", f"thigh.{s}", 'X', 25) for s in "LR"],
    # arms (aim the bones at world directions; g = +1 for the left arm, -1 for the right)
    "arm_side": [("aim", f"{b}.{s}", (g, 0, 0)) for s, g in (("L", 1), ("R", -1)) for b in ("upper_arm", "forearm", "hand")],
    "arm_fwd": [("aim", f"{b}.{s}", (0.1 * g, -1, 0)) for s, g in (("L", 1), ("R", -1)) for b in ("upper_arm", "forearm", "hand")],
    "elbow90": [x for s, g in (("L", 1), ("R", -1)) for x in (("aim", f"upper_arm.{s}", (0.12 * g, 0.05, -1)), ("aim", f"forearm.{s}", (0.05 * g, -1, 0)), ("aim", f"hand.{s}", (0.05 * g, -1, 0)))],
    "elbow140": [x for s, g in (("L", 1), ("R", -1)) for x in (("aim", f"upper_arm.{s}", (0.12 * g, 0.05, -1)), ("aim", f"forearm.{s}", (0.1 * g, -0.45, 0.9)), ("aim", f"hand.{s}", (0.1 * g, -0.45, 0.9)))],
    "arm_cross": [x for s, g in (("L", 1), ("R", -1)) for x in (("aim", f"upper_arm.{s}", (-0.5 * g, -1, -0.25)), ("aim", f"forearm.{s}", (-1 * g, -0.25, 0.15)), ("aim", f"hand.{s}", (-1 * g, -0.25, 0.15)))],
    "squat": [x for s in "LR" for x in (("turn", f"thigh.{s}", 'X', -95), ("turn", f"shin.{s}", 'X', 120), ("turn", f"foot.{s}", 'X', -25))] + [("move", "pelvis", (0, 0.12, -0.42))],
}
def move(name, d):
    bpy.context.view_layer.update()
    pb = rig.pose.bones[name]; pb.matrix = Matrix.Translation(Vector(d)) @ pb.matrix
for op, name, *v in P[pose]:
    {"aim": lambda: aim(name, v[0]), "turn": lambda: turn(name, v[0], v[1]), "move": lambda: move(name, v[0])}[op]()
bpy.context.view_layer.update()
sys.argv = sys.argv[:sys.argv.index("--")+1] + [f"{args[0]}_{pose}", "HUM_Body"] + args[2:]
exec(open(os.path.join(os.path.dirname(__file__), "views.py")).read())
