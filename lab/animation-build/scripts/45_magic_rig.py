"""Magic rig: MAG_Root (empty, child of RIG_Claude, in front of his hands, faces -Y) carries the props
fade, shot, dist, size, wrap, wrap_to, spin_rate, puff, sparkle. Children: MAG_Ring (empty, driven location/scale) with MAG_Ring_Main/Inner/Wisp,
MAG_Puff_1-3 (smoke, grow with `puff`), MAG_Orbit/MAG_Sparkles (grow with `sparkle`). Materials MAG_MAT_Magic(/Smoke) read MAG_Root["fade"].
Also adds CAR_ctrl["dash_glow"] driving the dash screen / monitor / accent emission. Idempotent. Run after 04, 42."""
import bpy, math
from mathutils import Matrix
rig = bpy.data.objects["RIG_Claude"]
for o in list(bpy.data.objects):
    if o.name.startswith("MAG_"): bpy.data.objects.remove(o)
for m in list(bpy.data.materials):
    if m.name.startswith("MAG_MAT"): bpy.data.materials.remove(m)
col = bpy.data.collections.get("MAGIC") or bpy.data.collections.new("MAGIC")
if col.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(col)
for o in col.objects: col.objects.unlink(o)
def new_empty(n, parent):
    e = bpy.data.objects.new(n, None); e.empty_display_type = 'ARROWS'; e.empty_display_size = 0.15; col.objects.link(e); e.parent = parent; e["anim_owner"] = "claude"; return e
root = new_empty("MAG_Root", rig); root.location = (0, -0.30, 0.38)
PR = {"fade": (0.0, 0, 1, "ring visibility 0..1 (drives the material FADE)"), "shot": (0.0, 0, 1, "0 at his hand .. 1 at the target (travels `dist` metres along -Y)"),
      "dist": (1.2, 0, 20, "metres to the target along MAG_Root -Y"), "size": (1.0, 0.01, 4, "ring scale"), "wrap": (0.0, 0, 1, "0 open .. 1 tightened around the target"),
      "wrap_to": (0.7, 0.1, 1, "scale factor at wrap=1"), "spin_rate": (1.0, -10, 10, "ring spin speed (turns per second)"), "puff": (0.0, 0, 1, "smoke puffs scale 0..1"), "sparkle": (0.0, 0, 1, "sparkle orbit scale 0..1")}
for k, (d, lo, hi, tip) in PR.items():
    root[k] = float(d); ui = root.id_properties_ui(k); ui.update(default=float(d)); ui.update(min=float(lo), max=float(hi)); ui.update(description=tip)
ring = new_empty("MAG_Ring", root); ring.rotation_euler = (math.radians(90), 0, 0)
orbit = new_empty("MAG_Orbit", ring)
def drv(obj, path, idx, expr, props):
    fc = obj.driver_add(path, idx) if idx is not None else obj.driver_add(path); d = fc.driver; d.type = 'SCRIPTED'; d.expression = expr
    for p in props:
        v = d.variables.new(); v.name = p; v.type = 'SINGLE_PROP'; v.targets[0].id = root; v.targets[0].data_path = f'["{p}"]'
drv(ring, "location", 1, "-shot*dist", ["shot", "dist"])
for i in range(3): drv(ring, "scale", i, "max(0.001, size*(1-(1-wrap_to)*wrap)*(0.2+0.8*fade))", ["size", "wrap", "wrap_to", "fade"])
# materials: copies reading MAG_Root fade
mats = {}
for src in ("V3A_MAT_Magic", "V3A_MAT_MagicSmoke"):
    m = bpy.data.materials[src].copy(); m.name = src.replace("V3A_MAT", "MAG_MAT"); nt = m.node_tree
    if nt.animation_data:
        for fc in nt.animation_data.drivers:
            if "FADE" in fc.data_path:
                v = fc.driver.variables[0]; v.targets[0].id = root; v.targets[0].data_path = '["fade"]'
    mats[src] = m
