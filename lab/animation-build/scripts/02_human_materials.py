"""Human look: the creator wants him as the original scan: one plain silver-grey material, no colours, no face.
Idempotent. Run via bridge after 01_human_rig.py."""
import bpy
HEX = "b4b9c2"
def lin(c): return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def main():
    body = bpy.data.objects["HUM_Body"]
    m = bpy.data.materials.get("HUM_silver") or bpy.data.materials.new("HUM_silver"); m.use_nodes = True
    c = [lin(int(HEX[i:i + 2], 16) / 255) for i in (0, 2, 4)]
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs["Base Color"].default_value = (*c, 1); b.inputs["Roughness"].default_value = 0.55; b.inputs["Metallic"].default_value = 0.35
    m.diffuse_color = (*c, 1)
    body.data.materials.clear(); body.data.materials.append(m)
    for p in body.data.polygons: p.material_index = 0
    return m.name
result = main()
