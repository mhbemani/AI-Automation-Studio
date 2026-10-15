"""Phase 3 / milestone 2: MAG_ring_shoot (24), MAG_ring_wrap (30), MAG_ring_fade (18) keyed on the MAG_Root properties; CLA_magic_cast (24) on Claude's ctrl;
CAR_self_drive_start (48) on CAR_ctrl (dash_glow, a steering pulse, then distance rolls from rest to 2 m/s). Run via bridge after 45_magic_rig.py."""
import bpy, math, os
SKIP_MAIN40 = True
ROOT = os.environ.get("ANIM_ROOT") or os.path.dirname(os.path.abspath(__import__("bpy").data.filepath))
exec(open(os.path.join(ROOT, "scripts", "40_claude_locomotion.py")).read())
mroot = bpy.data.objects["MAG_Root"]; car = bpy.data.objects["CAR_ctrl"]
def obuild(obj, name, keys, defaults, interp='BEZIER'):
    old = bpy.data.actions.get(name)
    if old: bpy.data.actions.remove(old)
    a = bpy.data.actions.new(name); a.use_fake_user = True
    if obj.animation_data is None: obj.animation_data_create()
    obj.animation_data.action = a
    props = sorted({p for d in keys.values() for p in d})
    for f in sorted(keys):
        for p in props: obj[p] = float(keys[f].get(p, defaults[p])); obj.keyframe_insert(f'["{p}"]', frame=f)
    for fc in a.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = interp
    obj.animation_data.action = None
    for p, d in defaults.items(): obj[p] = float(d)
MD = dict(fade=0, shot=0, size=1, wrap=0, spin_rate=1, puff=0, sparkle=0)
# shoot: pops open at his hand, flies the `dist` metres to the target, a smoke puff at the start
obuild(mroot, "MAG_ring_shoot", {1: dict(fade=0, size=0.3, shot=0, spin_rate=4, puff=0), 5: dict(fade=1, size=0.8, shot=0, spin_rate=4, puff=0.8), 9: dict(fade=1, size=1.05, shot=0.04, spin_rate=3, puff=0.9),
       14: dict(fade=1, size=1, shot=0.55, spin_rate=2.5, puff=0.3), 21: dict(fade=1, size=1, shot=0.97, spin_rate=2, puff=0), 24: dict(fade=1, size=1, shot=1, spin_rate=2, puff=0)}, MD)
# wrap: ring (at the target) squeezes around it with a small overshoot, spins faster while it grips
obuild(mroot, "MAG_ring_wrap", {1: dict(fade=1, shot=1, wrap=0, size=1, spin_rate=2), 10: dict(fade=1, shot=1, wrap=0.5, size=1.04, spin_rate=3.5), 18: dict(fade=1, shot=1, wrap=1.0, size=1, spin_rate=4),
       24: dict(fade=1, shot=1, wrap=0.94, size=1, spin_rate=3), 30: dict(fade=1, shot=1, wrap=1.0, size=1, spin_rate=2.5)}, MD)
# fade: dissolves into sparkles (the orbit grows then is gone)
obuild(mroot, "MAG_ring_fade", {1: dict(fade=1, shot=1, wrap=1, size=1, sparkle=0, spin_rate=2.5), 6: dict(fade=0.8, shot=1, wrap=1, size=1.15, sparkle=0.7, spin_rate=3), 12: dict(fade=0.3, shot=1, wrap=1, size=1.45, sparkle=1, spin_rate=3.5),
       18: dict(fade=0, shot=1, wrap=1, size=1.7, sparkle=0, spin_rate=3.5)}, MD)
# cast: small wind-up, both arms push forward, body leans in, stretch then settle; determined sparkly eyes
EY = dict(eye_h_L=0.95, eye_h_R=0.95, eye_w=1.05, glint=1.5, blush=0.6)
def cast(f):
    t = {1: 0, 6: -1, 10: 1, 16: 0.9, 24: 0}
    ks = sorted(t); i = max(j for j in range(len(ks)) if ks[j] <= f)
    if i == len(ks) - 1: v = t[ks[i]]
    else:
        a, b = ks[i], ks[i + 1]; u = sm((f - a) / (b - a)); v = t[a] + (t[b] - t[a]) * u
    p = max(0.0, v); w = max(0.0, -v)
    d = dict(arm_fwd_L=80 * p - 20 * w, arm_fwd_R=80 * p - 20 * w, arm_len_L=1.0 + 0.6 * p, arm_len_R=1.0 + 0.6 * p, arm_L=10 * p + 25 * w, arm_R=10 * p + 25 * w,
             squash=0.3 * w - 0.2 * p, nod=-5 * p + 4 * w, lean=0, hop=0.0)
    for k, x in EY.items(): d[k] = DEFAULT[k] + (x - DEFAULT[k]) * min(1, abs(v) + p)
    return d
build("CLA_magic_cast", {f: cast(f) for f in (1, 4, 6, 8, 10, 13, 16, 20, 24)})
# car: glow on, steering pulse (wheel turns itself), then rolls from rest, 2 m/s by the end
dist = {f: 0.5 * 2.0 * (max(0, f - 24) / 24.0) ** 2 for f in range(24, 49, 4)}
ck = {}
for f in (1, 6, 10, 15, 20, 26, 32, 40, 48):
    ck[f] = dict(dash_glow=min(1.0, sm((f - 1) / 12.0)), steer={1: 0, 6: 0, 10: 0.07, 15: -0.07, 20: 0.03, 26: 0}.get(f, 0), distance=0.5 * 2.0 * (max(0, f - 24) / 24.0) ** 2)
obuild(car, "CAR_self_drive_start", ck, dict(dash_glow=0, steer=0, distance=0))
result = sorted(a.name for a in bpy.data.actions if a.name.startswith(("MAG_", "CLA_magic", "CAR_self")))
