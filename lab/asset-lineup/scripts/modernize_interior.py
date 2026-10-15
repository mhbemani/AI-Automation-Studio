"""Modernise the new car's interior (a little, still low-poly): charcoal leather and trim with a yellow accent line that ties to the
exterior, a slimmer dashboard with a digital instrument cluster, a free-standing centre touchscreen, vent slots, a centre console with a
gear dial, door panels with armrest / door pull / speaker / accent line (fitted to the body's side surface), and a flat-bottom
two-spoke steering wheel. Replaces the meshes of LU_NEW_CAR_Dashboard, _Int_DoorCards and _SteeringWheel (same objects, parents, transforms);
seats, floor, mirror and the body are untouched. Reads IN.blend, writes OUT.blend (never the input):
  Blender -b --factory-startup IN.blend --python lab/asset-lineup/scripts/modernize_interior.py -- OUT.blend"""
import bpy, bmesh, sys, math, numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
out = sys.argv[sys.argv.index("--") + 1]
P = lambda n: bpy.data.objects["LU_NEW_CAR_" + n]
root = P("Exterior"); inv = root.matrix_world.inverted()
dash, doors, wheel = P("Dashboard"), P("Int_DoorCards"), P("SteeringWheel")
Z0 = dash.location.z                       # the interior sits Z0 above its original coordinates

