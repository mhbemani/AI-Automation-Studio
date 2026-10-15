"""Copy the hand-made edits of the LEFT door (door skin, window glass, handle, mirror, inner door panel and the cut in the body) to the RIGHT door.
The edits are found by comparing the current file with BASE.blend (the file as make_doors.py wrote it, before the manual edits):
  * body:   faces the left edit removed from the body are removed on the right (matched by position, mirrored); faces it added are added mirrored and welded
  * doors:  Door_R and Int_DoorCard_R get the exact mirror image of the edited Door_L / Int_DoorCard_L; Door_R is put back on its (mirrored) hinge
Reads IN.blend (with your edits), writes OUT.blend (never the input):
  Blender -b --factory-startup IN.blend --python lab/asset-lineup/scripts/mirror_door_edits.py -- BASE.blend OUT.blend"""
import bpy, bmesh, sys, numpy as np
from mathutils import Vector, Matrix, kdtree
base_path, out = sys.argv[-2], sys.argv[-1]
in_path = bpy.data.filepath
WELD = 1.5e-3
P = lambda n: bpy.data.objects["LU_NEW_CAR_" + n]

def faces_rootlocal(objs):
    """per object: list of (centre, nverts, area, material, smooth, [vertex coords]) in root-local coords, doors closed"""
    root = P("Exterior"); root["door_L_open"] = 0.0; root["door_R_open"] = 0.0
    if "Door_L" in objs:
        dl, dr = P("Door_L"), P("Door_R"); dr.location = (-dl.location.x, dl.location.y, dl.location.z)
    bpy.context.view_layer.update(); inv = root.matrix_world.inverted(); res = {}
    for n in objs:
        o = P(n); bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(inv @ o.matrix_world); bm.faces.ensure_lookup_table()
        res[n] = [(np.array(f.calc_center_median()[:]), len(f.verts), f.calc_area(), f.material_index, f.smooth, [np.array(v.co[:]) for v in f.verts]) for f in bm.faces]; bm.free()
    return res
def match(la, lb, tol=0.002):
    kd = kdtree.KDTree(max(len(lb), 1))
    for i, t in enumerate(lb): kd.insert(Vector(t[0]), i)
    kd.balance(); ma, mb = {}, set()
    for i, t in enumerate(la):
        for co, j, d in kd.find_n(Vector(t[0]), 4):
            u = lb[j]
            if d < tol and j not in mb and u[1] == t[1] and abs(u[2] - t[2]) <= 0.05 * max(t[2], 1e-6) + 1e-7 and u[3] == t[3]: ma[i] = j; mb.add(j); break
    return ma, mb

OBJS = ("Ext_Body", "Door_L", "Int_DoorCard_L")
bpy.ops.wm.open_mainfile(filepath=base_path); base = faces_rootlocal(OBJS)
bpy.ops.wm.open_mainfile(filepath=in_path)
cur = faces_rootlocal(OBJS)
root = P("Exterior"); inv = root.matrix_world.inverted()
mir = lambda p: np.array([-p[0], p[1], p[2]])

# --- body: find the box that contains every face the left edit touched, then replace the mirrored box on the right by a mirror copy of the left box
ma, mb = match(base["Ext_Body"], cur["Ext_Body"])
touched = [t for i, t in enumerate(base["Ext_Body"]) if i not in ma] + [t for j, t in enumerate(cur["Ext_Body"]) if j not in mb]
pts = np.array([p for t in touched for p in t[5]])
MARGIN = 0.04
lo, hi = pts.min(0) - MARGIN, pts.max(0) + MARGIN
lo[0] = max(lo[0], 0.0)
print("left edit touched %d faces; box x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f" % (len(touched), lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
body = P("Ext_Body"); Mb = inv @ body.matrix_world
bm = bmesh.new(); bm.from_mesh(body.data); bm.transform(Mb); bm.faces.ensure_lookup_table()
inbox = lambda c, sgn: lo[0] <= sgn * c[0] <= hi[0] and lo[1] <= c[1] <= hi[1] and lo[2] <= c[2] <= hi[2]
src = [f for f in bm.faces if inbox(f.calc_center_median(), 1)]
dst = [f for f in bm.faces if inbox(f.calc_center_median(), -1)]
print("  left box faces", len(src), "- replacing", len(dst), "faces on the right")
data = [([np.array(v.co[:]) for v in f.verts], f.material_index, f.smooth) for f in src]
bmesh.ops.delete(bm, geom=dst, context="FACES_ONLY")
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
old = list(bm.verts); kdv = kdtree.KDTree(max(len(old), 1))
for i, v in enumerate(old): kdv.insert(v.co, i)
kdv.balance(); cache = {}
def vert(p):
    key = tuple(np.round(p, 5))
    if key in cache: return cache[key]
    hit = kdv.find_range(Vector(p), WELD)
    v = old[min(hit, key=lambda h: h[2])[1]] if hit else bm.verts.new(Vector(p))
    cache[key] = v; return v
made = 0
for vs, m, sm in data:
    vv = [vert(np.array([-p[0], p[1], p[2]])) for p in vs][::-1]
    if len(set(vv)) < 3: continue
    try:
        f = bm.faces.new(vv); f.material_index = m; f.smooth = sm; made += 1
    except ValueError: pass
print("  added", made, "mirrored faces")
bm.transform(Mb.inverted()); bm.to_mesh(body.data); bm.free(); body.data.update()

# --- doors and inner panel: exact mirror of the edited left ones
def mirror_object(src, dst):
    Ms = inv @ src.matrix_world; Md = (inv @ dst.matrix_world).inverted()
    b = bmesh.new(); b.from_mesh(src.data); b.transform(Ms)
    for v in b.verts: v.co.x = -v.co.x
    bmesh.ops.reverse_faces(b, faces=b.faces[:]); b.transform(Md)
    old = dst.data; me = bpy.data.meshes.new(old.name); b.to_mesh(me); b.free()
    for m in src.data.materials: me.materials.append(m)
    dst.data = me
    for s in dst.material_slots: s.link = "DATA"
    if old.users == 0: bpy.data.meshes.remove(old)
dl, dr = P("Door_L"), P("Door_R")
dr.location = (-dl.location.x, dl.location.y, dl.location.z); bpy.context.view_layer.update()
mirror_object(dl, dr); mirror_object(P("Int_DoorCard_L"), P("Int_DoorCard_R"))
print("Door_R and Int_DoorCard_R rebuilt as the mirror of the left ones")
bpy.ops.wm.save_as_mainfile(filepath=out, copy=False)
print("saved", out)
