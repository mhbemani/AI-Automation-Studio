"""Claude's favourite cushion: a yellow-orange pillow with gold piping, corner tassels, a button and a tiny pixel sparkle, for the main Claude (V3-A)
on his own plinth. It is bouncy: a shape key "Squash" is driven by Claude's feet height (he stands on it; lower him and it flattens and bulges,
lift him and it springs back), plus a manual slider  squash_manual  (0..1) on the cushion for previewing. A 60-frame jump loop (anticipation, launch,
stretch, land, squash, small rebound) is keyed on Claude. Cushion and Claude hang under one empty,  LU_V3A_Set,  so he can carry it everywhere
(move the empty). Reads IN.blend, writes OUT.blend (never the input):
  Blender -b --factory-startup IN.blend --python lab/asset-lineup/scripts/add_cushion.py -- OUT.blend"""
import bpy, bmesh, sys, math
from pathlib import Path
from mathutils import Vector, Matrix
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lineup_lib as L
out = sys.argv[sys.argv.index("--") + 1]
if "LU_V3A_Cushion" in bpy.data.objects: raise SystemExit("cushion already exists in this file")
sc = bpy.context.scene
claude = bpy.data.objects["LU_V3A_CHAR_Claude"]; plinth = bpy.data.objects["LU_Plinth_V3A_Claude"]
coll = bpy.data.collections["LU_V3A_Claude"]
CX, CY, TOP = plinth.location.x, plinth.location.y, L.PLINTH_H
A, Bk, HT, HB = 0.42, 0.32, 0.125, 0.095           # half width, half depth, top dome height, bottom height
PTOP, PBOT = 2.4, 5.0
SQ = 0.45                                           # thickness left at full squash
def zt(x, y):
    u, v = abs(x) / A, abs(y) / Bk
    z = HT * math.sqrt(max(0.0, (1 - min(u, 1) ** PTOP) * (1 - min(v, 1) ** PTOP)))
    return z - 0.04 * math.exp(-(x * x + y * y) / 0.07 ** 2)                    # button dimple
def zb(x, y):
    u, v = abs(x) / A, abs(y) / Bk
    return -HB * math.sqrt(max(0.0, (1 - min(u, 1) ** PBOT) * (1 - min(v, 1) ** PBOT)))

# ---- materials
mat = lambda n, c, r=0.9: L.mat_simple(n, c, r)
m_body = mat("V3A_MAT_CushionBody", (0.95, 0.46, 0.02), 0.85)      # yellow-orange (#F7B52A-ish)
m_body.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (0.95, 0.46, 0.02, 1); m_body.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.18
m_pipe = mat("V3A_MAT_CushionPiping", (1.0, 0.70, 0.17), 0.6)
m_btn = mat("V3A_MAT_CushionButton", (0.68, 0.18, 0.095), 0.7)  # Claude orange
m_tas = mat("V3A_MAT_CushionTassel", (1.0, 0.62, 0.12), 0.8)

bm = bmesh.new(); NX, NY = 20, 14
def grid(sign):
    g = {}
    for i in range(NX + 1):
        for j in range(NY + 1):
            x = A * (2 * i / NX - 1); y = Bk * (2 * j / NY - 1)
            edge = i in (0, NX) or j in (0, NY)
            key = (i, j) if not edge else (i, j)
            z = 0.0 if edge else (zt(x, y) if sign > 0 else zb(x, y))
            g[(i, j)] = (x, y, z)
    return g
gt, gb = grid(1), grid(-1)
V = {}
for (i, j), p in gt.items(): V[("t", i, j)] = bm.verts.new(p)
for (i, j), p in gb.items():
    V[("b", i, j)] = V[("t", i, j)] if (i in (0, NX) or j in (0, NY)) else bm.verts.new(p)
for i in range(NX):
    for j in range(NY):
        f = bm.faces.new((V[("t", i, j)], V[("t", i + 1, j)], V[("t", i + 1, j + 1)], V[("t", i, j + 1)])); f.material_index = 0; f.smooth = True
        f = bm.faces.new((V[("b", i, j + 1)], V[("b", i + 1, j + 1)], V[("b", i + 1, j)], V[("b", i, j)])); f.material_index = 0; f.smooth = True
# piping: a rope swept around the seam
path = [(i, 0) for i in range(NX)] + [(NX, j) for j in range(NY)] + [(i, NY) for i in range(NX, 0, -1)] + [(0, j) for j in range(NY, 0, -1)]
pts = [Vector((gt[p][0], gt[p][1], 0.0)) for p in path]; n = len(pts); R_ = 0.014
rings = []
for k, p in enumerate(pts):
    t = (pts[(k + 1) % n] - pts[k - 1]).normalized(); out_ = Vector((t.y, -t.x, 0)).normalized()
    c = Vector((p.x, p.y, 0)) + out_ * 0.004
    rings.append([bm.verts.new(c + (out_ * math.cos(a) + Vector((0, 0, 1)) * math.sin(a)) * R_) for a in [2 * math.pi * s / 6 for s in range(6)]])
for k in range(n):
    for s in range(6):
        f = bm.faces.new((rings[k][s], rings[k][(s + 1) % 6], rings[(k + 1) % n][(s + 1) % 6], rings[(k + 1) % n][s])); f.material_index = 1; f.smooth = True
