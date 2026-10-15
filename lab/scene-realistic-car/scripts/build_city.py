# City: a closed rounded-rectangle ring street (the car can lap forever), game-style realistic.
# Re-runnable: deletes only objects with cs_owner "city" that the creator has not marked user_locked; meshes and
# materials it owns are rebuilt in place. Fixed seed -> the same city every run.
# Ring centreline: x -172..188, y 0..216 (360 x 216 m), corner radius R=16. Street cross-section (creator's
# choice A): 13 m curb to curb = parking 2.5 | lane 4 | lane 4 | parking 2.5, 0.15 m curbs, 4 m sidewalks.
# The car drives counter-clockwise in the right lane = the outer lane, 2 m outside the centreline (lane radius 18).
# Pickup on the south straight: car stop (5,-2) heading +X, 167 m before the first corner; exit door (1.5,-10.5).
# Edge k runs from corner k to k+1 (0 south, 1 east, 2 north, 3 west); s = distance along it, off = lateral offset
# (+ = outward / the outer side). Every model built here faces +Y (its front) like the stylised scene's kit.
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

OWN = "city"
for o in [o for o in bpy.data.objects if o.get("cs_owner") == OWN and not o.get("user_locked")]:
    bpy.data.objects.remove(o)
taken = {o.name for o in bpy.data.objects}
CITY, LIBC = bpy.data.collections["01_CITY"], bpy.data.collections["00_LIB"]
rng = random.Random(7)
A = bpy.path.abspath("//assets/")

X0, X1, Y0, Y1, R = -172, 188, 0, 216, 16
HALF, WALK, CURB, LANE = 6.5, 4.0, 0.15, 2.0
FRONT = HALF + WALK            # building frontage line (10.5 m from the centreline)
DEPTH = 18                     # building depth
CORNERS = [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)]
CX, CY = (X0 + X1) / 2, (Y0 + Y1) / 2
PICKUP = Vector((5, Y0 - LANE)); EXIT_DOOR = Vector((1.5, Y0 - FRONT))

def edge(k):
    a, b = Vector(CORNERS[k]), Vector(CORNERS[(k + 1) % 4])
    t = (b - a).normalized(); return a, b, t, Vector((t.y, -t.x)), (b - a).length
def at(k, s, off, z=0.0):
    a, b, t, n, L = edge(k); p = a + t * s + n * off; return Vector((p.x, p.y, z))
yaw = lambda f: math.atan2(-f.x, f.y)                       # rotation turning a +Y-facing model to face f

# ---------------------------------------------------------------------------------------------- materials
def mat(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bs.outputs[0], out.inputs[0]); return m, nt, bs

def img(path, non_color=False):
    i = bpy.data.images.load(path, check_existing=True)
    if non_color: i.colorspace_settings.name = "Non-Color"
    return i

def pbr(name, maps, size_m, box=False, tint=None, z0=0.0, rough_mul=1.0):
    """Image PBR on object coordinates in metres (no UVs needed; linked duplicates keep the scale).
    maps: dict color/normal/rough -> file. box: box projection (walls); z0 shifts the texture vertically."""
    m, nt, bs = mat(name)
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Location"].default_value = (0, 0, -z0 / size_m)
    mp.inputs["Scale"].default_value = (1 / size_m,) * 3
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    def tex(key, nc):
        n = nt.nodes.new("ShaderNodeTexImage"); n.image = img(maps[key], nc)
        if box: n.projection = "BOX"; n.projection_blend = 0.1
        nt.links.new(mp.outputs[0], n.inputs[0]); return n
    c = tex("color", False)
    if tint:
        mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1; mix.inputs["B"].default_value = (*tint, 1)
        nt.links.new(c.outputs[0], mix.inputs["A"]); nt.links.new(mix.outputs["Result"], bs.inputs["Base Color"])
    else: nt.links.new(c.outputs[0], bs.inputs["Base Color"])
    if "rough" in maps:
        r = tex("rough", True); mth = nt.nodes.new("ShaderNodeMath"); mth.operation = "MULTIPLY"
        mth.inputs[1].default_value = rough_mul; nt.links.new(r.outputs[0], mth.inputs[0])
        nt.links.new(mth.outputs[0], bs.inputs["Roughness"])
    if "normal" in maps:
        nn = tex("normal", True); nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(nn.outputs[0], nm.inputs["Color"]); nt.links.new(nm.outputs[0], bs.inputs["Normal"])
    m.diffuse_color = (*(tint or (0.5, 0.5, 0.5)), 1)
    return m