# ---------------- materials
M = bpy.data.materials
trim, soft, hard, screen, leather = M["NEW_MAT_CarTrim"], M["NEW_MAT_CarDashSoft"], M["NEW_MAT_CarDash"], M["NEW_MAT_CarScreen"], M["NEW_MAT_CarLeather"]
black = M["NEW_MAT_CarBlackTrim"]
accent = M.get("NEW_MAT_CarAccent") or M.new("NEW_MAT_CarAccent"); accent.use_nodes = True
b = accent.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.87, 0.52, 0.03, 1); b.inputs["Roughness"].default_value = 0.4
trim.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.055, 0.055, 0.06, 1)    # was cream
trim.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.7
sb = screen.node_tree.nodes["Principled BSDF"]
sb.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1); sb.inputs["Emission Color"].default_value = (0.12, 0.35, 1.0, 1); sb.inputs["Emission Strength"].default_value = 0.55
sb.inputs["Specular IOR Level"].default_value = 0.15
nt = leather.node_tree; bs = nt.nodes["Principled BSDF"]
if not any(n.name == "LU_Charcoal" for n in nt.nodes):                    # darken the brown leather: 88% charcoal, keeps a little of the worn texture
    l = next(l for l in nt.links if l.to_socket == bs.inputs["Base Color"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.name = "LU_Charcoal"; mx.data_type = "RGBA"; mx.blend_type = "MIX"; mx.inputs[0].default_value = 0.88
    mx.inputs[7].default_value = (0.10, 0.10, 0.11, 1)
    nt.links.new(l.from_socket, mx.inputs[6]); nt.links.new(mx.outputs[2], bs.inputs["Base Color"])
    mx.location = (bs.location.x - 220, bs.location.y)

# ---------------- mesh helpers (object-local = original root-local coordinates)
def box(bm, x0, x1, y0, y1, z0, z1, mat, bevel=0.0, seg=2):
    before = set(bm.faces)
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r["verts"]:
        v.co = Vector((x0 + (v.co.x + .5) * (x1 - x0), y0 + (v.co.y + .5) * (y1 - y0), z0 + (v.co.z + .5) * (z1 - z0)))
    if bevel:
        bmesh.ops.bevel(bm, geom=list({e for v in r["verts"] for e in v.link_edges}), offset=min(bevel, 0.45 * min(x1 - x0, y1 - y0, z1 - z0)), segments=seg, profile=0.5, affect="EDGES")
    for f in set(bm.faces) - before: f.material_index = mat; f.smooth = bool(bevel)
def finish(obj, bm, mats):
    me = bpy.data.meshes.new(obj.data.name + ".v2"); bm.to_mesh(me); bm.free()
    for m in mats: me.materials.append(m)
    old = obj.data; obj.data = me
    if old.users == 0: bpy.data.meshes.remove(old)
    me.name = old.name if False else me.name

# ---------------- dashboard (slots: 0 hard, 1 soft, 2 screen, 3 accent)
bm = bmesh.new()
box(bm, -0.84, 0.84, -1.00, -0.60, 0.50, 0.80, 1, 0.03)                    # dash body, soft-touch
for xa, xb in ((-0.74, -0.235), (0.235, 0.74)):                            # yellow accent line along the dash face, interrupted by the monitor
    box(bm, xa, xb, -0.602, -0.590, 0.655, 0.675, 3, 0.004, 1)
for z in (0.715, 0.745):                                                   # slim passenger vent slots
    box(bm, -0.72, -0.30, -0.604, -0.590, z, z + 0.014, 0, 0.003, 1)
box(bm, 0.66, 0.78, -0.604, -0.590, 0.70, 0.74, 0, 0.004, 1)               # driver-side end vent
box(bm, -0.78, -0.66, -0.604, -0.590, 0.70, 0.74, 0, 0.004, 1)             # passenger-side end vent
box(bm, 0.28, 0.56, -0.74, -0.62, 0.80, 0.90, 0, 0.018)                    # instrument cluster pod
box(bm, 0.30, 0.54, -0.624, -0.617, 0.815, 0.885, 2, 0, 1)                 # digital cluster screen
box(bm, -0.12, 0.12, -0.58, 0.55, 0.27, 0.46, 1, 0.03)                     # centre console
box(bm, -0.085, 0.085, -0.50, 0.05, 0.46, 0.468, 0, 0.004, 1)              # piano-black console top
box(bm, -0.10, 0.10, 0.12, 0.52, 0.46, 0.50, 1, 0.03)                      # console armrest pad
for ang in range(0, 360, 45):                                              # gear dial (octagon, r 3 cm)
    pass
r = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=12, radius1=0.032, radius2=0.028, depth=0.03)
bmesh.ops.translate(bm, vec=(0, -0.30, 0.483), verts=r["verts"])
for f in {f for v in r["verts"] for f in v.link_faces}: f.material_index = 0; f.smooth = True
finish(dash, bm, [hard, soft, screen, accent])

# ---------------- monitor: slim rounded glass slab stuck on the dash face + a separate 16:9 screen plane with UVs (for videos later)
MON_W, MON_H, MON_CZ, MON_T, MON_R = 0.44, 0.44 * 9 / 16 + 0.012, 0.67, 0.012, 0.014     # outer size; screen is 0.428 x 0.2408 (16:9)
SCR_W = 0.428; SCR_H = SCR_W * 9 / 16
YF = -0.600                                                                  # dash face (y); the slab sticks out toward the driver (+y)
def monitor_objects():
    bmB = bmesh.new(); pts = []
    for cx, cz, a0 in ((MON_W / 2 - MON_R, MON_H / 2 - MON_R, 0), (-MON_W / 2 + MON_R, MON_H / 2 - MON_R, 90), (-MON_W / 2 + MON_R, -MON_H / 2 + MON_R, 180), (MON_W / 2 - MON_R, -MON_H / 2 + MON_R, 270)):
        for k in range(6): pts.append((cx + MON_R * math.cos(math.radians(a0 + k * 18)), cz + MON_R * math.sin(math.radians(a0 + k * 18))))
    back = [bmB.verts.new((x, YF, MON_CZ + z)) for x, z in pts]; front = [bmB.verts.new((x, YF + MON_T, MON_CZ + z)) for x, z in pts]
    n = len(pts); fb = bmB.faces.new(back[::-1]); ff = bmB.faces.new(front)
    for k in range(n): bmB.faces.new((back[k], back[(k + 1) % n], front[(k + 1) % n], front[k]))
    bmesh.ops.recalc_face_normals(bmB, faces=bmB.faces[:])
    bmesh.ops.bevel(bmB, geom=[e for e in bmB.edges if all(abs(v.co.y - (YF + MON_T)) < 1e-6 for v in e.verts)], offset=0.003, segments=2, profile=0.5, affect="EDGES")
    for f in bmB.faces: f.smooth = True
    meB = bpy.data.meshes.new("NEW_CAR_Monitor"); bmB.to_mesh(meB); bmB.free(); meB.materials.append(black)
    bmS = bmesh.new(); yS = YF + MON_T + 0.0006
    vs = [bmS.verts.new((sx * SCR_W / 2, yS, MON_CZ + sz * SCR_H / 2)) for sx, sz in ((1, -1), (-1, -1), (-1, 1), (1, 1))]   # viewed from +y the right-hand side is -x
    f = bmS.faces.new(vs); f.normal_update()
    if f.normal.y < 0: bmesh.ops.reverse_faces(bmS, faces=[f])
    uv = bmS.loops.layers.uv.new("UVMap")
    for lp in f.loops: lp[uv].uv = ((SCR_W / 2 - lp.vert.co.x) / SCR_W, (lp.vert.co.z - MON_CZ) / SCR_H + 0.5)
    meS = bpy.data.meshes.new("NEW_CAR_Monitor_Screen"); bmS.to_mesh(meS); bmS.free()
    mon = M.get("NEW_MAT_CarMonitor") or M.new("NEW_MAT_CarMonitor"); mon.use_nodes = True
    nt = mon.node_tree
    if "VIDEO_TEXTURE" not in nt.nodes:                                       # default: dark blue standby gradient; link VIDEO_TEXTURE (Image Texture, Source = Movie) into Emission Color to play a video
        nt.nodes.clear()
        out_ = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission"); em.name = "EMISSION"
        tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.name = "STANDBY_GRADIENT"
        ramp.color_ramp.elements[0].color = (0.01, 0.015, 0.05, 1); ramp.color_ramp.elements[1].color = (0.05, 0.12, 0.45, 1)
        vid = nt.nodes.new("ShaderNodeTexImage"); vid.name = "VIDEO_TEXTURE"; vid.label = "VIDEO_TEXTURE (unlinked: set a movie, link Color to Emission)"
        em.inputs["Strength"].default_value = 1.0
        nt.links.new(tc.outputs["UV"], sep.inputs[0]); nt.links.new(sep.outputs["Y"], ramp.inputs["Fac"]); nt.links.new(ramp.outputs["Color"], em.inputs["Color"]); nt.links.new(em.outputs["Emission"], out_.inputs["Surface"])
        for nn, (x, y) in ((tc, (-800, 0)), (sep, (-600, 0)), (ramp, (-400, 0)), (vid, (-700, -300)), (em, (-150, 0)), (out_, (50, 0))): nn.location = (x, y)
    meS.materials.append(mon)
    for nm, me_ in (("LU_NEW_CAR_Monitor", meB), ("LU_NEW_CAR_Monitor_Screen", meS)):
        o = bpy.data.objects.get(nm)
        if o is None:
            o = bpy.data.objects.new(nm, me_)
            for c in dash.users_collection: c.objects.link(o)
            o.parent = root; o.matrix_parent_inverse = dash.matrix_parent_inverse.copy(); o.location = dash.location
        else:
            old = o.data; o.data = me_
            if old.users == 0: bpy.data.meshes.remove(old)
        for sl in o.material_slots: sl.link = "DATA"
    bpy.data.objects["LU_NEW_CAR_Monitor_Screen"]["note"] = "16:9 screen plane, UV 0-1 (u runs toward -x as the driver sees it). Material NEW_MAT_CarMonitor: link node VIDEO_TEXTURE to Emission to show videos."
monitor_objects()

# ---------------- door panels, fitted to the body side (measured by rays against the body)
bm_b = bmesh.new(); bm_b.from_mesh(P("Ext_Body").data); bm_b.transform(inv @ P("Ext_Body").matrix_world); bvh = BVHTree.FromBMesh(bm_b)
def side_x(zlocal):
    xs = [h.x for y in np.arange(-0.8, 0.85, 0.1) if (h := bvh.ray_cast(Vector((2.0, y, zlocal + Z0)), Vector((-1, 0, 0)))[0]) is not None and h.x > 0.75]
    return min(xs) if xs else 0.85
zs = [0.30, 0.40, 0.50, 0.60, 0.70]
outer = [min(side_x(z) - 0.016, 0.93) for z in zs]
print("door panel outer x per height:", [(z, round(x, 3)) for z, x in zip(zs, outer)])
bm = bmesh.new()
for sx in (1, -1):
    T = 0.05                                                              # panel thickness
    poly = [(sx * (x - T), z) for x, z in zip(outer, zs)] + [(sx * x, z) for x, z in zip(outer[::-1], zs[::-1])]
    y0, y1 = -0.80, 0.84
    r0 = [bm.verts.new((px, y0, pz)) for px, pz in poly]; r1 = [bm.verts.new((px, y1, pz)) for px, pz in poly]
    fs = [bm.faces.new(r0), bm.faces.new(r1[::-1])] + [bm.faces.new((r0[k], r0[(k + 1) % len(poly)], r1[(k + 1) % len(poly)], r1[k])) for k in range(len(poly))]
    for f in fs: f.material_index = 0
    bmesh.ops.recalc_face_normals(bm, faces=fs)
    xin = outer[2] - T                                                    # inner face x at mid height
    sgn = lambda a, b: (sx * a, sx * b) if sx > 0 else (sx * b, sx * a)
    xa, xb = sgn(xin - 0.085, xin + 0.004); box(bm, xa, xb, -0.50, 0.25, 0.46, 0.53, 1, 0.025)                 # armrest
    xa, xb = sgn(xin - 0.012, xin + 0.004); box(bm, xa, xb, 0.12, 0.36, 0.585, 0.625, 2, 0.006, 1)             # door pull
    xa, xb = sgn(xin - 0.008, xin + 0.004); box(bm, xa, xb, -0.78, 0.82, 0.683, 0.699, 3, 0.003, 1)            # accent line
    xa, xb = sgn(xin - 0.010, xin + 0.004); box(bm, xa, xb, -0.70, -0.40, 0.33, 0.42, 2, 0.02)                 # speaker grille
box(bm, -0.60, 0.60, 0.96, 1.12, 0.27, 0.76, 1, 0.03)                    # rear bulkhead (between the arches)
finish(doors, bm, [trim, soft, hard, accent])

# ---------------- steering wheel: flat-bottom D ring + two spokes (local XY plane, -y = bottom as before)
bm = bmesh.new(); R, rr, FLAT = 0.19, 0.0165, -0.145; N = 56
path = [Vector((R * math.cos(2 * math.pi * i / N), max(R * math.sin(2 * math.pi * i / N), FLAT), 0)) for i in range(N)]
rings = []
for i, p in enumerate(path):
    t = (path[(i + 1) % N] - path[i - 1]).normalized(); nrm = Vector((t.y, -t.x, 0)); zax = Vector((0, 0, 1))
    thick = rr * (1.0 + 0.25 * (abs(p.x) > 0.12))                            # thicker grips at 3 and 9 o'clock
    rings.append([bm.verts.new(p + (nrm * math.cos(a) + zax * math.sin(a)) * thick) for a in [2 * math.pi * k / 8 for k in range(8)]])
for i in range(N):
    for k in range(8):
        f = bm.faces.new((rings[i][k], rings[i][(k + 1) % 8], rings[(i + 1) % N][(k + 1) % 8], rings[(i + 1) % N][k])); f.smooth = True; f.material_index = 0
box(bm, -0.07, 0.07, -0.06, 0.06, -0.022, 0.022, 0, 0.02)                    # hub
box(bm, 0.05, 0.19, -0.030, 0.012, -0.010, 0.010, 0, 0.004, 1)               # right spoke
box(bm, -0.19, -0.05, -0.030, 0.012, -0.010, 0.010, 0, 0.004, 1)             # left spoke
box(bm, -0.012, 0.012, R - 0.012, R + 0.018, -0.006, 0.020, 1, 0.002, 1)     # yellow 12 o'clock marker
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
finish(wheel, bm, [black, accent])
bpy.ops.wm.save_as_mainfile(filepath=out, copy=False)
print("saved", out)
