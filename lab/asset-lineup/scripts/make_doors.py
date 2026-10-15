"""Cut the two doors out of the new car's body so they can open and close.
For each side: the door skin (side wall between the front and rear door lines), the side window glass (windows stay up),
the door handle and the side mirror become their own object  LU_NEW_CAR_Door_L / _R  (origin on the hinge, front edge, vertical axis);
the inner door panel becomes  LU_NEW_CAR_Int_DoorCard_L / _R  and is parented to the door. A black jamb is extruded around the opening
in the body and a thin black edge around the door. One control per door on the car root:  door_L_open / door_R_open  (0 = closed ... 1 = 65 degrees),
driven onto the door's Z rotation (plus a rotation limit). L = +x (driver side, left-hand drive), R = -x.
Reads IN.blend, writes OUT.blend (never the input):
  Blender -b --factory-startup IN.blend --python lab/asset-lineup/scripts/make_doors.py -- OUT.blend"""
import bpy, bmesh, sys, math, numpy as np
from mathutils import Vector, Matrix
out = sys.argv[sys.argv.index("--") + 1]
YF, YR = -0.82, 0.84                      # door front / rear lines (body-local y; front is -y)
MAX_OPEN = math.radians(65)
GAP = 0.0015                              # shrink the door edge by 1.5 mm so a seam shows
P = lambda n: bpy.data.objects["LU_NEW_CAR_" + n]
root, body = P("Exterior"), P("Ext_Body")
if "LU_NEW_CAR_Door_L" in bpy.data.objects: raise SystemExit("doors already exist in this file")
Mb = root.matrix_world.inverted() @ body.matrix_world                # body-local -> root-local
black_slot = next(i for i, s in enumerate(body.material_slots) if s.material.name == "NEW_Material.033")
coll = body.users_collection[0]

bm = bmesh.new(); bm.from_mesh(body.data)
bm.transform(Mb)                                                      # work in root-local coordinates
uvl = bm.loops.layers.uv.active
def islands(bm):
    bm.verts.ensure_lookup_table(); seen = set(); out_ = []
    for v in bm.verts:
        if v.index in seen: continue
        st = [v]; comp = []; seen.add(v.index)
        while st:
            x = st.pop(); comp.append(x)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen: seen.add(y.index); st.append(y)
        out_.append(comp)
    return out_
isl = islands(bm); main = max(isl, key=len); main_set = set(main)

