"""1) Rebuild the four wheels of the new car as clean round lathe meshes (32 segments, smooth shading, hard edges only at the real corners):
   rounded tyre, dark dish with 5 raised spokes, hub cap. Same size, offset and two materials as the finished back-right wheel
   (tyre NEW_Material.073, rim NEW_Material.071); left wheels mirrored, front wheels shifted like copy_wheels.py did.
2) Make the two front seats 8 percent smaller (uniform scale about the seat base) so the headrests clear the roof.
Reads IN.blend, writes OUT.blend (never the input):
  Blender -b --factory-startup IN.blend --python lab/asset-lineup/scripts/round_wheels_shrink_seats.py -- OUT.blend"""
import bpy, bmesh, sys, math
from mathutils import Vector, Matrix
out = sys.argv[sys.argv.index("--") + 1]
SEAT_SCALE, SEG = 0.92, 32
root = bpy.data.objects["LU_NEW_CAR_Exterior"]
W = {n: bpy.data.objects["LU_NEW_CAR_Wheel_" + n] for n in ("back-right", "back-left", "front-right", "front-left")}
tire_m, rim_m = bpy.data.materials["NEW_Material.073"], bpy.data.materials["NEW_Material.071"]

# profile (x along the axle, outward is -x; r = radius), material 0 = tyre, 1 = rim
PROFILE = [(-0.136, 0.0, 1), (-0.142, 0.030, 1), (-0.130, 0.052, 1),       # hub cap
           (-0.118, 0.062, 0), (-0.118, 0.205, 0),                          # dark dish
           (-0.134, 0.222, 1), (-0.148, 0.226, 1),                          # rim lip
           (-0.167, 0.246, 0), (-0.166, 0.292, 0), (-0.152, 0.322, 0),      # outer sidewall + shoulder
           (-0.122, 0.335, 0), (0.024, 0.335, 0),                           # tread
           (0.062, 0.322, 0), (0.092, 0.292, 0), (0.100, 0.246, 0),         # inner shoulder + sidewall
           (0.082, 0.205, 0), (0.040, 0.196, 1), (0.020, 0.0, 1)]           # inner barrel, back disc
def wheel_mesh(name, mirrored, dx):
    bm = bmesh.new(); n = len(PROFILE)
    pts = []
    for j in range(SEG):
        a = 2 * math.pi * j / SEG
        pts.append([None if PROFILE[i][1] == 0 else bm.verts.new((PROFILE[i][0], PROFILE[i][1] * math.cos(a), PROFILE[i][1] * math.sin(a))) for i in range(n)])
    axis = {i: bm.verts.new((PROFILE[i][0], 0, 0)) for i in range(n) if PROFILE[i][1] == 0}
    V = lambda j, i: axis[i] if PROFILE[i][1] == 0 else pts[j % SEG][i]
    for j in range(SEG):
        for i in range(n - 1):
            vs = [V(j, i), V(j + 1, i), V(j + 1, i + 1), V(j, i + 1)]
            vs = [v for k, v in enumerate(vs) if k == 0 or v is not vs[k - 1]]
            if len(set(vs)) < 3: continue
            f = bm.faces.new(list(dict.fromkeys(vs))); f.material_index = PROFILE[i][2] if PROFILE[i][2] == PROFILE[i + 1][2] else (0 if PROFILE[i][1] > 0.2 else 1); f.smooth = True
    # hard (sharp) circumferential edges where the profile turns more than 40 degrees, and the hub cap / dish seam
    for i in range(1, n - 1):
        a0 = Vector((PROFILE[i][0] - PROFILE[i - 1][0], PROFILE[i][1] - PROFILE[i - 1][1])); a1 = Vector((PROFILE[i + 1][0] - PROFILE[i][0], PROFILE[i + 1][1] - PROFILE[i][1]))
        if a0.length and a1.length and math.degrees(a0.angle(a1)) > 40:
            for e in bm.edges:
                if all(abs(v.co.x - PROFILE[i][0]) < 1e-6 and abs(math.hypot(v.co.y, v.co.z) - PROFILE[i][1]) < 1e-6 for v in e.verts): e.smooth = False
    for k in range(5):                                                       # 5 raised spokes (rim material), from the hub to the lip
        ang = 2 * math.pi * k / 5 + math.pi / 2
        before = set(bm.faces)
        r = bmesh.ops.create_cube(bm, size=1.0)
        for v in r["verts"]:
            v.co = Vector((-0.1235 + v.co.x * 0.012, 0.0, 0.0)) + Vector((0, (v.co.y + 0.5) * 0.17 + 0.045, v.co.z * (0.036 if v.co.y < 0 else 0.026)))
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(ang - math.pi / 2, 3, "X"), verts=r["verts"])
        for f in set(bm.faces) - before: f.material_index = 1; f.smooth = False
    for v in bm.verts: v.co.x = (-v.co.x if mirrored else v.co.x) + dx
    if mirrored: bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(tire_m); me.materials.append(rim_m)
    return me
half = lambda o: abs(o.matrix_world.translation.y - root.matrix_world.translation.y)
for n, o in W.items():
    left = "left" in n
    dx = 0.0 if n == "back-right" else (half(o) - half(W["back-right"])) * (1 if not left else -1)
    old = o.data
    o.data = wheel_mesh("NEW_LIB_Hero_Wheel_" + n, left, dx)
    for s in o.material_slots: s.link = "DATA"
    if old.users == 0: bpy.data.meshes.remove(old)
    print("wheel", n, "faces", len(o.data.polygons), "mirrored", left, "shift", round(dx, 3))
for side in ("FL", "FR"):
    s = bpy.data.objects[f"LU_NEW_CAR_Seat_{side}"]
    s.scale = (SEAT_SCALE,) * 3
bpy.ops.wm.save_as_mainfile(filepath=out, copy=False)
print("saved", out)
