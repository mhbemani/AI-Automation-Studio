#!/usr/bin/env python3
"""Performance solver (stdlib only): authored beats + narration + on-screen geometry -> per-frame rig channels.

  solver.py --work work/1 --aspect 16:9 --profile ../rig_profile_facet.json --camera-cfg ../pipeline/character.json --out work/1/performance_16x9.json
            [--frames a-b] [--selftest]

Layers (all always on, every pose is a blend, nothing is switched):
  scripted gestures  (rig_profile 'gestures': keyframe tables relative to the cue-word onset, aimed at real screen targets)
  emotion            (12 parameter sets, smoothly interpolated between beats)
  gaze               (saccade-like eyes, slower head, returns to the viewer at sentence ends / pauses, glances at the diagram)
  speech mouth       (narration amplitude envelope + emotion bias, closed in silence)
  prosody emphasis   (stressed words get a small nod / torso pulse where the script has no beat)
  blinks, idle breathing/weight shift/head drift, crown + hand follow-through (2nd-order springs)
Output channels are WORLD-aligned rotations relative to the parent bone (quaternion w,x,y,z), locations, scales: see RIG_PROFILE.md."""
import json, math, os, random, sys, argparse

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)

# ---------------------------------------------------------------- small vector / quaternion kit (tuples)
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def mul(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def length(a): return math.sqrt(dot(a, a))
def unit(a):
    n = length(a); return (a[0] / n, a[1] / n, a[2] / n) if n > 1e-12 else (0.0, 0.0, -1.0)
def lerp(a, b, k): return a + (b - a) * k
def vlerp(a, b, k): return (lerp(a[0], b[0], k), lerp(a[1], b[1], k), lerp(a[2], b[2], k))
def clamp(x, lo, hi): return max(lo, min(hi, x))
def ss(x): x = clamp(x, 0.0, 1.0); return x * x * (3 - 2 * x)                       # smoothstep
def rad(d): return d * math.pi / 180.0
def deg(r): return r * 180.0 / math.pi

QI = (1.0, 0.0, 0.0, 0.0)
def qmul(a, b):
    return (a[0] * b[0] - a[1] * b[1] - a[2] * b[2] - a[3] * b[3], a[0] * b[1] + a[1] * b[0] + a[2] * b[3] - a[3] * b[2],
            a[0] * b[2] - a[1] * b[3] + a[2] * b[0] + a[3] * b[1], a[0] * b[3] + a[1] * b[2] - a[2] * b[1] + a[3] * b[0])
def qconj(q): return (q[0], -q[1], -q[2], -q[3])
def qnorm(q):
    n = math.sqrt(sum(x * x for x in q)); return tuple(x / n for x in q) if n > 1e-12 else QI
def qaxis(axis, d):
    a = unit(axis); h = rad(d) / 2; s = math.sin(h); return (math.cos(h), a[0] * s, a[1] * s, a[2] * s)
def qrot(q, v):
    u = (q[1], q[2], q[3]); t = mul(cross(u, v), 2.0)
    return add(add(v, mul(t, q[0])), cross(u, t))
def qshort(a, b):   # shortest-arc rotation taking unit vector a to b
    a, b = unit(a), unit(b); d = dot(a, b)
    if d < -0.999999:
        ax = cross(a, (1, 0, 0)); ax = cross(a, (0, 1, 0)) if length(ax) < 1e-6 else ax
        return qaxis(ax, 180.0)
    c = cross(a, b); return qnorm((1 + d, c[0], c[1], c[2]))
def qnlerp(qs, ws):   # weighted normalised lerp with hemisphere alignment
    acc = [0.0] * 4; ref = qs[0]
    for q, w in zip(qs, ws):
        s = 1.0 if sum(x * y for x, y in zip(q, ref)) >= 0 else -1.0
        for i in range(4): acc[i] += s * w * q[i]
    return qnorm(tuple(acc))
def euler_q(yaw=0.0, pitch=0.0, roll=0.0):   # world axes: yaw about Z, pitch about X (+ = look down), roll about Y; applied roll first
    return qmul(qaxis((0, 0, 1), yaw), qmul(qaxis((1, 0, 0), pitch), qaxis((0, 1, 0), roll)))

# ---------------------------------------------------------------- keyframe tables relative to the apex
def resolve_keys(keys, H):
    out, last = [], -1e9
    for t, v in keys:
        tt = float(t) if not isinstance(t, str) else (H if t == "H" else H + float(t[2:]))
        tt = max(tt, last); out.append((tt, v)); last = tt
    return out
def kfe(pts, tau):
    if not pts: return 0.0
    if tau <= pts[0][0]: return pts[0][1]
    if tau >= pts[-1][0]: return pts[-1][1]
    for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
        if t0 <= tau <= t1: return v0 if t1 - t0 < 1e-9 else lerp(v0, v1, ss((tau - t0) / (t1 - t0)))
    return pts[-1][1]

# ---------------------------------------------------------------- 2nd-order spring (follow-through): critically-ish damped tracker
class Spring:
    def __init__(self, omega, zeta, dim): self.w, self.z, self.x, self.v = omega, zeta, [0.0] * dim, [0.0] * dim; self.init = False
    def step(self, target, dt):
        if not self.init: self.x = list(target); self.init = True
        n = max(1, int(math.ceil(dt * self.w / 0.25)))     # sub-steps keep the explicit integrator stable
        h = dt / n
        for _ in range(n):
            for i in range(len(self.x)):
                a = self.w * self.w * (target[i] - self.x[i]) - 2 * self.z * self.w * self.v[i]
                self.v[i] += a * h; self.x[i] += self.v[i] * h
        return self.x

# ---------------------------------------------------------------- camera (pinhole, square clip) + clip<->video pixel mapping
class Cam:
    def __init__(self, cfg, lens=50.0, sensor=36.0):
        a, e = rad(cfg["azimuthDeg"]), rad(cfg["elevationDeg"]); self.tz = cfg["targetZ"]
        d = max(cfg["visHeight"] * lens / sensor, 3.0 * lens / sensor)       # same rule as stagecfg.apply for a square frame
        self.C = (math.sin(a) * math.cos(e) * d, -math.cos(a) * math.cos(e) * d, math.sin(e) * d + self.tz)
        self.f = unit(sub((0, 0, self.tz), self.C)); self.r = unit(cross(self.f, (0, 0, 1))); self.u = cross(self.r, self.f)
        self.th = sensor / 2 / lens
    def uv(self, P):   # world point -> clip uv (0..1, v down)
        v = sub(P, self.C); z = dot(v, self.f)
        return (0.5 + 0.5 * dot(v, self.r) / z / self.th, 0.5 - 0.5 * dot(v, self.u) / z / self.th)
    def ray(self, uv):   # clip uv -> unit direction from the camera
        x = (uv[0] - 0.5) * 2 * self.th; y = (0.5 - uv[1]) * 2 * self.th
        return unit(add(add(self.f, mul(self.r, x)), mul(self.u, y)))
    def to_viewer(self, P): return unit(sub(self.C, P))

# ---------------------------------------------------------------- the solver
class Solver:
    def __init__(self, work, aspect, profile, camcfg, seed=11):
        self.P = profile; self.G = profile["geometry"]; self.aspect = aspect
        j = lambda n: json.load(open(os.path.join(work, n)))
        self.project = j("project.json"); self.words = j("words.json"); self.beats_in = j("beats.json")["beats"]
        self.geom = j("geometry.json")[aspect]; self.fps = self.project["fps"]; self.N = self.geom["frames"]
        self.cam = Cam(camcfg["camera"], self.G["camera"]["lens"], self.G["camera"]["sensor"])
        self.framing = self.project["character"]["framing"]; self.rng = random.Random(seed)
        self.wav = os.path.join(work, "narration.wav"); self.report = {"adjusted": [], "autoBeats": [], "hand": []}
        self.sc_of_frame = []
        for f in range(self.N):
            k = 0
            for s in self.geom["scenes"]:
                if s["startFrame"] <= f: k = s["index"]
            self.sc_of_frame.append(k)
        self.trace = set(); self.trace_out = []
        self.mouth_env = self._mouth()
        self.prepare_beats(); self.prepare_prosody(); self.prepare_gaze_masks(); self.prepare_blinks()

    # ---- narration-driven layers
    def _mouth(self):
        import lipsync
        env = lipsync.envelope(self.wav, self.fps); gate = self.P["mouth"]["gate"]
        return [0.0 if (v < gate) else v for v in env] + [0.0] * (self.N + 2)

    def assign_hands(self):
        """main hand per gesture: the hand on the side of the target; when the target is ambiguous (viewer / self / centred text) alternate and avoid a hand that is busy with an earlier gesture"""
        busy = {"L": -1e9, "R": -1e9}; last = "L"
        for b in self.beats:
            arms = self.P["gestures"][b["gesture"]].get("arms", {}); start = b["apex"] - b["lead"]; end = b["apex"] + b["H"] + 0.45
            if "B" in arms and "M" not in arms: busy["L"] = busy["R"] = max(busy["L"], end, busy["R"]); continue
            if "M" not in arms: continue
            fa = int(clamp(round(b["apex"] * self.fps), 0, self.N - 1)); tp = self.target_px(b["target"], b["si"], fa); r = self.geom["rect"][fa]; cx = r[0] + r[2] * self.framing["centerX"]
            if b["hand"] in ("L", "R"): side = b["hand"]
            elif tp is not None and abs(tp[0] - cx) > 0.12 * r[2]: side = "R" if tp[0] > cx else "L"
            else:
                side = "L" if last == "R" else "R"; other = "L" if side == "R" else "R"
                if busy[side] > start and busy[other] <= start: side = other
            b["side"] = side; last = side; busy[side] = max(busy[side], end)
            self.report["hand"].append({"scene": b["scene"], "t": round(b["t"], 2), "gesture": b["gesture"], "hand": side})

    # ---- beats -> gesture instances (lead-in, 0.8 s rule, at least one gesture per sentence)
    def _init_beat(self, b, i):
        g = self.P["gestures"][b["gesture"]]; b["i"] = i; b.pop("_k", None)
        H = b["hold"] if b.get("hold") is not None else g.get("hold", 0.5)
        if b["gesture"] == "track":   # hold the aim for the packet's flight
            pk = self.geom["scenes"][b["si"]]["packets"][int(b["target"].split(":")[1])]
            H = max(0.3, (pk["endFrame"] - pk["startFrame"]) / self.fps)
        b["H"] = H; b["side"] = None
        b["lead"] = max(0.0, -self.first_key(b, g))
        b["apex"] = max(b["t"], b["lead"]); b["shift"] = round(b["apex"] - b["t"], 3) or None   # no gesture can start before frame 0
        b["amp"] = self.P["emotions"][b["emotion"]]["amp"] * (0.45 + 0.55 * b["amp_i"])
    def prepare_beats(self):
        R = self.P["rules"]; beats = [dict(b) for b in self.beats_in]; beats.sort(key=lambda b: b["t"])
        for i, b in enumerate(beats): b["amp_i"] = b["intensity"]; self._init_beat(b, i)
        prev_big = None
        for b in beats:   # no two big gestures closer than 0.8 s: the second is toned down (aims keep hitting the target; amplitude and extras shrink)
            if prev_big is not None and b["apex"] - prev_big["apex"] < R["minGestureGapSec"]:
                b["amp_i"] = b["intensity"] * R["reduceFactor"]; b["reduced"] = True
                self.report["adjusted"].append({"scene": b["scene"], "gesture": b["gesture"], "t": b["t"], "gapSec": round(b["apex"] - prev_big["apex"], 3), "intensity": b["intensity"], "effective": round(b["amp_i"], 3), "after": prev_big["gesture"]})
            b["big"] = b["amp_i"] > R["bigAbove"]
            if b["big"]: prev_big = b
        by_scene = {}
        for w in self.words: by_scene.setdefault(w["scene"], []).append(w)
        for sid, ws in by_scene.items():   # at least one gesture per sentence: a light beat on the first stressed word of any sentence without one
            s0 = 0
            for k, w in enumerate(ws):
                if w["sentenceEnd"] or k == len(ws) - 1:
                    a, z = ws[s0]["at"], w["to"]
                    if not any(a - 0.3 <= b["apex"] <= z + 0.2 for b in beats):
                        pick = max(ws[s0:k + 1], key=lambda x: (len("".join(c for c in x["w"] if c.isalpha())) > 3) * 10 + (x["to"] - x["at"]))
                        nb = {"scene": sid, "si": pick["si"], "j": -1, "t": pick["at"], "cue": pick["w"], "gesture": "beat", "target": "viewer", "emotion": beats[0]["emotion"], "intensity": 0.4, "hold": None, "hand": "auto", "amp_i": 0.4, "auto": True, "big": False}
                        beats.append(nb); self.report["autoBeats"].append({"scene": sid, "t": pick["at"], "word": pick["w"]})
                    s0 = k + 1
        beats.sort(key=lambda b: b["t"])
        for i, b in enumerate(beats): self._init_beat(b, i)
        self.beats = beats; self.events = []; self.assign_hands()

    # ---- prosody: stressed content words nod/pulse where no beat is scripted
    def prepare_prosody(self):
        pp = self.P["prosody"]; self.pulses = []
        stop = set("a an the and or but so to of in on at it its is are was be been being that this these those you your yours i we they he she them his her their our us with for from as by if then than into out up just how what when why who".split())
        env = self.mouth_env; sc = []
        for k, w in enumerate(self.words):
            f0 = int(w["at"] * self.fps); f1 = max(f0 + 1, int(min(w["to"], w["at"] + 0.45) * self.fps))
            loud = max(env[f0:f1 + 1] or [0.0]); dur = (w["to"] - w["at"]) / max(1, len(w["w"]))
            if len("".join(c for c in w["w"].lower() if c.isalpha())) >= pp["minWordLen"] and "".join(c for c in w["w"].lower() if c.isalpha()) not in stop:
                sc.append((loud + 4.0 * dur, w))
        if not sc: return
        sc.sort(key=lambda x: -x[0]); keep = sc[:max(1, int(len(sc) * pp["topShare"]))]; keep.sort(key=lambda x: x[1]["at"]); last = -9.0
        for _, w in keep:
            t = w["at"]
            if t - last < pp["minGapSec"]: continue
            if any(abs(t - b["apex"]) < pp["beatClearSec"] for b in self.beats): continue
            self.pulses.append(t); last = t

    def prepare_gaze_masks(self):
        # pauses: from a sentence end to the next word onset (or scene end) the gaze goes back to the viewer
        G = self.P["gaze"]; self.pause = []
        for k, w in enumerate(self.words):
            nxt = next((x for x in self.words[k + 1:] if x["scene"] == w["scene"]), None)
            gap = (nxt["at"] - w["to"]) if nxt else 9.0
            end = nxt["at"] if nxt else w["to"] + 0.35
            if (w["sentenceEnd"] or gap >= G["pauseReturn"]) and end - (w["to"] + 0.05) >= 0.25: self.pause.append((w["to"] + 0.05, end))
        # glances at the diagram while explaining (flow scenes only, where no gesture already looks around)
        self.glances = []
        t_last = -9.0
        for w in self.words:
            sc = self.geom["scenes"][w["si"]]
            if sc["type"] != "flow": continue
            if w["at"] - t_last < G["glanceEvery"]: continue
            if any(b["apex"] - 0.6 <= w["at"] <= b["apex"] + b["H"] + 0.8 for b in self.beats): continue
            if w["clauseEnd"] or w["sentenceEnd"]: continue
            self.glances.append((w["at"], w["at"] + G["glanceLen"], w["si"])); t_last = w["at"]

    def prepare_blinks(self):
        B = self.P["blink"]; t = self.rng.uniform(0.9, 1.8); self.blinks = []
        T = self.N / self.fps
        while t < T: self.blinks.append(t); t += self.rng.uniform(B["min"], B["max"])

    # ---- target lookup
    def target_px(self, spec, si, f):
        sc = self.geom["scenes"][si]; kind, _, arg = spec.partition(":")
        if kind == "viewer": return None
        if kind == "self":   # the character's chest, projected through the clip placement of this frame
            u, v = self.cam.uv(tuple(self.G["chest"])); r = self.geom["rect"][f]; return (r[0] + u * r[2], r[1] + v * r[2])
        if kind == "diagram": return tuple(sc["diagram"])
        if kind == "node": return tuple(sc["nodes"][arg])
        if kind == "text": l = sc["text"][int(arg)]; return (l["cx"], l["cy"])
        if kind == "packet":
            pk = sc["packets"][int(arg)]; i = clamp(f - pk["startFrame"], 0, len(pk["xy"]) - 1); return tuple(pk["xy"][int(i)])
        raise ValueError(spec)
    def px_to_uv(self, px, f):
        r = self.geom["rect"][f]; return ((px[0] - r[0]) / r[2], (px[1] - r[1]) / r[2])

    # ---- kinematics helpers
    def sph(self, sx, theta, psi):   # arm direction: theta from hanging-down, psi azimuth (0 outward, 90 forward = -Y)
        th, ps = rad(theta), rad(psi)
        return (sx * math.sin(th) * math.cos(ps), -math.sin(th) * math.sin(ps), -math.cos(th))
    def aim_dir(self, S, uv_target, phi, f0=None):
        cam = self.cam; s0 = cam.uv(S); L = self.G["armLen"] + self.G["handLen"]
        dx, dy = uv_target[0] - s0[0], -(uv_target[1] - s0[1]); alpha = math.atan2(dy, dx); ph = rad(clamp(phi, 0, 88))
        d = None
        for _ in range(5):
            dd = add(mul(add(mul(cam.r, math.cos(alpha)), mul(cam.u, math.sin(alpha))), math.cos(ph)), mul(cam.f, -math.sin(ph)))
            d = unit(dd); p1 = cam.uv(add(S, mul(d, L))); beta = math.atan2(-(p1[1] - s0[1]), p1[0] - s0[0])
            err = math.atan2(math.sin(math.atan2(dy, dx) - beta), math.cos(math.atan2(dy, dx) - beta)); alpha += err
        return d
    def ik2(self, S, Pt, hint):
        l1, l2 = self.G["armLen"], self.G["handLen"]; v = sub(Pt, S); D = clamp(length(v), abs(l1 - l2) + 1e-3, l1 + l2 - 1e-3); e = unit(v)
        a = (l1 * l1 - l2 * l2 + D * D) / (2 * D); h = math.sqrt(max(l1 * l1 - a * a, 0.0))
        p = sub(hint, mul(e, dot(hint, e))); p = unit(p) if length(p) > 1e-6 else (0, 0, -1)
        W = add(add(S, mul(e, a)), mul(p, h)); return unit(sub(W, S)), unit(sub(add(S, mul(e, D)), W))

    # ================================================================ per-frame solve
    def solve(self, frames=None):
        P, N, fps = self.P, self.N, self.fps; lim = P["limits"]; geo = self.G
        f0, f1 = frames if frames else (0, N)
        out = {k: [] for k in ("root", "torso", "head", "crown", "eye_L", "eye_R", "mouth_L", "mouth_R", "brow_L", "brow_R", "arm_L", "arm_R", "hand_L", "hand_R", "leg_L", "leg_R")}
        crown = Spring(P["spring"]["crownOmega"], P["spring"]["crownZeta"], 3)
        handS = {"L": Spring(P["spring"]["handOmega"], P["spring"]["handZeta"], 3), "R": Spring(P["spring"]["handOmega"], P["spring"]["handZeta"], 3)}
        gaze_eye = None; gaze_head = None; dbg = []
        emo_keys = self.emotion_keys(); last_blink_t = -9.0; hist = []
        rest = {s: (self.sph(sx, *geo["restArm"]), self.sph(sx, *geo["restHand"])) for s, sx in (("L", -1), ("R", 1))}
        st_phase = [self.rng.uniform(0, 6.28) for _ in range(8)]
        for f in range(f0, f1):
            t = f / fps; si = self.sc_of_frame[f]; dt = 1.0 / fps
            E = self.emotion_at(emo_keys, t); amp_e = E["amp"]
            # ---- active gestures at this frame
            act = []
            for b in self.beats:
                g = P["gestures"][b["gesture"]]; tau = t - b["apex"]
                lo = b["apex"] + self.first_key(b, g); hi = b["apex"] + self.last_key(b, g)
                if lo - 0.05 <= t <= hi + 0.05: act.append((b, g, tau))
            # ---- layered torso / head / root contributions
            tor = [0.0, 0.0, 0.0]; hd = [0.0, 0.0, 0.0]; rt = [0.0, 0.0, 0.0]; sq = 0.0; rise = 0.0; face = {"smile": 0.0, "browRaise": 0.0}
            gz_w = 0.0; gz_dirs = []
            tgt_cache = {}
            for b, g, tau in act:
                amp = b["amp"]; H = b["H"]; keys = self.keys(b, g)
                tp = tgt_cache.get(b["i"])
                if tp is None: tp = tgt_cache[b["i"]] = self.target_px(b["target"], b["si"], f)
                if "torso" in g:
                    T_ = g["torso"]
                    if "pitch" in T_: tor[0] += kfe(keys[(b["i"], "torso", "pitch")], tau) * amp
                    if "roll" in T_: tor[2] += kfe(keys[(b["i"], "torso", "roll")], tau) * amp
                    if "twist" in T_ and tp is not None:
                        r = self.geom["rect"][f]; side = 1.0 if tp[0] > r[0] + r[2] * self.framing["centerX"] else -1.0
                        tor[1] += side * T_.get("twistDeg", 0) * amp * kfe(keys[(b["i"], "torso", "twist")], tau)
                if "head" in g:
                    Hh = g["head"]
                    if "pitch" in Hh: hd[0] += kfe(keys[(b["i"], "head", "pitch")], tau) * amp
                    if "yaw" in Hh: hd[1] += kfe(keys[(b["i"], "head", "yaw")], tau) * amp
                    if "roll" in Hh: hd[2] += kfe(keys[(b["i"], "head", "roll")], tau) * amp
                    if "gaze" in Hh:
                        w = kfe(keys[(b["i"], "head", "gaze")], tau)
                        if w > 1e-3: gz_dirs.append((w, tp)); gz_w = max(gz_w, w)
                if "root" in g:
                    for ax, idx in (("x", 0), ("y", 1), ("z", 2)):
                        if ax in g["root"]: rt[idx] += kfe(keys[(b["i"], "root", ax)], tau) * amp
                if "shoulder" in g: rise += kfe(keys[(b["i"], "shoulder", "rise")], tau) * amp
                if "face" in g:
                    for k in ("smile", "browRaise"):
                        if k in g["face"]: face[k] += kfe(keys[(b["i"], "face", k)], tau) * amp
            # ---- prosody pulses (stress where there is no beat)
            pl = P["prosody"]["pulseLen"]; pulse = 0.0
            for tp_ in self.pulses:
                x = (t - tp_) / pl
                if 0 <= x <= 1: pulse = max(pulse, math.sin(math.pi * x) ** 2)
            hd[0] += P["prosody"]["nodDeg"] * pulse * amp_e; tor[0] += P["prosody"]["leanDeg"] * pulse * amp_e; face["browRaise"] += P["prosody"]["browRaise"] * pulse
            # ---- idle: breathing, weight shift (torso roll/lean, never sliding feet), head drift
            I = P["idle"]; sp = E["idleSpeed"]
            breath = math.sin(2 * math.pi * t * sp / I["breathPeriod"])
            sq += I["breathAmp"] * breath
            tor[2] += I["swayRoll"] * math.sin(2 * math.pi * t * sp / I["swayPeriod"] + st_phase[0])
            tor[0] += I["swayLean"] * math.sin(2 * math.pi * t * sp / (I["swayPeriod"] * 0.63) + st_phase[1])
            rt[2] += 0.006 * breath
            for k, (fr, ay, ap) in enumerate(I["headNoise"]):
                hd[1] += ay * math.sin(2 * math.pi * fr * sp * t + st_phase[2 + k]); hd[0] += ap * 0.6 * math.sin(2 * math.pi * fr * 0.7 * sp * t + st_phase[5 + k % 3])
            # ---- emotion posture
            tor[0] += E["lean"]; hd[2] += E["headRoll"]
            tor = [clamp(tor[0], *lim["torsoLean"]), clamp(tor[1], *lim["torsoTwist"]), clamp(tor[2], *lim["torsoRoll"])]
            Qt = euler_q(tor[1], tor[0], tor[2])
            Troot = tuple(rt)
            ptor = add(Troot, geo["torsoPivot"])
            def body(p): return add(Troot, add(geo["torsoPivot"], qrot(Qt, sub(p, geo["torsoPivot"]))))
            # ---- gaze (viewer by default; beat target when a gesture asks, back to the viewer in pauses)
            hp0 = body(geo["headPivot"]); Eye0 = add(hp0, qrot(Qt, sub(geo["eyeMid"], geo["headPivot"]))); uv_eye = self.cam.uv(Eye0)
            vdir = self.cam.to_viewer(Eye0)
            yaw_v = P["viewer"]["headYaw"]
            pm = 1.0
            for a, z in self.pause:
                if a <= t <= z: pm = min(pm, 1 - ss((t - a) / 0.12))
                elif z < t <= z + 0.2: pm = min(pm, ss((t - z) / 0.2))
            yg = yaw_v; pg = 0.0
            wsum = sum(w for w, _ in gz_dirs)
            gl = 0.0
            for a, z, gsi in self.glances:
                if a - 0.1 <= t <= z + 0.2 and gsi == si: gl = max(gl, min(ss((t - (a - 0.1)) / 0.2), 1 - ss((t - z) / 0.2)))
            goals = []
            for w, tp in gz_dirs:
                if tp is None: continue
                goals.append((w * pm, self.px_to_uv(tp, f)))
            if gl > 0: goals.append((gl * P["gaze"]["glanceAmount"], self.px_to_uv(tuple(self.geom["scenes"][si]["diagram"]), f)))
            for w, uvt in goals:
                dist = math.hypot(uvt[0] - uv_eye[0], uvt[1] - uv_eye[1]); kap = min(P["gaze"]["maxTurnDeg"], P["gaze"]["turnPerClipUnit"] * dist)
                alpha = math.atan2(-(uvt[1] - uv_eye[1]), uvt[0] - uv_eye[0])
                gdir = unit(add(mul(vdir, math.cos(rad(kap))), mul(add(mul(self.cam.r, math.cos(alpha)), mul(self.cam.u, math.sin(alpha))), math.sin(rad(kap)))))
                yt = deg(math.atan2(gdir[0], -gdir[1])); pt = deg(math.asin(clamp(gdir[2], -1, 1)))
                yg = lerp(yg, yt, clamp(w, 0, 1)); pg = lerp(pg, pt, clamp(w, 0, 1))
            if gaze_eye is None: gaze_eye = [yg, pg]; gaze_head = [yg * P["viewer"]["headShare"], pg * P["viewer"]["headShare"]]
            def lp(cur, goal, tau): k = 1 - math.exp(-dt / tau); return [cur[0] + (goal[0] - cur[0]) * k, cur[1] + (goal[1] - cur[1]) * k]
            G_ = P["gaze"]
            gaze_eye = lp(gaze_eye, [yg, pg], G_["tauEye"])
            gaze_head = lp(gaze_head, [yg * P["viewer"]["headShare"] if goals else yg * P["viewer"]["headShare"], pg * P["viewer"]["headShare"]], G_["tauHead"])
            # blink: scheduled + on a large gaze shift (goal moved > afterShift deg within 6 frames)
            hist.append(yg); big_shift = len(hist) > 6 and abs(yg - hist[-7]) > P["blink"]["afterShift"] and (t - last_blink_t) > 1.0
            if big_shift: self.blinks.append(t + 0.05); self.blinks.sort(); last_blink_t = t + 0.05
            blink = 1.0
            for bt in self.blinks:
                x = t - bt
                if 0 <= x <= P["blink"]["close"] + P["blink"]["open"]:
                    blink = 1 - (ss(x / P["blink"]["close"]) if x < P["blink"]["close"] else 1 - ss((x - P["blink"]["close"]) / P["blink"]["open"])); last_blink_t = bt
            # head total world rotation from gaze + gesture adds + emotion
            head_yaw = clamp(gaze_head[0] + hd[1], *lim["headYaw"]); head_pitch = clamp(-(gaze_head[1] + E["headPitch"]) + hd[0], -lim["headPitch"][1], -lim["headPitch"][0])
            head_roll = clamp(hd[2], *lim["headRoll"])
            Rh = euler_q(head_yaw, head_pitch, head_roll); q_head = qmul(qconj(Qt), Rh)
            resid_y = gaze_eye[0] - head_yaw; resid_p = gaze_eye[1] + head_pitch
            es = lim["eyeShift"]; ex = clamp(0.0098 * resid_y + E["lookX"], -es, es); ez = clamp(0.0098 * resid_p + E["lookY"], -es, es)
            # ---- crown follow-through (overlap): lag of head roll/yaw and body bob
            cin = [head_roll * 0.6 + tor[2], head_yaw * 0.25 + tor[1], rt[2] * 40.0]; cs = crown.step(cin, dt); cg = P["spring"]["crownGain"]
            crown_q = euler_q(-cg * 2.5 * (cs[1] - cin[1]), -cg * 0.6 * (cs[2] - cin[2]), -cg * 2.5 * (cs[0] - cin[0]))   # crown trails the head (overlap), bends opposite to quick moves
            # ---- arms
            arm_q = {}; hand_q = {}; hand_scale = {}
            sh_off = (0.0, 0.0, rise)
            for side, sx in (("L", -1), ("R", 1)):
                S = body(add((sx * geo["shoulder"][0], geo["shoulder"][1], geo["shoulder"][2]), sh_off))
                cmds = []   # (weight, da, dh, fist)
                for b, g, tau in act:
                    arms = g.get("arms")
                    if not arms: continue
                    keys = self.keys(b, g); H = b["H"]; amp = b["amp"]
                    for slot in ("M", "O", "B"):
                        if slot not in arms: continue
                        if slot == "B": pass
                        elif (slot == "M") != (b["side"] == side): continue
                        spec = arms[slot]; w = kfe(keys[(b["i"], "arm" + slot, "w")], tau)
                        if w <= 1e-4: continue
                        strict = b["gesture"] in ("point_at", "track")
                        red = b.get("reduced") and not strict and spec["mode"] != "aim"
                        low = red or slot == "O"   # supporting (O) arm poses and toned-down gestures never override a busy arm
                        da_, dh_ = self.arm_cmd(b, spec, slot, keys, tau, side, sx, S, Qt, Troot, f, amp)
                        fi = kfe(keys[(b["i"], "arm" + slot, "fist")], tau) if (b["i"], "arm" + slot, "fist") in keys else 0.0
                        cmds.append((w, da_, dh_, fi, 0 if low else 1, b["apex"], spec["mode"] == "aim"))
                # idle arm sway
                da0, dh0 = rest[side]
                sway = I["armSway"] * math.sin(2 * math.pi * t * sp / 3.1 + st_phase[3] + (0 if side == "L" else 1.7))
                da0 = self.sph(sx, geo["restArm"][0] + sway, geo["restArm"][1]); dh0 = self.sph(sx, geo["restHand"][0] + sway * 1.3, geo["restHand"][1])
                # composite the commands "over" the rest pose, oldest first; toned-down non-aim gestures go underneath (their weight is halved too),
                # so a newer gesture crossfades in smoothly and an aimed gesture always ends exactly on its target
                cmds.sort(key=lambda c: (c[4], c[5]))
                qa_, qh_, fist = qshort((0, 0, -1), da0), qshort((0, 0, -1), dh0), 0.0
                for w, ca, ch, fi, rank, ap, _aim in cmds:
                    qa_ = qnlerp([qa_, qshort((0, 0, -1), ca)], [1 - w, w]); qh_ = qnlerp([qh_, qshort((0, 0, -1), ch)], [1 - w, w]); fist = lerp(fist, fi, w)
                qA, qH = qa_, qh_; da = qrot(qA, (0, 0, -1)); dh = qrot(qH, (0, 0, -1))
                if f in self.trace: self.trace_out.append({"f": f, "side": side, "cmds": [{"w": round(c[0], 3), "rank": c[4], "apex": round(c[5], 2), "da": [round(x, 3) for x in c[1]], "dh": [round(x, 3) for x in c[2]]} for c in cmds], "da": [round(x, 3) for x in da], "dh": [round(x, 3) for x in dh]})
                # hand follow-through: the hand trails the arm (spring on the arm direction)
                lag = handS[side].step(list(da), dt); aimw = max([c[0] for c in cmds if c[6]] or [0.0]); trail = mul(sub(lag, da), P["spring"]["handGain"] * 2.2 * (1 - clamp(aimw, 0, 1)))   # an aimed finger stays on its line (no follow-through while aiming)
                dh = unit(add(dh, trail))
                arm_q[side] = qmul(qconj(Qt), qshort((0, 0, -1), da)); hand_q[side] = qmul(qconj(qshort((0, 0, -1), da)), qshort((0, 0, -1), dh))
                hand_scale[side] = 1.0 - 0.34 * clamp(fist, 0, 1)
                arm_loc = (0.0, 0.0, rise)
                out["arm_" + side].append({"q": arm_q[side], "l": arm_loc})
                out["hand_" + side].append({"q": hand_q[side], "s": (hand_scale[side], hand_scale[side], 1.0 - 0.15 * clamp(fist, 0, 1))})
            # ---- face
            op = clamp((self.mouth_env[f] if f < len(self.mouth_env) else 0.0) * (1.15 if E["smile"] > 0.8 else 1.0), 0, 1)
            fc = face_channels(P, E, op, blink, ex, ez, face["smile"], face["browRaise"])
            for k, v in fc.items(): out[k].append(v)
            out["root"].append({"l": Troot, "s": (1 / math.sqrt(1 + sq), 1 / math.sqrt(1 + sq), 1 + sq)})
            out["torso"].append({"q": Qt, "s": (1.0, 1.0, 1.0)})
            out["head"].append({"q": q_head})
            out["crown"].append({"q": crown_q})
            for side in ("L", "R"): out["leg_" + side].append({"l": (-Troot[0], -Troot[1], 0.0)})
            dbg.append({"f": f, "gaze_eye": [round(gaze_eye[0], 2), round(gaze_eye[1], 2)], "head_yaw": round(head_yaw, 2), "act": [b["gesture"] for b, _, _ in act]})
        self.dbg = dbg
        return out

    # ---- helpers used by solve()
    def keys(self, b, g):
        if "_k" in b: return b["_k"]
        K = {}; H = b["H"]; i = b["i"]
        for part in ("head", "torso", "root", "shoulder", "face"):
            for ch, kk in g.get(part, {}).items():
                if isinstance(kk, list) and kk and isinstance(kk[0], list): K[(i, part, ch)] = resolve_keys(kk, H)
        for slot, spec in g.get("arms", {}).items():
            for ch in ("w", "dphi", "dtheta", "dhand", "fist", "dtip"):
                if ch in spec: K[(i, "arm" + slot, ch)] = resolve_keys(spec[ch], H)
            if "osc" in spec: K[(i, "arm" + slot, "oscw")] = resolve_keys(spec["osc"]["w"], H)
        b["_k"] = K; return K
    def first_key(self, b, g):
        K = self.keys(b, g); return min([p[0][0] for p in K.values() if p] or [-0.3])
    def last_key(self, b, g):
        K = self.keys(b, g); return max([p[-1][0] for p in K.values() if p] or [0.3])

    def arm_cmd(self, b, spec, slot, keys, tau, side, sx, S, Qt, Troot, f, amp):
        geo = self.G; i = b["i"]; mode = spec["mode"]; g = self.P["gestures"][b["gesture"]]
        if mode == "aim":
            tp = self.target_px(b["target"] if spec.get("target") != "viewer" else "viewer", b["si"], f)
            r = self.geom["rect"][f]
            if tp is None:   # viewer: aim up and slightly inward from the shoulder, mostly toward the camera
                s0 = self.cam.uv(S); uvt = (s0[0] - sx * 0.03, s0[1] - 0.10)
            else:
                uvt = self.px_to_uv(tp, f)
                if "sweep" in spec:   # open-palm sweep across the diagram during the hold
                    du, dv = spec["sweep"][0], spec["sweep"][1]; uvt = (uvt[0] + du * (2 * clamp((tau + 0.1) / max(b["H"], 0.3), 0, 1) - 1), uvt[1] + dv)
            phi = spec["phi"] + (kfe(keys[(i, "arm" + slot, "dphi")], tau) * amp if (i, "arm" + slot, "dphi") in keys else 0.0)
            da = self.aim_dir(S, uvt, phi); dh = da
            hb = spec.get("handBend", 0.0)
            if hb:   # palm up: hand tilts up from the arm direction (in the plane of arm and the vertical)
                dh = unit(add(mul(da, math.cos(rad(hb))), mul((0, 0, 1), math.sin(rad(hb)))))
            if (i, "arm" + slot, "dhand") in keys: dh = unit(add(dh, mul((0, 0, -1), math.sin(rad(kfe(keys[(i, "arm" + slot, "dhand")], tau) * amp)))))
            return da, dh
        if mode == "pose":
            th, ps = spec["pose"]; dth = kfe(keys[(i, "arm" + slot, "dtheta")], tau) * amp if (i, "arm" + slot, "dtheta") in keys else 0.0
            da = self.sph(sx, th + dth, ps); hth, hps = spec.get("hand", spec["pose"]); dhn = kfe(keys[(i, "arm" + slot, "dhand")], tau) * amp if (i, "arm" + slot, "dhand") in keys else dth
            dh = self.sph(sx, hth + dhn, hps)
            if "osc" in spec:   # hand swings side to side in the screen plane (wave)
                o = spec["osc"]; ow = kfe(keys[(i, "arm" + slot, "oscw")], tau)
                ang = o["amp"] * amp * ow * math.sin(2 * math.pi * o["hz"] * tau); dh = qrot(qaxis((0, 1, 0), ang), dh)
            return da, dh
        if mode == "ik":
            tip = list(spec["tip"]); dtp = kfe(keys[(i, "arm" + slot, "dtip")], tau) * amp if (i, "arm" + slot, "dtip") in keys else 0.0
            tip = (sx * tip[0], tip[1], tip[2] + dtp)
            if "osc" in spec:
                o = spec["osc"]; ow = kfe(keys[(i, "arm" + slot, "oscw")], tau); ph = 2 * math.pi * o["hz"] * tau; a = o["amp"] * amp * ow
                if o["kind"] == "tip_xz": tip = (tip[0] + a * math.sin(ph) * sx, tip[1], tip[2] + a * math.cos(ph * 0.9 + (0 if sx > 0 else 2.4)))
                elif o["kind"] == "tip_z_alt": tip = (tip[0], tip[1], tip[2] + a * math.sin(ph) * (1 if sx > 0 else -1))
            hint = (sx * spec["bend"][0], spec["bend"][1], spec["bend"][2])
            Pw = add(Troot, add(geo["torsoPivot"], qrot(Qt, sub(tip, geo["torsoPivot"]))))
            return self.ik2(S, Pw, qrot(Qt, hint))
        raise ValueError(mode)

    # ---- emotion keyframes: the first beat's emotion holds from t=0; each later one fades in around its apex
    def emotion_keys(self):
        ks = []
        for b in self.beats:
            if b.get("auto"): continue
            ks.append((b["apex"], b["emotion"]))
        ks.sort(); return ks
    def emotion_at(self, ks, t):
        EM = self.P["emotions"]
        if not ks: return dict(EM["friendly"])
        cur = ks[0][1]; prev = ks[0][1]; k_t = -1e9
        for ta, name in ks:
            if t >= ta - 0.35: prev, cur, k_t = cur, name, ta - 0.35
        if t < ks[0][0] - 0.35: return dict(EM[ks[0][1]])
        a, b = EM[prev], EM[cur]; u = ss((t - k_t) / 0.6)
        return {k: lerp(a[k], b[k], u) for k in a if not k.startswith("_")}

def face_channels(P, E, op, blink, ex, ez, smile_add=0.0, brow_add=0.0):
    """emotion parameters + mouth opening -> eye / mouth / brow channels (shared with the emotion-sheet tool)"""
    lim = P["limits"]; M = P["mouth"]; sm = clamp(E["smile"] + smile_add, -1, 1)
    mw = E["mouthWidth"] * (1 + M["widthOpen"] * op); tilt = sm * M["smileTilt"]; mo = lerp(M["openMin"], 1.0, op)
    eye_open = clamp(E["eyeOpen"] * (1 - 0.55 * E["squint"]), 0.12, 1.4) * blink; eye_tilt = E["squint"] * 16.0
    br = clamp(E["browRaise"] + brow_add, -0.5, 1.0); o = {}
    for side, sx in (("L", -1), ("R", 1)):
        o["eye_" + side] = {"l": (ex, 0.0, ez), "s": (1.0, 1.0, eye_open), "q": qaxis((0, 1, 0), sx * eye_tilt)}
        o["mouth_" + side] = {"s": (mw, 1.0, mo), "q": qaxis((0, 1, 0), (-sx) * tilt), "l": (0.0, 0.0, 0.012 * sm)}
        o["brow_" + side] = {"l": (0.0, 0.0, br * lim["browRaise"] - 0.012 * (1 - blink)), "q": qaxis((0, 1, 0), sx * E["browTilt"])}
    return o

def to_json(solver, out, f0):
    ch = {}
    for bone, arr in out.items():
        ch[bone] = {}
        for key in ("q", "l", "s"):
            if arr and key in arr[0]: ch[bone][key] = [[round(x, 5) for x in a[key]] for a in arr]
    return ch

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work"); ap.add_argument("--aspect", default="16:9"); ap.add_argument("--profile"); ap.add_argument("--camera-cfg"); ap.add_argument("--out")
    ap.add_argument("--frames"); ap.add_argument("--trace"); ap.add_argument("--selftest", action="store_true"); a = ap.parse_args()
    if a.selftest: return selftest()
    prof = json.load(open(a.profile)); cam = json.load(open(a.camera_cfg))
    S = Solver(a.work, a.aspect, prof, cam)
    if a.trace: S.trace = set(int(x) for x in a.trace.split(","))
    fr = tuple(int(x) for x in a.frames.split("-")) if a.frames else None
    out = S.solve(fr); f0 = fr[0] if fr else 0
    for b in S.beats:   # resolved numbers for the verification tools
        fa = int(clamp(round(b["apex"] * S.fps), 0, S.N - 1)); b["apexFrame"] = fa; tp = S.target_px(b["target"], b["si"], fa); b["targetApex"] = list(tp) if tp else None
        fm = int(clamp(round((b["apex"] + b["H"] / 2) * S.fps), 0, S.N - 1)); b["midFrame"] = fm; tm = S.target_px(b["target"], b["si"], fm); b["targetMid"] = list(tm) if tm else None
        b["onsetFrame"] = round(b["t"] * S.fps)
    res = {"fps": S.fps, "aspect": a.aspect, "frames": S.N, "f0": f0, "count": len(out["root"]), "channels": to_json(S, out, f0),
           "beats": [{k: b.get(k) for k in ("scene", "si", "j", "t", "apex", "cue", "gesture", "target", "emotion", "intensity", "amp_i", "H", "side", "reduced", "auto", "shift", "lead", "apexFrame", "midFrame", "onsetFrame", "targetApex", "targetMid")} for b in S.beats],
           "report": S.report, "pulses": S.pulses, "glances": S.glances, "blinks": S.blinks, "debug": S.dbg[:: 5]}
    json.dump(res, open(a.out, "w"));
    if a.trace: print("TRACE " + json.dumps(S.trace_out))
    print("solved %s: %d frames, %d beats (%d auto, %d toned down), %d prosody pulses, %d glances, %d blinks -> %s" % (a.aspect, res["count"], len(S.beats), len(S.report["autoBeats"]), len(S.report["adjusted"]), len(S.pulses), len(S.glances), len(S.blinks), a.out))

def selftest():
    # kinematics + keyframe sanity (no files needed)
    assert abs(kfe(resolve_keys([[-0.2, 0], [0, 1], ["H", 1], ["H+0.4", 0]], 0.5), 0.0) - 1.0) < 1e-9
    assert kfe(resolve_keys([[-0.2, 0], [0, 1]], 0.5), -0.3) == 0
    q = qshort((0, 0, -1), (1, 0, 0)); v = qrot(q, (0, 0, -1)); assert abs(v[0] - 1) < 1e-9
    assert abs(length(qrot(euler_q(30, 10, 5), (0, -1, 0))) - 1) < 1e-9
    cam = Cam({"azimuthDeg": 24, "elevationDeg": 9, "targetZ": 1.3, "visHeight": 3.8}); u = cam.uv((0, 0, 1.3)); assert abs(u[0] - 0.5) < 1e-6 and abs(u[1] - 0.5) < 1e-6
    r = cam.ray((0.7, 0.3)); p = add(cam.C, mul(r, 5.0)); u2 = cam.uv(p); assert abs(u2[0] - 0.7) < 1e-6 and abs(u2[1] - 0.3) < 1e-6
    class Dummy(Solver):
        def __init__(self): self.cam = cam; self.G = {"armLen": 0.44, "handLen": 0.46}
    d = Dummy(); S = (0.6, 0.0, 1.0); tgt = (0.93, 0.35)
    for phi in (10, 30, 60):
        dd = d.aim_dir(S, tgt, phi); L = 0.9; tip = d.cam.uv(add(S, mul(dd, L))); s0 = d.cam.uv(S)
        # the ray from the shoulder through the tip must pass through the target pixel: cross product of 2D vectors ~ 0
        cr = (tip[0] - s0[0]) * (tgt[1] - s0[1]) - (tip[1] - s0[1]) * (tgt[0] - s0[0]); assert abs(cr) < 2e-3, (phi, cr)
    da, dh = d.ik2((0.6, 0, 1.0), (0.12, -0.42, 0.9), (0.5, 0.4, -0.2)); W = add((0.6, 0, 1.0), mul(da, 0.44)); tip = add(W, mul(dh, 0.46)); assert length(sub(tip, (0.12, -0.42, 0.9))) < 1e-6
    print("solver selftest ok")

if __name__ == "__main__": main()
