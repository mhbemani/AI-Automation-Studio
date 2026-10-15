# Claude's car, polygon diet (2026-10-09): BlenderKit "Low poly plymouth car" (Rohit Gupta, Royalty Free), imported once by
# import_assets.py as LIB_Hero_* (scaled 1.06, about 7.3K tris incl. wheels), recoloured to the creator's yellow (black
# vinyl roof kept), its window materials turned into glass, plus a light interior built here (<= 5K tris).
# Seating (creator): Claude drives in the LEFT front seat (local +X), the human sits in the RIGHT front seat (local -X).
# CAR_Exterior is the root (faces local -Y; keeps drive_car's Follow Path); its own mesh is empty, every part is a
# child in car-local coordinates. Re-runnable: rebuilds objects with cs_owner "car"/"parked" (not user_locked).
# Contract names kept: CAR_Wheel_front-left/-right, back-left/-right (pivot = wheel centre, axle = local X, rest
# rotation 0), CAR_SteeringWheel (rim in its local XY, tilt -70 deg about X, spin about Z), CAR_RearViewMirror
# (+_Glass, _Stem; a plain prop), CAR_Seat_FL/FR, CAR_Dashboard, CAR_Int_Floor.
# animate.py constants for this car: WHEEL_R 0.355, WHEELBASE 2.92 (printed in `result`).
# Parked cars: 5 linked duplicates of LIB_JDM (one mesh, smoothed by shading only) with per-object paint.
import bpy, bmesh, math
from mathutils import Vector, Matrix

car = bpy.data.objects["CAR_Exterior"]; car["cs_owner"] = "car"
for o in [o for o in bpy.data.objects if o.get("cs_owner") in ("car", "parked") and o is not car and not o.get("user_locked")]:
    bpy.data.objects.remove(o)
taken = {o.name for o in bpy.data.objects}
COLL = bpy.data.collections["02_CAR"]
FLOOR_Z = 0.27

# empty root mesh (the old placeholder / sedan body goes away)
old = car.data
car.data = bpy.data.meshes.get("CAR_Root") or bpy.data.meshes.new("CAR_Root")
if old is not car.data and old.users == 0: bpy.data.meshes.remove(old)

# ---------------------------------------------------------------------------------------------- materials
def mat(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bs.outputs[0], out.inputs[0]); return m, nt, bs, out
def flat(name, color, rough=0.5, metal=0.0, emit=None, strength=0.0):
    m, nt, bs, _ = mat(name)
    bs.inputs["Base Color"].default_value = (*color, 1); bs.inputs["Roughness"].default_value = rough
    bs.inputs["Metallic"].default_value = metal
    if emit: bs.inputs["Emission Color"].default_value = (*emit, 1); bs.inputs["Emission Strength"].default_value = strength
    m.diffuse_color = (*color, 1); return m
def glass(name, tint, alpha):
    m = flat(name, tint, rough=0.03); bs = m.node_tree.nodes["Principled BSDF"]
    bs.inputs["Alpha"].default_value = alpha
    m.surface_render_method = "BLENDED"; m.use_transparency_overlap = False; m.use_backface_culling = False
    m.diffuse_color = (*tint, alpha); return m
def leather(name, tint):
    m, nt, bs, _ = mat(name); p = bpy.path.abspath("//assets/polyhaven/textures/brown_leather/brown_leather_")
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (3, 3, 3)
    nt.links.new(tc.outputs["Object"], mp.inputs[0])
    def tex(f, nc):
        n = nt.nodes.new("ShaderNodeTexImage"); n.image = bpy.data.images.load(p + f, check_existing=True)
        if nc: n.image.colorspace_settings.name = "Non-Color"
        n.projection = "BOX"; n.projection_blend = 0.3; nt.links.new(mp.outputs[0], n.inputs[0]); return n
    c = tex("diff_1k.jpg", False); mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1; mix.inputs["B"].default_value = (*tint, 1)
    nt.links.new(c.outputs[0], mix.inputs["A"]); nt.links.new(mix.outputs["Result"], bs.inputs["Base Color"])
    r = tex("rough_1k.jpg", True); nt.links.new(r.outputs[0], bs.inputs["Roughness"])
    nn = tex("nor_gl_1k.jpg", True); nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 0.6
    nt.links.new(nn.outputs[0], nm.inputs["Color"]); nt.links.new(nm.outputs[0], bs.inputs["Normal"])
    m.diffuse_color = (0.55, 0.35, 0.2, 1); return m
