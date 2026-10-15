"""Blender wrapper around lab/character/render_clip.py (not edited): registers the camera framing from character.json, then runs it unchanged.
   blender -b <blend> -P render_char.py -- --camera-cfg character.json <render_clip.py args...>
   Swap contract for a better character: the .blend must expose what render_clip.py needs (armature object "FacetRig" with bones
   root/torso/head/eye_L/eye_R/mouth/..., actions idle talk point_left point_right wave think celebrate enter exit @30 fps, camera object "STAGE_camera");
   point character.json at it and, if the proportions differ, edit camera + framing there. Nothing else in the pipeline changes."""
import sys, os, json, runpy
a = sys.argv[sys.argv.index("--") + 1:]
cfg = json.load(open(a[a.index("--camera-cfg") + 1])); i = a.index("--camera-cfg"); del a[i:i + 2]
blend_dir = os.path.dirname(os.path.abspath(__import__("bpy").data.filepath)); sys.path.insert(0, blend_dir)
import stagecfg
c = cfg["camera"]; stagecfg.CAMERAS[c["name"]] = (c["targetZ"], c["visHeight"], c["azimuthDeg"], c["elevationDeg"], c["aspect"])
for k, v in cfg.get("quality", {}).items(): stagecfg.QUALITY[k] = tuple(v)   # optional per-preset (short_side_px, samples) override
sys.argv = [sys.argv[0], "--"] + a
runpy.run_path(os.path.join(blend_dir, "render_clip.py"), run_name="__main__")
