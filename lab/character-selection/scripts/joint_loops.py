"""Add edge loops around the knees and ankles (env JOINTS=knee,ankle default; JOINTS=elbow for the elbows: +-2.5 cm) (the scan has no clean loops, so the leg is cut by planes):
each joint gets 2 cuts perpendicular to the leg, only through that leg's faces near the joint.
  knee: 2.5 cm above and below the knee joint (plane normal = mid-direction of thigh and shin)
  ankle: 2 cm above and 1 cm below the ankle joint (plane normal = shin direction)
New vertices get interpolated weights; run leg_weights.py afterwards to re-apply the leg rules to them.
Run: Blender -b --factory-startup character_selection_lab.blend --python scripts/joint_loops.py  (env OUT=)"""
import bpy, bmesh, os
o = bpy.data.objects["HUM_Body"]; rig = bpy.data.objects["RIG_Human"]
for ob in (o, rig):
    bpy.context.view_layer.objects.active = ob
    if ob.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
B = rig.data.bones; gn = {g.index: g.name for g in o.vertex_groups}
bm = bmesh.new(); bm.from_mesh(o.data); dl = bm.verts.layers.deform.active
JOINTS = os.environ.get("JOINTS", "knee,ankle").split(",")
def side_of(v, parts=("thigh", "shin", "foot")):
    d = v[dl]
    names = [gn[k] for k, w in d.items() if w > 0.01]
    return {n[-1] for n in names if n.startswith(parts)}
report = []; cut = set()
for s in "LR":
    H, K, A = B[f"thigh.{s}"].head_local, B[f"thigh.{s}"].tail_local, B[f"shin.{s}"].tail_local
    dt, ds = (K - H).normalized(), (A - K).normalized()
    nk = (dt + ds).normalized()
    E, Wr = B[f"forearm.{s}"].head_local, B[f"forearm.{s}"].tail_local
    ne = ((E - B[f"upper_arm.{s}"].head_local).normalized() + (Wr - E).normalized()).normalized()
    cuts = {"knee": (K, nk, (-0.025, 0.025), 0.16, ("thigh", "shin", "foot")), "ankle": (A, ds, (-0.02, 0.01), 0.14, ("thigh", "shin", "foot")),
            "elbow": (E, ne, (-0.025, 0.025), 0.13, ("upper_arm", "forearm"))}
    for joint in JOINTS:
        P, n, offs, R, parts = cuts[joint]
        for off in offs:
            faces = [f for f in bm.faces if all(s in side_of(v, parts) and (v.co - P).length < R for v in f.verts)]
            geom = list({x for f in faces for x in list(f.verts) + list(f.edges)}) + faces
            before = len(bm.verts)
            res = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=P + n * off, plane_no=n, dist=0.002)
            cut |= {g for g in res["geom_cut"] if isinstance(g, bmesh.types.BMVert)}
            report.append(f"{joint}.{s} {off*100:+.1f} cm: +{len(bm.verts) - before} verts")
# clean-up: a cut passing within 5 mm of an existing vertex leaves a sliver; merge those pairs
near = list({x for v in cut if v.is_valid for x in [v] + [e.other_vert(v) for e in v.link_edges]})
merged = len(bm.verts); bmesh.ops.remove_doubles(bm, verts=near, dist=0.005); merged -= len(bm.verts)
report.append(f"merged {merged} near-duplicate verts")
bm.normal_update(); bm.to_mesh(o.data); o.data.update()
print("LOOPS", " | ".join(report), "| total verts", len(o.data.vertices))
bpy.ops.wm.save_as_mainfile(filepath=os.environ.get("OUT", bpy.data.filepath))
