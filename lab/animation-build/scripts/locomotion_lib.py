"""Pure-python foot plan for the human walk (no Blender needed). Units m / degrees. fwd = along his facing (-Y), up = +Z.
One cycle = 24 frames = two steps; a foot's phase p in [0,1): heel strike at 0, toe-off at 0.6.
foot(p) -> (ankle_fwd, ankle_up, pitch_deg)   pitch + = toes up. Ankle heights are above the ground at the flat foot (ANKLE_H)."""
import math
ANKLE_H, HEEL, BALL = 0.076, 0.07, 0.18      # ankle height; ankle->heel (back) and ankle->ball (forward) distances
STRIKE_PITCH, TOEOFF_PITCH = 12.0, 25.0     # toe up at heel strike, toe down at toe-off (deg)
LIFT = 0.07                                  # extra foot lift at mid swing
T_FLAT, T_HEELOFF, T_TOEOFF = 0.08, 0.45, 0.60
def sstep(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def rot(f, u, phi_deg):                      # rotate a vector (fwd, up) toe-up by phi
    a = math.radians(phi_deg); return f * math.cos(a) - u * math.sin(a), f * math.sin(a) + u * math.cos(a)
def foot(p, stride=1.2, c0=0.24):
    """stride = metres per cycle (body speed = stride/24 per frame), c0 = heel contact point at heel strike (ahead of the body centre)."""
    c = lambda q: c0 - stride * q            # heel contact point relative to the body while the heel/foot is planted
    if p < T_FLAT:                           # heel strike: pivot about the heel, toe comes down
        phi = STRIKE_PITCH * (1 - sstep(p / T_FLAT)); f, u = rot(HEEL, ANKLE_H, phi); return c(p) + f, u, phi
    if p < T_HEELOFF: return c(p) + HEEL, ANKLE_H, 0.0       # flat foot
    if p < T_TOEOFF:                         # heel lifts, ball stays planted
        th = TOEOFF_PITCH * sstep((p - T_HEELOFF) / (T_TOEOFF - T_HEELOFF))
        ball = c(T_HEELOFF) + HEEL + BALL - stride * (p - T_HEELOFF)
        f, u = rot(-BALL, ANKLE_H, -th); return ball + f, u, -th
    # swing
    u_ = (p - T_TOEOFF) / (1 - T_TOEOFF)
    f0, z0, p0 = foot(T_TOEOFF - 1e-6, stride, c0); f1, z1, p1 = foot(0.0, stride, c0)
    f1 += stride * 1.0 * 0   # strike point is at the cycle start (p = 0)
    s = sstep(u_ ** 0.9)
    return f0 + (f1 - f0) * s, z0 + (z1 - z0) * s + LIFT * math.sin(math.pi * u_), p0 + (p1 - p0) * sstep(u_ ** 0.6)
def planted_error(stride=1.2, c0=0.24):
    """max drift of the ankle's WORLD position (relative position + body travel) while the foot is flat on the ground."""
    ws = [foot(p / 100, stride, c0)[0] + stride * (p / 100) for p in range(int(T_FLAT * 100) + 1, int(T_HEELOFF * 100))]
    return max(ws) - min(ws)
if __name__ == "__main__":
    for p in (0, 0.04, 0.08, 0.2, 0.45, 0.5, 0.6, 0.7, 0.8, 0.9, 0.999): print(p, [round(x, 3) for x in foot(p)])
    print("planted drift", round(planted_error(), 6))
    # leg reach: hip height must exceed sqrt(L^2 - fwd^2) + ankle_up
    L = 0.818; hip = 0.887
    worst = max((foot(p / 100)[0] ** 2 + (hip - foot(p / 100)[1]) ** 2) ** 0.5 for p in range(100)); print("max hip-ankle distance (leg length 0.818):", round(worst, 3))