report = {}
for sx in (1, -1):
    tag = "L" if sx > 0 else "R"
    # 1. cut the big side strips at the front and rear door lines (only the faces of this side wall)
    for yline in (YF, YR):
        geom = [g for f in bm.faces if sx * f.calc_center_median().x > 0.5 and f.verts[0] in main_set and f.calc_area() > 0.01
                and min(v.co.y for v in f.verts) < yline < max(v.co.y for v in f.verts) and min(v.co.z for v in f.verts) > 2.15 and max(v.co.z for v in f.verts) < 3.0
                for g in [f] + list(f.edges) + list(f.verts)]
        bmesh.ops.bisect_plane(bm, geom=list(set(geom)), dist=1e-5, plane_co=(0, yline, 0), plane_no=(0, 1, 0), use_snap_center=False, clear_outer=False, clear_inner=False)
    bm.faces.ensure_lookup_table()
    # 2. door faces: main-shell side wall inside the door lines; plus the whole small islands that belong to the door (glass, handle, mirror, trim)
    door_faces = set()
    for f in bm.faces:
        c = f.calc_center_median()
        if sx * c.x > 0.55 and YF - 1e-4 < c.y < YR + 1e-4 and 2.2 < c.z < 3.3 and f.verts[0] in main_set and f.calc_area() > 0:
            if all(YF - 1e-3 <= v.co.y <= YR + 1e-3 for v in f.verts): door_faces.add(f)
    for comp in isl:
        if comp is main: continue
        a = np.array([v.co[:] for v in comp]); ctr = (a.min(0) + a.max(0)) / 2
        if sx * a.min(0)[0] > 0.5 and YF - 0.05 <= a.min(0)[1] and a.max(0)[1] <= YR + 0.06 and ctr[2] > 2.6 and ctr[2] < 3.3:   # glass, handle, mirror (arch lips are lower / further back)
            for v in comp: door_faces.update(v.link_faces)
    print(tag, "door faces:", len(door_faces))
    bm.faces.ensure_lookup_table()
    dset = set(f.index for f in door_faces)
    # 3. a copy of the whole mesh, keep only door faces there; remove them from the body
    dbm = bm.copy(); dbm.faces.ensure_lookup_table()
    bmesh.ops.delete(dbm, geom=[f for f in dbm.faces if f.index not in dset], context="FACES_ONLY")
    bmesh.ops.delete(dbm, geom=[v for v in dbm.verts if not v.link_faces], context="VERTS")
    # the opening in the body: split nothing, just delete the door faces (their edges become the hole boundary); jamb = extrude the hole boundary inward
    bmesh.ops.delete(bm, geom=list(door_faces), context="FACES_ONLY")
    hole = [e for e in bm.edges if e.is_boundary and sx * (e.verts[0].co.x + e.verts[1].co.x) / 2 > 0.5 and
            YF - 1e-3 <= min(e.verts[0].co.y, e.verts[1].co.y) and max(e.verts[0].co.y, e.verts[1].co.y) <= YR + 1e-3 and 2.2 < (e.verts[0].co.z + e.verts[1].co.z) / 2 < 3.0
            and (abs(e.verts[0].co.y - e.verts[1].co.y) < 1e-3 and (abs(e.verts[0].co.y - YF) < 1e-3 or abs(e.verts[0].co.y - YR) < 1e-3) or abs(e.verts[0].co.z - e.verts[1].co.z) < 0.02 and e.verts[0].co.z < 2.4)]
    ex = bmesh.ops.extrude_edge_only(bm, edges=hole)
    ev = [g for g in ex["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(-sx * 0.05, 0, 0), verts=ev)
    for g in ex["geom"]:
        if isinstance(g, bmesh.types.BMFace): g.material_index = black_slot; g.smooth = False
    report[tag] = (len(door_faces), len(hole))
    # 4. build the door object: hinge at the front edge on the skin's outer line
    dv = [v for v in dbm.verts if abs(v.co.y - YF) < 1e-3]
    hx = max(abs(v.co.x) for v in dv) * sx if dv else sx * 0.96
    H = Vector((hx, YF, 2.62))
    # 1.5 mm seam: move the door's rim vertices inward
    dbm.verts.ensure_lookup_table()
    cy = (YF + YR) / 2
    for v in dbm.verts:
        if abs(v.co.y - YF) < 1e-3: v.co.y += GAP
        elif abs(v.co.y - YR) < 1e-3: v.co.y -= GAP
    # thin black edge around the door: extrude the door's boundary toward the cabin
    bnd = [e for e in dbm.edges if e.is_boundary and ((abs(e.verts[0].co.y - e.verts[1].co.y) < 1e-3 and (abs(e.verts[0].co.y - (YF + GAP)) < 1e-3 or abs(e.verts[0].co.y - (YR - GAP)) < 1e-3)) or (abs(e.verts[0].co.z - e.verts[1].co.z) < 0.02 and e.verts[0].co.z < 2.4))]
    ex = bmesh.ops.extrude_edge_only(dbm, edges=bnd)
    ev = [g for g in ex["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(dbm, vec=(-sx * 0.035, 0, 0), verts=ev)
    for g in ex["geom"]:
        if isinstance(g, bmesh.types.BMFace): g.material_index = black_slot; g.smooth = False
    for v in dbm.verts: v.co -= H
    me = bpy.data.meshes.new("NEW_CAR_Door_" + tag); dbm.to_mesh(me); dbm.free()
    for s in body.material_slots: me.materials.append(s.material)
    d = bpy.data.objects.new("LU_NEW_CAR_Door_" + tag, me); coll.objects.link(d)
    d.parent = root; d.location = H; d.matrix_parent_inverse = Matrix.Identity(4)
    d["hinge"] = "front edge, vertical axis"
    # inner door panel -> its own object under the door
    dc = P("Int_DoorCards"); mdc = dc.matrix_world
    pb = bmesh.new(); pb.from_mesh(dc.data); pb.faces.ensure_lookup_table()
    keep = [f for f in pb.faces if sx * f.calc_center_median().x > 0.6]
    pb2 = pb.copy(); pb2.faces.ensure_lookup_table()
    kidx = set(f.index for f in keep)
    bmesh.ops.delete(pb2, geom=[f for f in pb2.faces if f.index not in kidx], context="FACES_ONLY"); bmesh.ops.delete(pb2, geom=[v for v in pb2.verts if not v.link_faces], context="VERTS")
    bmesh.ops.delete(pb, geom=[f for f in pb.faces if f.index in kidx], context="FACES_ONLY"); bmesh.ops.delete(pb, geom=[v for v in pb.verts if not v.link_faces], context="VERTS")
    pb.to_mesh(dc.data); pb.free()
    pme = bpy.data.meshes.new("NEW_CAR_Int_DoorCard_" + tag); pb2.to_mesh(pme); pb2.free()
    for s in dc.material_slots: pme.materials.append(s.material)
    po = bpy.data.objects.new("LU_NEW_CAR_Int_DoorCard_" + tag, pme); coll.objects.link(po)
    po.parent = root; po.matrix_parent_inverse = dc.matrix_parent_inverse.copy(); po.location = dc.location
    bpy.context.view_layer.update()
    mw = po.matrix_world.copy(); po.parent = d; po.matrix_parent_inverse = d.matrix_world.inverted(); po.matrix_world = mw
    # control + driver + limit
    key = f"door_{tag}_open"
    root[key] = 0.0; root.id_properties_ui(key).update(min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, description=f"{tag} door: 0 closed ... 1 fully open (65 degrees)")
    fc = d.driver_add("rotation_euler", 2); dr = fc.driver; dr.type = "SCRIPTED"
    var = dr.variables.new(); var.name = "o"; var.type = "SINGLE_PROP"; var.targets[0].id = root; var.targets[0].data_path = f'["{key}"]'
    dr.expression = f"{-sx}*o*{MAX_OPEN:.6f}"
    lim = d.constraints.new("LIMIT_ROTATION"); lim.use_limit_z = True; lim.min_z = -MAX_OPEN if sx > 0 else 0.0; lim.max_z = 0.0 if sx > 0 else MAX_OPEN; lim.owner_space = "LOCAL"
bm.transform(Mb.inverted())
bm.to_mesh(body.data); bm.free(); body.data.update()
print("report", report)
bpy.ops.wm.save_as_mainfile(filepath=out, copy=False)
print("saved", out)
