"""Claude stress test: extremes of every control, numeric penetration/escape check + contact sheet.
python3 scripts/stress_claude.py"""
import subprocess, os, sys, json
from PIL import Image, ImageDraw
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BL = [sys.executable, os.path.join(D, "bridge", "bl.py")]
def bl(*a): return subprocess.run(BL + list(a), capture_output=True, text=True, cwd=D)
POSES = {
 "rest": {}, "squash_max": dict(squash=1), "stretch_max": dict(squash=-1),
 "arms_up_120": dict(arm_L=120, arm_R=120), "arms_down_-70": dict(arm_L=-70, arm_R=-70), "arms_fwd_90": dict(arm_fwd_L=90, arm_fwd_R=90, arm_L=0), "arms_back_-90": dict(arm_fwd_L=-90, arm_fwd_R=-90),
 "lean_25": dict(lean=25), "nod_25": dict(nod=25), "nod_-25": dict(nod=-25), "turn_60": dict(turn=60),
 "eyes_tall_wide": dict(eye_h_L=2.0, eye_h_R=2.0, eye_w=1.8, eye_y=.06), "eyes_low_small": dict(eye_h_L=.1, eye_h_R=.1, eye_w=.4, eye_y=-.06),
 "look_corner": dict(look_x=.05, look_y=-.05), "eye_roll_35": dict(eye_roll=35), "blink": dict(eye_open=0), "blush_glint": dict(blush=1, glint=1.6),
}
CHECK = r'''
exec(open("scripts/claude_test_lib.py").read())
import bmesh
rig=bpy.data.objects["RIG_Claude"]; dg=bpy.context.evaluated_depsgraph_get()
def verts(name):
    o=bpy.data.objects[name].evaluated_get(dg); me=o.to_mesh(); out=[o.matrix_world@v.co for v in me.vertices]; o.to_mesh_clear(); return out
e=ev(); pb=e.pose.bones["body"]; Dm=pb.matrix@rig.data.bones["body"].matrix_local.inverted()
Dinv=Dm.inverted(); W=rig.matrix_world.inverted()
lo=V((-0.30,-0.15,0.10)); hi=V((0.30,0.15,0.50)); sh=0.002
def inside_depth(vs):
    worst=0.0
    for v in vs:
        p=Dinv@(W@v)
        if all(lo[i]+sh<p[i]<hi[i]-sh for i in range(3)):
            worst=max(worst,min(min(p[i]-lo[i],hi[i]-p[i]) for i in range(3)))
    return round(worst*1000,1)
res={}
res["arm_L_in_body_mm"]=inside_depth(verts("CLA_Arm_L")); res["arm_R_in_body_mm"]=inside_depth(verts("CLA_Arm_R"))
# eyes must stay on the front face: x within +-0.29, z within 0.11..0.49 (body-local)
bad=0
for n in ("CLA_Eye_L","CLA_Eye_R","CLA_Glint_L","CLA_Glint_R","CLA_Blush_L","CLA_Blush_R"):
    for v in verts(n):
        p=Dinv@(W@v)
        if not (-0.295<p.x<0.295 and 0.105<p.z<0.495): bad+=1
res["face_parts_off_front"]=bad
sq=[V(v) for v in verts("CLA_Body")]
res["body_scale_xyz"]=[round(x,3) for x in e.pose.bones["squash"].scale]; res["vol"]=round(res["body_scale_xyz"][0]*res["body_scale_xyz"][1]*res["body_scale_xyz"][2],3)
result=res
'''
def run():
    out = {}
    OUT = f"{D}/previews/stress_claude"; os.makedirs(OUT, exist_ok=True)
    bl("exec", 'exec(open("scripts/_cam.py").read()); exec(open("scripts/claude_test_lib.py").read()); studio(); iso("CLA_","RIG_Claude","ANIM_"); bpy.data.objects["RIG_Claude"].hide_render=True; reset(); cam((-1.2,-1.8,0.45),(-1.2,0,0.32),50)')
    for n, p in POSES.items():
        bl("exec", f"reset(); setp(**{p!r})")
        r = bl("exec", CHECK); out[n] = r.stdout.strip().replace("result: ", "") or r.stderr.strip()[-300:]
        bl("snap", f"{OUT}/{n}.png", "ANIM_CAM", "--size", "400x300", "--render")
    bl("exec", "reset()")
    T = (300, 225); cols = 6; names = list(POSES)
    sh = Image.new("RGB", (T[0] * cols, T[1] * ((len(names) + cols - 1) // cols)), (40, 40, 40)); d = ImageDraw.Draw(sh)
    for i, n in enumerate(names):
        sh.paste(Image.open(f"{OUT}/{n}.png").convert("RGB").resize(T), ((i % cols) * T[0], (i // cols) * T[1])); d.text(((i % cols) * T[0] + 5, (i // cols) * T[1] + 4), n, fill=(255, 230, 80))
    sh.save(f"{D}/stills/claude_stress_sheet.jpg", quality=88); json.dump(out, open(f"{D}/stills/claude_stress_numbers.json", "w"), indent=1)
    return out
if __name__ == "__main__":
    for k, v in run().items(): print(k, v)
