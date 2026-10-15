"""Checks of Claude's locomotion (bridge): loop closure, planted-foot drift, foot height, frame counts -> stills/claude_locomotion_checks.json"""
import bpy, json, math, os
from mathutils import Vector as V
ROOT = os.environ.get("ANIM_ROOT") or os.path.dirname(os.path.abspath(__import__("bpy").data.filepath))
rig = bpy.data.objects["RIG_Claude"]
for o in bpy.data.objects:
    if o.name.startswith(("CLA_", "RIG_Claude")): o.hide_viewport = False
res = {}
for name, cyc, stride in (("CLA_walk_cycle", 24, 0.40), ("CLA_run_cycle", 16, 0.5714)):
    a = bpy.data.actions[name]; f0, f1 = a.frame_range
    r = {"range": [int(f0), int(f1)], "length_ok": int(f1 - f0) == cyc, "loop_max_diff": round(max(abs(fc.evaluate(f0) - fc.evaluate(f1)) for fc in a.fcurves), 6)}
    rig.animation_data_create().action = a; bpy.context.scene.frame_set(500)
    v = stride / cyc; data = {k: [] for k in (1, 2, 3, 4)}; zs = []
    for f in range(1, cyc + 1):
        bpy.context.scene.frame_set(f); e = rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
        for k in (1, 2, 3, 4):
            t = V(e.pose.bones[f"leg_{k}"].tail); data[k].append((f, t.y - v * (f - 1), t.z)); zs.append(t.z)
    drift = 0.0; stance_frames = {}
    for k in (1, 2, 3, 4):
        groups = []; grp = []
        for f, y, z in data[k] + data[k]:                       # twice so a stance that wraps around the loop end is one group
            if z < 0.0002: grp.append((f, y))
            elif grp: groups.append(grp); grp = []
        if grp: groups.append(grp)
        g = max(groups, key=len); stance_frames[k] = len(g)
        # drift within the group measured against body travel (frames repeat after the wrap: add one cycle of travel)
        ws = []; base = g[0][0]
        for f, y in g:
            ff = f if f >= base else f + cyc
            ws.append(y + v * (f - 1) - v * (ff - 1))
        drift = max(drift, (max(ws) - min(ws)))
    res[name] = {**r, "foot_drift_cm_in_stance": round(drift * 100, 3), "min_foot_z_mm": round(min(zs) * 1000, 2), "max_foot_z_cm": round(max(zs) * 100, 2), "stance_frames_per_leg": stance_frames}
rig.animation_data.action = None
json.dump(res, open(os.path.join(ROOT, "stills", "claude_locomotion_checks.json"), "w"), indent=1); result = res
