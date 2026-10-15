"""Read the creator's hand-edited holding-phone pose from the live session -> scripts/phone_hold_pose.json (+ a snapshot image)."""
import bpy, json, math, os
from mathutils import Matrix
ROOT = os.environ.get("ANIM_ROOT") or os.path.dirname(os.path.abspath(__import__("bpy").data.filepath))
rig = bpy.data.objects["RIG_Human"]; sock = bpy.data.objects["HUM_PhoneSocket"]
if rig.mode != 'POSE': bpy.ops.object.mode_set(mode='POSE')
out = {"bones": {}, "props": {}, "socket": {}}
for pb in rig.pose.bones:
    m = pb.matrix_basis
    if pb.matrix_basis != Matrix.Identity(4): out["bones"][pb.name] = [list(r) for r in m]
for n in ("thigh_parent.L", "thigh_parent.R", "upper_arm_parent.L", "upper_arm_parent.R"): out["props"][n] = rig.pose.bones[n]["IK_FK"]
out["socket"] = {"parent_bone": sock.parent_bone, "inverse": [list(r) for r in sock.matrix_parent_inverse], "location": list(sock.location), "rotation": list(sock.rotation_euler)}
dg = bpy.context.evaluated_depsgraph_get()
out["phone_world"] = [list(r) for r in sock.evaluated_get(dg).matrix_world]
json.dump(out, open(os.path.join(ROOT, "scripts", "phone_hold_pose.json"), "w"), indent=1)
# what changed vs the hold_read frame 1 pose
a = bpy.data.actions["HUM_phone_hold_read"]; rig.animation_data_create().action = a; bpy.context.scene.frame_set(500); bpy.context.scene.frame_set(1)
e = rig.evaluated_get(bpy.context.evaluated_depsgraph_get()); changed = []
for pb in rig.pose.bones:
    d = (Matrix(out["bones"].get(pb.name, Matrix.Identity(4))) - e.pose.bones[pb.name].matrix_basis)
    mx = max(abs(x) for r in d for x in r)
    if mx > 0.02: changed.append((pb.name, round(mx, 3)))
rig.animation_data.action = None
rig.update_tag(); bpy.context.view_layer.update()
result = {"bones_saved": len(out["bones"]), "ik_fk": out["props"], "changed_vs_old_pose": sorted(changed, key=lambda x: -x[1])[:25], "socket": out["socket"]["parent_bone"]}
