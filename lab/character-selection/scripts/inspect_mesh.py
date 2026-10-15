"""Print basic facts about the reference mesh. Run: Blender -b character_selection_lab.blend --python scripts/inspect_mesh.py"""
import bpy, bmesh
from mathutils import Vector
o = bpy.data.objects["Lowpoly Male Standing"]
me = o.data
print("loc", tuple(o.location), "rot", tuple(o.rotation_euler), "scale", tuple(o.scale), "parent", o.parent, "mods", [m.type for m in o.modifiers])
print("verts", len(me.vertices), "faces", len(me.polygons), "vgroups", len(o.vertex_groups), "shapekeys", bool(me.shape_keys), "mats", [m.name if m else None for m in me.materials])
ws = [o.matrix_world @ v.co for v in me.vertices]
mn = Vector(map(min, zip(*ws))); mx = Vector(map(max, zip(*ws)))
print("bbox min", tuple(round(c,3) for c in mn), "max", tuple(round(c,3) for c in mx))
bm = bmesh.new(); bm.from_mesh(me)
islands, seen = [], set()
for v in bm.verts:
    if v.index in seen: continue
    stack, isl = [v], []
    seen.add(v.index)
    while stack:
        a = stack.pop(); isl.append(a.index)
        for e in a.link_edges:
            b = e.other_vert(a)
            if b.index not in seen: seen.add(b.index); stack.append(b)
    islands.append(isl)
print("islands", len(islands), sorted((len(i) for i in islands), reverse=True)[:10])
print("nonmanifold edges", sum(not e.is_manifold for e in bm.edges))
# horizontal slices: x-extent per height band, to locate shoulders/hips/knees
import collections
band = collections.defaultdict(list)
for p in ws: band[round(p.z*20)/20].append(p)
for z in sorted(band):
    xs=[p.x for p in band[z]]; ys=[p.y for p in band[z]]
    print(f"z {z:5.2f} n {len(xs):4d} x {min(xs):6.3f}..{max(xs):6.3f} y {min(ys):6.3f}..{max(ys):6.3f}")
