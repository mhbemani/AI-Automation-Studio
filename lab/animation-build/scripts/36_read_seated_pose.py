"""Read the creator's hand-fixed seated pose (arms, wrists, fingers, both sides) from the live session -> scripts/seated_hands_pose.json"""
import bpy, json, os
from mathutils import Matrix
ROOT = os.environ.get("ANIM_ROOT") or os.path.dirname(os.path.abspath(__import__("bpy").data.filepath))
rig = bpy.data.objects["RIG_Human"]
if rig.mode != 'POSE': bpy.ops.object.mode_set(mode='POSE')
FING = [f"{n}.{s}" for s in "LR" for n in [f"f_{f}.0{i}" for f in ("index", "middle", "ring", "pinky") for i in (1, 2, 3)] + [f"thumb.0{i}" for i in (1, 2, 3)]]
SET = [f"{n}.{s}" for s in "LR" for n in ("shoulder", "upper_arm_fk", "forearm_fk", "hand_fk")] + FING
out = {n: [list(r) for r in rig.pose.bones[n].matrix_basis] for n in SET}
# which bones differ from the old seated pose (HUM_pass_hands_lap frame 1)?
a = bpy.data.actions["HUM_pass_hands_lap"]; ad = rig.animation_data_create(); old_action = ad.action
changed = []
saved = {n: rig.pose.bones[n].matrix_basis.copy() for n in SET}
ad.action = a; bpy.context.scene.frame_set(500); bpy.context.scene.frame_set(1)
e = rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
for n in SET:
    d = saved[n] - e.pose.bones[n].matrix_basis; mx = max(abs(x) for r in d for x in r)
    if mx > 0.03: changed.append((n, round(mx, 2)))
ad.action = None
for n, m in saved.items(): rig.pose.bones[n].matrix_basis = m
rig.update_tag(); bpy.context.view_layer.update()
json.dump(out, open(os.path.join(ROOT, "scripts", "seated_hands_pose.json"), "w"), indent=1)
result = {"saved": len(out), "changed_vs_old": sorted(changed, key=lambda x: -x[1])[:30]}
