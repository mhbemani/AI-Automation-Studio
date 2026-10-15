"""Face layout (metres, rest pose, scaled 1.75 m human; character faces -Y, his left = +X). Shared by 01 and 03."""
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
SPEC = dict(cx=0.036, eye_z=1.613, eye_dx=0.029, eye_a=0.0135, eye_b=0.0090, brow_z=1.640, brow_dx_in=0.010, brow_dx_out=0.047,
            mouth_z=1.558, mouth_hw=0.021, jaw_pivot_z=1.60)
_bvh = {}
def bvh():
    b = bpy.data.objects["HUM_Body"]
    key = (len(b.data.vertices), len(b.data.polygons))
    if _bvh.get("key") != key:
        verts = [v.co.copy() for v in b.data.vertices]
        _bvh["t"] = BVHTree.FromPolygons(verts, [tuple(p.vertices) for p in b.data.polygons]); _bvh["key"] = key
    return _bvh["t"]
def hit(x, z):
    loc, n, i, d = bvh().ray_cast(Vector((x, -0.6, z)), Vector((0, 1, 0)))
    return loc, n
def surface(x, z, off=0.0, r=0.005):
    """point on the face 'envelope' above (x,z): most forward of 5 samples, pushed out along the normal."""
    loc, n = hit(x, z)
    if loc is None: return None
    y = loc.y
    for dx, dz in ((r, 0), (-r, 0), (0, r), (0, -r)):
        l2, _ = hit(x + dx, z + dz)
        if l2 is not None: y = min(y, l2.y)
    n = n.normalized()
    if n.y > 0: n = -n
    return Vector((x, y, z)) + n * off