M = {
    "trim": flat("MAT_CarTrim", (0.52, 0.46, 0.38), 0.85),
    "black": flat("MAT_CarBlackTrim", (0.02, 0.02, 0.022), 0.35),
    "seat": leather("MAT_CarLeather", (1.55, 1.2, 0.95)),
    "dash": flat("MAT_CarDash", (0.045, 0.045, 0.05), 0.6),
    "dash_top": flat("MAT_CarDashSoft", (0.09, 0.085, 0.08), 0.8),
    "carpet": flat("MAT_CarCarpet", (0.08, 0.075, 0.07), 0.95),
    "screen": flat("MAT_CarScreen", (0.02, 0.03, 0.05), 0.15, emit=(0.35, 0.6, 1.0), strength=0.6),
    "mirror": flat("MAT_Mirror", (0.9, 0.9, 0.9), 0.0, 1.0),
    "glass": glass("MAT_CarGlass", (0.5, 0.6, 0.62), 0.10),
}

# ---------------------------------------------------------------------------------------------- the hero car (from 00_LIB)
SRC_PARTS = [o for o in bpy.data.collections["00_LIB"].objects if o.name.startswith("LIB_Hero_")]
assert SRC_PARTS, "run import_assets.py first (LIB_Hero_* missing)"
wheels = {}
for src in SRC_PARTS:
    tail = src.name[len("LIB_Hero_"):]
    nm = "CAR_" + tail if tail.startswith("Wheel_") else "CAR_Ext_" + tail
    if nm in taken: continue
    o = src.copy(); o.name = nm; o["cs_owner"] = "car"; o["hero_part"] = True; COLL.objects.link(o)
    o.parent = car; o.matrix_parent_inverse = Matrix(); o.location = src.location; o.rotation_euler = (0, 0, 0)
    if tail.startswith("Wheel_"): wheels[nm] = src.location.copy()
roles = {sl.material["hero_role"]: sl.material for o in SRC_PARTS for sl in o.material_slots if sl.material and "hero_role" in sl.material}
paint = next(sl.material for o in SRC_PARTS for sl in o.material_slots if sl.material and sl.material.get("hero_role") == "paint")
pb = next(n for n in paint.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
pb.inputs["Base Color"].default_value = (0.87, 0.52, 0.03, 1)        # the creator's yellow
pb.inputs["Metallic"].default_value = 0.35; pb.inputs["Roughness"].default_value = 0.25
if "Coat Weight" in pb.inputs: pb.inputs["Coat Weight"].default_value = 0.6
for o in [o for o in car.children if o.get("hero_part")]:
    for sl in o.material_slots:
        if sl.material and sl.material.get("hero_role") == "glass": sl.material = M["glass"]
# inside of the shell: back faces of the paint and the black vinyl roof show a light beige headliner / door trim
for m in [roles.get("paint"), roles.get("roof")]:
    if not m or m.node_tree.nodes.get("CS_Backface"): continue
    nt = m.node_tree; out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output)
    shader = out.inputs["Surface"].links[0].from_socket
    tr = nt.nodes.new("ShaderNodeBsdfPrincipled"); tr.name = "CS_Trim"; tr.inputs["Base Color"].default_value = (0.62, 0.56, 0.47, 1)
    tr.inputs["Roughness"].default_value = 0.85
    geo = nt.nodes.new("ShaderNodeNewGeometry"); mix = nt.nodes.new("ShaderNodeMixShader"); mix.name = "CS_Backface"
    nt.links.new(geo.outputs["Backfacing"], mix.inputs[0]); nt.links.new(shader, mix.inputs[1])
    nt.links.new(tr.outputs[0], mix.inputs[2]); nt.links.new(mix.outputs[0], out.inputs["Surface"])

