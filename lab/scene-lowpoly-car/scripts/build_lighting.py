# Golden-hour lighting + Eevee settings for the 8 GB M2. Run after build_car.py (it adds headlight
# material slots to CAR_Body). Re-runnable: rebuilds objects tagged cs_owner="light" and its own nodes.
import bpy, math
from mathutils import Vector

sc = bpy.context.scene
for o in [o for o in bpy.data.objects if o.get("cs_owner") == "light" and not o.get("user_locked")]:
    bpy.data.objects.remove(o)
taken = {o.name for o in bpy.data.objects}
LIGHTS = bpy.data.collections["05_LIGHTS"]
car = bpy.data.objects["CAR_Exterior"]

def light(name, kind, loc, energy, color, parent=None, rot=(0, 0, 0), size=0.25, shadow=True, coll=LIGHTS):
    if name in taken: return bpy.data.objects[name]
    d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = color; d.use_shadow = shadow
    if kind in ("POINT", "SPOT"): d.shadow_soft_size = size
    if kind == "AREA": d.size = size
    if kind == "SUN": d.angle = math.radians(size)
    o = bpy.data.objects.new(name, d); o["cs_owner"] = "light"; coll.objects.link(o)
    o.parent = parent; o.location = loc; o.rotation_euler = [math.radians(a) for a in rot]
    return o

def emissive(name, color, strength):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Emission Color"].default_value = (*color, 1); b.inputs["Emission Strength"].default_value = strength
    return m

WARM = (1.0, 0.62, 0.32)

# 1) World: the sunset HDRI lights the scene and shows in reflections; camera rays see a clean painted
#    gradient instead of the HDRI's photo of Venice (it showed through gaps in the skyline).
w = sc.world; nt = w.node_tree; N = nt.nodes
for n in [n for n in N if n.name.startswith("SKY_")]: N.remove(n)
out, bg, env = N["World Output"], N["Background"], N["HDRI"]
bg.inputs["Strength"].default_value = 0.4
def node(t, name, x, y):
    n = N.new(t); n.name = name; n.location = (x, y); return n
tc = node("ShaderNodeTexCoord", "SKY_Coord", -900, 400)
sep = node("ShaderNodeSeparateXYZ", "SKY_Sep", -700, 400)
ramp = node("ShaderNodeValToRGB", "SKY_Ramp", -500, 400)
r = ramp.color_ramp; r.elements[0].position = 0.0; r.elements[0].color = (1.0, 0.45, 0.2, 1)    # horizon
r.elements[1].position = 0.45; r.elements[1].color = (0.12, 0.16, 0.35, 1)                        # zenith
mid = r.elements.new(0.12); mid.color = (0.85, 0.42, 0.38, 1)
sky = node("ShaderNodeBackground", "SKY_Paint", -200, 400); sky.inputs["Strength"].default_value = 1.0
lp = node("ShaderNodeLightPath", "SKY_Path", -200, 650)
mix = node("ShaderNodeMixShader", "SKY_Mix", 100, 300)
L = nt.links
L.new(tc.outputs["Generated"], sep.inputs[0]); L.new(sep.outputs["Z"], ramp.inputs[0])
L.new(ramp.outputs["Color"], sky.inputs["Color"])
L.new(lp.outputs["Is Camera Ray"], mix.inputs[0]); L.new(bg.outputs[0], mix.inputs[1]); L.new(sky.outputs[0], mix.inputs[2])
L.new(mix.outputs[0], out.inputs["Surface"])

# 2) Low warm sun from the west (behind the car's arrival direction): long raking shadows down the street.
light("LIGHT_Sun", "SUN", (0, 0, 30), 5.0, (1.0, 0.55, 0.25), rot=(78, 0, -100), size=2.0)

# 3) Street lamps: a small emissive bulb mesh + a shadowless warm point light under each lamp head.
bulb_me = bpy.data.meshes.get("LIGHT_LampBulb")
if not bulb_me:
    bulb_me = bpy.data.meshes.new("LIGHT_LampBulb")
    bulb_me.from_pydata([(-.15, -.25, 0), (.15, -.25, 0), (.15, .25, 0), (-.15, .25, 0)], [], [(0, 1, 2, 3)])
    bulb_me.materials.append(emissive("MAT_LampBulb", (1.0, 0.75, 0.45), 12))
for lamp in [o for o in bpy.data.objects if o.name.startswith("CITY_StreetLight_")]:
    head = lamp.matrix_world @ Vector((0, 1.55, 5.08))   # under the end of the curved arm (lamp-local)
    tag = lamp.name[len("CITY_StreetLight_"):]
    light(f"LIGHT_Street_{tag}", "POINT", head - Vector((0, 0, 0.15)), 250, (1.0, 0.7, 0.4), size=0.3, shadow=False)
    if f"LIGHT_Bulb_{tag}" not in taken:
        b = bpy.data.objects.new(f"LIGHT_Bulb_{tag}", bulb_me); b["cs_owner"] = "light"; LIGHTS.objects.link(b)
        b.location = head - Vector((0, 0, 0.02)); b.rotation_euler = lamp.rotation_euler