def flat(name, color, rough=0.5, metal=0.0, emit=None, strength=0.0):
    m, nt, bs = mat(name)
    bs.inputs["Base Color"].default_value = (*color, 1); bs.inputs["Roughness"].default_value = rough
    bs.inputs["Metallic"].default_value = metal
    if emit: bs.inputs["Emission Color"].default_value = (*emit, 1); bs.inputs["Emission Strength"].default_value = strength
    m.diffuse_color = (*color, 1); return m

PH, AC = A + "polyhaven/textures/", A + "ambientcg/"
phm = lambda a, r: {"color": f"{PH}{a}/{a}_diff_{r}.jpg", "normal": f"{PH}{a}/{a}_nor_gl_{r}.jpg", "rough": f"{PH}{a}/{a}_rough_{r}.jpg"}
acm = lambda a, r: {"color": f"{AC}{a}/{a}_{r}-JPG_Color.jpg", "normal": f"{AC}{a}/{a}_{r}-JPG_NormalGL.jpg", "rough": f"{AC}{a}/{a}_{r}-JPG_Roughness.jpg"}
M = {
    "road": pbr("MAT_Asphalt", phm("asphalt_02", "1k"), 5.0, tint=(0.75, 0.75, 0.78)),
    "walk": pbr("MAT_Sidewalk", phm("concrete_pavement", "1k"), 1.8),
    "curb": pbr("MAT_Curb", phm("brushed_concrete", "1k"), 1.5, box=True),
    "plaza": pbr("MAT_Plaza", phm("brushed_concrete", "1k"), 2.5),
    "paint": flat("MAT_RoadPaint", (0.85, 0.85, 0.82), 0.6),
    "paint_y": flat("MAT_RoadPaintYellow", (0.85, 0.62, 0.08), 0.6),
    # facades: texture tile = whole number of 3.5 m floors, starting above the 4.8 m shop band
    "glass_tower": pbr("MAT_Facade_Glass", acm("Facade001", "1K"), 35.0, box=True, z0=4.8, rough_mul=0.5),
    "office": pbr("MAT_Facade_Office", acm("Facade006", "1K"), 28.0, box=True, z0=4.8),
    "concrete_lit": pbr("MAT_Facade_Concrete", acm("Facade017", "1K"), 42.0, box=True, z0=4.8),
    "brick": pbr("MAT_Facade_Brick", acm("Facade020A", "1K"), 21.0, box=True, z0=4.8),
    "render": pbr("MAT_Facade_WhiteRender", phm("beige_wall_001", "1k"), 2.5, box=True, tint=(1.2, 1.3, 1.45)),
    "shopglass": flat("MAT_ShopGlass", (0.04, 0.05, 0.06), 0.08, 0.0),
    "frame": flat("MAT_DarkMetal", (0.05, 0.05, 0.055), 0.35, 0.8),
    "fascia": flat("MAT_Fascia", (0.12, 0.12, 0.13), 0.5),
    "roof": flat("MAT_Roof", (0.32, 0.31, 0.3), 0.85),
    "wood": flat("MAT_WoodSlat", (0.26, 0.14, 0.07), 0.55),
    "pole": flat("MAT_PolePaint", (0.16, 0.17, 0.18), 0.4, 0.6),
    "lamp": flat("MAT_LampLED", (0.9, 0.9, 0.85), 0.3, emit=(1.0, 0.82, 0.6), strength=0.0),   # lit in build_lighting
    "sig_r": flat("MAT_SignalRed", (0.25, 0.02, 0.02), 0.2, emit=(1, 0.05, 0.02), strength=0.0),
    "sig_a": flat("MAT_SignalAmber", (0.25, 0.15, 0.02), 0.2, emit=(1, 0.55, 0.05), strength=0.0),
    "sig_g": flat("MAT_SignalGreen", (0.02, 0.2, 0.08), 0.2, emit=(0.1, 1, 0.45), strength=0.0),
    "trunk": flat("MAT_TreeTrunk", (0.17, 0.12, 0.08), 0.85),
    "ground": flat("MAT_Ground", (0.22, 0.22, 0.21), 0.9),
}
# White render with ribbon windows: a z-periodic mask mixes glass into the plaster (works on every side).
def ribbon(name, base):
    m = base.copy(); m.name = name; nt = m.node_tree; bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    gl = nt.nodes.new("ShaderNodeBsdfPrincipled"); gl.inputs["Base Color"].default_value = (0.03, 0.04, 0.05, 1)
    gl.inputs["Roughness"].default_value = 0.06; gl.inputs["Metallic"].default_value = 0.2
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    fl = nt.nodes.new("ShaderNodeMath"); fl.operation = "WRAP"; fl.inputs[1].default_value = 4.8; fl.inputs[2].default_value = 8.3
    nt.links.new(sep.outputs["Z"], fl.inputs[0])            # z wrapped into one 3.5 m floor starting at 4.8
    lo = nt.nodes.new("ShaderNodeMath"); lo.operation = "GREATER_THAN"; lo.inputs[1].default_value = 5.75
    hi = nt.nodes.new("ShaderNodeMath"); hi.operation = "LESS_THAN"; hi.inputs[1].default_value = 7.75
    nt.links.new(fl.outputs[0], lo.inputs[0]); nt.links.new(fl.outputs[0], hi.inputs[0])
    mk = nt.nodes.new("ShaderNodeMath"); mk.operation = "MULTIPLY"
    nt.links.new(lo.outputs[0], mk.inputs[0]); nt.links.new(hi.outputs[0], mk.inputs[1])
    hz = nt.nodes.new("ShaderNodeMath"); hz.operation = "GREATER_THAN"; hz.inputs[1].default_value = 4.9
    nt.links.new(sep.outputs["Z"], hz.inputs[0])
    mk2 = nt.nodes.new("ShaderNodeMath"); mk2.operation = "MULTIPLY"
    nt.links.new(mk.outputs[0], mk2.inputs[0]); nt.links.new(hz.outputs[0], mk2.inputs[1])
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mk2.outputs[0], mix.inputs[0]); nt.links.new(bs.outputs[0], mix.inputs[1]); nt.links.new(gl.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0]); return m
M["white"] = ribbon("MAT_Facade_WhiteRibbon", M["render"])

