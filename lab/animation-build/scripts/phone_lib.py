"""Phone-in-hand helpers (run inside Blender, bridge): put the phone (HUM_PhoneSocket on DEF-hand.R) at a world pose by posing the right IK hand control."""
import bpy, math
from mathutils import Matrix, Vector as V
rig = bpy.data.objects["RIG_Human"]
def _rest_socket_rel():
    """socket pose relative to the DEF-hand.R bone in the bind pose (constant)."""
    saved = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
    for pb in rig.pose.bones: pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    sock = bpy.data.objects["HUM_PhoneSocket"].evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.copy()
    rel = rig.data.bones["DEF-hand.R"].matrix_local.inverted() @ sock
    for n, m in saved.items(): rig.pose.bones[n].matrix_basis = m
    bpy.context.view_layer.update(); return rel
REL = _rest_socket_rel()
def phone_matrix(pos, eyes=(0.04, 0.0, 1.62), tilt_back=0.0):
    """world matrix of the phone: screen (local -Y) faces `eyes`, long axis (+Z) points up (tilted by the geometry)."""
    P = V(pos); n = (V(eyes) - P).normalized(); up = V((0, 0, 1)); L = (up - n * up.dot(n)).normalized()
    Y = -n; Z = L; X = Y.cross(Z).normalized(); Y = Z.cross(X).normalized()
    return Matrix(((X.x, Y.x, Z.x, P.x), (X.y, Y.y, Z.y, P.y), (X.z, Y.z, Z.z, P.z), (0, 0, 0, 1)))
def set_hand_ik(phone_world):
    """pose hand_ik.R so that the socket (phone) is at phone_world; arm must be in IK mode."""
    target_def = phone_world @ REL.inverted()               # where DEF-hand.R must be
    d = target_def @ rig.data.bones["DEF-hand.R"].matrix_local.inverted()
    pb = rig.pose.bones["hand_ik.R"]; pb.rotation_mode = 'XYZ'
    pb.matrix = d @ rig.data.bones["hand_ik.R"].matrix_local
    rig.update_tag(); bpy.context.view_layer.update()
def phone_world():
    return bpy.data.objects["HUM_PhoneSocket"].evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.copy()
def ik_arm(side, on):
    rig.pose.bones[f"upper_arm_parent.{side}"]["IK_FK"] = 0.0 if on else 1.0
    rig.update_tag(); bpy.context.view_layer.update()
