"""Milestone 5: Claude's actions, all keyed on the ctrl custom properties of RIG_Claude (24 fps, fake users).
CLA_idle (96 loop), CLA_blink (6), CLA_emoeyes_<8> (8 frames, pose blend-in), CLA_emobody_<8> (16 frames), CLA_talk_pulse (12 loop),
CLA_look_left/right/up/down/camera (6), CLA_look_around (60). Loops: the last key equals the first (frame count = length + 1 key).
Pose actions: frame 1 = neutral, last frame = the held pose (play forward to blend in, backwards to blend out). Idempotent."""
import bpy, math, sys, os
ROOT = os.environ.get("ANIM_ROOT") or os.path.dirname(os.path.abspath(__import__("bpy").data.filepath))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import importlib, claude_presets as cp; importlib.reload(cp)
rig = bpy.data.objects["RIG_Claude"]; ctrl = rig.pose.bones["ctrl"]
UI = {k: ctrl.id_properties_ui(k).as_dict() for k in ctrl.keys() if k not in ("_RNA_UI",)}
DEFAULT = {k: v["default"] for k, v in UI.items()}
def clamp(k, v): return float(max(UI[k]["min"], min(UI[k]["max"], float(v))))

def reset_props():
    for k, v in DEFAULT.items(): ctrl[k] = float(v)

def build(name, keys, interp='BEZIER', cycles=False, props=None):
    """keys: {frame: {prop: value}}; props = list of props to key at every key frame (value defaults to DEFAULT)."""
    old = bpy.data.actions.get(name)
    if old: bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True
    if rig.animation_data is None: rig.animation_data_create()
    rig.animation_data.action = act
    allp = props or sorted({p for d in keys.values() for p in d})
    for f in sorted(keys):
        reset_props()
        for p in allp: ctrl[p] = clamp(p, keys[f].get(p, DEFAULT[p]))
        for p in allp: ctrl.keyframe_insert(f'["{p}"]', frame=f, group="CLA_ctrl")
    for fc in act.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = interp
        if cycles: fc.modifiers.new('CYCLES')
    rig.animation_data.action = None
    reset_props()
    act["frames"] = f"{min(keys)}-{max(keys)}"
    return act

def blend(base, target, t): return base + (target - base) * t

def main():
    out = {}
    eye_props, body_props = list(cp.EYE_DEFAULT), list(cp.BODY_DEFAULT)
    # --- eyes / body emotion poses
    for e in cp.EMOTIONS:
        tgt = cp.preset(e, "neutral")
        k = {1: {p: DEFAULT[p] for p in eye_props}}
        k[4] = {p: blend(DEFAULT[p], tgt[p], 1.12) for p in eye_props}       # little pop
        k[8] = {p: tgt[p] for p in eye_props}
        build(f"CLA_emoeyes_{e}", k, props=eye_props)
        tgt = cp.preset("neutral", e)
        k = {1: {p: DEFAULT[p] for p in body_props}}
        k[3] = {p: blend(DEFAULT[p], tgt[p], -0.12) for p in body_props}      # anticipation dip
        k[9] = {p: blend(DEFAULT[p], tgt[p], 1.18) for p in body_props}      # overshoot
        k[12] = {p: blend(DEFAULT[p], tgt[p], 0.96) for p in body_props}     # settle
        k[16] = {p: tgt[p] for p in body_props}
        build(f"CLA_emobody_{e}", k, props=body_props)
    # --- blink
    build("CLA_blink", {1: {"eye_open": 1.0}, 2: {"eye_open": .5}, 3: {"eye_open": 0.0}, 4: {"eye_open": .2}, 5: {"eye_open": .7}, 6: {"eye_open": 1.0}}, interp='LINEAR', props=["eye_open"])
    # --- idle (96 loop; key 97 == key 1)
    k = {}
    for f in range(1, 98, 4):
        ph = 2 * math.pi * ((f - 1) % 96) / 96
        k[f] = dict(squash=-0.03 * math.sin(2 * ph), bob=0.004 * math.sin(2 * ph), arm_L=3 + 3 * math.sin(2 * ph + .5), arm_R=3 + 3 * math.sin(2 * ph + .9),
                    lean=1.2 * math.sin(ph), turn=1.0 * math.sin(ph + 1), look_x=0.006 * math.sin(ph + 2), look_y=0.003 * math.sin(2 * ph))
    k[97] = dict(k[1])
    build("CLA_idle", k, cycles=True)
    # --- talk pulse (12 frame loop, 2 syllables); the live version is driven by the `talk` property
    build("CLA_talk_pulse", {1: {"talk": 0.0}, 3: {"talk": 1.0}, 6: {"talk": .25}, 8: {"talk": .8}, 11: {"talk": 0.1}, 13: {"talk": 0.0}}, cycles=True)
    # --- looks (eyes only; 6 frames, pose)
    for nme, (lx, ly, gl) in dict(left=(-.04, 0, 1.0), right=(.04, 0, 1.0), up=(0, .035, 1.0), down=(0, -.03, 1.0), camera=(0, 0, 1.3)).items():
        build(f"CLA_look_{nme}", {1: {"look_x": 0, "look_y": 0, "glint": 1.0}, 4: {"look_x": lx * 1.1, "look_y": ly * 1.1, "glint": gl}, 6: {"look_x": lx, "look_y": ly, "glint": gl}}, props=["look_x", "look_y", "glint"])
    build("CLA_look_around", {1: dict(look_x=0, look_y=0, turn=0), 10: dict(look_x=-.04, look_y=0, turn=-8), 22: dict(look_x=.04, look_y=0, turn=8),
                              34: dict(look_x=0, look_y=.035, turn=0), 42: dict(look_x=0, look_y=.035, turn=0), 52: dict(look_x=-.02, look_y=-.02, turn=-4), 60: dict(look_x=0, look_y=0, turn=0)},
          props=["look_x", "look_y", "turn"])
    return sorted(a.name for a in bpy.data.actions if a.name.startswith("CLA_"))
result = main()
