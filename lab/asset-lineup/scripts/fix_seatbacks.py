"""Rebuild the pinched seat backs of the new car's two front seats as a rounded centre panel with two side bolsters
(bevelled boxes under the existing subsurf). Same object names, parents, transforms, material and modifier; same overall
size (0.6 wide, 0.16 deep, 0.6 high, origin at the base) so headrests and posts still fit.
Reads IN.blend, writes OUT.blend (never the input):
  Blender -b --factory-startup IN.blend --python lab/asset-lineup/scripts/fix_seatbacks.py -- OUT.blend"""
import bpy, bmesh, sys
from mathutils import Vector
out = sys.argv[sys.argv.index("--") + 1]

def shape(bm, x0, x1, y0, y1, z0, z1, bevel):
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r["verts"]:
        v.co = Vector(((x0 + x1) / 2 + v.co.x * (x1 - x0), (y0 + y1) / 2 + v.co.y * (y1 - y0), (z0 + z1) / 2 + v.co.z * (z1 - z0)))
    es = list({e for v in r["verts"] for e in v.link_edges})
    bmesh.ops.bevel(bm, geom=es, offset=bevel, segments=2, profile=0.5, affect="EDGES")

def back_mesh(name):
    bm = bmesh.new()
    shape(bm, -0.21, 0.21, -0.03, 0.10, 0.0, 0.60, 0.035)        # centre panel: rounded top and corners
    for sx in (-1, 1):
        shape(bm, sx * 0.20 if sx > 0 else -0.30, 0.30 if sx > 0 else -0.20, -0.06, 0.07, 0.03, 0.56, 0.035)   # side bolsters, 6 cm proud of the panel
    for f in bm.faces: f.smooth = True
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return me

for side in ("FL", "FR"):
    o = bpy.data.objects[f"LU_NEW_CAR_Seat_{side}_Back"]
    mat = o.data.materials[0]
    me = back_mesh(f"NEW_CAR_Seat_{side}_Back.002")
    me.materials.append(mat)
    o.data = me
for k in list(bpy.data.meshes):
    if k.users == 0: bpy.data.meshes.remove(k)
bpy.ops.wm.save_as_mainfile(filepath=out, copy=False)
print("saved", out)
