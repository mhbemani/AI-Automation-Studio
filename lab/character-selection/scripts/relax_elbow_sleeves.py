"""Relax the sleeve around each elbow at REST: the straightened scan sleeve keeps crumples and dents from its original
bent pose. Sleeve vertices within ZONE of the elbow (measured along the arm) are smoothed (Laplacian, ITER passes,
strength fading from 1 at the elbow to 0 at the zone edge), then every 2 cm slice of the sleeve is scaled back
around the bone to its original mean radius, so the sleeve keeps its size and only the folds/dents go.
Hands, the shoulder and the body are not touched. Run: Blender -b <blend> --python scripts/relax_elbow_sleeves.py  (env ZONE, ITER, OUT)"""
import bpy, bmesh, os, collections
from mathutils import Vector
from mathutils.geometry import intersect_point_line
ZONE, ITER, F = float(os.environ.get("ZONE", "0.10")), int(os.environ.get("ITER", "6")), 0.5
o = bpy.data.objects["HUM_Body"]; rig = bpy.data.objects["RIG_Human"]
for ob in (o, rig):
    bpy.context.view_layer.objects.active = ob
    if ob.mode != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')
B = rig.data.bones; gn = {g.index: g.name for g in o.vertex_groups}
bm = bmesh.new(); bm.from_mesh(o.data); dl = bm.verts.layers.deform.active
def wsum(v, names): return sum(w for k, w in v[dl].items() if gn[k] in names)
report = []
for s in "LR":
    S, E, W = B[f"upper_arm.{s}"].head_local, B[f"forearm.{s}"].head_local, B[f"forearm.{s}"].tail_local
    arm = (f"upper_arm.{s}", f"forearm.{s}")
    def proj(p):
        best = None
        for a, b, sign in ((S, E, -1), (E, W, 1)):
            q, t = intersect_point_line(p, a, b); t = min(1, max(0, t)); q = a + (b - a) * t
            d = (p - q).length
            if best is None or d < best[0]: best = (d, (q - E).length * sign, q)
        return best
    zone = {}
    for v in bm.verts:
        if wsum(v, arm) < 0.5 or any(gn[k].startswith(("hand", "f_", "thumb")) for k in v[dl].keys()): continue
        d, along, q = proj(v.co)
        if abs(along) < ZONE: zone[v] = (1 - abs(along) / ZONE) ** 0.5
    def slices():
        sl = collections.defaultdict(list)
        for v in zone:
            d, along, q = proj(v.co); sl[round(along / 0.02)].append((v, d, q))
        return sl
    before = {k: sum(x[1] for x in r) / len(r) for k, r in slices().items()}
    mins_before = min(x[1] for r in slices().values() for x in r)
    for _ in range(ITER):
        new = {}
        for v, f in zone.items():
            nb = [e.other_vert(v).co for e in v.link_edges]
            new[v] = v.co.lerp(sum(nb, Vector()) / len(nb), F * f)
        for v, c in new.items(): v.co = c
    for k, r in slices().items():                       # restore each slice's mean radius
        if k not in before: continue
        now = sum(x[1] for x in r) / len(r); sc = before[k] / max(now, 1e-6)
        for v, d, q in r: v.co = q + (v.co - q) * (1 + (sc - 1) * zone[v])
    mins_after = min(x[1] for r in slices().values() for x in r)
    report.append(f"{s}: {len(zone)} sleeve verts relaxed, thinnest point {mins_before*100:.1f} -> {mins_after*100:.1f} cm from the bone")
bm.normal_update(); bm.to_mesh(o.data); o.data.update()
print("RELAX", " | ".join(report))
bpy.ops.wm.save_as_mainfile(filepath=os.environ.get("OUT", bpy.data.filepath))