# ---------------------------------------------------------------------------------------------- mesh helpers
def own_mesh(name, verts, faces, mats, mat_idx=None):
    me = bpy.data.meshes.get(name)
    if me: me.clear_geometry(); me.materials.clear()
    else: me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    for m in mats: me.materials.append(m)
    if mat_idx: me.polygons.foreach_set("material_index", mat_idx)
    me.validate(); me.update(); return me

def obj(name, me, loc=(0, 0, 0), rz=0.0, shadow=True, coll=CITY):
    if name in taken: return None
    o = bpy.data.objects.new(name, me); o["cs_owner"] = OWN; coll.objects.link(o)
    o.location = loc; o.rotation_euler.z = rz; o.visible_shadow = shadow; return o

class MB:   # tiny mesh builder: boxes / cylinders with a material index each
    def __init__(s): s.v, s.f, s.mi = [], [], []
    def box(s, x0, x1, y0, y1, z0, z1, m, top=True, bottom=False):
        b = len(s.v)
        s.v += [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        fs = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)] + ([(4, 5, 6, 7)] if top else []) + ([(3, 2, 1, 0)] if bottom else [])
        s.f += [tuple(b + i for i in q) for q in fs]; s.mi += [m] * len(fs)
    def cyl(s, x, y, z0, z1, r0, r1, m, seg=10, cap=True):
        b = len(s.v)
        for z, r in ((z0, r0), (z1, r1)):
            s.v += [(x + r * math.cos(2 * math.pi * i / seg), y + r * math.sin(2 * math.pi * i / seg), z) for i in range(seg)]
        s.f += [(b + i, b + (i + 1) % seg, b + seg + (i + 1) % seg, b + seg + i) for i in range(seg)]; s.mi += [m] * seg
        if cap: s.f.append(tuple(b + seg + i for i in range(seg))); s.mi.append(m)
    def mesh(s, name, mats): return own_mesh(name, s.v, s.f, mats, s.mi)

def bevel(me, w=0.03):   # soft game-style edges on owned meshes (applied once, not a modifier)
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=w, segments=1, affect="EDGES", clamp_overlap=True)
    bm.to_mesh(me); bm.free()

# ---------------------------------------------------------------------------------------------- ring sampler
def loop(off, step=4.0, adeg=3):
    """Closed loop at lateral offset `off`: list of (point, tangent). Same parametrisation for any offset."""
    pts = []
    for k in range(4):
        a, b, t, n, L = edge(k); tc = b - t * R - n * R
        m = max(1, round((L - 2 * R) / step))
        pts += [(a + t * (R + (L - 2 * R) * i / m) + n * off, t) for i in range(m)]
        for d in range(0, 90, adeg):
            r = math.radians(d); dirv = n * math.cos(r) + t * math.sin(r)
            pts.append((tc + dirv * (R + off), (t * math.cos(r) - n * math.sin(r)).normalized()))
    return pts