# ---------------------------------------------------------------------------------------------- interior
class MB:   # rounded boxes (bevelled) with one material each
    def __init__(s): s.bm = bmesh.new(); s.mats = []
    def box(s, x0, x1, y0, y1, z0, z1, m, bev=0.0, seg=2):
        if m not in s.mats: s.mats.append(m)
        r = bmesh.ops.create_cube(s.bm, size=1, matrix=Matrix.Translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)) @
                                  Matrix.Diagonal(((x1 - x0), (y1 - y0), (z1 - z0), 1)))
        if bev:
            es = list({e for v in r["verts"] for e in v.link_edges})
            bmesh.ops.bevel(s.bm, geom=es, offset=bev, segments=seg, affect="EDGES", clamp_overlap=True)
        for f in s.bm.faces:
            if not f.tag: f.material_index = s.mats.index(m); f.tag = True
    def obj(s, name, parent=car, loc=(0, 0, 0), soft=0):
        for f in s.bm.faces: f.tag = False; f.smooth = True
        me = bpy.data.meshes.new(name); s.bm.to_mesh(me); s.bm.free()
        for m in s.mats: me.materials.append(m)
        if not soft: me.set_sharp_from_angle(angle=math.radians(40))
        if name in taken: return bpy.data.objects[name]
        o = bpy.data.objects.new(name, me); o["cs_owner"] = "car"; COLL.objects.link(o)
        o.parent = parent; o.matrix_parent_inverse = Matrix(); o.location = loc
        if soft:   # padded look: subdivision over the bevelled boxes
            m = o.modifiers.new("Soft", "SUBSURF"); m.levels = soft; m.render_levels = soft
        return o

CAB_Y0, CAB_Y1, CAB_X = -0.95, 1.15, 0.90        # cabin (measured): windshield base .. rear bulkhead, inner half width
SEAT_TOP, SEAT_Y = 0.40, 0.28                      # cushion top / seat centre (roof inside is ~1.32)
# Interior diet (<= 5K tris): bevels with 1-2 segments, subdivision only on the seats (level 1).
f = MB(); f.box(-CAB_X, CAB_X, CAB_Y0, CAB_Y1, FLOOR_Z - 0.03, FLOOR_Z, M["carpet"]); f.obj("CAR_Int_Floor")
f = MB()
f.box(-CAB_X, CAB_X, 0.95, 1.18, FLOOR_Z, 0.80, M["trim"], 0.04, 1)                                   # rear bulkhead
for sx in (1, -1):
    f.box(*sorted((sx * (CAB_X - 0.07), sx * (CAB_X - 0.01))), CAB_Y0 + 0.25, 0.9, 0.50, 0.57, M["dash_top"], 0.02, 1)   # armrests
    f.box(*sorted((sx * (CAB_X - 0.02), sx * (CAB_X + 0.03))), CAB_Y0 + 0.1, 0.95, FLOOR_Z, 0.78, M["trim"])            # door cards
f.obj("CAR_Int_DoorCards")
dsh = MB()
dsh.box(-CAB_X, CAB_X, -1.00, -0.58, 0.45, 0.82, M["dash"], 0.05, 2)
dsh.box(-CAB_X, CAB_X, -1.02, -0.66, 0.80, 0.88, M["dash_top"], 0.03, 1)
dsh.box(0.22, 0.60, -0.70, -0.57, 0.78, 0.92, M["dash"], 0.03, 1)              # instrument binnacle (driver, +X)
dsh.box(-0.16, 0.16, -0.62, -0.57, 0.60, 0.78, M["screen"], 0.01, 1)          # centre screen
dsh.box(-0.13, 0.13, -0.60, 0.60, FLOOR_Z, 0.48, M["dash"], 0.03, 1)          # centre console
dsh.obj("CAR_Dashboard")

