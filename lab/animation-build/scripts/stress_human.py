"""Host-side driver: stress poses of the human rig -> contact sheet + numbers.
python3 scripts/stress_human.py   (needs the bridge Blender with RIG_Human + HUM_Body)"""
import subprocess, json, os, sys
from PIL import Image, ImageDraw
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BL = [sys.executable, os.path.join(D, "bridge", "bl.py")]
OUT = os.path.join(D, "previews", "stress_human"); os.makedirs(OUT, exist_ok=True)
def bl(*a): return subprocess.run(BL + list(a), capture_output=True, text=True, cwd=D)
X, Y, Z = "X", "Y", "Z"
POSES = {
 "neutral": [],
 "arms_up": [("upper_arm_fk.L", Y, -150), ("upper_arm_fk.R", Y, 150)],
 "elbows_120": [("forearm_fk.L", X, -120), ("forearm_fk.R", X, -120)],
 "head_turn_L70": [("head", Z, 70)],
 "head_turn_R70": [("head", Z, -70)],
 "spine_twist": [("spine_fk.002", Z, 30), ("spine_fk.003", Z, 25)],
 "seated": [("torso", "move", (0, 0.1, -0.5)), ("thigh_fk.L", X, -90), ("thigh_fk.R", X, -90), ("shin_fk.L", X, 90), ("shin_fk.R", X, 90)],
 "crouch": [("torso", "move", (0, -0.1, -0.45)), ("thigh_fk.L", X, -110), ("thigh_fk.R", X, -110), ("shin_fk.L", X, 120), ("shin_fk.R", X, 120), ("spine_fk.001", X, -20)],
 "ankle_flex": [("foot_fk.L", X, -30), ("foot_fk.R", X, 30)],
}
FINGERS = [f"{n}.{s}" for s in "LR" for n in [f"f_{f}.0{i}" for f in ("index","middle","ring","pinky") for i in (1,2,3)] + [f"thumb.0{i}" for i in (1,2,3)]]
POSES["finger_curl"] = [(f, "local", 60) for f in FINGERS]
VIEWS = {"front": ((0, -4.2, 0.9), (0, 0, 0.9)), "side": ((4.2, 0, 0.9), (0, 0, 0.9))}
CLOSE = {"finger_curl": {"front": ((0.0, -1.5, 1.1), (0.0, 0.0, 1.1)), "side": ((1.5, 0, 1.1), (0, 0, 1.1))},
         "head_turn_L70": {"front": ((0.05, -1.2, 1.55), (0.05, 0.1, 1.55)), "side": ((1.3, 0.1, 1.55), (0.05, 0.1, 1.55))},
         "head_turn_R70": {"front": ((0.05, -1.2, 1.55), (0.05, 0.1, 1.55)), "side": ((1.3, 0.1, 1.55), (0.05, 0.1, 1.55))}}
def run(selected=None):
    res = {}
    bl("exec", 'exec(open("scripts/rigtest_lib.py").read()); exec(open("scripts/_cam.py").read()); studio(); iso("HUM_Body","RIG_Human","ANIM_"); bpy.data.objects["RIG_Human"].hide_viewport=False; bpy.data.objects["RIG_Human"].hide_render=True')
    for name, ops in POSES.items():
        if selected and name not in selected: continue
        code = ['r=bpy.data.objects["RIG_Human"]; b=bpy.data.objects["HUM_Body"]', 'reset_pose(r,True)']
        for bone, ax, v in ops:
            if ax == "move": code.append(f'move_world(r,{bone!r},{v})')
            elif ax == "local":
                code.append(f'pb=r.pose.bones[{bone!r}]; pb.rotation_mode="XYZ"; pb.rotation_euler[0]=math.radians({v})')
            else: code.append(f'rot_world(r,{bone!r},{ax!r},{v})')
        code.append('result=metrics(b)')
        p = bl("exec", "\n".join(code))
        res[name] = p.stdout.strip().replace("result: ", "") or p.stderr.strip()[-200:]
        for view, (loc, tgt) in {**VIEWS, **CLOSE.get(name, {})}.items():
            bl("exec", f'cam({loc},{tgt},{50 if name not in CLOSE else 70})')
            bl("snap", f"{OUT}/{name}_{view}.png", "ANIM_CAM", "--size", "500x625", "--render")
    # restore neutral
    bl("exec", 'reset_pose(bpy.data.objects["RIG_Human"],True)')
    names = [n for n in POSES if not selected or n in selected]
    T = (360, 450)
    sheet = Image.new("RGB", (T[0] * 2 * 3, T[1] * ((len(names) + 2) // 3)), (40, 40, 40)); dr = ImageDraw.Draw(sheet)
    for i, n in enumerate(names):
        for j, v in enumerate(("front", "side")):
            im = Image.open(f"{OUT}/{n}_{v}.png").convert("RGB").resize(T)
            x, y = ((i % 3) * 2 + j) * T[0], (i // 3) * T[1]
            sheet.paste(im, (x, y)); dr.text((x + 6, y + 4), f"{n} / {v}", fill=(255, 230, 80))
    sheet.save(f"{D}/stills/human_stress_sheet.jpg", quality=88)
    json.dump(res, open(f"{D}/stills/human_stress_numbers.json", "w"), indent=1)
    return res
if __name__ == "__main__":
    for k, v in run(sys.argv[1:] or None).items(): print(k, v)