def band(name, o0, o1, z0, z1, m, wall=None):
    """Ring band between offsets o0<o1 at height z1 (top), optional curb wall at offset `wall` from z0 to z1."""
    p0, p1 = loop(o0), loop(o1); N = len(p0); v, f = [], []
    for (a, _), (b, _) in zip(p0, p1): v += [(a.x, a.y, z1), (b.x, b.y, z1)]
    f += [(2 * i + 1, 2 * ((i + 1) % N) + 1, 2 * ((i + 1) % N), 2 * i) for i in range(N)]   # normals +Z
    if wall is not None:
        pw = loop(wall); b0 = len(v); sgn = 1 if wall == o0 else -1
        for p, _ in pw: v += [(p.x, p.y, z0), (p.x, p.y, z1)]
        for i in range(N):
            q = (b0 + 2 * i, b0 + 2 * ((i + 1) % N), b0 + 2 * ((i + 1) % N) + 1, b0 + 2 * i + 1)
            f.append(q if sgn > 0 else q[::-1])
    return obj(name, own_mesh(name, v, f, [m]))

band("CITY_Road", -HALF, HALF, 0, 0.0, M["road"])
band("CITY_Sidewalk_Outer", HALF, FRONT, 0, CURB, M["walk"], wall=HALF)
band("CITY_Sidewalk_Inner", -FRONT, -HALF, 0, CURB, M["walk"], wall=-HALF)
band("CITY_Apron_Outer", FRONT, FRONT + 60, 0, CURB, M["plaza"])          # ground behind the outer frontage
# Inner block floor: the polygon inside the inner frontage line.
ip = loop(-FRONT); obj("CITY_InnerBlock", own_mesh("CITY_InnerBlock", [(p.x, p.y, CURB) for p, _ in ip], [tuple(range(len(ip)))], [M["plaza"]]))
G = 900
obj("CITY_Ground", own_mesh("CITY_Ground", [(CX - G, CY - G, -0.05), (CX + G, CY - G, -0.05), (CX + G, CY + G, -0.05), (CX - G, CY + G, -0.05)],
                            [(0, 1, 2, 3)], [M["ground"]]), shadow=False)

# ---------------------------------------------------------------------------------------------- road markings
CROSS = [(0, 92), (0, 262), (1, 108), (2, 120), (2, 250), (3, 96)]   # signalised mid-block crosswalks (edge, s)
def near_cross(k, s, d): return any(k == ck and abs(s - cs) < d for ck, cs in CROSS)
mk = MB()
def strip(k, s0, s1, off, w, m):
    a, b, t, n, L = edge(k); p0 = a + t * s0 + n * (off - w / 2); p1 = a + t * s1 + n * (off - w / 2)
    q0, q1 = p0 + n * w, p1 + n * w; i = len(mk.v); z = 0.015
    mk.v += [(q0.x, q0.y, z), (q1.x, q1.y, z), (p1.x, p1.y, z), (p0.x, p0.y, z)]; mk.f.append((i, i + 1, i + 2, i + 3)); mk.mi.append(m)
for k in range(4):
    a, b, t, n, L = edge(k)
    s = R + 2
    while s + 3 < L - R:                                  # dashed centre line: 3 m dash, 6 m gap
        if not near_cross(k, s, 6): strip(k, s, s + 3, 0, 0.14, 0)
        s += 9
    for off in (-4.0, 4.0):                               # parking-lane edge lines (solid), broken at crosswalks
        segs = [R + 2]
        for ck, cs in sorted(CROSS):
            if ck == k: segs += [cs - 5, cs + 5]
        segs.append(L - R - 2)
        for s0, s1 in zip(segs[::2], segs[1::2]): strip(k, s0, s1, off, 0.12, 0)
    for ck, cs in CROSS:                                  # zebra bars (parallel to traffic) + stop lines
        if ck != k: continue
        o = -HALF + 0.4
        while o < HALF - 0.4: strip(k, cs - 1.6, cs + 1.6, o + 0.25, 0.5, 0); o += 1.0
        strip(k, cs - 3.0, cs - 2.7, -2.0, 4.0, 0); strip(k, cs + 2.7, cs + 3.0, 2.0, 4.0, 0)
obj("CITY_RoadMarkings", mk.mesh("CITY_RoadMarkings", [M["paint"]]), shadow=False)

