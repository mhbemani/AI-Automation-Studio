# Animation of the whole video, built from production/timeline.json + the two speech envelopes.
# Idempotent and deterministic (fixed seeds): re-run it after ANY scene change. It only writes F-curves in ANIM_*
# actions, a few helper objects tagged cs_owner="anim", timeline markers and constraints; anything with
# user_locked=True (or an action not named ANIM_*) is left alone. Works in the live GUI (bl.py file) and headless
# (blender -b scene.blend -P scripts/animate.py).
# Chain after any scene edit:  build_city -> build_car -> build_characters -> build_cameras -> build_lighting ->
#                              drive_car -> animate   (build_city/build_car/build_characters recreate objects)
# Sections: 1 markers+mirror, 2 car (wheels, steering, motion cues), 3 street human + phone, 4 Claude, 5 seated human,
#           6 camera drift, 7 visibility.
import bpy, os, math, random, re
from mathutils import Vector, Matrix, Euler, Quaternion
import numpy as np
exec(open(os.path.join(os.path.dirname(bpy.data.filepath), "scripts", "_anim_util.py")).read())

sc = bpy.context.scene
O = bpy.data.objects
def locked(o): return bool(o.get("user_locked"))
def deg(x): return math.radians(x)
F = np.array(FRAMES, dtype=float)
T = (F - 1) / FPS                                   # seconds
ENV = {k: np.array(json.load(open(os.path.join(PROD, f"envelope_{k}.json")))) for k in ("claude", "human")}
assert len(ENV["claude"]) == N
log = []

sc.frame_start, sc.frame_end = 1, N
sc.render.fps, sc.render.fps_base = FPS, 1

def lowpass(x, alpha):                               # one-pole smoothing, deterministic
    y = np.empty_like(x, dtype=float); acc = x[0]
    for i, v in enumerate(x): acc += alpha * (v - acc); y[i] = acc
    return y

def smooth(x, sigma_frames):                         # Gaussian smoothing (edge-padded)
    r = int(sigma_frames * 3); k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma_frames) ** 2); k /= k.sum()
    return np.convolve(np.pad(x, r, mode="edge"), k, mode="valid")

def noise(seed, freqs=(0.23, 0.41, 0.77)):           # low-frequency noise in about [-1, 1]
    rng = random.Random(seed); ph = [rng.uniform(0, 2 * math.pi) for _ in freqs]
    return sum(np.sin(2 * math.pi * f * T + p) for f, p in zip(freqs, ph)) / len(freqs) * 1.6

# ---------------------------------------------------------------------------------------------- 1. shots + mirror
for mk in [m for m in sc.timeline_markers if re.match(r"(SHOT\d+|S\d\d)_", m.name)]: sc.timeline_markers.remove(mk)
for s in SHOTS:
    sc.timeline_markers.new(f"{s['id']}_{s['camera'][4:]}", frame=s["startFrame"]).camera = O[s["camera"]]
sc.camera = O[SHOTS[0]["camera"]]

# ------------------------------------------------------------------------------------------------- 2. car motion
car, path = O["CAR_Exterior"], O["CITY_DrivePath"]
L = path["length_m"]
et = path.data.animation_data.action.fcurves.find("eval_time") if path.data.animation_data and path.data.animation_data.action else None
assert et, "run drive_car.py first"
DIST = np.array([et.evaluate(f) / 100.0 - L for f in FRAMES])    # metres from the pickup stop (negative = before it)
V = np.gradient(DIST) * FPS                                      # m/s
V_s = smooth(V, 2.0); A_LONG = np.gradient(V_s) * FPS            # m/s^2
# curvature of the lane path vs. distance along it (poly spline: heading change per segment, Gaussian-smoothed)
pts = [path.matrix_world @ Vector(p.co[:3]) for p in path.data.splines[0].points]
n = len(pts); seg = [(pts[(i + 1) % n] - pts[i]) for i in range(n)]
seglen = np.array([s.length for s in seg]); cum = np.concatenate([[0], np.cumsum(seglen)])[:-1]   # start s of each segment
head = np.array([math.atan2(s.y, s.x) for s in seg])
dpsi = np.array([(head[(i + 1) % n] - head[i] + math.pi) % (2 * math.pi) - math.pi for i in range(n)])   # turn at vertex i+1
ds = 0.25; grid = np.arange(0, L, ds); kap = np.zeros(len(grid))
vert_s = (cum + seglen) % L                                      # arclength of each vertex (end of its segment)
for i in range(n):                                               # spread each vertex' turn over its neighbouring half-segments
    half = 0.5 * (seglen[i] + seglen[(i + 1) % n]); a = vert_s[i] - half / 2
    j0 = int(round(a / ds)); cnt = max(1, int(round(half / ds)))
    for j in range(cnt): kap[(j0 + j) % len(grid)] += dpsi[i] / (cnt * ds)