# 4) Car: emissive head/tail lights (Kenney colormap texels: yellow front, red rear) + two headlight spots.
me = car.data
HEAD, TAIL = emissive("MAT_CarHeadlight", (1.0, 0.85, 0.55), 6), emissive("MAT_CarTaillight", (1.0, 0.08, 0.05), 4)
for m in (HEAD, TAIL):
    if m.name not in me.materials: me.materials.append(m)
ih, it = me.materials.find(HEAD.name), me.materials.find(TAIL.name)
img = next(n for n in me.materials[0].node_tree.nodes if n.type == "TEX_IMAGE").image
px, (W, H), uvs = img.pixels[:], img.size, me.uv_layers.active.data
for p in me.polygons:
    if p.material_index != 0: continue
    u = sum(uvs[i].uv.x for i in p.loop_indices) / p.loop_total
    v = sum(uvs[i].uv.y for i in p.loop_indices) / p.loop_total
    i = (min(H - 1, int(v * H)) * W + min(W - 1, int(u * W))) * 4
    rr, gg, bb = px[i:i + 3]
    if rr > 0.95 and gg > 0.75 and bb < 0.3 and p.center.y < -1.8: p.material_index = ih     # yellow, front
    elif rr > 0.8 and gg < 0.3 and bb < 0.3 and p.center.y > 2.1: p.material_index = it      # red, rear
for s, x in (("L", 0.62), ("R", -0.62)):
    light(f"LIGHT_CarHead_{s}", "SPOT", (x, -2.3, 1.15), 150, (1.0, 0.88, 0.7), parent=car, rot=(80, 0, 180), size=0.05)
    bpy.data.objects[f"LIGHT_CarHead_{s}"].data.spot_size = math.radians(55)

# 5) Interior: soft roof fill so both faces read, and a cool rim from the rear window onto the human/Claude.
light("LIGHT_CarFill", "AREA", (0, 0.1, 2.08), 18, (1.0, 0.85, 0.7), parent=car, size=0.9, shadow=False)
light("LIGHT_CarRim", "AREA", (0.0, 1.25, 1.95), 10, (0.6, 0.7, 1.0), parent=car, rot=(-60, 0, 0), size=0.5, shadow=False)
light("LIGHT_ClaudeFace", "POINT", (0.3, -0.75, 1.45), 6, (1.0, 0.8, 0.6), parent=car, size=0.2, shadow=False)

# 6) Lit windows: on the shared building materials, the blue window-glass texels emit warm light on a
#    random ~60% of buildings (Object Info random), so the city reads as early evening.
bmats = {m for o in bpy.data.collections["01_CITY"].objects if o.type == "MESH"
         and any(k in o.name for k in ("Bldg", "BG_", "Exit")) for m in o.data.materials if m}
for m in bmats:
    T = m.node_tree; NN = T.nodes
    for n in [n for n in NN if n.name.startswith("WIN_")]: NN.remove(n)
    tex = next(n for n in NN if n.type == "TEX_IMAGE"); bsdf = NN["Principled BSDF"]
    def mn(t, name, op=None, val=None):
        n = NN.new(t); n.name = name
        if op: n.operation = op
        if val is not None: n.inputs[1].default_value = val
        return n
    sepc = mn("ShaderNodeSeparateColor", "WIN_Sep")
    sub = mn("ShaderNodeMath", "WIN_BminusR", "SUBTRACT"); gt = mn("ShaderNodeMath", "WIN_IsGlass", "GREATER_THAN", 0.25)
    info = mn("ShaderNodeObjectInfo", "WIN_Info"); on = mn("ShaderNodeMath", "WIN_Lit", "GREATER_THAN", 0.4)
    mul = mn("ShaderNodeMath", "WIN_Mask", "MULTIPLY"); stren = mn("ShaderNodeMath", "WIN_Strength", "MULTIPLY", 3.0)
    T.links.new(tex.outputs["Color"], sepc.inputs[0])
    T.links.new(sepc.outputs["Blue"], sub.inputs[0]); T.links.new(sepc.outputs["Red"], sub.inputs[1])
    T.links.new(sub.outputs[0], gt.inputs[0]); T.links.new(info.outputs["Random"], on.inputs[0])
    T.links.new(gt.outputs[0], mul.inputs[0]); T.links.new(on.outputs[0], mul.inputs[1])
    T.links.new(mul.outputs[0], stren.inputs[0]); T.links.new(stren.outputs[0], bsdf.inputs["Emission Strength"])
    bsdf.inputs["Emission Color"].default_value = (1.0, 0.68, 0.35, 1)

# Windshield: almost no specular, else the bright interior reflects as a milky haze over the road.
bpy.data.materials["MAT_CarGlass"].node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.05

# 7) Eevee for the 8 GB M2: modest samples; ray tracing at full resolution (the mirror probe needs it,
#    and half resolution blurs the face in the mirror).
ee = sc.eevee
ee.taa_render_samples = 32; ee.taa_samples = 16
ee.use_raytracing = True; ee.ray_tracing_method = "SCREEN"; ee.ray_tracing_options.resolution_scale = "1"
ee.use_shadows = True; ee.shadow_ray_count = 1; ee.shadow_step_count = 4
ee.use_volumetric_shadows = False
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
bpy.data.orphans_purge(do_recursive=True)
result = (len([o for o in bpy.data.objects if o.get("cs_owner") == "light"]), len(bmats))