# ---------------------------------------------------------------------------------------------- buildings
def building_mesh(name, w, h, kind):
    """w wide (x), DEPTH deep (y from -DEPTH to 0), front at y=0 facing +Y. Shop band 0..4.2 (recessed glass),
    fascia 4.2..4.8, body to h with the facade material, roof slab and a rooftop plant box."""
    b = MB(); hw = w / 2
    b.box(-hw + 0.3, hw - 0.3, -DEPTH + 0.3, -0.35, 0, 4.2, 1, top=False)          # shop glass, recessed
    for x in [-hw + 0.3 + i * (w - 0.6) / max(1, round((w - 0.6) / 4.5)) for i in range(round((w - 0.6) / 4.5) + 1)]:
        b.box(x - 0.08, x + 0.08, -0.45, -0.25, 0, 4.2, 2)                          # mullions
    b.box(-hw, hw, -DEPTH, 0, 4.2, 4.8, 3, bottom=True)                              # fascia
    b.box(-hw, hw, -DEPTH, 0, 4.8, h, 0)                                             # body
    b.box(-hw, hw, -DEPTH, 0, h, h + 0.6, 4)                                         # parapet/roof slab
    b.box(-hw * 0.4, hw * 0.2, -DEPTH * 0.7, -DEPTH * 0.3, h + 0.6, h + 2.6, 4)        # rooftop plant
    if kind == "white":                                                              # wood-slat accent
        for i in range(9): b.box(hw - 3.6 + i * 0.4, hw - 3.5 + i * 0.4, 0.0, 0.12, 4.8, h, 5)
    body = {"glass_tower": "glass_tower", "office": "office", "concrete": "concrete_lit", "brick": "brick", "white": "white"}[kind]
    me = b.mesh(name, [M[body], M["shopglass"], M["frame"], M["fascia"], M["roof"], M["wood"]])
    return me

VARIANTS = []   # (mesh, width)
for i, (kind, w, floors) in enumerate([("office", 18, 6), ("office", 24, 9), ("white", 16, 4), ("white", 22, 6),
                                       ("brick", 14, 5), ("brick", 20, 6), ("glass_tower", 24, 12), ("concrete", 20, 8),
                                       ("white", 26, 5), ("office", 14, 5)]):
    VARIANTS.append((building_mesh(f"CITY_BldgMesh_{i:02d}_{kind}", w, 4.8 + 3.5 * floors, kind), w))

CORNER_MESH = building_mesh("CITY_BldgMesh_Corner", DEPTH, 4.8 + 3.5 * 14, "glass_tower")

def row(k, side, s0, s1, tag, skip=()):
    """Buildings along edge k (side +1 outer, -1 inner) between s0..s1, fronts facing the road, flush ends."""
    picks, used = [], 0.0
    while True:
        me, w = rng.choice(VARIANTS)
        if used + w + 0.5 > s1 - s0: break
        picks.append((me, w)); used += w + 0.5
    if not picks: return
    gap = (s1 - s0 - sum(w for _, w in picks)) / len(picks); s = s0
    a, b, t, n, L = edge(k)
    for i, (me, w) in enumerate(picks):
        s += gap / 2 + w / 2
        if not any(lo <= s <= hi for lo, hi in skip):
            obj(f"CITY_Bldg_{tag}_{i:02d}", me, at(k, s, side * FRONT), yaw(-n * side))
        s += w / 2 + gap / 2

# The exit building: modern white with a glazed lobby; door centre at EXIT_DOOR (x=1.5).
eb = MB(); EW, EH = 24, 4.8 + 3.5 * 5
eb.box(-EW / 2, EW / 2, -DEPTH, 0, 4.8, EH, 0, bottom=True)
eb.box(-EW / 2, EW / 2, -DEPTH, 0, EH, EH + 0.6, 4)
eb.box(-EW / 2, -1.5, -DEPTH, -0.2, 0, 4.8, 0, top=False)                         # solid base left
eb.box(4.5, EW / 2, -DEPTH, -0.2, 0, 4.8, 0, top=False)                           # solid base right
eb.box(-1.5, 4.5, -DEPTH, -1.2, 0, 4.8, 1, top=False)                             # lobby glass (recessed 1.2 m)
for x in (-1.5, 0.3, 2.7, 4.5): eb.box(x - 0.07, x + 0.07, -1.25, -1.1, 0, 3.4, 2)   # door frames
eb.box(-1.5, 4.5, -1.25, -1.1, 3.3, 3.45, 2)                                      # transom
eb.box(-2.5, 5.5, -1.2, 2.2, 3.6, 3.8, 3, bottom=True)                            # canopy over the door
for i in range(11): eb.box(EW / 2 - 4.6 + i * 0.4, EW / 2 - 4.5 + i * 0.4, 0.0, 0.12, 4.8, EH, 5)
emesh = eb.mesh("CITY_ExitBuildingMesh", [M["white"], M["shopglass"], M["frame"], M["fascia"], M["roof"], M["wood"]])
obj("CITY_ExitBuilding", emesh, (0, Y0 - FRONT, 0))
door = obj("CITY_ExitDoor", None, (EXIT_DOOR.x, EXIT_DOOR.y - 1.15, CURB))
if door: door.empty_display_type = "SINGLE_ARROW"; door.rotation_euler.z = math.pi   # marker: walk direction -Y? (out = +Y)

