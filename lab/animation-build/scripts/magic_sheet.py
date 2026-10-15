"""Host: sheet of the combined magic sequence (cast + ring shoot/wrap/fade on a target). python3 scripts/magic_sheet.py out.jpg f1,f2,..."""
import subprocess, os, sys
from PIL import Image, ImageDraw
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def bl(*a): return subprocess.run([sys.executable, os.path.join(D, "bridge", "bl.py")] + list(a), capture_output=True, text=True, cwd=D)
out = sys.argv[1]; frames = sys.argv[2].split(",")
print(bl("exec", '''
exec(open("scripts/_cam.py").read()); exec(open("scripts/claude_test_lib.py").read()); exec(open("scripts/magic_test_lib.py").read()); exec(open("scripts/magic_lib.py").read())
studio(); iso("CLA_","RIG_Claude","CUS_","MAG_")
for o in bpy.data.objects:
    if o.name.startswith(("CLA_","RIG_Claude","MAG_")): o.hide_viewport=False; o.hide_render=False
for o in list(bpy.data.objects):
    if o.name=="ANIM_floor": bpy.data.objects.remove(o)
bpy.ops.mesh.primitive_plane_add(size=40, location=(0,0,-0.002)); fl=bpy.context.active_object; fl.name="ANIM_floor"
fm=bpy.data.materials.get("ANIM_floor") or bpy.data.materials.new("ANIM_floor"); fm.use_nodes=True; fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.35,.36,.38,1); fl.data.materials.append(fm)
rig=bpy.data.objects["RIG_Claude"]; rig.location=(0,0,0); reset(); bpy.data.objects["CUS_Cushion"].hide_render=True; mag_reset()
aim_magic((0.0,-1.4,0.38)); bpy.data.objects["MAG_Root"]["wrap_to"]=0.7
def strips(obj, seq):
    ad=obj.animation_data_create(); ad.action=None
    for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
    for n,st in seq:
        tr=ad.nla_tracks.new(); s=tr.strips.new(n,st,bpy.data.actions[n]); s.extrapolation="HOLD" if st==seq[0][1] else "NOTHING"
strips(rig,[("CLA_magic_cast",1)]); strips(bpy.data.objects["MAG_Root"],[("MAG_ring_shoot",8),("MAG_ring_wrap",31),("MAG_ring_fade",61)])
cam((2.3,-2.2,1.1),(0.1,-0.7,0.4),40)''').stdout[-300:])
tiles = []
for f in frames:
    bl("exec", f'bpy.context.scene.frame_set(500); bpy.context.scene.frame_set({f})')
    p = f"{D}/previews/_ms_{f}.png"; bl("snap", p, "ANIM_CAM", "--size", "400x400", "--render"); tiles.append((f"f{f}", p))
bl("exec", '''for o in (rig, bpy.data.objects["MAG_Root"]):
    for t in list(o.animation_data.nla_tracks): o.animation_data.nla_tracks.remove(t)
reset(); mag_reset(); bpy.data.objects["MAG_Root"].rotation_mode="XYZ"; bpy.data.objects["MAG_Root"].rotation_euler=(0,0,0); rig.location=(-1.2,0,0)''')
cols = min(6, len(tiles)); rows = (len(tiles) + cols - 1) // cols
sh = Image.new("RGB", (400 * cols, 400 * rows), (40, 40, 40)); d = ImageDraw.Draw(sh)
for i, (lab, p) in enumerate(tiles): sh.paste(Image.open(p).convert("RGB"), ((i % cols) * 400, (i // cols) * 400)); d.text(((i % cols) * 400 + 5, (i // cols) * 400 + 4), lab, fill=(255, 230, 80))
sh.save(out, quality=88)