def copy_obj(srcname, name, parent, mat_swap=True):
    s = bpy.data.objects[srcname]; o = s.copy(); o.data = s.data.copy() if s.data else None; o.name = name
    if o.data: o.data.name = name
    col.objects.link(o); o.parent = parent; o.matrix_parent_inverse = Matrix.Identity(4); o.location = s.location; o.rotation_euler = s.rotation_euler; o.scale = s.scale
    o.hide_viewport = False; o.hide_render = False; o.hide_set(False); o["anim_owner"] = "claude"
    for k in ("rigify_owner_rig",):
        if k in o: del o[k]
    if o.data and hasattr(o.data, "materials"):
        for i, mm in enumerate(o.data.materials):
            if mm and mm.name in mats: o.data.materials[i] = mats[mm.name]
    if o.animation_data: o.animation_data_clear()
    return o
rings = [copy_obj(f"LU_V3A_Magic_Ring_{n}", f"MAG_Ring_{n}", ring) for n in ("Main", "Inner", "Wisp")]
for r, sgn in zip(rings, (1, -1.6, 0.7)): drv(r, "rotation_euler", 2, f"{sgn}*frame/24*spin_rate*2*pi", ["spin_rate"])
puffs = [copy_obj(f"LU_V3A_Magic_Puff_{i}", f"MAG_Puff_{i}", ring) for i in (1, 2, 3)]
for p in puffs:
    for i in range(3): drv(p, "scale", i, "max(0.001, puff)", ["puff"])
sp = copy_obj("LU_V3A_Magic_Sparkles", "MAG_Sparkles", orbit)
for i in range(3): drv(orbit, "scale", i, "max(0.001, sparkle)", ["sparkle"])
drv(orbit, "rotation_euler", 2, "frame/24*spin_rate*1.5*pi", ["spin_rate"])
for o in col.objects:
    if o.type == 'MESH': o.visible_shadow = False
# car dash glow
car = bpy.data.objects["CAR_ctrl"]; car["dash_glow"] = 0.0
ui = car.id_properties_ui("dash_glow"); ui.update(default=0.0); ui.update(min=0.0, max=1.0); ui.update(description="0..1 dash screen, monitor and accent glow (magic blue-violet)")
def car_drv(matname, node, inp, expr):
    m = bpy.data.materials[matname]; n = m.node_tree.nodes[node]; s = n.inputs[inp]
    if inp in ("Emission Strength", "Strength") and m.node_tree.animation_data:
        for fc in list(m.node_tree.animation_data.drivers):
            if fc.data_path == f'nodes["{node}"].inputs["{inp}"].default_value': m.node_tree.animation_data.drivers.remove(fc)
    fc = s.driver_add("default_value"); d = fc.driver; d.type = 'SCRIPTED'; d.expression = expr
    v = d.variables.new(); v.name = "g"; v.type = 'SINGLE_PROP'; v.targets[0].id = car; v.targets[0].data_path = '["dash_glow"]'
car_drv("NEW_MAT_CarScreen", "Principled BSDF", "Emission Strength", "0.55 + 2.5*g")
acc = bpy.data.materials["NEW_MAT_CarAccent"].node_tree.nodes["Principled BSDF"]; acc.inputs["Emission Color"].default_value = (0.45, 0.30, 1.0, 1.0)
car_drv("NEW_MAT_CarAccent", "Principled BSDF", "Emission Strength", "3.0*g")
mm = bpy.data.materials["NEW_MAT_CarMonitor"].node_tree.nodes["EMISSION"]
base = 1.0   # the monitor emission strength from 05_car_and_phone.py (read from the node only before any driver exists)
car_drv("NEW_MAT_CarMonitor", "EMISSION", "Strength", f"{base} + 2.0*g")
bpy.context.view_layer.update()
result = {"mag": sorted(o.name for o in col.objects), "monitor_base": base}
