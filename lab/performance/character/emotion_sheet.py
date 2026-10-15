"""Stills of the 12 emotions on a frozen neutral pose (face channels from solver.face_channels) + three mouth openings.
blender -b facet.blend -P emotion_sheet.py -- --out DIR --profile ../rig_profile_facet.json --camera-cfg ../pipeline/character.json [--res 560] [--camera face]"""
import bpy, sys, os, json, argparse
HERE = os.path.dirname(os.path.abspath(bpy.data.filepath)); sys.path.insert(0, HERE)
import stagecfg, rigpose, solver
ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--profile", required=True); ap.add_argument("--camera-cfg", required=True); ap.add_argument("--res", type=int, default=560)
ap.add_argument("--zoom", type=float, default=0.42); ap.add_argument("--az", type=float); ap.add_argument("--el", type=float); ap.add_argument("--only")
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:])
P = json.load(open(a.profile)); cfg = json.load(open(a.camera_cfg)); k = cfg["camera"]
stagecfg.CAMERAS["face"] = (1.72, 3.8 * a.zoom, a.az if a.az is not None else k["azimuthDeg"], a.el if a.el is not None else k["elevationDeg"], "1:1"); stagecfg.QUALITY["draft"] = (a.res, 6)
sc = bpy.context.scene; cam = bpy.data.objects["STAGE_camera"]; stagecfg.apply(sc, cam, "face", "draft", "1:1")
rig = rigpose.Rig(); os.makedirs(a.out, exist_ok=True)
names = [n for n in P["emotions"] if not n.startswith("_")]
if a.only: names = a.only.split(",")
cases = [(n, P["emotions"][n], 0.0) for n in names] + [("friendly_open0.5", P["emotions"]["friendly"], 0.5), ("excited_open1", P["emotions"]["excited"], 1.0)]
for name, E, op in cases:
    ch = solver.face_channels(P, E, op, 1.0, 0.0, E["lookY"] if "lookY" in E else 0.0)
    ch["head"] = {"q": solver.euler_q(P["viewer"]["headYaw"] * P["viewer"]["headShare"], -E["headPitch"], E["headRoll"])}
    one = {b: {kk: [vv] for kk, vv in c.items()} for b, c in ch.items()}
    rig.pose_frame(one, 0); sc.render.filepath = os.path.join(a.out, "emo_%s.png" % name); bpy.ops.render.render(write_still=True)
print("EMOTIONS", len(cases))