# button in the dimple
bt = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=14, radius1=0.026, radius2=0.018, depth=0.02)
bmesh.ops.translate(bm, vec=(0, 0, zt(0, 0) + 0.006), verts=bt["verts"])
for f in {f for v in bt["verts"] for f in v.link_faces}: f.material_index = 2; f.smooth = True
# tassels at the four corners (cone + ball)
for sx in (-1, 1):
    for sy in (-1, 1):
        d = Vector((sx * 0.7, sy * 0.7, -0.6)).normalized(); base = Vector((sx * A, sy * Bk, 0.0))
        cone = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=True, segments=8, radius1=0.017, radius2=0.006, depth=0.05)
        q = Vector((0, 0, 1)).rotation_difference(d)
        bmesh.ops.transform(bm, matrix=Matrix.Translation(base + d * 0.03 + d * 0.015) @ q.to_matrix().to_4x4(), verts=cone["verts"])
        ball = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.022)
        bmesh.ops.translate(bm, vec=base + d * 0.075, verts=ball["verts"])
        for f in {f for v in cone["verts"] + ball["verts"] for f in v.link_faces}: f.material_index = 3; f.smooth = True
# tiny pixel sparkle (plus sign of 5 squares) in the front-left corner area, Claude orange
sp = 0.026
for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
    x0, y0 = -0.27 + dx * sp * 1.4, -0.17 + dy * sp * 1.4
    verts = [bm.verts.new((x0 + a * sp / 2 * 0.95, y0 + b * sp / 2 * 0.95, zt(x0 + a * sp / 2, y0 + b * sp / 2) + 0.0015)) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    f = bm.faces.new(verts); f.material_index = 2; f.smooth = False
me = bpy.data.meshes.new("V3A_Cushion"); bm.to_mesh(me); bm.free()
for m in (m_body, m_pipe, m_btn, m_tas): me.materials.append(m)
cush = bpy.data.objects.new("LU_V3A_Cushion", me); coll.objects.link(cush)

# ---- the "set" empty: Claude + cushion together (carry it by moving the empty)
setE = bpy.data.objects.new("LU_V3A_Set", None); setE.empty_display_type = "PLAIN_AXES"; setE.empty_display_size = 0.15; coll.objects.link(setE)
setE.location = (CX, CY, TOP); setE["note"] = "move this empty to carry Claude and his cushion together"
cush.parent = setE; cush.location = (0, 0, HB)
# feet height on top of the cushion (average over Claude's four legs)
legs = [bpy.data.objects[f"LU_V3A_CHAR_Claude_Leg_{i}"] for i in (1, 2, 3, 4)]
lx = [(-0.225, 0.0), (-0.125, 0.0), (0.125, 0.0), (0.225, 0.0)]
zf = sum(zt(x, y) for x, y in lx) / 4                            # top surface under the feet (cushion-local)
zbf = sum(zb(x, y) for x, y in lx) / 4
REST = HB + zf                                                    # Claude's root height above the plinth top when the cushion is relaxed
THICK = zf - zbf
claude.parent = None
mw = Matrix.Translation((CX, CY, TOP + REST)); claude.matrix_world = mw
claude.parent = setE; claude.matrix_parent_inverse = setE.matrix_world.inverted(); claude.location = (0, 0, REST)
bpy.context.view_layer.update()

# ---- shape key: squash (bottom stays on the plinth, top comes down, sides bulge)
cush.shape_key_add(name="Basis")
sk = cush.shape_key_add(name="Squash")
for i, v in enumerate(me.vertices):
    x, y, z = v.co; zbot = zb(x, y)
    w = 1.0 - ((abs(x) / A) ** 6) * 0.0
    sk.data[i].co = Vector((x * 1.12, y * 1.12, zbot + SQ * (z - zbot)))
sk.value = 0.0
cush["squash_manual"] = 0.0; cush.id_properties_ui("squash_manual").update(min=0.0, max=1.0, description="preview the squash by hand (0 = relaxed, 1 = flattened); the cushion also squashes when Claude's feet go down")
fc = sk.driver_add("value"); dr = fc.driver; dr.type = "SCRIPTED"
v1 = dr.variables.new(); v1.name = "c"; v1.type = "TRANSFORMS"; v1.targets[0].id = claude; v1.targets[0].transform_type = "LOC_Z"; v1.targets[0].transform_space = "WORLD_SPACE"
v2 = dr.variables.new(); v2.name = "m"; v2.type = "SINGLE_PROP"; v2.targets[0].id = cush; v2.targets[0].data_path = '["squash_manual"]'
rest_world = TOP + REST; D = (1 - SQ) * THICK
dr.expression = f"min(1, max(0, ({rest_world:.5f} - c) / {D:.5f}) + m)"

# ---- 60-frame jump loop on Claude (height + squash/stretch)
F = [(1, 0.0, (1, 1, 1)), (9, -0.95 * D, (1.07, 1.07, 0.88)), (19, 0.30, (0.95, 0.95, 1.10)), (29, 0.0, (1, 1, 1)), (34, -0.8 * D, (1.06, 1.06, 0.90)), (43, 0.12, (0.98, 0.98, 1.04)), (51, 0.0, (1, 1, 1)), (60, 0.0, (1, 1, 1))]
claude.animation_data_create()
act = bpy.data.actions.new("Claude_Jump_on_Cushion"); claude.animation_data.action = act
for f, dz, s in F:
    claude.location = (0, 0, REST + dz); claude.scale = s
    claude.keyframe_insert("location", index=2, frame=f); claude.keyframe_insert("scale", frame=f)
claude.location = (0, 0, REST); claude.scale = (1, 1, 1)
sc.frame_start, sc.frame_end = 1, 60; sc.frame_set(1)
print("cushion done: rest height", round(REST, 3), "squash drop", round(D, 3), "tris", len(me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=out, copy=False)
print("saved", out)
