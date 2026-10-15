"""Claude's magic ring ("hollow"): a translucent, smoky, glowing ring (cyan to violet, flowing colour) with a thin inner ring, a wispy outer ring,
small pixel sparkles and three smoke puffs, built beside the main Claude on his plinth. For later: it will be shot from Claude's hands to wrap
things he cannot do with his little hands (steering wheel ...), then fade away.
Controls on the empty LU_V3A_Magic_Ring: fade (0 invisible ... 1 fully visible), spin (speed). Everything is parented to the empty, so move / scale / rotate it
to aim it. One shared material V3A_MAT_Magic (Blended, emission + smoky noise alpha); the colour flow and the smoke move with the frame number.
A 60-frame idle loop spins the rings and orbits the sparkles. Reads IN.blend, writes OUT.blend (never the input):
  Blender -b --factory-startup IN.blend --python lab/asset-lineup/scripts/add_magic_ring.py -- OUT.blend"""
import bpy, bmesh, sys, math, random
from pathlib import Path
from mathutils import Vector, Matrix
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lineup_lib as L
out = sys.argv[sys.argv.index("--") + 1]
if "LU_V3A_Magic_Ring" in bpy.data.objects: raise SystemExit("magic ring already exists in this file")
sc = bpy.context.scene
plinth = bpy.data.objects["LU_Plinth_V3A_Claude"]
coll = bpy.data.collections.new("LU_V3A_Magic"); bpy.data.collections["LU_Assets"].children.link(coll)
random.seed(7)

# ---------------- material: blended, glowing, smoky
mat = bpy.data.materials.new("V3A_MAT_Magic"); mat.use_nodes = True
mat.surface_render_method = "BLENDED"; mat.use_backface_culling = False; mat.show_transparent_back = False
nt = mat.node_tree; nt.nodes.clear(); N = nt.nodes; K = nt.links.new
out_ = N.new("ShaderNodeOutputMaterial"); mix = N.new("ShaderNodeMixShader"); tr = N.new("ShaderNodeBsdfTransparent"); em = N.new("ShaderNodeEmission")
tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); grad = N.new("ShaderNodeTexGradient"); grad.gradient_type = "RADIAL"
ramp = N.new("ShaderNodeValToRGB"); ramp.name = "MAGIC_COLOURS"
cols = [(0.0, (0.0, 0.55, 1.0)), (0.33, (0.42, 0.10, 1.0)), (0.66, (0.05, 0.40, 1.0)), (1.0, (0.0, 0.55, 1.0))]
ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[0].color = cols[0][0], (*cols[0][1], 1)
ramp.color_ramp.elements[1].position, ramp.color_ramp.elements[1].color = cols[3][0], (*cols[3][1], 1)
for pos, c in cols[1:3]:
    e = ramp.color_ramp.elements.new(pos); e.color = (*c, 1)
