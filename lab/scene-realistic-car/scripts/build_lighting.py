# Golden hour, look A (creator, 2026-10-09): warm and friendly, not dark; low bright sun, peachy sky, lamps just on.
# Run after build_city/build_car/build_characters/build_phone/build_cameras. Re-runnable: rebuilds objects tagged
# cs_owner="light" (not user_locked) and its own SKY_* world nodes; sets material strengths and Eevee settings.
import bpy, math
from mathutils import Vector

sc = bpy.context.scene
for o in [o for o in bpy.data.objects if o.get("cs_owner") == "light" and not o.get("user_locked")]:
    bpy.data.objects.remove(o)
taken = {o.name for o in bpy.data.objects}
LIGHTS = bpy.data.collections["05_LIGHTS"]
car = bpy.data.objects["CAR_Exterior"]
WARM = (1.0, 0.72, 0.45)

def light(name, kind, loc, energy, color, parent=None, aim=None, size=0.25, shadow=True, spot=None):
    if name in taken: return bpy.data.objects[name]
    d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = color; d.use_shadow = shadow
    if kind in ("POINT", "SPOT"): d.shadow_soft_size = size
    if kind == "AREA": d.size = size
    if kind == "SUN": d.angle = math.radians(size)
    if spot: d.spot_size = math.radians(spot); d.spot_blend = 0.4
    o = bpy.data.objects.new(name, d); o["cs_owner"] = "light"; LIGHTS.objects.link(o)
    o.parent = parent; o.location = loc
    if aim is not None: o.rotation_mode = "QUATERNION"; o.rotation_quaternion = Vector(aim).to_track_quat("-Z", "Y")
    return o

def emission(mat_name, strength, color=None):
    m = bpy.data.materials.get(mat_name)
    if not m: return
    for n in m.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED" and "Emission Strength" in n.inputs:
            n.inputs["Emission Strength"].default_value = strength
            if color: n.inputs["Emission Color"].default_value = (*color, 1)
        if n.type == "EMISSION":
            n.inputs[1].default_value = strength
            if color: n.inputs[0].default_value = (*color, 1)

# 1) World: the HDRI lights the scene and shows in reflections; camera rays see a painted golden-hour gradient
#    (the HDRI is a rooftop photo: its foreground would show through gaps in the skyline).
w = sc.world; nt = w.node_tree; N = nt.nodes
for n in [n for n in N if n.name.startswith("SKY_")]: N.remove(n)
out, bg = N["World Output"], N["Background"]
bg.inputs["Strength"].default_value = 0.55
def node(t, name, x, y):
    n = N.new(t); n.name = name; n.location = (x, y); return n
tc = node("ShaderNodeTexCoord", "SKY_Coord", -900, 400); sep = node("ShaderNodeSeparateXYZ", "SKY_Sep", -700, 400)
ramp = node("ShaderNodeValToRGB", "SKY_Ramp", -500, 400); r = ramp.color_ramp
r.elements[0].position = 0.0; r.elements[0].color = (1.0, 0.62, 0.38, 1)        # peachy horizon
r.elements[1].position = 0.5; r.elements[1].color = (0.30, 0.45, 0.78, 1)       # soft blue zenith
r.elements.new(0.14).color = (0.98, 0.72, 0.58, 1)
sky = node("ShaderNodeBackground", "SKY_Paint", -200, 400); sky.inputs["Strength"].default_value = 1.1
lp = node("ShaderNodeLightPath", "SKY_Path", -200, 650); mix = node("ShaderNodeMixShader", "SKY_Mix", 100, 300)
L = nt.links
L.new(tc.outputs["Generated"], sep.inputs[0]); L.new(sep.outputs["Z"], ramp.inputs[0]); L.new(ramp.outputs["Color"], sky.inputs["Color"])
L.new(lp.outputs["Is Camera Ray"], mix.inputs[0]); L.new(bg.outputs[0], mix.inputs[1]); L.new(sky.outputs[0], mix.inputs[2])
L.new(mix.outputs[0], out.inputs["Surface"])

# 2) Sun: low-ish (28 deg) from the east, straight down the pickup street behind CAM_EST_Street: the street and the
#    human at the door get warm sun (from the north-east the 25-40 m buildings put the whole street in shade).
AZ, EL = math.radians(8), math.radians(28)
to_sun = Vector((math.cos(EL) * math.cos(AZ), math.cos(EL) * math.sin(AZ), math.sin(EL)))
light("LIGHT_Sun", "SUN", (0, 0, 50), 4.4, (1.0, 0.70, 0.45), aim=-to_sun, size=1.2)