kap = np.convolve(np.pad(kap, 40, mode="wrap"), np.exp(-0.5 * (np.arange(-40, 41) * ds / 3.0) ** 2) / (3.0 * math.sqrt(2 * math.pi) / ds), mode="valid")
LEAD = 2.5                                                       # the driver turns the wheel a little before the corner
KAPPA = np.interp((L + DIST + LEAD) % L, grid, kap, period=L)    # 1/m, + = left turn
A_LAT = V_s ** 2 * KAPPA                                         # m/s^2, + = towards the left
WHEELBASE, WHEEL_R, STEER_RATIO = 2.38, 0.54, 12.0
STEER = np.arctan(WHEELBASE * KAPPA)                             # road-wheel angle, + = left
for nme in ("front-left", "front-right", "back-left", "back-right"):
    w = O["CAR_Wheel_" + nme]
    if locked(w): continue
    w.rotation_mode = "XYZ"; wa = new_action(w, "Wheel_" + nme)
    key(wa, "rotation_euler", 0, FRAMES, list(DIST / WHEEL_R))   # forward roll = + about the axle (car-local X)
    key(wa, "rotation_euler", 1, FRAMES, [0.0] * N)
    key(wa, "rotation_euler", 2, FRAMES, list(STEER if "front" in nme else 0 * STEER))
sw = O["CAR_SteeringWheel"]
if not locked(sw):
    sw.rotation_mode = "ZYX"                                     # tilt about X (rest), spin about its own axis (Z)
    swa = new_action(sw, "SteeringWheel")
    key(swa, "rotation_euler", 0, FRAMES, [deg(-70)] * N); key(swa, "rotation_euler", 1, FRAMES, [0.0] * N)
    key(swa, "rotation_euler", 2, FRAMES, list(STEER * STEER_RATIO))   # + = anticlockwise seen by the driver = left
log.append(f"car: dist {DIST[0]:.1f}..{DIST[-1]:.1f} m, max steer {np.degrees(np.abs(STEER).max()):.1f} deg, max a_lat {np.abs(A_LAT).max():.2f} m/s2")

# Claude's hands: two grip points on the wheel rim (they turn with it), arms point at them (Track-To, no keys)
for side, x in (("L", 0.19), ("R", -0.19)):
    nm = f"CAR_WheelGrip_{side}"
    g = O.get(nm)
    if not g:
        g = bpy.data.objects.new(nm, None); g.empty_display_type = "SPHERE"; g.empty_display_size = 0.02
        bpy.data.collections["02_CAR"].objects.link(g)
    g["cs_owner"] = "anim"; g.parent = sw; g.matrix_parent_inverse = Matrix(); g.location = (x, 0, 0)
    arm = O[f"CHAR_Claude_Arm_{side}"]
    if locked(arm): continue
    for c in [c for c in arm.constraints if c.name == "GripWheel"]: arm.constraints.remove(c)
    c = arm.constraints.new("TRACK_TO"); c.name = "GripWheel"; c.target = g
    c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"

# ------------------------------------------------------------------------------- 3. street human, walk, phone
st, stm = O["CHAR_Human_Street"], O["CHAR_Human_Street_Mesh"]
cam_phone, phone = O["CAM_PHONE_CU"], O["PROP_Phone"]
P0 = Vector((1.5, -7.7)); FINAL_FACE = deg(100)                  # = where build_characters puts him (his state at frame 1)
rest_mat = Matrix.Translation((P0.x, P0.y, 0)) @ Matrix.Rotation(FINAL_FACE, 4, "Z")   # CAM_PHONE_CU was built relative to this
if not locked(cam_phone) and cam_phone.parent is not st:         # keep the over-the-shoulder phone shot glued to him
    cam_phone.parent = st; cam_phone.matrix_parent_inverse = rest_mat.inverted()

WALK_START, AT_CURB = CUES["human_exit_start"], CUES["human_at_curb"]
LAST_ST = CUES["drive_start"]                                    # the street human leaves the picture at the cut to the car
CAR_STOP_X = path.data.splines[0].points[0].co[0]
P1 = Vector((CAR_STOP_X - 0.97, -4.55))                          # rear-right door of the stopped car (rear seat is 0.97 m behind the car centre)
STRIDE = 1.6                                                     # metres per 24-frame walk cycle (measured from the Walk action)
walk = bpy.data.actions["Human Armature|Human Armature|Walk"]
wc = {}                                                          # bone -> {"location": [3 fcurves], "rotation_quaternion": [4]}
for fc in walk.fcurves:
    m = re.match(r'pose\.bones\["(.*)"\]\.(location|rotation_quaternion)$', fc.data_path)
    if m: wc.setdefault(m.group(1), {}).setdefault(m.group(2), {})[fc.array_index] = fc