for k in range(4):
    a, b, t, n, L = edge(k)
    if k == 0:
        row(k, 1, -FRONT, -X0 - EW / 2 - 0.5, "0Oa"); row(k, 1, -X0 + EW / 2 + 0.5, L + FRONT, "0Ob")
    else:
        row(k, 1, -FRONT, L + FRONT, f"{k}O")
    row(k, -1, R + FRONT + 2, L - R - FRONT - 2, f"{k}I")
    # outer corner lot (the DEPTH x DEPTH square diagonally behind both frontages): a glass tower
    obj(f"CITY_Bldg_Corner_{k}", CORNER_MESH, at(k, L + FRONT + DEPTH / 2, FRONT), yaw(-n))

# ---------------------------------------------------------------------------------------------- street furniture
def furniture_mesh(name, build, mats):
    b = MB(); build(b); return b.mesh(name, mats)
lampm = furniture_mesh("CITY_LampMesh", lambda b: (b.cyl(0, 0, 0, 8.0, 0.11, 0.07, 0), b.box(-0.04, 0.04, 0, 2.2, 7.85, 7.95, 0),
                                                    b.box(-0.18, 0.18, 1.6, 2.5, 7.75, 7.9, 0), b.box(-0.15, 0.15, 1.65, 2.45, 7.72, 7.75, 1)),
                       [M["pole"], M["lamp"]])
def signal(b):
    b.cyl(0, 0, 0, 3.4, 0.07, 0.06, 0)
    b.box(-0.17, 0.17, -0.12, 0.12, 2.4, 3.3, 0)                                   # head (faces +Y = traffic)
    for z, mi in ((3.1, 1), (2.85, 2), (2.6, 3)): b.box(-0.08, 0.08, 0.12, 0.15, z - 0.08, z + 0.08, mi)
sigm = furniture_mesh("CITY_SignalMesh", signal, [M["pole"], M["sig_r"], M["sig_a"], M["sig_g"]])
def tree_mesh(name, seed):
    r = random.Random(seed); b = MB(); b.cyl(0, 0, 0, 3.2, 0.16, 0.09, 0, seg=8)
    me = b.mesh(name, [M["trunk"]]); bm = bmesh.new(); bm.from_mesh(me)
    for i in range(7):   # leafy clumps (game-style canopy)
        rad = r.uniform(1.0, 1.6); c = Vector((r.uniform(-1.2, 1.2), r.uniform(-1.2, 1.2), r.uniform(3.6, 5.8)))
        ico = bmesh.ops.create_icosphere(bm, subdivisions=3, radius=rad, matrix=Matrix.Translation(c))
        for v in ico["verts"]: v.co += v.normal * r.uniform(-0.12, 0.12)
        for f in {f for v in ico["verts"] for f in v.link_faces}: f.material_index = 1
    for f in bm.faces: f.smooth = f.material_index == 1
    bm.to_mesh(me); bm.free()
    leaf, nt, bs = mat(f"MAT_TreeLeaf")
    if not any(n.type == "TEX_NOISE" for n in nt.nodes):
        ns = nt.nodes.new("ShaderNodeTexNoise"); ns.inputs["Scale"].default_value = 2.5
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = (0.05, 0.16, 0.04, 1); ramp.color_ramp.elements[1].color = (0.22, 0.38, 0.08, 1)
        nt.links.new(ns.outputs["Fac"], ramp.inputs[0]); nt.links.new(ramp.outputs[0], bs.inputs["Base Color"])
        bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.4
        n2 = nt.nodes.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 18
        nt.links.new(n2.outputs["Fac"], bump.inputs["Height"]); nt.links.new(bump.outputs[0], bs.inputs["Normal"])
        bs.inputs["Roughness"].default_value = 0.75; leaf.diffuse_color = (0.12, 0.28, 0.06, 1)
    me.materials.append(leaf); return me
