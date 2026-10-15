"""Stage: camera, 3-point lights, shadow-catcher ground, render settings. Idempotent (clears STAGE_* objects)."""
import bpy, os, sys
from math import radians as rad
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import stagecfg

if "FacetRig" not in bpy.data.objects: bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "facet.blend"))
sc = bpy.context.scene
for o in [o for o in bpy.data.objects if o.name.startswith("STAGE_")]: bpy.data.objects.remove(o)

def light(name, kind, loc, target, energy, color, size, spot_deg=None):
    ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = color
    ld.use_shadow = True
    if kind == 'AREA': ld.shape = 'RECTANGLE'; ld.size = size; ld.size_y = size * 0.7
    o = bpy.data.objects.new("STAGE_" + name, ld); sc.collection.objects.link(o)
    o.location = loc
    from mathutils import Vector
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return o

T = (0, 0, 1.2)
light("key", 'AREA', (-3.4, -4.4, 3.0), T, 850, (1.0, 0.95, 0.88), 3.2)      # soft warm key, camera-left
light("fill", 'AREA', (4.2, -3.0, 1.6), T, 220, (0.55, 0.72, 1.0), 3.0)       # cool fill, low, camera-right
light("rim", 'AREA', (2.2, 3.6, 3.2), T, 340, (1.0, 0.45, 0.62), 1.6)       # strong coloured rim/back (warm magenta)
light("rim2", 'AREA', (-3.0, 3.2, 2.4), T, 500, (0.35, 0.85, 1.0), 1.4)       # cool rim from the other side

# contact shadow: Eevee Next has no working shadow catcher, so a procedural soft blob (transparent, black) rides the root bone
bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0.02, 0.003)); g = bpy.context.object; g.name = "STAGE_shadow"
g.scale = (1.05, 0.8, 1); g.visible_glossy = False
m = bpy.data.materials.new("STAGE_shadow"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
m.surface_render_method = 'BLENDED'; m.use_transparency_overlap = False
N = nt.nodes.new; L = nt.links.new
tc = N("ShaderNodeTexCoord"); sub = N("ShaderNodeVectorMath"); sub.operation = 'SUBTRACT'; sub.inputs[1].default_value = (0.5, 0.5, 0)
ln = N("ShaderNodeVectorMath"); ln.operation = 'LENGTH'
mr = N("ShaderNodeMapRange"); mr.inputs[1].default_value = 0.0; mr.inputs[2].default_value = 1.0; mr.inputs[3].default_value = 1.0; mr.inputs[4].default_value = 0.0
pw = N("ShaderNodeMath"); pw.operation = 'POWER'; pw.inputs[1].default_value = 1.8
ml = N("ShaderNodeMath"); ml.operation = 'MULTIPLY'; ml.inputs[1].default_value = 0.55
tr = N("ShaderNodeBsdfTransparent"); em = N("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.01, 0.01, 0.03, 1)
mx = N("ShaderNodeMixShader"); out = N("ShaderNodeOutputMaterial")
L(tc.outputs["Object"], ln.inputs[0]); L(ln.outputs["Value"], mr.inputs[0])
L(mr.outputs[0], pw.inputs[0]); L(pw.outputs[0], ml.inputs[0]); L(ml.outputs[0], mx.inputs[0])
L(tr.outputs[0], mx.inputs[1]); L(em.outputs[0], mx.inputs[2]); L(mx.outputs[0], out.inputs["Surface"])
g.data.materials.append(m)
rg = bpy.data.objects["FacetRig"]; g.parent = rg; g.parent_type = 'BONE'; g.parent_bone = "root"
pb = rg.data.bones["root"]
g.matrix_parent_inverse = (rg.matrix_world @ pb.matrix_local @ __import__("mathutils").Matrix.Translation((0, pb.length, 0))).inverted()

cam = bpy.data.objects.new("STAGE_camera", bpy.data.cameras.new("STAGE_camera")); sc.collection.objects.link(cam)
stagecfg.apply(sc, cam, "full", "draft")

w = bpy.data.worlds.get("FacetWorld") or bpy.data.worlds.new("FacetWorld"); sc.world = w
w.use_nodes = True; bg = w.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.35, 0.42, 0.6, 1); bg.inputs["Strength"].default_value = 0.35   # very low ambient
r = sc.render; r.engine = 'BLENDER_EEVEE_NEXT'; r.film_transparent = True
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGBA'; r.image_settings.color_depth = '8'
r.image_settings.compression = 15
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
sc.view_settings.exposure = 0; sc.view_settings.gamma = 1
sc.display_settings.display_device = 'sRGB'
sc.eevee.use_shadows = True; sc.eevee.use_raytracing = False
sc.eevee.shadow_ray_count = 2; sc.eevee.shadow_step_count = 8
sc.frame_start, sc.frame_end = 1, 60
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "facet.blend"), compress=True)
print("STAGE OK", os.path.getsize(os.path.join(HERE, "facet.blend")))
