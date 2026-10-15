# Car interior for CAR_Exterior (Kenney sedan, faces -Y in its local space; left-hand drive:
# driver sits on the car's LEFT = local +X, the human sits BACK RIGHT = local -X, +Y).
# Everything is parented to CAR_Exterior in local coordinates, so the car can move along a path.
# Re-runnable: rebuilds objects tagged cs_owner="car" (except user_locked) and the glass split.
# Cabin measured from the window faces: windshield y -0.99..-0.38, roof to y 1.06, rear window
# y 1.06..1.28, belt line z 1.44, roof z ~2.2, inner width x ±0.99, body bottom z 0.27.
import bpy, math

car = bpy.data.objects["CAR_Exterior"]
car["cs_owner"] = "car"   # build_city.py then leaves it alone
for o in [o for o in bpy.data.objects if o.get("cs_owner") == "car" and o is not car and not o.get("user_locked")]:
    bpy.data.objects.remove(o)
for o in [o for o in car.children if "_wheel-" in o.name]:   # old build_city wheel copies (owner "stage")
    bpy.data.objects.remove(o)
taken = {o.name for o in bpy.data.objects}
COLL = bpy.data.collections["02_CAR"]

# Wheels: copies of the library sedan's wheels (pivots at the wheel centres), owned by this script.
for w in bpy.data.objects["LIB_sedan"].children:
    n = "CAR_Wheel_" + w.name.split("wheel-")[1]   # CAR_Wheel_front-left ...
    if n in taken: continue
    k = w.copy(); k.name = n; k["cs_owner"] = "car"; COLL.objects.link(k); k.parent = car

def mat(name, color, metal=0.0, rough=0.6, alpha=1.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough; b.inputs["Alpha"].default_value = alpha
    m.diffuse_color = (*color, alpha)
    if alpha < 1: m.surface_render_method = "BLENDED"; m.use_transparency_overlap = False
    return m

GLASS = mat("MAT_CarGlass", (0.75, 0.85, 0.95), rough=0.05, alpha=0.04)
SEAT = mat("MAT_CarSeat", (0.09, 0.08, 0.08), rough=0.8)
DASH = mat("MAT_CarDash", (0.05, 0.05, 0.055), rough=0.5)
FLOOR = mat("MAT_CarFloor", (0.04, 0.04, 0.04), rough=0.9)
MIRROR = mat("MAT_Mirror", (0.9, 0.9, 0.9), metal=1.0, rough=0.0)

# 1) Own (single-user) body mesh with the window faces on a glass material slot.
if car.data.users > 1 or car.data.name != "CAR_Body":
    car.data = car.data.copy(); car.data.name = "CAR_Body"
me = car.data
if len(me.materials) < 2: me.materials.append(GLASS)
img = next(n for n in me.materials[0].node_tree.nodes if n.type == "TEX_IMAGE").image
px, (W, H), uvs = img.pixels[:], img.size, me.uv_layers.active.data
for p in me.polygons:   # window faces are the pale blue-white texels of the Kenney colormap
    u = sum(uvs[i].uv.x for i in p.loop_indices) / p.loop_total
    v = sum(uvs[i].uv.y for i in p.loop_indices) / p.loop_total
    i = (min(H - 1, int(v * H)) * W + min(W - 1, int(u * W))) * 4
    p.material_index = 1 if (px[i] > 0.85 and px[i + 1] > 0.93 and px[i + 2] > 0.98) else 0

# 2) Simple interior parts (boxes), parented to the car.
def box(name, center, size, m, tilt=0.0, parent=car):
    """Box with its origin at the bottom centre (sensible pivot for seat backs)."""
    if name in taken: return bpy.data.objects[name]
    sx, sy, sz = (s / 2 for s in size)
    vs = [(x, y, z) for x in (-sx, sx) for y in (-sy, sy) for z in (0, 2 * sz)]
    fs = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    mesh = bpy.data.meshes.new(name); mesh.from_pydata(vs, [], fs); mesh.materials.append(m)
    o = bpy.data.objects.new(name, mesh); o["cs_owner"] = "car"; COLL.objects.link(o)
    o.parent = parent; o.location = center; o.rotation_euler.x = math.radians(tilt)
    return o

FLOOR_Z = 0.55
box("CAR_Int_Floor", (0, 0.1, FLOOR_Z - 0.02), (1.9, 2.5, 0.02), FLOOR)
box("CAR_Dashboard", (0, -0.95, 1.05), (1.95, 0.45, 0.38), DASH)
for side, x in (("L", 0.48), ("R", -0.48)):   # front seats; L = driver (Claude)
    base = box(f"CAR_Seat_F{side}", (x, -0.15, FLOOR_Z), (0.55, 0.55, 0.38), SEAT)
    back = box(f"CAR_Seat_F{side}_Back", (0, 0.27, 0.38), (0.55, 0.12, 0.6), SEAT, tilt=-12, parent=base)
    box(f"CAR_Seat_F{side}_Headrest", (0, 0.0, 0.62), (0.3, 0.1, 0.18), SEAT, parent=back)
rear = box("CAR_Seat_Rear", (0, 0.85, FLOOR_Z), (1.8, 0.5, 0.36), SEAT)
box("CAR_Seat_Rear_Back", (0, 0.24, 0.36), (1.8, 0.12, 0.62), SEAT, tilt=-15, parent=rear)

# Steering wheel (driver side) on a short column out of the dash; origin = wheel centre.
if "CAR_SteeringWheel" not in taken:
    bpy.ops.mesh.primitive_torus_add(major_radius=0.19, minor_radius=0.025, major_segments=20, minor_segments=6)
    sw = bpy.context.active_object; sw.name = sw.data.name = "CAR_SteeringWheel"; sw["cs_owner"] = "car"
    for c in sw.users_collection: c.objects.unlink(sw)
    COLL.objects.link(sw); sw.data.materials.append(DASH)
    sw.parent = car; sw.location = (0.48, -0.55, 1.28); sw.rotation_euler = (math.radians(-70), 0, 0)
    box("CAR_SteeringColumn", (0, 0, -0.02), (0.06, 0.06, 0.32), DASH, tilt=180, parent=sw)

# Rear-view mirror at the top centre of the windshield; the mirror face points back (+Y).
# Its exact angle is tuned in milestone 6 so both camera shots see a face in it.
# Lower, further forward, a bit toward the driver and larger than real (0.36 m): in this short cabin a
# roof-height mirror only sees the top of Claude's head. Aimed by build_cameras.py.
mb = box("CAR_RearViewMirror", (0.15, -0.62, 1.66), (0.36, 0.04, 0.11), DASH)
gl = box("CAR_RearViewMirror_Glass", (0, 0.021, 0.008), (0.34, 0.002, 0.094), MIRROR, parent=mb)
st = box("CAR_RearViewMirror_Stem", (0, -0.0, 0.11), (0.02, 0.02, 0.25), DASH, parent=mb)
for o in (mb, gl, st): o.hide_probe_plane = True   # else the mirror probe captures the mirror's own back
bpy.data.orphans_purge(do_recursive=True)
result = sorted(o.name for o in car.children_recursive)