TREES = [tree_mesh(f"CITY_TreeMesh_{i}", 10 + i) for i in range(3)]

def lib_put(src, name, loc, rz):
    if name in taken: return
    o = bpy.data.objects[src].copy(); o.name = name; o["cs_owner"] = OWN; CITY.objects.link(o)
    o.location = loc; o.rotation_mode = "XYZ"; o.rotation_euler = (0, 0, rz)

PICKUP_ZONE = (-8.0, 14.0)    # south outer sidewalk, x range kept clear around the exit door and the car stop
def clear(k, side, s):
    if near_cross(k, s, 5): return False
    if k == 0 and side == 1 and PICKUP_ZONE[0] < s + X0 < PICKUP_ZONE[1]: return False
    return True

for k in range(4):
    a, b, t, n, L = edge(k)
    for side, tag in ((1, "O"), (-1, "I")):
        ph = 0 if side == 1 else 15
        for i, s in enumerate(range(int(R + 6 + ph), int(L - R - 4), 30)):   # lamps every 30 m, staggered
            if clear(k, side, s): obj(f"CITY_Lamp_{k}{tag}_{i:02d}", lampm, at(k, s, side * (HALF + 0.5), CURB), yaw(-n * side))
        for i, s in enumerate(range(int(R + 13), int(L - R - 4), 15)):        # trees between the lamps
            if clear(k, side, s) and (s - R - 6 - ph) % 30 > 4:
                obj(f"CITY_Tree_{k}{tag}_{i:02d}", rng.choice(TREES), at(k, s, side * (HALF + 1.4), CURB), rng.uniform(0, 6.28))
        for i, s in enumerate(range(int(R + 24), int(L - R - 10), 60)):       # benches / bins / boxes / hydrants
            if not clear(k, side, s): continue
            p = at(k, s, side * (FRONT - 0.7), CURB); f = -n * side
            lib_put("LIB_Bench", f"CITY_Bench_{k}{tag}_{i:02d}", p, yaw(f) + math.pi)
            if clear(k, side, s + 2.6): lib_put("LIB_TrashCan", f"CITY_Bin_{k}{tag}_{i:02d}", at(k, s + 2.6, side * (FRONT - 0.6), CURB), 0)
            if not clear(k, side, s + 9): continue
            if i % 2: lib_put("LIB_Hydrant", f"CITY_Hydrant_{k}{tag}_{i:02d}", at(k, s + 9, side * (HALF + 0.6), CURB), yaw(f))
            else: lib_put("LIB_UtilityBox", f"CITY_UtilBox_{k}{tag}_{i:02d}", at(k, s + 9, side * (FRONT - 0.5), CURB), yaw(f) + math.pi)
        for i, s in enumerate(range(int(R + 40), int(L - R), 70)):            # manholes in the lanes
            lib_put("LIB_Manhole", f"CITY_Manhole_{k}{tag}_{i:02d}", at(k, s, side * 2.0, -0.05), 0)
    for j, (ck, cs) in enumerate(CROSS):                                       # signals at both curbs, facing traffic
        if ck != k: continue
        obj(f"CITY_Signal_{k}_{j}O", sigm, at(k, cs - 3.5, HALF + 0.4, CURB), yaw(-t))
        obj(f"CITY_Signal_{k}_{j}I", sigm, at(k, cs + 3.5, -HALF - 0.4, CURB), yaw(t))
# a hydrant at the pickup curb for the opening shot
lib_put("LIB_Hydrant", "CITY_Hydrant_Pickup", (-6.5, Y0 - HALF - 0.6, CURB), 0)

# ---------------------------------------------------------------------------------------------- background
BGV = []
for i, (w, d, h, m) in enumerate([(30, 24, 40, "office"), (24, 24, 62, "glass_tower"), (36, 20, 28, "brick"),
                                  (28, 28, 50, "concrete_lit"), (22, 22, 34, "white"), (40, 30, 84, "glass_tower")]):
    b = MB(); b.box(-w / 2, w / 2, -d, 0, 0, h, 0); b.box(-w / 2, w / 2, -d, 0, h, h + 0.8, 1)
    BGV.append((b.mesh(f"CITY_BGMesh_{i}", [M[m], M["roof"]]), w))
