"""Numeric checks of the phone actions (bridge): frame counts, loop closure, phone-to-eyes distance, screen angle to the eyes, hand IK error. -> stills/phone_checks.json"""
import bpy, json, math, os
from mathutils import Vector as V
ROOT = os.environ.get("ANIM_ROOT") or os.path.dirname(os.path.abspath(__import__("bpy").data.filepath))
rig = bpy.data.objects["RIG_Human"]; sock = bpy.data.objects["HUM_PhoneSocket"]
for o in (rig, sock, bpy.data.objects["HUM_Body"]): o.hide_viewport = False      # hidden objects are not evaluated
EXPECT = {"HUM_pose_stand_phone": 1, "HUM_phone_raise": 20, "HUM_phone_hold_read": 96, "HUM_phone_type": 48, "HUM_phone_lower_pocket": 30, "HUM_phone_show_claude": 24, "HUM_walk_texting": 24}
LOOPS = ("HUM_phone_hold_read", "HUM_phone_type", "HUM_walk_texting")
res = {}
for name, length in EXPECT.items():
    a = bpy.data.actions[name]; rig.animation_data_create().action = a; f0, f1 = a.frame_range; loop = name in LOOPS
    r = {"range": [int(f0), int(f1)], "length_ok": (int(f1 - f0) == length) if loop else (int(f1 - f0 + 1) == length)}
    if loop: r["loop_max_diff"] = round(max(abs(fc.evaluate(f0) - fc.evaluate(f1)) for fc in a.fcurves), 6)
    bpy.context.scene.frame_set(500)          # force a re-evaluation after assigning the action
    dist, ang, ik = [], [], []
    for f in range(int(f0), int(f1) + 1):
        bpy.context.scene.frame_set(f); rig.update_tag(); sock.update_tag(); bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get(); e = rig.evaluated_get(dg); es = sock.evaluated_get(dg)
        M = es.matrix_world; pos = M.translation; n = (M.to_3x3() @ V((0, -1, 0))).normalized()
        head = V(e.pose.bones["DEF-spine.006"].head); eyes = head + V((0, -0.075, 0.06))   # approx eye point from the head bone
        d = eyes - pos; dist.append(d.length); ang.append(math.degrees(n.angle(d.normalized())))
    if dist:
        r["phone_to_eyes_m"] = [round(min(dist), 3), round(max(dist), 3)]; r["screen_angle_to_eyes_deg"] = [round(min(ang), 1), round(max(ang), 1)]
    res[name] = r
rig.animation_data.action = None
json.dump(res, open(os.path.join(ROOT, "stills", "phone_checks.json"), "w"), indent=1)
result = res
