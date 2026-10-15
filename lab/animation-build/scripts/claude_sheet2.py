"""Host: frame sheet of Claude actions with the cushion (and ring). python3 scripts/claude_sheet2.py out.jpg view action:f1,f2 ...   views: wide | close | front"""
import subprocess, os, sys
from PIL import Image, ImageDraw
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BL = [sys.executable, os.path.join(D, "bridge", "bl.py")]
def bl(*a): return subprocess.run(BL + list(a), capture_output=True, text=True, cwd=D)
out, view = sys.argv[1], sys.argv[2]; specs = [a.split(":") for a in sys.argv[3:]]
VIEWS = {"wide": ((1.3, -3.2, 1.3), (-0.5, 0.0, 0.5), 40), "close": ((1.4, -1.7, 0.7), (-0.1, 0, 0.3), 45), "front": ((0.0, -2.6, 0.9), (0.0, 0, 0.35), 45), "run": ((2.4, -2.6, 1.2), (0.0, -0.8, 0.2), 45), "magic": ((1.8, -3.0, 1.2), (0.3, -0.8, 0.5), 40)}
loc, tgt, lens = VIEWS[view]
SETUP = f'''
exec(open("scripts/_cam.py").read()); exec(open("scripts/claude_test_lib.py").read()); studio(); iso("CLA_","RIG_Claude","CUS_","MAG_","CAR_","ANIM_")
for o in bpy.data.objects:
    if o.name.startswith(("CLA_","RIG_Claude","CUS_","MAG_")): o.hide_viewport=False
    if o.name.startswith("CAR_") : o.hide_render=True
for o in list(bpy.data.objects):
    if o.name.startswith("ANIM_mark") or o.name=="ANIM_floor": bpy.data.objects.remove(o)
bpy.ops.mesh.primitive_plane_add(size=40, location=(0,0,-0.002)); fl=bpy.context.active_object; fl.name="ANIM_floor"
fm=bpy.data.materials.get("ANIM_floor") or bpy.data.materials.new("ANIM_floor"); fm.use_nodes=True; fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.35,.36,.38,1); fl.data.materials.append(fm)
rig=bpy.data.objects["RIG_Claude"]; rig.hide_render=True; rig.location=(0,0,0); reset()
cam({loc},{tgt},{lens})
'''
bl("exec", SETUP)
tiles = []
for act, frames in specs:
    for f in frames.split(","):
        HIDE_CUS = ('cushion' not in act.lower() and 'sit' not in act.lower())
        bl("exec", f'ad=rig.animation_data_create(); ad.action=None\nfor t in list(ad.nla_tracks): ad.nla_tracks.remove(t)\ns=ad.nla_tracks.new().strips.new("{act}",1,bpy.data.actions["{act}"]); s.extrapolation="HOLD"\nreset(); bpy.data.objects["CUS_Cushion"].hide_render = {HIDE_CUS}; bpy.context.scene.frame_set(500); bpy.context.scene.frame_set({f})')
        p = f"{D}/previews/_c2_{act}_{f}.png"; bl("snap", p, "ANIM_CAM", "--size", "400x400", "--render"); tiles.append((f"{act[4:]} f{f}", p))
bl("exec", 'for t in list(rig.animation_data.nla_tracks): rig.animation_data.nla_tracks.remove(t)\nreset(); rig.location=(-1.2,0,0)')
cols = min(6, len(tiles)); rows = (len(tiles) + cols - 1) // cols
sh = Image.new("RGB", (400 * cols, 400 * rows), (40, 40, 40)); d = ImageDraw.Draw(sh)
for i, (lab, p) in enumerate(tiles): sh.paste(Image.open(p).convert("RGB"), ((i % cols) * 400, (i // cols) * 400)); d.text(((i % cols) * 400 + 5, (i // cols) * 400 + 4), lab, fill=(255, 230, 80))
sh.save(out, quality=88)