# 3) Street lamps: LED heads glow, plus a shadowless warm point light under each head (lamps "just on").
emission("MAT_LampLED", 6.0, (1.0, 0.80, 0.55))
for lamp in [o for o in bpy.data.objects if o.name.startswith("CITY_Lamp_")]:
    head = lamp.matrix_world @ Vector((0, 2.05, 7.55))
    light("LIGHT_" + lamp.name[5:], "POINT", head, 90, (1.0, 0.78, 0.5), size=0.25, shadow=False)
emission("MAT_SignalRed", 4.0); emission("MAT_SignalGreen", 0.0); emission("MAT_SignalAmber", 0.0)
# Shops: the shopfront glass glows warm from inside (open shops), very low so it stays glass.
sg = bpy.data.materials.get("MAT_ShopGlass")
if sg:
    b = sg.node_tree.nodes["Principled BSDF"]; b.inputs["Emission Color"].default_value = (1.0, 0.70, 0.42, 1)
    b.inputs["Emission Strength"].default_value = 0.35

# 4) Car: the Vulcar's LED tubes on, plus two soft headlight spots.
for m in bpy.data.materials:
    if m.name.startswith("Head Light Led Tube"): emission(m.name, 8.0, (1.0, 0.95, 0.88))
    if m.name.startswith("Tailight Led Tube"): emission(m.name, 5.0, (1.0, 0.06, 0.03))
for s, x in (("L", 0.62), ("R", -0.62)):
    light(f"LIGHT_CarHead_{s}", "SPOT", (x, -2.62, 0.66), 120, (1.0, 0.92, 0.8), parent=car, aim=(0, -1, -0.12), size=0.05, spot=60)

# 5) Interior: warm fill through the glass roof, a soft key on each face from the dashboard, a cool rim from behind.
light("LIGHT_CarFill", "AREA", (0, 0.1, 1.33), 5, (1.0, 0.86, 0.72), parent=car, aim=(0, 0, -1), size=0.9, shadow=False)
light("LIGHT_KeyClaude", "AREA", (0.15, -0.75, 1.02), 2.5, (1.0, 0.85, 0.7), parent=car, aim=(0.27, 0.71, -0.06), size=0.35, shadow=False)
light("LIGHT_KeyHuman", "AREA", (-0.15, -0.75, 1.15), 2.5, (1.0, 0.85, 0.7), parent=car, aim=(-0.27, 0.91, 0.05), size=0.35, shadow=False)
light("LIGHT_CarRim", "AREA", (0.0, 1.05, 1.25), 3, (0.65, 0.75, 1.0), parent=car, aim=(0, -1, -0.25), size=0.6, shadow=False)

# 6) Materials: car glass a touch tinted (the coupe read like a convertible), windshield without milky specular;
#    phone text darker on a slightly dimmer screen (it washed out under AgX).
g = bpy.data.materials.get("MAT_CarGlass")
if g:
    b = g.node_tree.nodes["Principled BSDF"]; b.inputs["Alpha"].default_value = 0.22
    b.inputs["Base Color"].default_value = (0.08, 0.10, 0.11, 1); b.inputs["Specular IOR Level"].default_value = 0.25
emission("MAT_UI_Background", 0.95); emission("MAT_UI_Text", 1.0, (0.015, 0.013, 0.012)); emission("MAT_UI_TextGrey", 1.0, (0.25, 0.24, 0.22))

# 7) Depth of field: the street shot (long lens) focuses on the human at the door; the phone close-up on the screen.
def dof(cam_name, target_name, fstop):
    c = bpy.data.objects.get(cam_name); t = bpy.data.objects.get(target_name)
    if not c or not t: return
    c.data.dof.use_dof = True; c.data.dof.focus_object = t; c.data.dof.aperture_fstop = fstop
dof("CAM_EST_Street", "CHAR_Human_Street", 2.8)
for n in ("CAM_PHONE_CU", "CAM_HUMAN_POV", "CAM_CLAUDE_POV", "CAM_INT_TwoShot"):   # phone: one depth at 20 cm, DOF only blurs
    c = bpy.data.objects.get(n)
    if c: c.data.dof.use_dof = False

# 8) Eevee for the 8 GB M2 (values from the stylised render tuning: light_threshold 0.005 keeps the lamps).
ee = sc.eevee
ee.taa_render_samples = 32; ee.taa_samples = 16
ee.use_raytracing = True; ee.ray_tracing_method = "SCREEN"; ee.ray_tracing_options.resolution_scale = "2"
ee.use_shadows = True; ee.shadow_ray_count = 1; ee.shadow_step_count = 4
ee.light_threshold = 0.005; ee.use_volumetric_shadows = False
ee.shadow_pool_size = "256"   # diet: half the default 512 MB shadow pool (measured -0.27 GB, no visible change in our shots)
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"; sc.view_settings.exposure = 0.0
bpy.data.orphans_purge(do_recursive=True)
result = {"lights": len([o for o in bpy.data.objects if o.get("cs_owner") == "light"])}
