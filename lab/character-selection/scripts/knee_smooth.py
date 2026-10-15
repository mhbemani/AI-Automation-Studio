"""Smoother bent knees: a Corrective Smooth modifier limited to the knees (vertex group KNEE_SMOOTH).
Corrective Smooth only smooths what the bending changed (the rest shape stays exactly as modelled), so creases and
pinches in a bent knee are relaxed while the straight leg is untouched.
KNEE_SMOOTH = 1 within INNER of each knee joint, fading to 0 at OUTER. Modifier order used: Armature -> contact -> knee smooth (it also smooths the contact push); run with INNER=0.08 OUTER=0.15 FACTOR=1.0 ITER=16.
Run: Blender -b --factory-startup character_selection_lab.blend --python scripts/knee_smooth.py  (env OUT=, INNER, OUTER, FACTOR, ITER)"""
import bpy, os
INNER, OUTER = float(os.environ.get("INNER", "0.06")), float(os.environ.get("OUTER", "0.12"))
FACTOR, ITER = float(os.environ.get("FACTOR", "0.8")), int(os.environ.get("ITER", "8"))
o = bpy.data.objects["HUM_Body"]; rig = bpy.data.objects["RIG_Human"]
for ob in (o, rig):
    bpy.context.view_layer.objects.active = ob
    if ob.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
GROUP = os.environ.get("GROUP", "KNEE_SMOOTH")
CENTERS = os.environ.get("CENTERS", "shin").split(",")        # joint = head of these bones
MEMBERS = os.environ.get("MEMBERS", "thigh,shin").split(",")   # only vertices of these bones (same side)
B = rig.data.bones
K = {s: [B[f"{c}.{s}"].head_local for c in CENTERS] for s in "LR"}
gi = {g.name: g.index for g in o.vertex_groups}
legs = {gi[f"{b}.{s}"]: s for b in MEMBERS for s in "LR"}
vg = o.vertex_groups.get(GROUP) or o.vertex_groups.new(name=GROUP)
n = 0
for v in o.data.vertices:
    sides = {legs[g.group] for g in v.groups if g.group in legs and g.weight > 0.01}   # only that leg's own vertices
    w = 0.0
    for s in sides:
      for k_ in K[s]:
        d = (v.co - k_).length
        w = max(w, 1.0 if d <= INNER else max(0.0, 1 - (d - INNER) / (OUTER - INNER)))
    if w > 0: vg.add([v.index], w, 'REPLACE'); n += 1
    else: vg.remove([v.index])
m = o.modifiers.get(GROUP) or o.modifiers.new(GROUP, 'CORRECTIVE_SMOOTH')
m.vertex_group = GROUP; m.factor = FACTOR; m.iterations = ITER
m.smooth_type = 'LENGTH_WEIGHTED'; m.rest_source = 'ORCO'; m.use_pin_boundary = True
o.modifiers.move(o.modifiers.find(GROUP), len(o.modifiers) - 1)
print("SMOOTH", GROUP, "vertices", n, "| modifiers", [x.name for x in o.modifiers], "| factor", FACTOR, "iterations", ITER)
bpy.ops.wm.save_as_mainfile(filepath=os.environ.get("OUT", bpy.data.filepath))
