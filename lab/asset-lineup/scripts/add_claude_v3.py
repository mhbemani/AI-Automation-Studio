"""Add a third Claude, built after Anthropic's Claude Code mascot ("Clawd"): a wide horizontal orange block (12 x 8 pixel units,
3:2), two small dark vertical-rectangle eyes, a short square arm on each side, four short legs, sharp pixel edges, flat colour #D77757.
Pixel unit u = 5 cm. Added to a lineup .blend as collection LU_V3_Claude (own plinth, placard, cameras), between the NEW and OLD Claude.
Reads IN.blend, writes OUT.blend (never the input):
  Blender -b --factory-startup IN.blend --python lab/asset-lineup/scripts/add_claude_v3.py -- OUT.blend"""
import bpy, bmesh, sys, math
from pathlib import Path
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lineup_lib as L
out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
U = 0.05
W, H, D = 12 * U, 8 * U, 6 * U          # body
LEG_H = 2 * U
BODY_BEVEL, LIMB_BEVEL = 0.006, 0.013      # body edges: a little; hands and legs: a little more (metres)
X0, Y0 = -10.5, 0.0                        # column of the other Claudes, y between the NEW and OLD rows
srgb = lambda c: tuple(((x / 255) / 12.92 if x / 255 <= 0.04045 else (((x / 255) + 0.055) / 1.055) ** 2.4) for x in c)
mat_o = L.mat_simple("V3_MAT_ClaudeOrange", srgb((215, 119, 87)), 0.6, emit=srgb((215, 119, 87)))   # rgb(215,119,87) = Claude Code's mascot colour
mat_o.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.32   # lifts it to the logo orange under AgX; keeps the flat sticker look
mat_e = L.mat_simple("V3_MAT_ClaudeEye", (0.012, 0.010, 0.010), 0.5)

# idempotent: remove a previous V3 (objects, cameras, plinth, placard, collection) before adding it again
for o in [o for o in bpy.data.objects if o.name.startswith(("LU_V3_", "LU_Plinth_V3", "LU_Placard_V3", "LU_Tag_V3", "LU_Label_V3", "LU_CAM_V3", "LU_CAM_Compare_Claude3"))]:
    bpy.data.objects.remove(o)
if "LU_V3_Claude" in bpy.data.collections:
    bpy.data.collections.remove(bpy.data.collections["LU_V3_Claude"])
coll = bpy.data.collections.new("LU_V3_Claude")
bpy.data.collections["LU_Assets"].children.link(coll)

def part(name, w, d, h, centre, mat, parent=None, origin=None, bevel=0.0):
    """box w x d x h whose centre is at `centre` (root-local); object origin at `origin` (default: centre) so parts can be rigged later"""
    o = origin if origin is not None else centre
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * w, v.co.y * d, v.co.z * h)) + (Vector(centre) - Vector(o))
    if bevel:      # small soft edge: a 2-segment bevel, smooth-shaded with weighted normals so the big faces stay flat
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=2, profile=0.5, affect="EDGES")
    ob = L.new_mesh_obj(name, bm, mat, coll)
    ob.location = o
    for f in ob.data.polygons: f.use_smooth = bool(bevel)
    if bevel:
        m = ob.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL"); m.keep_sharp = True; m.weight = 50
    if parent: ob.parent = parent
    return ob

root = part("LU_V3_CHAR_Claude", W, D, H, (0, 0, LEG_H + H / 2), mat_o, origin=(0, 0, 0), bevel=BODY_BEVEL)   # origin on the ground, under the centre
objs = [root]
for s, n in ((-1, "L"), (1, "R")):
    objs.append(part(f"LU_V3_CHAR_Claude_Arm_{n}", 2 * U, 2 * U, 2 * U, (s * (W / 2 + U), 0, LEG_H + 3 * U), mat_o, root, origin=(s * W / 2, 0, LEG_H + 3 * U), bevel=LIMB_BEVEL))
    objs.append(part(f"LU_V3_CHAR_Claude_Eye_{n}", U, 0.012, 2 * U, (s * 3.5 * U, -D / 2 + 0.002, LEG_H + 5 * U), mat_e, root))