def seat(name, x, y):
    z0 = SEAT_TOP - FLOOR_Z
    s = MB(); s.box(-0.27, 0.27, -0.27, 0.25, 0, z0, M["seat"], 0.05, 2)
    s.box(-0.30, -0.22, -0.25, 0.22, 0.06, z0 + 0.05, M["seat"], 0.03, 1); s.box(0.22, 0.30, -0.25, 0.22, 0.06, z0 + 0.05, M["seat"], 0.03, 1)
    base = s.obj(name, loc=(x, y, FLOOR_Z), soft=1)
    b = MB(); b.box(-0.27, 0.27, -0.06, 0.08, 0, 0.60, M["seat"], 0.05, 2)
    b.box(-0.30, -0.21, -0.02, 0.10, 0.05, 0.52, M["seat"], 0.03, 1); b.box(0.21, 0.30, -0.02, 0.10, 0.05, 0.52, M["seat"], 0.03, 1)
    back = b.obj(name + "_Back", parent=base, loc=(0, 0.25, z0 - 0.03), soft=1); back.rotation_euler.x = math.radians(-18)
    h = MB(); h.box(-0.13, 0.13, -0.05, 0.07, 0, 0.18, M["seat"], 0.05, 2); h.obj(name + "_Headrest", parent=back, loc=(0, 0.0, 0.63), soft=1)
    return base
seat("CAR_Seat_FL", 0.42, SEAT_Y)        # driver: Claude
seat("CAR_Seat_FR", -0.42, SEAT_Y)       # passenger: the human

# steering wheel: rim in its local XY, tilted -70 deg about X (contract); origin = rim centre (24 x 6 rim: light)
if "CAR_SteeringWheel" not in taken:
    bm = bmesh.new(); seg, mseg, R0, r0 = 24, 6, 0.185, 0.018
    bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.05, radius2=0.05, depth=0.05)
    rings = []
    for i in range(seg):
        a = 2 * math.pi * i / seg; c = Vector((R0 * math.cos(a), R0 * math.sin(a), 0)); rd = Vector((math.cos(a), math.sin(a), 0))
        rings.append([bm.verts.new(c + (rd * math.cos(2 * math.pi * j / mseg) + Vector((0, 0, 1)) * math.sin(2 * math.pi * j / mseg)) * r0) for j in range(mseg)])
    for i in range(seg):
        A, B = rings[i], rings[(i + 1) % seg]
        for j in range(mseg): bm.faces.new((A[j], A[(j + 1) % mseg], B[(j + 1) % mseg], B[j]))
    for a in (0, math.pi, 1.5 * math.pi):
        bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Rotation(a, 4, "Z") @ Matrix.Translation((0.105, 0, 0)) @ Matrix.Diagonal((0.15, 0.035, 0.015, 1)))
    me = bpy.data.meshes.new("CAR_SteeringWheel"); bm.to_mesh(me); bm.free(); me.materials.append(M["black"])
    for p in me.polygons: p.use_smooth = True
    sw = bpy.data.objects.new("CAR_SteeringWheel", me); sw["cs_owner"] = "car"; COLL.objects.link(sw)
    sw.parent = car; sw.matrix_parent_inverse = Matrix(); sw.location = (0.42, -0.36, 0.80)
    sw.rotation_mode = "ZYX"; sw.rotation_euler = (math.radians(-70), 0, 0)
    c = MB(); c.box(-0.03, 0.03, -0.03, 0.03, -0.26, 0.0, M["black"]); c.obj("CAR_SteeringColumn", parent=sw)

