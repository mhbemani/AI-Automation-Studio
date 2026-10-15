"""Single-frame pose actions for Claude's 8 emotions (eyes + body, absolute values): CLA_pose_<emotion>, frame 1, fake user.
(The human's absolute poses are HUM_pose_neutral / HUM_pose_seated.) Run via bridge."""
import bpy, sys, os, importlib
ROOT = os.environ.get("ANIM_ROOT") or os.path.dirname(os.path.abspath(__import__("bpy").data.filepath))
sys.path.insert(0, os.path.join(ROOT, "scripts")); import claude_presets as cp; importlib.reload(cp)
rig = bpy.data.objects["RIG_Claude"]; ctrl = rig.pose.bones["ctrl"]
UI = {k: ctrl.id_properties_ui(k).as_dict() for k in ctrl.keys()}
for e in cp.EMOTIONS:
    n = f"CLA_pose_{e}"; old = bpy.data.actions.get(n)
    if old: bpy.data.actions.remove(old)
    a = bpy.data.actions.new(n); a.use_fake_user = True
    if rig.animation_data is None: rig.animation_data_create()
    rig.animation_data.action = a
    vals = cp.preset(e, e)
    for p, v in vals.items(): ctrl[p] = float(v); ctrl.keyframe_insert(f'["{p}"]', frame=1, group="CLA_ctrl")
    rig.animation_data.action = None
for k, v in {kk: vv["default"] for kk, vv in UI.items()}.items(): ctrl[k] = float(v)
result = [a.name for a in bpy.data.actions if a.name.startswith("CLA_pose_")]