def walk_pose(frame):
    out = {}
    for b, d in wc.items():
        loc = Vector([d["location"][i].evaluate(frame) for i in range(3)]) if "location" in d else Vector()
        q = Quaternion([d["rotation_quaternion"][i].evaluate(frame) for i in range(4)]) if "rotation_quaternion" in d else Quaternion()
        out[b] = (loc, q.normalized())
    return out
RIGHT_ARM = {b.name for b in st.pose.bones if b.name.startswith("Right") and "Leg" not in b.name and "Foot" not in b.name and "Toe" not in b.name}
STAND = {"LeftArm": (72, 0, 0), "RightArm": (72, 0, 0), "RightForeArm": (0, 0, -90), }   # texting pose; the head stays level: CAM_PHONE_CU sits just in front of his face and is glued to the body, not the head
def stand_pose(extra=None):
    d = {b.name: (Vector(), Quaternion()) for b in st.pose.bones}
    for k, e in {**STAND, **(extra or {})}.items(): d[k] = (Vector(), Euler([deg(v) for v in e], "XYZ").to_quaternion())
    return d
def mix(a, b, w):
    out = {}
    for k in a:
        lb, qb = b.get(k, (Vector(), Quaternion()))
        qa = a[k][1]
        if qa.dot(qb) < 0: qb = -qb
        out[k] = (a[k][0].lerp(lb, w), qa.slerp(qb, w))
    return out

if not locked(st):
    for b in st.pose.bones: b.rotation_mode = "QUATERNION"
    D = (P1 - P0).length; DIR = (P1 - P0).normalized(); HEAD = math.atan2(DIR.y, DIR.x)
    RAMP_IN, RAMP_OUT = 5, 8; nwalk = AT_CURB - WALK_START
    vmax = D / (nwalk - (RAMP_IN + RAMP_OUT) / 2)
    def walked(f):                                               # metres from P0 (trapezoid speed profile)
        t = f - WALK_START
        if t <= 0: return 0.0
        if t >= nwalk: return D
        if t < RAMP_IN: return vmax * t * t / (2 * RAMP_IN)
        s_in = vmax * RAMP_IN / 2
        if t < nwalk - RAMP_OUT: return s_in + vmax * (t - RAMP_IN)
        u = nwalk - t; return D - vmax * u * u / (2 * RAMP_OUT)
    car_x = lambda f: CAR_STOP_X + DIST[f - 1]                    # the car on the straight (+X heading)
    names = [b.name for b in st.pose.bones]
    pose_keys = {nm: [] for nm in names}; obj_keys = {"x": [], "y": [], "z": [], "rz": []}
    frames_st = list(range(1, LAST_ST + 1))
    for f in frames_st:
        d = walked(f)
        # walk weight: 1 while moving, blended in/out over a few frames
        w = smoothstep((f - WALK_START) / 5.0) * (1 - smoothstep((f - AT_CURB) / 10.0))
        extra = {}
        pos = P0 + DIR * d
        face_w = HEAD * w + FINAL_FACE * (1 - w)                  # world facing of the body
        # after he stops: head follows the arriving car (yaw towards it, clamped), looks up from the phone
        look = 0.0
        if f >= AT_CURB:
            to_car = Vector((car_x(f) - pos.x, -2.0 - pos.y)); ang = math.atan2(to_car.y, to_car.x) - face_w
            ang = (ang + math.pi) % (2 * math.pi) - math.pi
            look = max(-70, min(70, math.degrees(ang))) * smoothstep((f - CUES["car_arrive_start"] + 10) / 30.0)
        up = smoothstep((f - CUES["car_arrive_start"] + 10) / 20.0)  # lifts his head from the phone when the car arrives
        extra = {"Head": (-2 * up, look * 0.4, 0), "Neck": (0, look * 0.3, 0), "Spine2": (0, look * 0.3, 0)}
        breath = 0.6 * math.sin(2 * math.pi * 0.27 * (f - 1) / FPS)
        extra["Spine1"] = (breath, 0, 0)
        wp = walk_pose(1 + ((d / STRIDE) * 24.0) % 24.0)
        target = mix(stand_pose(extra), wp, w)
        for nm in RIGHT_ARM: target[nm] = stand_pose(extra)[nm]  # the phone arm stays in the texting pose
        for nm in names:
            loc, q = target[nm]; pb = st.pose.bones[nm]; pb.location = loc; pb.rotation_quaternion = q
            pose_keys[nm].append((loc, q))
        # keep the lower foot on the ground while walking (the Walk action bobs the hips): lift = rest ankle height - lowest ankle
        dg = bpy.context.evaluated_depsgraph_get(); dg.update(); e = st.evaluated_get(dg)
        lift = max(0.0, 0.062 - min(e.pose.bones["LeftFoot"].head.z, e.pose.bones["RightFoot"].head.z)) if w > 0.01 else 0.0
        obj_keys["x"].append(pos.x); obj_keys["y"].append(pos.y); obj_keys["z"].append(lift)
        rz = (HEAD + math.pi / 2) * w + FINAL_FACE * (1 - w) if True else 0   # rig faces +X at rest; walk clip faces -Y (hips yaw -90)
        obj_keys["rz"].append(rz)
    sa = new_action(st, "StreetHuman")
    key(sa, "location", 0, frames_st, obj_keys["x"]); key(sa, "location", 1, frames_st, obj_keys["y"])
    key(sa, "location", 2, frames_st, obj_keys["z"])
    st.rotation_mode = "XYZ"
    key(sa, "rotation_euler", 0, frames_st, [0] * len(frames_st)); key(sa, "rotation_euler", 1, frames_st, [0] * len(frames_st))
    key(sa, "rotation_euler", 2, frames_st, obj_keys["rz"])
    for nm in names:
        pk = pose_keys[nm]
        for i in range(3):
            vals = [p[0][i] for p in pk]
            if any(abs(v) > 1e-6 for v in vals): key(sa, f'pose.bones["{nm}"].location', i, frames_st, vals)
        for i in range(4):
            vals = [p[1][i] for p in pk]
            if any(abs(v - (1.0 if i == 0 else 0.0)) > 1e-6 for v in vals): key(sa, f'pose.bones["{nm}"].rotation_quaternion', i, frames_st, vals)
    log.append(f"street human: walk {D:.2f} m in {nwalk} frames ({D / nwalk * FPS:.2f} m/s), curb at ({P1.x:.2f},{P1.y:.2f})")

