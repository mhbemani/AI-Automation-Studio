"""Replace the lumpy headrests of the new car's two front seats by a simple real-looking one:
a bevelled leather pad on two thin black posts. Same object names, parents, transforms, material and subsurf as before;
the posts are two new small objects (LU_NEW_CAR_Seat_F?_Headrest_Posts) parented to the seat back.
Reads IN.blend, writes OUT.blend (never the input):
  Blender -b --factory-startup IN.blend --python lab/asset-lineup/scripts/fix_headrests.py -- OUT.blend"""
import bpy, bmesh, sys, math
from mathutils import Vector, Matrix
out = sys.argv[sys.argv.index("--") + 1]
W, T, H = 0.24, 0.085, 0.17            # pad width, thickness, height (m)
POST_X, POST_R, POST_Z0, POST_Z1 = 0.065, 0.011, -0.07, 0.01   # posts go 7 cm into the seat back top, end under the pad

def pad_mesh(name):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * W, v.co.y * T, v.co.z * H + H / 2))
    bmesh.ops.bevel(bm, geom=bm.edges[:], offset=0.022, segments=2, profile=0.5, affect="EDGES")
    for v in bm.verts:                      # a touch of curvature: the face toward the head (-y) bulges
        v.co.y -= 0.012 * max(0.0, 1 - (v.co.x / (W / 2)) ** 2) * (1 if v.co.y < 0 else 0)
    for f in bm.faces: f.smooth = True
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return me

def posts_mesh(name):
    bm = bmesh.new()
    for sx in (-POST_X, POST_X):
        r = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=8, radius1=POST_R, radius2=POST_R, depth=POST_Z1 - POST_Z0)
        bmesh.ops.translate(bm, vec=(sx, 0, (POST_Z0 + POST_Z1) / 2), verts=r["verts"])
    for f in bm.faces: f.smooth = True
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return me

trim = bpy.data.materials["NEW_MAT_CarBlackTrim"]
for side in ("FL", "FR"):
    h = bpy.data.objects[f"LU_NEW_CAR_Seat_{side}_Headrest"]
    back = h.parent
    old = h.data
    me = pad_mesh(f"NEW_CAR_Seat_{side}_Headrest.002")
    me.materials.append(old.materials[0])
    h.data = me
    h.location = (0, 0, 0.63)               # unchanged: 3 cm above the top of the seat back
    pn = f"LU_NEW_CAR_Seat_{side}_Headrest_Posts"
    po = bpy.data.objects.get(pn)
    if po is None:
        po = bpy.data.objects.new(pn, posts_mesh(f"NEW_CAR_Seat_{side}_Headrest_Posts"))
        po.data.materials.append(trim)
        for c in h.users_collection: c.objects.link(po)
    po.parent = back; po.location = h.location; po.rotation_euler = h.rotation_euler
    for k in list(bpy.data.meshes):
        if k.users == 0: bpy.data.meshes.remove(k)
bpy.ops.wm.save_as_mainfile(filepath=out, copy=False)
print("saved", out)