for k in range(4):
    a, b, t, n, L = edge(k)
    s = -FRONT - 40
    while s < L + 40:                                     # second ring behind the outer rows
        me, w = rng.choice(BGV); s += w / 2
        obj(f"CITY_BG_{k}_{int(s + 100):04d}", me, at(k, s, FRONT + DEPTH + 8 + rng.uniform(0, 12)), yaw(-n), shadow=False)
        s += w / 2 + rng.uniform(2, 8)
    s = -180
    while s < L + 180:                                    # far skyline
        me, w = rng.choice(BGV); s += w / 2
        o = obj(f"CITY_BGFar_{k}_{int(s + 200):04d}", me, at(k, s, 110 + rng.uniform(0, 70)), yaw(-n), shadow=False)
        s += w / 2 + rng.uniform(4, 20)
# inner block: mid-rise boxes on a grid around a small park
for i, x in enumerate(range(X0 + R + 52, X1 - R - 40, 34)):
    for j, y in enumerate(range(int(Y0 + FRONT + DEPTH + 20), int(Y1 - FRONT - DEPTH - 10), 34)):
        if abs(x - CX) < 50 and abs(y - CY) < 30:
            if (i + j) % 2 == 0: obj(f"CITY_Tree_Park_{i:02d}_{j:02d}", rng.choice(TREES), (x, y, CURB), rng.uniform(0, 6.28))
            continue
        me, w = rng.choice(BGV)
        obj(f"CITY_BG_In_{i:02d}_{j:02d}", me, (x, y, 0), rng.randrange(4) * math.pi / 2, shadow=False)

# ---------------------------------------------------------------------------------------------- drive path
# Closed poly curve along the right lane starting at the pickup stop; corners are 1-degree arcs (radius R+LANE).
pts = [PICKUP]
for k in range(4):
    a, b, t, n, L = edge(k); tc = b - t * R - n * R
    pts += [tc + (n * math.cos(math.radians(d)) + t * math.sin(math.radians(d))) * (R + LANE) for d in range(91)]
dense = []
for p0, p1 in zip(pts, pts[1:] + pts[:1]):
    m = max(1, math.ceil((p1 - p0).length / 8)); dense += [p0.lerp(p1, i / m) for i in range(m)]
path = bpy.data.objects.get("CITY_DrivePath")
if path and not path.get("user_locked"):
    cu = path.data; bpy.data.objects.remove(path); bpy.data.curves.remove(cu); path = None
if not path:
    cu = bpy.data.curves.new("CITY_DrivePath", "CURVE"); cu.dimensions = "3D"; cu.use_path = True
    sp = cu.splines.new("POLY"); sp.points.add(len(dense) - 1); sp.use_cyclic_u = True
    for q, v in zip(sp.points, dense): q.co = (v.x, v.y, 0, 1)
    path = bpy.data.objects.new("CITY_DrivePath", cu); path["cs_owner"] = OWN; CITY.objects.link(path)
    path["length_m"] = sum((dense[i] - dense[i - 1]).length for i in range(len(dense)))

# Placeholder car until build_car.py exists (only created if missing; build_car replaces its mesh in place).
if not bpy.data.objects.get("CAR_Exterior"):
    b = MB(); b.box(-0.92, 0.92, -2.35, 2.35, 0.25, 0.85, 0)   # low slab: the eye-height test camera sees over it
    car = bpy.data.objects.new("CAR_Exterior", b.mesh("CAR_Placeholder", [flat("MAT_CarPlaceholder", (0.8, 0.1, 0.1))]))
    car["cs_owner"] = "car"; bpy.data.collections["02_CAR"].objects.link(car)
    car.location = (*PICKUP, 0); car.rotation_euler.z = math.radians(90)   # faces local -Y -> world +X

# Working cameras
def workcam(name, loc, rot, lens=24, ortho=None):
    c = bpy.data.objects.get(name)
    if not c:
        c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); bpy.data.collections["04_CAMERAS"].objects.link(c)
    c.location = loc; c.rotation_euler = rot; c.data.lens = lens; c.data.clip_end = 2000
    if ortho: c.data.type = "ORTHO"; c.data.ortho_scale = ortho
workcam("CAM_WORK_Top", (CX, CY, 400), (0, 0, 0), ortho=440)
workcam("CAM_WORK_Overview", (-30, -40, 22), (math.radians(68), 0, math.radians(-35)))
bpy.data.orphans_purge(do_recursive=True); bpy.context.view_layer.update()
city = [o for o in bpy.data.objects if o.get("cs_owner") == OWN]
result = {"objects": len(city), "path_m": round(path["length_m"], 1),
          "tris": sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in city if o.type == "MESH")}