# rear-view mirror: a plain prop at the top of the windshield
mb = MB(); mb.box(-0.13, 0.13, -0.025, 0.02, -0.04, 0.04, M["black"], 0.015, 1); mir = mb.obj("CAR_RearViewMirror", loc=(0.0, -0.46, 1.21))
g = MB(); g.box(-0.12, 0.12, 0.0, 0.002, -0.033, 0.033, M["mirror"]); g.obj("CAR_RearViewMirror_Glass", parent=mir, loc=(0, 0.021, 0))
st = MB(); st.box(-0.012, 0.012, -0.012, 0.012, 0.0, 0.08, M["black"]); st.obj("CAR_RearViewMirror_Stem", parent=mir, loc=(0, -0.01, 0.035))

# ---------------------------------------------------------------------------------------------- parked cars
# Diet: 5 linked duplicates of ONE mesh (LIB_JDM, 7.6K tris, smoothed by shading only in import_assets.py), each with an
# object-level paint override (a few material copies, no mesh copies).
jdm = bpy.data.objects["LIB_JDM"]
jpaint = next(sl.material for sl in jdm.material_slots if sl.material and sl.material.name.startswith("Paint"))
PSLOT = next(i for i, sl in enumerate(jdm.material_slots) if sl.material == jpaint)
PAL = [(0.8, 0.8, 0.78), (0.45, 0.05, 0.05), (0.04, 0.12, 0.3), (0.5, 0.52, 0.55), (0.05, 0.3, 0.33)]
for m in [m for m in bpy.data.materials if m.name.startswith("MAT_CarPaint_Parked")]: bpy.data.materials.remove(m)
PAINTS = []
for i, col in enumerate(PAL):
    m = jpaint.copy(); m.name = f"MAT_CarPaint_Parked{i}"
    for n in m.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED" and not n.inputs["Base Color"].is_linked: n.inputs["Base Color"].default_value = (*col, 1)
    PAINTS.append(m)
X0, X1, Y0, Y1 = -172, 188, 0, 216
CORN = [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)]
PARKED = [(0, 140, -1), (0, 100, 1), (1, 90, 1), (2, 150, -1), (3, 100, 1)]   # (edge, s, side): one is seen across the pickup street
city = bpy.data.collections["01_CITY"]
for i, (k, s_, side) in enumerate(PARKED):
    a, b = Vector(CORN[k]), Vector(CORN[(k + 1) % 4]); t = (b - a).normalized(); n = Vector((t.y, -t.x))
    p = a + t * s_ + n * side * 5.25; head = t if side == 1 else -t          # parked with the traffic of its lane
    nm = f"CITY_ParkedCar_{i:02d}"
    if nm in taken: continue
    o = bpy.data.objects.new(nm, jdm.data); o["cs_owner"] = "parked"; city.objects.link(o)
    o.location = (p.x, p.y, 0); o.rotation_euler.z = math.atan2(-head.x, head.y) + math.pi   # the JDM faces local -Y
    o.material_slots[PSLOT].link = "OBJECT"; o.material_slots[PSLOT].material = PAINTS[i]

bpy.data.orphans_purge(do_recursive=True)
def tris(o):
    dg = bpy.context.evaluated_depsgraph_get(); me = o.evaluated_get(dg).to_mesh(); n = sum(len(p.vertices) - 2 for p in me.polygons)
    o.evaluated_get(dg).to_mesh_clear(); return n
carparts = [o for o in car.children_recursive if o.type == "MESH" and not o.name.startswith(("CHAR_", "PROP_"))]
result = {"wheel_r": round(wheels["CAR_Wheel_front-left"].z, 3), "wheelbase": round(wheels["CAR_Wheel_back-left"].y - wheels["CAR_Wheel_front-left"].y, 3),
          "tris_exterior": sum(tris(o) for o in carparts if o.get("hero_part")), "tris_interior": sum(tris(o) for o in carparts if not o.get("hero_part"))}
