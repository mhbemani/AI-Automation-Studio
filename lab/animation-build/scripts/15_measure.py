"""Measurements on the library file (headless): triangles per part/rig (evaluated, modifiers applied) and a draft render of all three rigs.
/usr/bin/time -l Blender -b lab/animation-library/library_v1.blend --python lab/animation-build/scripts/15_measure.py"""
import bpy, time, json, os, math, mathutils
sc = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get()
rows = {}
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    e = o.evaluated_get(dg); me = e.to_mesh(); me.calc_loop_triangles(); t = len(me.loop_triangles); e.to_mesh_clear()
    grp = "human" if o.name.startswith(("HUM_",)) else "claude" if o.name.startswith("CLA_") else "phone" if o.name.startswith("PHN_") else "car" if o.name.startswith("CAR_") else "other"
    rows.setdefault(grp, {})[o.name] = t
tot = {g: sum(v.values()) for g, v in rows.items()}
print("@@M totals", json.dumps(tot)); print("@@M human", rows.get("human")); print("@@M claude", rows.get("claude")); 
print("@@M car top", sorted(rows["car"].items(), key=lambda kv: -kv[1])[:6]); print("@@M phone", rows.get("phone") and sum(rows["phone"].values()))
json.dump({"totals": tot, "parts": rows}, open(os.path.join(os.path.dirname(bpy.data.filepath), "../animation-build/stills/polycount_library.json"), "w"), indent=1)
# draft render: the three rigs side by side
O = bpy.data.objects
O["RIG_Claude"].location = (-1.6, 0, 0); O["RIG_Human"].location = (1.2, 0, 0); O["CAR_Exterior"].location = (0, 6.0, 0.0)
col = bpy.data.collections["CAR"]
exec(open(os.path.join(os.path.dirname(bpy.data.filepath), "../animation-build/scripts/_cam.py")).read())
studio()
cam((0.4, -5.0, 1.6), (0.2, 1.5, 0.9), 45)
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 960, 540, 100
sc.eevee.taa_render_samples = 16; sc.render.image_settings.file_format = "PNG"
sc.render.filepath = os.path.join(os.path.dirname(bpy.data.filepath), "../animation-build/stills/library_draft_render.png")
for o in bpy.data.objects:
    if o.type == 'ARMATURE': o.hide_render = True
t0 = time.time(); bpy.ops.render.render(write_still=True); print("@@M draft render %.2fs" % (time.time() - t0))