nz = N.new("ShaderNodeTexNoise"); nz.noise_dimensions = "3D"; nz.inputs["Scale"].default_value = 5.0; nz.inputs["Detail"].default_value = 3.0; nz.inputs["Roughness"].default_value = 0.6
nmp = N.new("ShaderNodeMapping"); nramp = N.new("ShaderNodeValToRGB"); nramp.name = "SMOKE_AMOUNT"
nramp.color_ramp.elements[0].position = 0.30; nramp.color_ramp.elements[0].color = (0, 0, 0, 1); nramp.color_ramp.elements[1].position = 0.75; nramp.color_ramp.elements[1].color = (1, 1, 1, 1)
fresnel = N.new("ShaderNodeLayerWeight"); fresnel.inputs["Blend"].default_value = 0.35
mulA = N.new("ShaderNodeMath"); mulA.operation = "MULTIPLY"; mulB = N.new("ShaderNodeMath"); mulB.operation = "MULTIPLY"; mulC = N.new("ShaderNodeMath"); mulC.operation = "MULTIPLY"
fade = N.new("ShaderNodeValue"); fade.name = "FADE"; fade.label = "FADE (driven by the empty's 'fade')"; fade.outputs[0].default_value = 1.0
base = N.new("ShaderNodeValue"); base.name = "BASE_ALPHA"; base.outputs[0].default_value = 0.85
obj = N.new("ShaderNodeObjectInfo")
add = N.new("ShaderNodeMath"); add.operation = "ADD"
em.inputs["Strength"].default_value = 1.3
K(tc.outputs["Object"], mp.inputs["Vector"]); K(mp.outputs["Vector"], grad.inputs["Vector"]); K(grad.outputs["Fac"], ramp.inputs["Fac"]); K(ramp.outputs["Color"], em.inputs["Color"])
K(tc.outputs["Object"], nmp.inputs["Vector"]); K(obj.outputs["Random"], add.inputs[0]); add.inputs[1].default_value = 0.0
K(nmp.outputs["Vector"], nz.inputs["Vector"]); K(nz.outputs["Fac"], nramp.inputs["Fac"])
K(nramp.outputs["Color"], mulA.inputs[0]); K(fresnel.outputs["Facing"], mulB.inputs[0]); mulB.inputs[1].default_value = -1.0   # (unused scale term kept simple)
# alpha = smoke * base * fade * (0.55 + 0.45 * (1 - facing))
inv_ = N.new("ShaderNodeMath"); inv_.operation = "SUBTRACT"; inv_.inputs[0].default_value = 1.0; K(fresnel.outputs["Facing"], inv_.inputs[1])
edge = N.new("ShaderNodeMath"); edge.operation = "MULTIPLY_ADD"; K(inv_.outputs[0], edge.inputs[0]); edge.inputs[1].default_value = 0.45; edge.inputs[2].default_value = 0.55
K(nramp.outputs["Color"], mulA.inputs[0]); K(base.outputs[0], mulA.inputs[1]); K(mulA.outputs[0], mulC.inputs[0]); K(fade.outputs[0], mulC.inputs[1])
mul4 = N.new("ShaderNodeMath"); mul4.operation = "MULTIPLY"; mul4.use_clamp = True; K(mulC.outputs[0], mul4.inputs[0]); K(edge.outputs[0], mul4.inputs[1])
K(mul4.outputs[0], mix.inputs["Fac"]); K(tr.outputs["BSDF"], mix.inputs[1]); K(em.outputs["Emission"], mix.inputs[2]); K(mix.outputs["Shader"], out_.inputs["Surface"])
for nn, (x, y) in ((tc, (-1100, 0)), (mp, (-900, 200)), (grad, (-700, 200)), (ramp, (-500, 200)), (nmp, (-900, -150)), (nz, (-700, -150)), (nramp, (-500, -150)), (fresnel, (-700, -400)), (inv_, (-500, -400)), (edge, (-300, -400)),
                   (base, (-500, -600)), (fade, (-500, -750)), (mulA, (-300, -150)), (mulC, (-150, -150)), (mul4, (0, -150)), (tr, (150, 100)), (em, (150, 300)), (mix, (350, 150)), (out_, (550, 150)), (obj, (-1100, -250)), (add, (-900, -300))):
    nn.location = (x, y)

# softer variant for the smoke puffs (fainter, bigger smoke)
mat2 = mat.copy(); mat2.name = "V3A_MAT_MagicSmoke"
mat2.node_tree.nodes["BASE_ALPHA"].outputs[0].default_value = 0.32
mat2.node_tree.nodes["SMOKE_AMOUNT"].color_ramp.elements[0].position = 0.38
# ---------------- objects (all parented to one empty)
CX, CY, CZ = plinth.location.x + 0.78, plinth.location.y - 0.15, 0.62
emp = bpy.data.objects.new("LU_V3A_Magic_Ring", None); emp.empty_display_type = "CIRCLE"; emp.empty_display_size = 0.3; coll.objects.link(emp)
emp.location = (CX, CY, CZ); emp.rotation_euler = (math.radians(78), 0, math.radians(-18))
emp["fade"] = 1.0; emp.id_properties_ui("fade").update(min=0.0, max=1.0, description="0 = invisible, 1 = fully visible")
emp["spin"] = 1.0; emp.id_properties_ui("spin").update(min=0.0, max=4.0, description="spin speed of the rings")
emp["note"] = "Claude's magic ring: aim it by moving / rotating this empty; fade 0 -> 1 makes it appear."
def new_obj(name, bm, parent=emp, material=None):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(material or mat)
    for f in me.polygons: f.use_smooth = True
    o = bpy.data.objects.new("LU_V3A_Magic_" + name, me); coll.objects.link(o); o.parent = parent; o.matrix_parent_inverse = Matrix.Identity(4)
    return o
def torus(R, r, seg=48, ring=12, wob=0.0, arc=2 * math.pi, start=0.0):
    bm = bmesh.new(); rows = []
    n = seg if arc >= 2 * math.pi - 1e-6 else seg + 1
    for i in range(n):
        a = start + arc * i / seg; rr = r * (1 + wob * math.sin(a * 5 + 1.3))
        c = Vector((R * math.cos(a), R * math.sin(a), 0)); rad = Vector((math.cos(a), math.sin(a), 0))
        rows.append([bm.verts.new(c + (rad * math.cos(t) + Vector((0, 0, 1)) * math.sin(t)) * rr) for t in [2 * math.pi * k / ring for k in range(ring)]])
    for i in range(n if arc >= 2 * math.pi - 1e-6 else n - 1):
        for k in range(ring): bm.faces.new((rows[i][k], rows[i][(k + 1) % ring], rows[(i + 1) % n][(k + 1) % ring], rows[(i + 1) % n][k]))
    return bm
