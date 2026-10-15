"""Store the rig's current pose (the creator's corrected standing pose) as scripts/neutral_pose.json; build_emotions.py
uses it as the neutral body pose that every emotion starts from. Run: Blender -b <blend> --python scripts/save_neutral_pose.py"""
import bpy, json, os
rig = bpy.data.objects["RIG_Human"]
pose = {}
for pb in rig.pose.bones:
    if pb.matrix_basis.is_identity: continue
    q = pb.matrix_basis.to_quaternion(); l = pb.matrix_basis.translation
    pose[pb.name] = {"rot": [round(x, 6) for x in q], "loc": [round(x, 6) for x in l]}
p = os.path.join(os.path.dirname(__file__), "neutral_pose.json")
json.dump(pose, open(p, "w"), indent=1)
print("NEUTRAL saved", len(pose), "bones ->", p)
