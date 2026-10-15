"""Render one hand isolated (faces touching its strongest-weight vertices), in its own PCA frame, from back / palm /
thumb side / pinky side / fingertips, with vertex numbers written to <prefix>_labels.json for overlaying.
Not saved. Run: Blender -b --factory-startup <blend> --python scripts/hand_closeup.py -- <prefix> [hand.R|hand.L]"""
import bpy, bmesh, sys, json, math
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
args = sys.argv[sys.argv.index("--")+1:]; prefix = args[0]; bone = args[1] if len(args) > 1 else "hand.R"
sc = bpy.context.scene; o = bpy.data.objects["HUM_Body"]
gi = {g.index: g.name for g in o.vertex_groups}
bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table(); dl = bm.verts.layers.deform.active
dom = lambda v: gi[max(v[dl].keys(), key=lambda k: v[dl][k])] if v[dl] else None
H = {v.index for v in bm.verts if dom(v) == bone}
keep = {f.index for f in bm.faces if any(v.index in H for v in f.verts)}
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context='FACES_ONLY')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
me = bpy.data.meshes.new("hand"); bm.to_mesh(me); hand = bpy.data.objects.new("hand", me); sc.collection.objects.link(hand)
for ob in sc.objects: ob.hide_render = ob is not hand
pts = [v.co.copy() for v in me.vertices]; c = sum(pts, Vector()) / len(pts)
# PCA via power iteration on the covariance
import itertools
C = Matrix(((0,)*3,)*3)
for p in pts:
    d = p - c
    for i, j in itertools.product(range(3), range(3)): C[i][j] += d[i] * d[j]
axes = []
for _ in range(3):
    v = Vector((1, 0.3, 0.2))
    for _ in range(100):
        v = C @ v
        for a in axes: v -= a * v.dot(a)
        v.normalize()
    axes.append(v)
L, Wd, T = axes  # length, width, thickness
import os
if os.environ.get("HAND_FRAME"):  # fixed frame "cx,cy,cz;Lx,Ly,Lz;Wx,..;Tx,.." so old/new renders match
    c, L, Wd, T = (Vector(map(float, g.split(","))) for g in os.environ["HAND_FRAME"].split(";"))
print("PCA", "len", tuple(round(x, 3) for x in L), "width", tuple(round(x, 3) for x in Wd), "thick", tuple(round(x, 3) for x in T))
ext = lambda a: (min((p - c).dot(a) for p in pts), max((p - c).dot(a) for p in pts))
print("EXTENT len %.3f..%.3f width %.3f..%.3f thick %.3f..%.3f" % (*ext(L), *ext(Wd), *ext(T)))
r = sc.render; r.engine = 'BLENDER_WORKBENCH'; r.resolution_x = r.resolution_y = 700
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (.8, .55, .45); sh.show_object_outline = True
sh.show_backface_culling = False
hand.modifiers.new("w", 'WIREFRAME').use_replace = False; hand.modifiers["w"].thickness = 0.0006
cd = bpy.data.cameras.new("C"); cd.type = 'ORTHO'; cd.ortho_scale = float(os.environ.get("ORTHO", "0.2"))
cam = bpy.data.objects.new("C", cd); sc.collection.objects.link(cam); sc.camera = cam
views = {"A_T+": T, "B_T-": -T, "C_W+": Wd, "D_W-": -Wd, "E_L+": L}
labels = {}
for n, d in views.items():
    cam.location = c + d * 1.0
    up = L if abs(d.dot(L)) < .9 else T
    cam.rotation_mode = 'QUATERNION'; cam.rotation_quaternion = (-d).to_track_quat('-Z', 'Y')
    # roll the camera so 'up' in the image is the hand's length axis
    bpy.context.view_layer.update()
    cur_up = cam.matrix_world.to_3x3() @ Vector((0, 1, 0)); want = (up - d * up.dot(d)).normalized()
    ang = math.atan2(cur_up.cross(want).dot(-d), cur_up.dot(want))
    cam.rotation_quaternion = Matrix.Rotation(-ang, 4, d).to_quaternion() @ cam.rotation_quaternion
    bpy.context.view_layer.update()
    r.filepath = f"{prefix}_{n}.png"; bpy.ops.render.render(write_still=True)
    # label only the vertices on the near side
    labels[n] = []
    for i, v in enumerate(me.vertices):
        s = world_to_camera_view(sc, cam, v.co)
        labels[n].append([i, s.x, s.y, (v.co - c).dot(d)])
json.dump({"labels": labels, "orig_index": [None] * 0}, open(f"{prefix}_labels.json", "w"))
