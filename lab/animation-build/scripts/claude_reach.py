"""Reach planning for Claude's stub arms (pure python, no Blender). Rig-local metres.
An arm can stretch to REACH_MAX x its 0.1 m length (never thinner). Its pivot slides on the side wall (arm_y -0.09..0.09, arm_z -0.10..0.15).
plan_reach(targets) -> dict per target: how to get a hand there: 'stretch' (within 2.3x), 'turn' (turn/lean the body and use one hand) or 'magic'."""
import math
ARM_LEN, REACH_MAX = 0.10, 2.3
PIVOT = {"L": (-0.30, 0.0, 0.25), "R": (0.30, 0.0, 0.25)}
SLIDE = dict(y=(-0.09, 0.09), z=(-0.10, 0.15))
def clamp(v, lo, hi): return max(lo, min(hi, v))
def reach_with_slide(side, target):
    """best slide for this arm toward target, and the remaining stretch ratio."""
    p = PIVOT[side]; sy = clamp(target[1] - p[1], *SLIDE["y"]); sz = clamp(target[2] - p[2], *SLIDE["z"])
    d = math.dist((p[0], p[1] + sy, p[2] + sz), target); return {"slide_y": sy, "slide_z": sz, "distance": d, "stretch": max(1.0, d / ARM_LEN)}
def plan_reach(targets, body_turn_deg_options=(0, 10, 20, 30, 45, 60)):
    out = {}
    for side, tgt in targets.items():
        r = reach_with_slide(side, tgt)
        if r["stretch"] <= REACH_MAX: out[side] = dict(mode="stretch", **r); continue
        best = None                                   # rotate the body about the vertical axis (yaw turns the pivot toward the target) and try again
        for a in body_turn_deg_options:
            for sgn in (1, -1):
                th = math.radians(sgn * a); c, s = math.cos(th), math.sin(th)
                tx, ty = tgt[0] * c + tgt[1] * s, -tgt[0] * s + tgt[1] * c           # target in the turned body frame
                rr = reach_with_slide(side, (tx, ty, tgt[2]))
                if rr["stretch"] <= REACH_MAX and (best is None or a < best["turn_deg"]): best = dict(mode="turn", turn_deg=sgn * a, **rr)
        out[side] = best or dict(mode="magic", **r)
    return out
if __name__ == "__main__":
    print(plan_reach({"L": (-0.45, -0.25, 0.3), "R": (0.40, -0.25, 0.3)}))
    print(plan_reach({"L": (-0.9, -0.1, 0.3), "R": (0.9, -0.1, 0.3)}))
