"""Add three 'cuter face' variants of the V3 Claude (no mouth) next to it, each with its own plinth, label and cameras.
V3 itself is not touched. Same body, arms, legs and bevels as add_claude_v3.py; only the face changes:
  A  eyes lower, bigger, with one white highlight
  B  A + two soft blush marks
  C  bigger, softer eyes with two highlights + blush
Idempotent (a previous A/B/C is removed first). Reads IN.blend, writes OUT.blend (never the input):
  Blender -b --factory-startup IN.blend --python lab/asset-lineup/scripts/add_claude_cute.py -- OUT.blend"""
import bpy, bmesh, sys, math
from pathlib import Path
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lineup_lib as L
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
U = 0.05
W, H, D = 12 * U, 8 * U, 6 * U
LEG_H = 2 * U
BODY_BEVEL, LIMB_BEVEL = 0.006, 0.013
srgb = lambda c: tuple(((x / 255) / 12.92 if x / 255 <= 0.04045 else (((x / 255) + 0.055) / 1.055) ** 2.4) for x in c)
mat_o = bpy.data.materials["V3_MAT_ClaudeOrange"]
mat_e = bpy.data.materials["V3_MAT_ClaudeEye"]
mat_w = L.mat_simple("V3_MAT_EyeHighlight", (1, 1, 1), 0.4, emit=(1, 1, 1))
mat_b = L.mat_simple("V3_MAT_Blush", srgb((236, 98, 96)), 0.6, emit=srgb((236, 98, 96)))
mat_b.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.25

# variant = (tag, label, x, eye (w, h, centre x, centre z) in u, highlights [(dx, dz, size)] in u from the eye centre, blush?, eye bevel)
VARIANTS = [
    ("V3A", "Eyes lower + highlight", -8.2, (1.2, 2.6, 3.4, 3.8), [(-0.25, 0.8, 0.5)], False, 0.0),
    ("V3B", "Eyes + highlight + blush", -5.9, (1.2, 2.6, 3.4, 3.8), [(-0.25, 0.8, 0.5)], True, 0.0),
    ("V3C", "Big soft eyes + blush", -3.6, (1.6, 3.2, 3.5, 3.9), [(-0.35, 0.95, 0.6), (0.3, -0.9, 0.3)], True, 0.005),
]
Y0 = 0.0
CAMS, LAB, STAGE = bpy.data.collections["LU_Cameras"], bpy.data.collections["LU_Labels"], bpy.data.collections["LU_Staging"]
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080