for i, x in enumerate((-4.5, -2.5, 2.5, 4.5), 1):
    objs.append(part(f"LU_V3_CHAR_Claude_Leg_{i}", U, 1.6 * U, LEG_H, (x * U, 0, LEG_H / 2), mat_o, root, origin=(x * U, 0, LEG_H), bevel=LIMB_BEVEL))
root.location = (X0, Y0, L.PLINTH_H)
bpy.context.view_layer.update()
lo, hi = L.world_bbox(objs); dims = tuple(round(v, 3) for v in (hi - lo)); tris = L.tri_count(objs)
root["lineup_source"] = {"file": "built by scripts/add_claude_v3.py", "object": "Claude Code mascot (Clawd) re-built from its pixel-art description", "git": "n/a"}
root["lineup_tris"] = tris; root["lineup_objects"] = len(objs); root["lineup_dims_m"] = list(dims)

# plinth, placard, cameras (same style as the other assets)
mat_pl = bpy.data.materials["LU_Plinth_NEW"]
mat_tag = L.mat_simple("LU_TagV3", (0.45, 0.25, 0.7), 0.8)
pl = L.cyl_obj("LU_Plinth_V3_Claude", 0.9, L.PLINTH_H, (X0, Y0, L.PLINTH_H / 2), mat_pl, bpy.data.collections["LU_Staging"])
mat_b, mat_t = bpy.data.materials["LU_Board"], bpy.data.materials["LU_Text"]
LAB = bpy.data.collections["LU_Labels"]
bw, bh, ang = 2.6, 0.8, math.radians(55)
board = L.box_obj("LU_Placard_V3_Claude", bw, bh, 0.03, (X0, Y0 - 0.9 - 0.45 - (bh / 2) * math.cos(ang), 0.03 + (bh / 2) * math.sin(ang)), mat_b, LAB)
board.rotation_euler = (ang, 0, 0)
fmt = lambda t: f"{t:,}"
L.text_obj("LU_Label_V3_Claude_name", "V3  Claude (mascot)", 0.24, (0, bh * 0.25, 0.02), (0, 0, 0), mat_t, LAB, parent=board)
L.text_obj("LU_Label_V3_Claude_src", "Claude Code mascot, rebuilt", 0.12, (0, -bh * 0.02, 0.02), (0, 0, 0), mat_t, LAB, parent=board)
L.text_obj("LU_Label_V3_Claude_info", f"{fmt(tris)} tris   " + " x ".join(f"{v:.2f}" for v in dims) + " m", 0.12, (0, -bh * 0.26, 0.02), (0, 0, 0), mat_t, LAB, parent=board)
strip = L.box_obj("LU_Tag_V3_Claude", bw, 0.07, 0.034, (0, -bh / 2 + 0.04, 0), mat_tag, LAB); strip.parent = board

sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
CAMS = bpy.data.collections["LU_Cameras"]
for sfx, az, el in (("Front", -90, 8), ("34", -50, 18)):
    cam = L.make_camera(f"LU_CAM_V3_Claude_{sfx}", CAMS, 70)
    L.fit_camera(cam, lo, hi, az, el, margin=0.10, lens=70)
# compare camera: the three Claudes (NEW, V3, OLD) in one shot
ls = [lo, hi]
for n in ("LU_NEW_CHAR_Claude", "LU_OLD_CHAR_Claude"):
    r = bpy.data.objects.get(n)
    if r:
        l2, h2 = L.world_bbox([c for c in bpy.data.collections[r.users_collection[0].name].objects]); ls += [l2, h2]
clo = Vector((min(v.x for v in ls), min(v.y for v in ls), 0)); chi = Vector((max(v.x for v in ls), max(v.y for v in ls), max(v.z for v in ls)))
cam = L.make_camera("LU_CAM_Compare_Claude3", CAMS, 70)
L.fit_camera(cam, clo, chi, -120, 12, margin=0.06, lens=70)
sc.camera = bpy.data.objects.get("LU_CAM_Overview") or sc.camera
print("V3 Claude", tris, "tris", dims, "m")
bpy.ops.wm.save_as_mainfile(filepath=out, copy=False)
print("saved", out)