# Phone: left-aligned typed text, one text object per prefix (visible for 2 frames each), then a sent bubble.
PH = TL["phone"]; MSG = PH["phoneText"]
def mat(name, color, emit=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = 0.5
    b.inputs["Emission Color"].default_value = (*color, 1); b.inputs["Emission Strength"].default_value = emit
    return m
BUBBLE, WHITE = mat("MAT_PhoneBubble", (0.0, 0.1, 0.75), 0.4), mat("MAT_PhoneTextWhite", (1, 1, 1), 0.6)
for o in [o for o in O if o.get("cs_owner") == "anim" and o.name.startswith("PROP_Phone_")]: bpy.data.objects.remove(o)
O["PROP_Phone_Text"].hide_render = O["PROP_Phone_Text"].hide_viewport = True     # the static full message from build_characters
COLL = bpy.data.collections["06_PROPS"]
def wrap(s):                                                     # same two lines as the static text: break after "wanna"
    cut = len("Claude, I wanna")
    return s if len(s) <= cut else s[:cut] + "\n" + s[cut:].lstrip(" ")
def text_obj(name, body, material, loc, align="LEFT", size=0.0085):
    cu = bpy.data.curves.new(name, "FONT"); cu.body = body; cu.size = size; cu.align_x = align; cu.align_y = "TOP"
    cu.materials.append(material)
    t = bpy.data.objects.new(name, cu); t["cs_owner"] = "anim"; COLL.objects.link(t)
    t.parent = phone; t.location = loc; t.rotation_euler = (deg(90), 0, 0); return t
def vis(o, spans, hidden_default=True):                          # spans: [(first_frame, last_frame_inclusive)] where visible
    act = get_action(o, "Vis_" + o.name); o.hide_render = o.hide_viewport = hidden_default
    fr, v = [1], [1.0 if hidden_default else 0.0]
    for a, b in spans: fr += [a, b + 1]; v += [0.0, 1.0]
    if fr[0] == fr[1]: fr, v = fr[1:], v[1:]
    for p in ("hide_render", "hide_viewport"): key(act, p, 0, fr, v, "CONSTANT")
t0, cps = PH["startFrame"], PH["charsPerSec"]
nchar = len(MSG)
frame_of = lambda k: t0 + int(math.ceil(k * FPS / cps))         # first frame on which k characters are visible: floor((f-t0)*cps/fps) >= k
typed = []
for k in range(1, nchar + 1):
    a = frame_of(k); b = (frame_of(k + 1) - 1) if k < nchar else PH["sendFrame"] - 1
    t = text_obj(f"PROP_Phone_Type_{k:02d}", wrap(MSG[:k]), O["PROP_Phone_Text"].data.materials[0], (-0.031, -0.0085, 0.1))
    vis(t, [(a, b)]); typed.append(t)
bub = bpy.data.objects.new("PROP_Phone_Bubble", bpy.data.meshes.new("PROP_Phone_Bubble")); bub["cs_owner"] = "anim"
bub.data.from_pydata([(-0.032, 0, 0.04), (0.032, 0, 0.04), (0.032, 0, 0.1), (-0.032, 0, 0.1)], [], [(0, 1, 2, 3)]); bub.data.materials.append(BUBBLE)
COLL.objects.link(bub); bub.parent = phone; bub.location = (0, -0.0088, 0)
sent = text_obj("PROP_Phone_Sent", wrap(MSG), WHITE, (-0.028, -0.0095, 0.095))
for o in (bub, sent): vis(o, [(PH["sendFrame"], CUES["drive_start"] - 1)])
log.append(f"phone: {nchar} chars typed from frame {t0} to {frame_of(nchar)}, sent at {PH['sendFrame']}")

# ------------------------------------------------------------------------------------------------- 4. Claude
EMO = {   # emotion -> parameters at intensity 1 (degrees / metres / factors); pitch + = leans forward, roll + = toward Claude's left
    "neutral":    dict(),
    "happy":      dict(pitch=-2, roll=3, lift=0.012, stretch=0.02, eye_sz=0.50, eye_sx=1.10, eye_tilt=16, bounce=0.008, bounce_hz=2.0),
    "curious":    dict(pitch=3, roll=7, yaw=-4, stretch=0.02, eye_sz=1.20, eye_asym=0.22, eye_dx=-0.012),
    "excited":    dict(pitch=4, lift=0.02, stretch=0.05, eye_sz=1.30, eye_sx=1.20, bounce=0.018, bounce_hz=3.2, sway=2.5, sway_hz=2.4),
    "surprised":  dict(pitch=-4, lift=0.035, stretch=0.08, eye_sz=1.55, eye_sx=1.15),
    "thoughtful": dict(pitch=2, roll=-6, yaw=-3, eye_sz=0.75, eye_dy=0.04, eye_dx=-0.02, sway=1.2, sway_hz=0.5),
    "proud":      dict(pitch=-6, lift=0.02, stretch=0.05, eye_sz=0.55, eye_sx=1.05, eye_tilt=10),
    "amused":     dict(pitch=1, eye_sz=0.50, eye_tilt=12, bounce=0.010, bounce_hz=3.0, sway=3.0, sway_hz=1.6),
}
KEYS = ("pitch", "roll", "yaw", "lift", "stretch", "eye_sz", "eye_sx", "eye_tilt", "eye_asym", "eye_dx", "eye_dy", "bounce", "bounce_hz", "sway", "sway_hz")
REST = dict(eye_sz=1.0, eye_sx=1.0, bounce_hz=2.0, sway_hz=1.0)
BODY_GAIN = 1.8                                                  # emotions must read from the side view (and in a 100 px mirror)
FORCE = globals().get("FORCE_EMOTION") or {}                    # preview only: {"claude": ("surprised", 1.0)} holds one emotion all video
def emotion_track(who, attack=0.22):
    """Per-frame dict of smoothed parameters from emotionKeys (hold until next key, intensity-scaled)."""
    keys = TL["emotionKeys"][who] if who not in FORCE else [{"frame": 1, "emotion": FORCE[who][0], "intensity": FORCE[who][1]}]; out = {k: np.zeros(N) for k in KEYS}; inten = np.zeros(N)
    cur = None
    kk = 0
    series = {k: np.zeros(N) for k in KEYS}
    for i, f in enumerate(FRAMES):
        while kk < len(keys) and keys[kk]["frame"] <= f: cur = keys[kk]; kk += 1
        e = EMO.get(cur["emotion"], {}) if cur else {}
        a = cur["intensity"] if cur else 0.0
        inten[i] = a
        for k in KEYS:
            base = REST.get(k, 0.0); g = BODY_GAIN if k in ("pitch", "roll", "yaw", "lift", "stretch", "sway", "bounce") else 1.0
            series[k][i] = base + (e.get(k, base) - base) * a * g
    for k in KEYS: out[k] = lowpass(series[k], attack)
    out["_i"] = lowpass(inten, attack)
    return out

# glance at the mirror when the human starts speaking: ~14 frames after each human line start
glance = np.zeros(N)
for ln in TL["lines"]:
    if ln["speaker"] == "human":
        s0 = ln["startFrame"] + 2
        for j in range(26):
            if s0 + j <= N: glance[s0 + j - 1] = max(glance[s0 + j - 1], math.sin(math.pi * j / 25) ** 0.7)
glance = lowpass(glance, 0.5)

claude = O["CHAR_Claude"]; claude_mat = None
if not locked(claude):
    em = emotion_track("claude", 0.2)
    env = lowpass(ENV["claude"], 0.6)                           # speech loudness 0..1 (already attack/release shaped)
    if "rest_loc" not in claude: claude["rest_loc"] = tuple(claude.location)
    base = Vector(claude["rest_loc"])
    claude.rotation_mode = "XYZ"
    # blinks at random times (fixed seed)
    rng = random.Random(11); blink = np.ones(N); t = 2.0
    while t < N / FPS:
        f0 = int(t * FPS) + 1
        for j, v in enumerate((0.6, 0.15, 0.1, 0.5)):
            if f0 + j <= N: blink[f0 + j - 1] = v
        t += rng.uniform(2.4, 5.2)
    ph_b = 2 * math.pi * em["bounce_hz"].cumsum() / FPS         # phases follow the (smoothed) frequency
    ph_s = 2 * math.pi * em["sway_hz"].cumsum() / FPS
    bounce = em["bounce"] * np.sin(ph_b) * (0.5 + 0.5 * env)
    sway = em["sway"] * np.sin(ph_s)
    # car physics: lean out of corners and back when accelerating (small)
    roll_car = -0.7 * A_LAT; pitch_car = -0.5 * A_LONG
    pitch = em["pitch"] + 2.0 * env + pitch_car - 3.0 * glance * 0
    roll = em["roll"] + sway + roll_car
    yaw = em["yaw"] - 9.0 * glance
    stretch = em["stretch"] + 0.045 * env
    lift = em["lift"] + 0.012 * env + bounce
    sx = 1 - 0.5 * stretch
    ca = new_action(claude, "Claude")
    key(ca, "location", 0, FRAMES, [base.x] * N); key(ca, "location", 1, FRAMES, [base.y] * N)
    key(ca, "location", 2, FRAMES, list(base.z + lift))
    key(ca, "rotation_euler", 0, FRAMES, list(np.radians(pitch))); key(ca, "rotation_euler", 1, FRAMES, list(np.radians(roll)))
    key(ca, "rotation_euler", 2, FRAMES, list(np.radians(yaw)))
    key(ca, "scale", 0, FRAMES, list(sx)); key(ca, "scale", 1, FRAMES, list(sx)); key(ca, "scale", 2, FRAMES, list(1 + stretch))
    for s, sign in (("L", 1), ("R", -1)):
        eye = O[f"CHAR_Claude_Eye_{s}"]
        if locked(eye): continue
        eye.rotation_mode = "XYZ"
        ebase = Vector(eye.location) if "rest_loc" not in eye else Vector(eye["rest_loc"]); eye["rest_loc"] = tuple(ebase)
        asym = 1 + sign * em["eye_asym"]                          # curious: one eye bigger
        sz = np.clip(em["eye_sz"] * asym * blink, 0.06, 2.0); sxw = em["eye_sx"] * (1 + 0.5 * (asym - 1))
        ea = new_action(eye, "ClaudeEye_" + s)
        key(ea, "location", 0, FRAMES, list(ebase.x + em["eye_dx"] + 0.0 * sz)); key(ea, "location", 1, FRAMES, [ebase.y] * N)
        key(ea, "location", 2, FRAMES, list(ebase.z + 0.065 * (1 - sz) + em["eye_dy"]))   # scale about the eye centre; the pivot is at its bottom
        key(ea, "rotation_euler", 0, FRAMES, [0.0] * N)
        key(ea, "rotation_euler", 1, FRAMES, list(np.radians(sign * em["eye_tilt"]))); key(ea, "rotation_euler", 2, FRAMES, [0.0] * N)
        key(ea, "scale", 0, FRAMES, list(sxw)); key(ea, "scale", 1, FRAMES, [1.0] * N); key(ea, "scale", 2, FRAMES, list(sz))
    def claude_mat(i):                                            # body -> car space at frame index i (for the mirror aim)
        r = Euler((math.radians(pitch[i]), math.radians(roll[i]), math.radians(yaw[i])), "XYZ").to_matrix().to_4x4()
        return Matrix.Translation((base.x, base.y, base.z + lift[i])) @ r @ Matrix.Diagonal((sx[i], sx[i], 1 + stretch[i], 1))
    log.append(f"claude: max lift {lift.max():.3f} m, pitch {pitch.min():.1f}..{pitch.max():.1f}, roll {roll.min():.1f}..{roll.max():.1f}, {int((blink < 1).sum())} blink frames")


# ---------------------------------------------------------------------------------- mirror (needs Claude's motion)
# One aim per camera is stored by build_cameras (aim_<camera>). CLAUDE_POV shots keep a constant aim (keyed at each cut);
# HUMAN_POV shots re-aim every frame at Claude's animated eye position, so the face stays in the mirror whatever he does
# (film cheat, nobody sees the mirror turn). Aim = bisector of (camera -> mirror) and (mirror -> eyes), as in build_cameras.
for cn in ("CAM_HUMAN_POV", "CAM_CLAUDE_POV"):                     # rest placement (car-local values); build_cameras clears these on a rebuild
    c = O[cn]
    if "rest_loc" not in c: c["rest_loc"] = tuple(c.location); c["rest_rot"] = tuple(c.rotation_euler)
mirror = O["CAR_RearViewMirror"]
if mirror.animation_data and mirror.animation_data.action and mirror.animation_data.action.name.startswith("CAR_RearView"):
    bpy.data.actions.remove(mirror.animation_data.action)       # the old 7-cut keys from build_cameras
ma = new_action(mirror, "Mirror")
if ma:
    Ml = Vector(mirror["M_local"]); camh = O["CAM_HUMAN_POV"]
    cam_l = camh.matrix_parent_inverse @ Vector(camh["rest_loc"])   # car-space camera position
    cam_of = {}
    for sh in SHOTS:
        for f in range(sh["startFrame"], min(sh["endFrame"], N + 1)): cam_of[f] = sh["camera"]
    first_int = next(s for s in SHOTS if s["shot"] == "INT")["camera"]
    eul = []; prev = None
    for i, f in enumerate(FRAMES):
        cam = cam_of.get(f, first_int)
        if cam == "CAM_HUMAN_POV" and claude_mat is not None:
            E = claude_mat(i) @ Vector((0, -0.255, 0.645))          # between the eyes (body space) -> car space
            n = ((cam_l - Ml).normalized() + (E - Ml).normalized()).normalized()
            e = n.to_track_quat("Y", "Z").to_euler("XYZ", prev) if prev else n.to_track_quat("Y", "Z").to_euler()
        else:
            e = Euler(mirror["aim_" + cam if cam != "CAM_EST_Street" and cam != "CAM_PHONE_CU" else "aim_" + first_int])
        eul.append(e); prev = e
    for k in range(3): key(ma, "rotation_euler", k, FRAMES, [e[k] for e in eul])
    log.append(f"mirror: per-frame aim on {sum(1 for f in FRAMES if cam_of.get(f)=='CAM_HUMAN_POV')} HUMAN_POV frames, constant on the others; cut keys at {[s['startFrame'] for s in SHOTS if s['shot']=='INT']}")

# ------------------------------------------------------------------------------------------------- 5. seated human
HEMO = {   # head (x nod +, y turn left +, z tilt toward his right shoulder +) and spine (x lean forward +) in degrees, at intensity 1
    "neutral":   dict(),
    "amused":    dict(hp=2, hz=-4, spine_x=1, nod=3.0, nod_hz=1.6),
    "curious":   dict(hz=-9, hy=7, hp=2, spine_x=5),
    "surprised": dict(hp=-7, hy=4, spine_x=-4),
    "happy":     dict(hp=2, hz=-3),
    "excited":   dict(hp=3, spine_x=3), "thoughtful": dict(hp=4, hz=3), "proud": dict(hp=-3),
}
HKEYS = ("hp", "hy", "hz", "spine_x", "nod", "nod_hz")
def human_track(who, attack):
    keys = TL["emotionKeys"][who] if who not in FORCE else [{"frame": 1, "emotion": FORCE[who][0], "intensity": FORCE[who][1]}]; series = {k: np.zeros(N) for k in HKEYS}; kk = 0; cur = None
    for i, f in enumerate(FRAMES):
        while kk < len(keys) and keys[kk]["frame"] <= f: cur = keys[kk]; kk += 1
        e = HEMO.get(cur["emotion"], {}) if cur else {}; a = cur["intensity"] if cur else 0.0
        for k in HKEYS:
            b = 1.5 if k == "nod_hz" else 0.0
            series[k][i] = b + (e.get(k, b) - b) * a
    return {k: lowpass(v, attack) for k, v in series.items()}
seated = O["CHAR_Human"]
if not locked(seated):
    hm = human_track("human", 0.16)
    henv = lowpass(ENV["human"], 0.6)
    # listening nods: a smooth nod ~12 frames into each of Claude's lines
    nodp = np.zeros(N)
    for ln in TL["lines"]:
        if ln["speaker"] == "claude":
            s = ln["startFrame"] + 12
            for j in range(14):
                if s + j <= N: nodp[s + j - 1] = max(nodp[s + j - 1], 4.5 * math.sin(math.pi * j / 13) ** 2)
    ph_n = 2 * math.pi * hm["nod_hz"].cumsum() / FPS
    nod = hm["nod"] * np.sin(ph_n)
    sway_y, sway_z, sway_x = 1.6 * noise(31), 1.1 * noise(32), 0.8 * noise(33)
    breath = 0.5 * np.sin(2 * math.pi * 0.26 * T)
    lean_lat = 0.8 * A_LAT                                         # + z = lean to his right (window side) = outward in left turns
    lean_lon = -0.5 * A_LONG
    sp_x = hm["spine_x"] + lean_lon + breath + 1.0 * henv
    hp = hm["hp"] + nod + nodp + 3.0 * henv + sway_x
    hy = hm["hy"] + sway_y
    hz = hm["hz"] + sway_z - 1.5 * henv
    sa2 = new_action(seated, "HumanSeated")
    REST_POSE = {"LeftArm": (80, 0, 0), "RightArm": (80, 0, 0), "LeftForeArm": (0, 0, 62), "RightForeArm": (0, 0, -62),
                 "LeftUpLeg": (88, 0, 0), "RightUpLeg": (88, 0, 0), "LeftLeg": (-88, 0, 0), "RightLeg": (-88, 0, 0)}
    def put(bone, comps):                                          # comps: 3 arrays (deg) or scalars
        for i in range(3):
            v = np.broadcast_to(np.asarray(comps[i], dtype=float), (N,))
            if np.any(np.abs(v) > 1e-9): key(sa2, f'pose.bones["{bone}"].rotation_euler', i, FRAMES, list(np.radians(v)))
    for b in seated.pose.bones: b.rotation_mode = "XYZ"
    for bone, r in REST_POSE.items(): put(bone, r)
    put("Spine", (sp_x * 0.3, 0, lean_lat * 0.3 + 0)); put("Spine1", (sp_x * 0.35, 0, lean_lat * 0.35)); put("Spine2", (sp_x * 0.35, 0, lean_lat * 0.35))
    put("Neck", (hp * 0.4, hy * 0.4, hz * 0.4)); put("Head", (hp * 0.6, hy * 0.6, hz * 0.6))
    log.append(f"human: head pitch {hp.min():.1f}..{hp.max():.1f}, yaw {hy.min():.1f}..{hy.max():.1f}, roll {hz.min():.1f}..{hz.max():.1f}")

# ------------------------------------------------------------------------------------------------ 6. camera drift
for cn, seed in (("CAM_HUMAN_POV", 41), ("CAM_CLAUDE_POV", 42)):
    c = O[cn]
    if locked(c): continue
    if "rest_loc" not in c: c["rest_loc"] = tuple(c.location); c["rest_rot"] = tuple(c.rotation_euler)
    rl, rr = Vector(c["rest_loc"]), Vector(c["rest_rot"]); c.rotation_mode = "XYZ"
    ca2 = new_action(c, "Handheld_" + cn)
    for i in range(3):
        key(ca2, "location", i, FRAMES, list(rl[i] + 0.005 * noise(seed * 10 + i)))
        key(ca2, "rotation_euler", i, FRAMES, list(rr[i] + math.radians(0.18) * noise(seed * 10 + 3 + i)))

# --------------------------------------------------------------------------------------------- 7. visibility
# the seated human only exists from the first interior shot (he "gets in" during the cut); the street human, the phone
# and its overlays leave with that cut. Constant-interpolated hide keys, both viewport and render.
FIRST_INT = next(s for s in SHOTS if s["shot"] == "INT")["startFrame"]
for o in (seated, O["CHAR_Human_Mesh"]):
    if not locked(o): vis(o, [(FIRST_INT, N)])
for o in (st, stm, phone, O["PROP_Phone_Screen"]):
    if not locked(o): vis(o, [(1, FIRST_INT - 1)], hidden_default=False)

sc.frame_set(1)
result = "\n".join(log)
