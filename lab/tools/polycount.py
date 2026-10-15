"""Polygon budget report for the car scenes (same method for every scene, so numbers compare).
Run headless:  /Applications/Blender.app/Contents/MacOS/Blender -b <scene.blend> --python lab/tools/polycount.py
Prints a readable summary plus one POLYJSON line.
Counts EVALUATED render-visible meshes (modifiers applied, linked duplicates and collection instances counted once
per instance; 00_LIB / LIB_* excluded). Groups by name prefix: car (CAR_*), claude (CHAR_Claude*), human_seated /
human_street (CHAR_Human*), city (CITY_*), props (PROP_*), other.
'in_camera' = objects whose bounding box overlaps each camera's frustum at sample frames (no occlusion culling, so it
is an upper bound; it is the same upper bound for every scene). Edit FR below if a scene uses other cameras/frames."""
import bpy, sys, json, collections
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
sc = bpy.context.scene
FR = {"CAM_EST_Street":[1,120,230], "CAM_PHONE_CU":[100,150], "CAM_HUMAN_POV":[200,340,700,1200], "CAM_CLAUDE_POV":[280,620,900]}
def group(name):
    for p,g in (("CAR_","car"),("CHAR_Claude","claude"),("CHAR_Human_Street","human_street"),("CHAR_Human","human_seated"),("CITY_","city"),("PROP_","props"),("LIB_","lib")):
        if name.startswith(p): return g
    return "other"
tri_cache={}
def tris(obj):
    key=(obj.original.data.name, tuple((m.type, getattr(m,"levels",0), getattr(m,"render_levels",0)) for m in obj.original.modifiers))
    if key not in tri_cache:
        me=obj.to_mesh(); me.calc_loop_triangles(); tri_cache[key]=(len(me.loop_triangles), len(me.polygons)); obj.to_mesh_clear()
    return tri_cache[key]
def collect(cam=None):
    dg=bpy.context.evaluated_depsgraph_get()
    out=collections.defaultdict(lambda:[0,0,0])  # tris, faces, objects
    for inst in dg.object_instances:
        o=inst.object
        if o.type!='MESH': continue
        src=(inst.parent.original if inst.is_instance and inst.parent else o.original)
        if src.hide_render or o.original.hide_render: continue
        name=src.name
        if name.startswith("LIB_") or (o.original.users_collection and o.original.users_collection[0].name=="00_LIB" and not inst.is_instance): continue
        if cam is not None:
            mw=inst.matrix_world
            cs=[world_to_camera_view(sc,cam,mw@Vector(c)) for c in o.bound_box]
            if all(c.z<=0 for c in cs): continue
            if all(c.x<0 for c in cs) or all(c.x>1 for c in cs) or all(c.y<0 for c in cs) or all(c.y>1 for c in cs): continue
        try: t,f=tris(o)
        except Exception: continue
        g=group(name); out[g][0]+=t; out[g][1]+=f; out[g][2]+=1
    return out
# totals in the whole scene (evaluated, render-visible, no culling)
sc.frame_set(1)
tot=collect()
res={"scene_total":{k:{"tris":v[0],"faces":v[1],"objects":v[2]} for k,v in tot.items()}}
# part breakdown for characters/car
dg=bpy.context.evaluated_depsgraph_get()
parts=collections.defaultdict(int)
for o in bpy.data.objects:
    if o.type=="MESH" and not o.hide_render and not o.name.startswith("LIB_"):
        e=o.evaluated_get(dg)
        try: t,_=tris(e)
        except Exception: continue
        parts[o.name]+=t
res["parts"]=dict(sorted(parts.items(), key=lambda kv:-kv[1])[:25])
# in-camera
incam={}
for cname, frames in FR.items():
    cam=bpy.data.objects.get(cname)
    if not cam: continue
    sc.camera=cam; rows=[]
    for f in frames:
        sc.frame_set(f); o=collect(cam)
        rows.append({"frame":f, **{k:o[k][0] for k in ("car","claude","human_seated","human_street","city","props","other")}, "total":sum(v[0] for v in o.values())})
    incam[cname]=rows
res["in_camera"]=incam
print("POLYJSON"+json.dumps(res))

# readable summary
_rows = [r for rr in res["in_camera"].values() for r in rr]
def _avg(g): return sum(r.get(g, 0) for r in _rows) / max(1, len(_rows))
print("=== POLYCOUNT SUMMARY (tris / faces) ===")
for k, v in res["scene_total"].items(): print(f"  scene total {k:13s} {v['tris']:>10,} tris {v['faces']:>10,} faces {v['objects']:>5} objs")
for g in ("car", "claude", "human_seated", "human_street", "city", "total"): print(f"  in-camera avg {g:13s} {_avg(g):>10,.0f} tris")
for c, rr in res["in_camera"].items(): print(f"  {c:16s} city avg {sum(r['city'] for r in rr)/len(rr):>10,.0f}   total avg {sum(r['total'] for r in rr)/len(rr):>10,.0f}")