main = new_obj("Ring_Main", torus(0.22, 0.034, wob=0.18))
inner = new_obj("Ring_Inner", torus(0.165, 0.012, seg=40, ring=8, wob=0.1)); inner.rotation_euler = (0, 0, 0.6)
wisp = new_obj("Ring_Wisp", torus(0.29, 0.007, seg=36, ring=6, arc=math.radians(250), start=math.radians(30), wob=0.3))
# sparkles: small pixel plus-signs and diamonds in the ring plane, orbiting on a pivot empty
pivot = bpy.data.objects.new("LU_V3A_Magic_Orbit", None); pivot.empty_display_size = 0.01; coll.objects.link(pivot); pivot.parent = emp
bmS = bmesh.new()
for k in range(9):
    a = 2 * math.pi * k / 9 + random.uniform(-0.2, 0.2); rad = 0.33 + 0.08 * random.random(); z = random.uniform(-0.06, 0.06); s = random.choice((0.014, 0.02, 0.026))
    c = Vector((rad * math.cos(a), rad * math.sin(a), z))
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)) if k % 3 == 0 else ((0, 0),):
        r = bmesh.ops.create_cube(bm := bmS, size=s)
        bmesh.ops.translate(bmS, vec=c + Vector((dx * s, dy * s, 0)), verts=r["verts"])
sp = new_obj("Sparkles", bmS, parent=pivot)
for f in sp.data.polygons: f.use_smooth = False
# smoke puffs trailing behind the ring (direction the ring will travel from: +x local)
for i, (x, y, z, r_) in enumerate(((0.43, 0.02, 0.0, 0.07), (0.60, -0.05, 0.03, 0.055), (0.74, 0.04, -0.02, 0.04))):
    bmP = bmesh.new(); ic = bmesh.ops.create_icosphere(bmP, subdivisions=2, radius=r_)
    for v in bmP.verts: v.co *= Vector((1.5, 1.0, 0.9)) * (1 + 0.12 * math.sin(v.co.x * 90 + i))
    puff = new_obj(f"Puff_{i + 1}", bmP, material=mat2); puff.location = (x, y, z)

# ---------------- driver: material fade follows the empty's 'fade'
for tree in (nt, mat2.node_tree):
    if tree.animation_data:
        for d_ in [d for d in tree.animation_data.drivers if 'FADE' in d.data_path]: tree.animation_data.drivers.remove(d_)
    fc = tree.driver_add('nodes["FADE"].outputs[0].default_value'); dr = fc.driver; dr.type = "SCRIPTED"
    var = dr.variables.new(); var.name = "f"; var.type = "SINGLE_PROP"; var.targets[0].id = emp; var.targets[0].data_path = '["fade"]'; dr.expression = "f"
# colour flow + smoke drift with the frame
for node, attr, expr in ((mp, "rotation", "frame * 0.045"), (nmp, "location", "frame * 0.01")):
    pass
fcm = nt.driver_add('nodes["%s"].inputs[2].default_value' % mp.name, 2); fcm.driver.type = "SCRIPTED"; fcm.driver.expression = "frame * 0.052"
fcn = nt.driver_add('nodes["%s"].inputs[1].default_value' % nmp.name, 2); fcn.driver.type = "SCRIPTED"; fcn.driver.expression = "frame * 0.012"

# ---------------- 60-frame idle loop: rings spin, sparkles orbit
for o, axis, turns in ((main, 2, 1), (inner, 2, -2), (wisp, 2, 1), (pivot, 2, -1)):
    o.rotation_mode = "XYZ"; base_ = o.rotation_euler[axis]
    for f, t in ((1, 0.0), (61, 1.0)):
        o.rotation_euler[axis] = base_ + turns * 2 * math.pi * t
        o.keyframe_insert("rotation_euler", index=axis, frame=f)
    o.rotation_euler[axis] = base_
    for fcv in o.animation_data.action.fcurves:
        for kp in fcv.keyframe_points: kp.interpolation = "LINEAR"
        fcv.modifiers.new("CYCLES")
sc.frame_start, sc.frame_end = 1, 60
print("magic ring built at", tuple(round(x, 2) for x in emp.location), "objects", len(coll.objects))
bpy.ops.wm.save_as_mainfile(filepath=out, copy=False)
print("saved", out)
