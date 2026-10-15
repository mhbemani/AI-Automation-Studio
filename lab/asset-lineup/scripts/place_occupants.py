"""Put the human (driver, left seat) and the main Claude (V3-A, passenger seat) inside the new car, as extra copies (the plinth versions stay).
Human: copy of the rigged scan, posed seated with analytic two-bone IK (legs to the floor, arms to the steering wheel), spine leaning back 8 degrees.
Claude: linked duplicate of LU_V3A_Claude sitting on the right seat. Both are parented to the car root, so they move with the car; doors can be opened around them.
Collection LU_InCar. Reads IN.blend, writes OUT.blend (never the input):
  Blender -b --factory-startup IN.blend --python lab/asset-lineup/scripts/place_occupants.py -- OUT.blend"""
import bpy, sys, math
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lineup_lib as L
out = sys.argv[sys.argv.index("--") + 1]
P = lambda n: bpy.data.objects["LU_NEW_CAR_" + n]
root = P("Exterior"); inv = root.matrix_world.inverted()
if "LU_InCar" in bpy.data.collections: raise SystemExit("occupants already placed in this file")
coll = bpy.data.collections.new("LU_InCar"); bpy.data.collections["LU_Assets"].children.link(coll)
SEAT_TOP, FLOOR = 2.524, 2.358                       # root-local z (measured on the seat cushion and the floor)

# ---------------- Claude on the passenger seat (x < 0), facing forward (-y)
src = [o for o in bpy.data.collections["LU_V3A_Claude"].objects]
croot, cobjs = L.dup_hierarchy(src, bpy.data.objects["LU_V3A_CHAR_Claude"], coll, "_InCar")
for o in cobjs:
    for c in list(o.users_collection):
        if c is not coll: c.objects.unlink(o)
croot.parent = root; croot.matrix_parent_inverse = Matrix.Identity(4)
croot.rotation_euler = (0, 0, 0); croot.location = (-0.46, 0.28, SEAT_TOP)
croot["lineup_note"] = "linked duplicate of LU_V3A_Claude, sitting on the passenger seat"

# ---------------- human on the driver seat (x > 0)
rig0, body0 = bpy.data.objects["LU_NEW_RIG_Human"], bpy.data.objects["LU_NEW_HUM_Body"]
rig = rig0.copy(); rig.name = "LU_NEW_RIG_Human_InCar"; coll.objects.link(rig)
body = body0.copy(); body.name = "LU_NEW_HUM_Body_InCar"; coll.objects.link(body)
for c in list(rig.users_collection):
    if c is not coll: c.objects.unlink(rig)
for c in list(body.users_collection):
    if c is not coll: c.objects.unlink(body)
for m in body.modifiers:
    if m.type == "ARMATURE": m.object = rig
rig.parent = root; rig.matrix_parent_inverse = Matrix.Identity(4); rig.rotation_euler = (0, 0, 0)
body.parent = rig; body.matrix_parent_inverse = Matrix.Identity(4); body.location = (0, 0, 0)
body.hide_viewport = True; body.hide_render = True                     # posing is faster without evaluating the body
PELVIS_T = Vector((0.42, 0.16, SEAT_TOP + 0.105))
a = rig.data; pelvis_rest = a.bones["pelvis"].head_local
rig.location = PELVIS_T - pelvis_rest                                   # armature space -> root-local is a pure translation
bpy.context.view_layer.update()
O = Vector(rig.location)
pb = rig.pose.bones
R = {n: (a.bones[n].head_local.copy(), a.bones[n].tail_local.copy()) for n in (b.name for b in a.bones)}
def restdir(n): return (R[n][1] - R[n][0]).normalized()
def length(n): return (R[n][1] - R[n][0]).length
def place(n, head, d):
    """absolute pose: bone n with its head at `head` (armature space) pointing along d, roll kept from rest"""
    q = restdir(n).rotation_difference(Vector(d).normalized())
    M = Matrix.Translation(head) @ q.to_matrix().to_4x4() @ a.bones[n].matrix_local.to_3x3().to_4x4()
    pb[n].matrix = M; bpy.context.view_layer.update()
def head_of(n): return Vector(pb[n].head)
def tail_of(n): return Vector(pb[n].tail)
def ik(S, T, la, lb, pole):
    d = (T - S); dist = min(d.length, la + lb - 1e-4); u = d.normalized(); T = S + u * dist
    x = (la * la - lb * lb + dist * dist) / (2 * dist); h = math.sqrt(max(la * la - x * x, 0.0))
    pp = (Vector(pole) - u * Vector(pole).dot(u)).normalized(); K = S + u * x + pp * h
    return K, T

# spine: lean back 12 degrees (back = +y)
lean = math.radians(8)
place("pelvis", R["pelvis"][0], Vector((0, math.sin(lean) * 0.5, 1)).normalized())
for n, k in (("spine", 1.0), ("chest", 0.9), ("neck", 0.5), ("head", 0.25)):
    place(n, head_of(n) if n == "pelvis" else Vector(pb[{"spine": "pelvis", "chest": "spine", "neck": "chest", "head": "neck"}[n]].tail), Vector((0, math.sin(lean) * k, math.cos(lean))))
# legs: hip -> ankle on the floor (right foot near the pedals), knees up and a little out
def local(p): return p - O                                              # root-local -> armature space
for side, sx, ankle in (("L", 1, Vector((0.42 + 0.10, -0.40, FLOOR + 0.10))), ("R", -1, Vector((0.42 - 0.09, -0.42, FLOOR + 0.11)))):
    S = head_of("thigh." + side); K, T = ik(S, local(ankle), length("thigh." + side), length("shin." + side), (sx * 0.15, -0.3, 1.0))
    place("thigh." + side, S, K - S); place("shin." + side, K, T - K)
    place("foot." + side, T, Vector((sx * 0.02, -0.92, -0.28)))
# arms: shoulder -> wrist on the steering wheel rim (points on the ring at the driver's left and right)
w = P("SteeringWheel"); ring = [inv @ (w.matrix_world @ Vector((0.19 * math.cos(t), 0.19 * math.sin(t), 0))) for t in [i * math.pi / 18 for i in range(36)]]
cz = (inv @ w.matrix_world.translation).z
left = min((p for p in ring if abs(p.z - (cz - 0.03)) < 0.07), key=lambda p: -p.x)          # the +x-most rim point near mid height = human's left hand
right = min((p for p in ring if abs(p.z - (cz - 0.03)) < 0.07), key=lambda p: p.x)
for side, sx, grip in (("L", 1, left), ("R", -1, right)):
    S = head_of("upper_arm." + side); K, T = ik(S, local(grip), length("upper_arm." + side), length("forearm." + side), (sx * 0.5, 0.3, -1.0))
    place("upper_arm." + side, S, K - S); place("forearm." + side, K, T - K); place("hand." + side, T, (T - K).normalized() + Vector((0, 0, -0.25)))
body.hide_viewport = False; body.hide_render = False
bpy.context.view_layer.update()
hp = inv @ (rig.matrix_world @ head_of("head")) ; ht = inv @ (rig.matrix_world @ tail_of("head"))
print("human head top (bone tail) root-local z:", round(ht.z, 3), " roof z near there is measured in the render")
bpy.ops.wm.save_as_mainfile(filepath=out, copy=False)
print("saved", out)
