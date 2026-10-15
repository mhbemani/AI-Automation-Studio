"""Phase 3 / milestone 1a: Claude walks and runs (trot: legs 1+4 against 2+3), on the ctrl properties only (leg_y_n slide = stride, leg_len_n = lift and bob compensation).
CLA_walk_cycle (24 loop, 0.40 m per cycle), CLA_run_cycle (16 loop, 0.53 m per cycle, with a flight phase), CLA_idle_to_walk (10), CLA_walk_to_idle (10).
Cycles are in place; the scene moves the root. Planted feet do not slide (checked). Run via bridge."""
import bpy, math, os
rig = bpy.data.objects["RIG_Claude"]; ctrl = rig.pose.bones["ctrl"]
for o in bpy.data.objects:
    if o.name.startswith(("CLA_", "RIG_Claude")): o.hide_viewport = False
UI = {k: ctrl.id_properties_ui(k).as_dict() for k in ctrl.keys()}
DEFAULT = {k: float(v["default"]) for k, v in UI.items()}
def clamp(k, v): return float(max(UI[k]["min"], min(UI[k]["max"], float(v))))
def sm(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
LEGS = (1, 2, 3, 4); PAIR = {1: 0.0, 4: 0.0, 2: 0.5, 3: 0.5}
def gait(p, kind):
    """props for phase p (0..1) of the trot. a = slide amplitude, stance = fraction of the cycle a foot is down."""
    if kind == "walk": a, stance, lift, bobamp, arm, nod, lean, cyc = 0.12, 0.60, 0.04, 0.014, 11.0, 3.0, 2.5, 24
    else:              a, stance, lift, bobamp, arm, nod, lean, cyc = 0.12, 0.42, 0.06, 0.030, 20.0, 9.0, 3.5, 16
    d = {}
    bob = bobamp * (0.5 - 0.5 * math.cos(4 * math.pi * (p - 0.15)))            # two beats per cycle
    for k in LEGS:
        q = (p + PAIR[k]) % 1.0
        if q < stance: y = -a + 2 * a * (q / stance); h = 0.0
        else: u = (q - stance) / (1 - stance); y = a - 2 * a * sm(u); h = lift * math.sin(math.pi * u)
        d[f"leg_y_{k}"] = y; d[f"leg_len_{k}"] = 1.0 + (bob - h) / 0.1; d.setdefault("_h", {})[k] = h
    d["bob"] = bob; d["lean"] = lean * math.sin(2 * math.pi * p); d["nod"] = nod + 1.2 * math.sin(4 * math.pi * p); d["squash"] = 0.03 * math.cos(4 * math.pi * (p - 0.15)) * (1 if kind == "walk" else 2)
    d["arm_fwd_L"] = arm * math.sin(2 * math.pi * p); d["arm_fwd_R"] = -arm * math.sin(2 * math.pi * p)
    d["arm_L"] = 4.0; d["arm_R"] = 4.0; d["look_y"] = -0.006; d["turn"] = 2.0 * math.sin(2 * math.pi * p)
    return d, cyc, 2 * a / stance
from mathutils import Vector as V
LEG_X = {1: -0.167, 2: -0.067, 3: 0.077, 4: 0.177}
def upd(): rig.update_tag(); bpy.context.view_layer.update()
def tail(k): return V(rig.evaluated_get(bpy.context.evaluated_depsgraph_get()).pose.bones[f"leg_{k}"].tail)
def plant(d):
    """the body leans, nods and bobs, which drags the legs with it: correct leg_x / leg_y / leg_len so that every foot ends up where the gait wants it."""
    for k, v in DEFAULT.items(): ctrl[k] = v
    for k, v in d.items():
        if not k.startswith("_"): ctrl[k] = clamp(k, v)
    tgt = {k: (LEG_X[k], d[f"leg_y_{k}"], max(0.0, (d[f"leg_len_{k}"] - 1) * 0 + 0.0)) for k in LEGS}
    for k in LEGS: tgt[k] = (LEG_X[k], d[f"leg_y_{k}"], d["_h"][k])
    out = dict(d)
    for it in range(4):
        upd()
        for k in LEGS:
            t = tail(k); gx, gy, gz = tgt[k]
            ctrl[f"leg_x_{k}"] = clamp(f"leg_x_{k}", ctrl[f"leg_x_{k}"] + (gx - t.x)); ctrl[f"leg_y_{k}"] = clamp(f"leg_y_{k}", ctrl[f"leg_y_{k}"] + (gy - t.y))
            ctrl[f"leg_len_{k}"] = clamp(f"leg_len_{k}", ctrl[f"leg_len_{k}"] - (gz - t.z) / 0.1)
    for k in LEGS:
        for n in ("leg_x_", "leg_y_", "leg_len_"): out[f"{n}{k}"] = ctrl[f"{n}{k}"]
    out.pop("_h"); return out
def build(name, keys, interp='BEZIER', cycles=False):
    old = bpy.data.actions.get(name)
    if old: bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True; rig.animation_data_create().action = act
    props = sorted({p for d in keys.values() for p in d})
    for f in sorted(keys):
        for p in props: ctrl[p] = clamp(p, keys[f].get(p, DEFAULT[p]))
        for p in props: ctrl.keyframe_insert(f'["{p}"]', frame=f, group="CLA_ctrl")
    for fc in act.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = interp
        if cycles: fc.modifiers.new('CYCLES')
    rig.animation_data.action = None
    for k, v in DEFAULT.items(): ctrl[k] = v
    return act
def main():
    log = {}
    for kind, name in (("walk", "CLA_walk_cycle"), ("run", "CLA_run_cycle")):
        _, cyc, stride = gait(0, kind); keys = {}
        for f in range(1, cyc + 1): keys[f] = plant(gait(((f - 1) % cyc) / cyc, kind)[0])
        keys[cyc + 1] = dict(keys[1])
        build(name, keys, interp='LINEAR' if cyc == 16 else 'BEZIER', cycles=True); log[name] = {"frames": cyc, "metres_per_cycle": round(stride, 3)}
    # idle <-> walk (10): blend between the idle's first pose and the walk's first pose
    idle = bpy.data.actions["CLA_idle"]; idle0 = {}
    for fc in idle.fcurves: idle0[fc.data_path.split('"')[3]] = fc.evaluate(1)
    w0 = plant(gait(0, "walk")[0]); props = set(idle0) | set(w0)
    A = {p: idle0.get(p, DEFAULT[p]) for p in props}; B = {p: w0.get(p, DEFAULT[p]) for p in props}
    build("CLA_idle_to_walk", {f: {p: A[p] + (B[p] - A[p]) * sm((f - 1) / 9.0) for p in props} for f in range(1, 11)})
    build("CLA_walk_to_idle", {f: {p: B[p] + (A[p] - B[p]) * sm((f - 1) / 9.0) for p in props} for f in range(1, 11)})
    return log
if "SKIP_MAIN40" not in globals(): result = main()
