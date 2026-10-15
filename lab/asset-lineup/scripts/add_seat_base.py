"""Give a floating seat a base: a pedestal and two slide rails from the floor up to the seat cushion, sized from the seat itself.
Default seat: LU_NEW_CAR_Seat_FL (the one the human sits on). Parent: car root (so it follows the car). Material: car black trim + dark metal.
Reads IN.blend, writes OUT.blend (never the input):
  Blender -b --factory-startup IN.blend --python lab/asset-lineup/scripts/add_seat_base.py -- OUT.blend [SeatName]"""
import bpy, bmesh, sys, numpy as np
from mathutils import Vector, Matrix
args = sys.argv[sys.argv.index("--") + 1:]; out = args[0]; seat_name = args[1] if len(args) > 1 else "Seat_FL"
P = lambda n: bpy.data.objects["LU_NEW_CAR_" + n]
root = P("Exterior"); inv = root.matrix_world.inverted()
seat = P(seat_name); floor = P("Int_Floor")
dg = bpy.context.evaluated_depsgraph_get()
e = seat.evaluated_get(dg); me = e.to_mesh(); pts = np.array([(inv @ (e.matrix_world @ v.co))[:] for v in me.vertices]); e.to_mesh_clear()
lo, hi = pts.min(0), pts.max(0)
floor_top = max((inv @ (floor.matrix_world @ v.co)).z for v in floor.data.vertices)
cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2; w, d = hi[0] - lo[0], hi[1] - lo[1]
zb = lo[2] + 0.004                                                       # seat bottom (tiny overlap so it is glued to the cushion)
print("seat", seat_name, "bbox", lo.round(3), hi.round(3), "floor top", round(floor_top, 3), "gap", round(lo[2] - floor_top, 3))
bm = bmesh.new()
def box(x0, x1, y0, y1, z0, z1, mat, bevel=0.0):
    before = set(bm.faces); r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r["verts"]: v.co = Vector((x0 + (v.co.x + .5) * (x1 - x0), y0 + (v.co.y + .5) * (y1 - y0), z0 + (v.co.z + .5) * (z1 - z0)))
    if bevel: bmesh.ops.bevel(bm, geom=list({ed for v in r["verts"] for ed in v.link_edges}), offset=min(bevel, 0.45 * min(x1 - x0, y1 - y0, z1 - z0)), segments=2, profile=0.5, affect="EDGES")
    for f in set(bm.faces) - before: f.material_index = mat; f.smooth = bool(bevel)
rail_z = floor_top + 0.03
for sx in (-1, 1):                                                       # slide rails on the floor, a little longer than the seat
    box(cx + sx * w * 0.36 - 0.022, cx + sx * w * 0.36 + 0.022, cy - d * 0.62, cy + d * 0.62, floor_top, rail_z, 1, 0.006)
box(cx - w * 0.30, cx + w * 0.30, cy - d * 0.42, cy + d * 0.40, rail_z, zb - 0.045, 0, 0.012)        # pedestal housing
for sx in (-1, 1):                                                       # seat-to-rail brackets
    box(cx + sx * w * 0.36 - 0.03, cx + sx * w * 0.36 + 0.03, cy - d * 0.38, cy + d * 0.34, rail_z, zb - 0.0, 0, 0.006)
box(cx - w * 0.36, cx + w * 0.36, cy - d * 0.46, cy + d * 0.44, zb - 0.045, zb, 0, 0.012)                  # cushion mount plate
box(cx - 0.04, cx + 0.04, cy - d * 0.50, cy - d * 0.46, zb - 0.09, zb - 0.07, 1, 0.004)                 # adjuster bar at the front
name = f"LU_NEW_CAR_{seat_name}_Base"
for o in [o for o in bpy.data.objects if o.name == name]: bpy.data.objects.remove(o)
mesh = bpy.data.meshes.new(name.replace("LU_", "")); bm.to_mesh(mesh); bm.free()
mesh.materials.append(bpy.data.materials["NEW_MAT_CarBlackTrim"]); mesh.materials.append(bpy.data.materials["NEW_Material.071"])
o = bpy.data.objects.new(name, mesh); seat.users_collection[0].objects.link(o)
o.parent = root; o.matrix_parent_inverse = Matrix.Identity(4)
bpy.ops.wm.save_as_mainfile(filepath=out, copy=False)
print("saved", out)