def build(tag, label, x0, eye, hls, blush, ebev):
    for o in [o for o in bpy.data.objects if o.name.startswith((f"LU_{tag}_", f"LU_Plinth_{tag}", f"LU_Placard_{tag}", f"LU_Tag_{tag}", f"LU_Label_{tag}", f"LU_CAM_{tag}"))]:
        bpy.data.objects.remove(o)
    if f"LU_{tag}_Claude" in bpy.data.collections: bpy.data.collections.remove(bpy.data.collections[f"LU_{tag}_Claude"])
    coll = bpy.data.collections.new(f"LU_{tag}_Claude"); bpy.data.collections["LU_Assets"].children.link(coll)

    def part(name, w, d, h, centre, mat, parent=None, origin=None, bevel=0.0):
        o = origin if origin is not None else centre
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co = Vector((v.co.x * w, v.co.y * d, v.co.z * h)) + (Vector(centre) - Vector(o))
        if bevel:
            bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=2, profile=0.5, affect="EDGES")
        ob = L.new_mesh_obj(name, bm, mat, coll); ob.location = o
        for f in ob.data.polygons: f.use_smooth = bool(bevel)
        if bevel:
            m = ob.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL"); m.keep_sharp = True; m.weight = 50
        if parent: ob.parent = parent
        return ob

    root = part(f"LU_{tag}_CHAR_Claude", W, D, H, (0, 0, LEG_H + H / 2), mat_o, origin=(0, 0, 0), bevel=BODY_BEVEL)
    objs = [root]
    ew, eh, ex, ez = eye
    for s, n in ((-1, "L"), (1, "R")):
        objs.append(part(f"LU_{tag}_CHAR_Claude_Arm_{n}", 2 * U, 2 * U, 2 * U, (s * (W / 2 + U), 0, LEG_H + 3 * U), mat_o, root, origin=(s * W / 2, 0, LEG_H + 3 * U), bevel=LIMB_BEVEL))
        ec = (s * ex * U, -D / 2 + 0.002, LEG_H + ez * U)
        objs.append(part(f"LU_{tag}_CHAR_Claude_Eye_{n}", ew * U, 0.012, eh * U, ec, mat_e, root, bevel=ebev))
        for i, (dx, dz, sz) in enumerate(hls, 1):
            hc = (ec[0] + dx * U, ec[1] - 0.008, ec[2] + dz * U)
            objs.append(part(f"LU_{tag}_CHAR_Claude_Eye_{n}_Glint{i}", sz * U, 0.006, sz * U, hc, mat_w, root))
        if blush:
            objs.append(part(f"LU_{tag}_CHAR_Claude_Blush_{n}", 1.7 * U, 0.008, 0.9 * U, (s * 4.7 * U, -D / 2 + 0.001, LEG_H + 1.9 * U), mat_b, root))
    for i, x in enumerate((-4.5, -2.5, 2.5, 4.5), 1):
        objs.append(part(f"LU_{tag}_CHAR_Claude_Leg_{i}", U, 1.6 * U, LEG_H, (x * U, 0, LEG_H / 2), mat_o, root, origin=(x * U, 0, LEG_H), bevel=LIMB_BEVEL))
    root.location = (x0, Y0, L.PLINTH_H)
    bpy.context.view_layer.update()
    lo, hi = L.world_bbox(objs); dims = tuple(round(v, 3) for v in (hi - lo)); tris = L.tri_count(objs)
    root["lineup_source"] = {"file": "built by scripts/add_claude_cute.py", "object": f"{label} (variant of V3 Claude)", "git": "n/a"}
    root["lineup_tris"] = tris; root["lineup_objects"] = len(objs); root["lineup_dims_m"] = list(dims)
    pl = L.cyl_obj(f"LU_Plinth_{tag}_Claude", 0.9, L.PLINTH_H, (x0, Y0, L.PLINTH_H / 2), bpy.data.materials["LU_Plinth_NEW"], STAGE)
    bw, bh, ang = 2.0, 0.7, math.radians(55)
    board = L.box_obj(f"LU_Placard_{tag}_Claude", bw, bh, 0.03, (x0, Y0 - 0.9 - 0.45 - (bh / 2) * math.cos(ang), 0.03 + (bh / 2) * math.sin(ang)), bpy.data.materials["LU_Board"], LAB)
    board.rotation_euler = (ang, 0, 0)
    mt = bpy.data.materials["LU_Text"]
    L.text_obj(f"LU_Label_{tag}_Claude_name", f"{tag[:2]}-{tag[2]}  Claude", 0.22, (0, bh * 0.25, 0.02), (0, 0, 0), mt, LAB, parent=board)
    L.text_obj(f"LU_Label_{tag}_Claude_src", label, 0.11, (0, -bh * 0.02, 0.02), (0, 0, 0), mt, LAB, parent=board)
    L.text_obj(f"LU_Label_{tag}_Claude_info", f"{tris:,} tris   " + " x ".join(f"{v:.2f}" for v in dims) + " m", 0.1, (0, -bh * 0.26, 0.02), (0, 0, 0), mt, LAB, parent=board)
    strip = L.box_obj(f"LU_Tag_{tag}_Claude", bw, 0.07, 0.034, (0, -bh / 2 + 0.04, 0), bpy.data.materials["LU_TagV3"], LAB); strip.parent = board
    for sfx, az, el in (("Front", -90, 8), ("34", -50, 18)):
        cam = L.make_camera(f"LU_CAM_{tag}_Claude_{sfx}", CAMS, 70)
        L.fit_camera(cam, lo, hi, az, el, margin=0.10, lens=70)
    return lo, hi

los, his = [], []
for v in VARIANTS:
    lo, hi = build(*v); los.append(lo); his.append(hi)
v3 = bpy.data.objects.get("LU_V3_CHAR_Claude")
if v3:
    l3, h3 = L.world_bbox([c for c in bpy.data.collections["LU_V3_Claude"].objects]); los.append(l3); his.append(h3)
for o in [o for o in bpy.data.objects if o.name == "LU_CAM_Compare_Cute"]: bpy.data.objects.remove(o)
cam = L.make_camera("LU_CAM_Compare_Cute", CAMS, 85)
clo = Vector((min(v.x for v in los), min(v.y for v in los), 0)); chi = Vector((max(v.x for v in his), max(v.y for v in his), max(v.z for v in his)))
L.fit_camera(cam, clo, chi, -90, 9, margin=0.06, lens=85)
sc.camera = bpy.data.objects.get("LU_CAM_Overview") or sc.camera
bpy.ops.wm.save_as_mainfile(filepath=out, copy=False)
print("saved", out)
