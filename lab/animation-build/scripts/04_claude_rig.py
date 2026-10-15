"""Claude armature (milestone 3). Copies the main V3-A parts from the lineup copy (appended in anim_work.blend) into
rig-local space (origin on the ground between his feet, front = -Y, +X = viewer's right), builds RIG_Claude with
one bone per part, rigid skinning (single full-weight vertex group per part, so his look stays exactly as it is),
a control bone `ctrl` whose custom properties drive eyes / glints / blush / arms / squash / lean through drivers.
Names keep the lineup's convention: *_L parts are on -X. Idempotent. Run via bridge, cwd lab/animation-build."""
import bpy, math, os
from mathutils import Vector as V, Matrix
ROOT = os.environ.get("ANIM_ROOT") or os.path.dirname(os.path.abspath(__import__("bpy").data.filepath))
LINEUP = os.path.join(ROOT, "snapshots", "lineup_2026-10-13.blend")
PFX = "LU_V3A_CHAR_Claude"
REACH_MAX = 2.3          # the arm may stretch to 2.3x its length (never thinner); beyond that: turn the body, one hand, or magic
RIG_LOC = (-1.2, 0, 0)   # where the rig object sits in anim_work.blend (data is rig-local)

# part object -> (new name, bone)
PARTS = {
 PFX: ("CLA_Body", "body"), PFX + "_Arm_L": ("CLA_Arm_L", "arm_L"), PFX + "_Arm_R": ("CLA_Arm_R", "arm_R"),
 PFX + "_Eye_L": ("CLA_Eye_L", "eye_L"), PFX + "_Eye_R": ("CLA_Eye_R", "eye_R"),
 PFX + "_Eye_L_Glint1": ("CLA_Glint_L", "glint_L"), PFX + "_Eye_R_Glint1": ("CLA_Glint_R", "glint_R"),
 PFX + "_Leg_1": ("CLA_Leg_1", "leg_1"), PFX + "_Leg_2": ("CLA_Leg_2", "leg_2"), PFX + "_Leg_3": ("CLA_Leg_3", "leg_3"), PFX + "_Leg_4": ("CLA_Leg_4", "leg_4"),
}
BLUSH = {"LU_V3B_CHAR_Claude_Blush_L": ("CLA_Blush_L", "blush_L"), "LU_V3B_CHAR_Claude_Blush_R": ("CLA_Blush_R", "blush_R")}

def cleanup():
    for o in list(bpy.data.objects):
        if o.get("anim_owner") == "claude": bpy.data.objects.remove(o)
    c = bpy.data.collections.get("CLAUDE")
    if c: bpy.data.collections.remove(c)
    for m in list(bpy.data.meshes):
        if m.name.startswith("CLA_") and m.users == 0: bpy.data.meshes.remove(m)

def fetch_blush():
    """blush meshes live in the V3B variant (not appended yet): bring over just those two objects."""
    have = {n: bpy.data.objects.get(n) for n in BLUSH}
    if all(have.values()): return
    with bpy.data.libraries.load(LINEUP, link=False) as (s, d):
        d.objects = [n for n in BLUSH if n in s.objects] + ["LU_V3B_CHAR_Claude"]
    for o in d.objects:
        if o.users_collection == (): bpy.data.collections["ANIM_Sources"].objects.link(o)
        o.hide_viewport = True; o.hide_render = True

BONES = {  # name: (head, tail, parent)   rig-local metres
 "root":    ((0, 0, 0), (0, -0.3, 0), None),
 "squash":  ((0, 0, 0), (0, 0, 0.1), "root"),
 "body":    ((0, 0, 0.1), (0, 0, 0.5), "squash"),
 "eye_L":   ((-0.17, -0.163, 0.29), (-0.17, -0.163, 0.36), "body"),
 "eye_R":   ((0.17, -0.163, 0.29), (0.17, -0.163, 0.36), "body"),
 "glint_L": ((-0.183, -0.160, 0.33), (-0.183, -0.160, 0.36), "body"),
 "glint_R": ((0.157, -0.160, 0.33), (0.157, -0.160, 0.36), "body"),
 "arm_L":   ((-0.3, 0, 0.25), (-0.4, 0, 0.25), "body"),
 "arm_R":   ((0.3, 0, 0.25), (0.4, 0, 0.25), "body"),
 "leg_1":   ((-0.167, 0, 0.1), (-0.167, 0, 0.0), "body"),
 "leg_2":   ((-0.067, 0, 0.1), (-0.067, 0, 0.0), "body"),
 "leg_3":   ((0.077, 0, 0.1), (0.077, 0, 0.0), "body"),
 "leg_4":   ((0.177, 0, 0.1), (0.177, 0, 0.0), "body"),
 "blush_L": ((-0.235, -0.149, 0.195), (-0.235, -0.149, 0.225), "body"),
 "blush_R": ((0.235, -0.149, 0.195), (0.235, -0.149, 0.225), "body"),
 "ctrl":    ((0, 0.0, 0.62), (0, 0.0, 0.72), "root"),
 "aim_L":   ((-0.55, -0.25, 0.3), (-0.55, -0.25, 0.36), "root"),     # reach targets: the arm aims at and stretches toward them (arm_aim_L/R > 0)
 "aim_R":   ((0.55, -0.25, 0.3), (0.55, -0.25, 0.36), "root"),
}
# custom properties on bone `ctrl`: name -> (default, min, max, description)
PROPS = {
 "eye_open": (1.0, 0.0, 1.4, "1 = open, 0 = closed (blink)"),
 "eye_h_L": (1.0, 0.1, 2.0, "left (-X) eye height scale"), "eye_h_R": (1.0, 0.1, 2.0, "right (+X) eye height scale"),
 "eye_w": (1.0, 0.4, 1.8, "eye width scale"), "eye_y": (0.0, -0.06, 0.06, "eyes up/down (m)"),
 "look_x": (0.0, -0.05, 0.05, "eyes left/right (m, + = viewer right)"), "look_y": (0.0, -0.05, 0.05, "eyes up/down look (m)"),
 "eye_roll": (0.0, -35.0, 35.0, "eye tilt (deg), mirrored: + = tops lean outward (droopy), - = tops lean inward (stern)"),
 "glint": (1.0, 0.0, 2.0, "eye glint size"), "blush": (0.0, 0.0, 1.0, "blush cheeks 0..1"),
 "arm_L": (0.0, -70.0, 120.0, "left (-X) arm raise (deg, + = up)"), "arm_R": (0.0, -70.0, 120.0, "right (+X) arm raise (deg, + = up)"),
 "arm_aim_L": (0.0, 0.0, 1.0, "left (-X) arm: 0 = manual raise/swing, 1 = aims at bone aim_L and stretches (never thinner, at most 2.3x longer)"), "arm_aim_R": (0.0, 0.0, 1.0, "right (+X) arm, same with aim_R"),
 "arm_y_L": (0.0, -0.09, 0.09, "left (-X) arm slides along his side wall, + = backward (m)"), "arm_y_R": (0.0, -0.09, 0.09, "right (+X) arm slides along the wall, + = backward (m)"),
 "arm_z_L": (0.0, -0.10, 0.15, "left arm slides up/down the wall (m)"), "arm_z_R": (0.0, -0.10, 0.15, "right arm slides up/down the wall (m)"),
 "leg_x_1": (0.0, -0.12, 0.12, "leg 1 slides sideways under the body (m)"), "leg_x_2": (0.0, -0.12, 0.12, "leg 2 slides sideways (m)"), "leg_x_3": (0.0, -0.12, 0.12, "leg 3 slides sideways (m)"), "leg_x_4": (0.0, -0.12, 0.12, "leg 4 slides sideways (m)"),
 "leg_y_1": (0.0, -0.14, 0.14, "leg 1 slides forward(-)/back(+) under the body (m)"), "leg_y_2": (0.0, -0.14, 0.14, "leg 2 slides forward/back (m)"), "leg_y_3": (0.0, -0.14, 0.14, "leg 3 slides forward/back (m)"), "leg_y_4": (0.0, -0.14, 0.14, "leg 4 slides forward/back (m)"),
 "aim_follow_L": (0.0, 0.0, 1.0, "1 = bone aim_L sticks to the car's wheel grip on his -X side (CAR_WheelGrip_R); needs the car in the file"), "aim_follow_R": (0.0, 0.0, 1.0, "1 = aim_R sticks to CAR_WheelGrip_L (the +X side)"),
 "leg_len_1": (1.0, 0.2, 2.2, "leg 1 length scale (only along the leg: shorter lifts the foot, longer reaches down); the hip stays on the body"), "leg_len_2": (1.0, 0.2, 2.2, "leg 2 length scale"), "leg_len_3": (1.0, 0.2, 2.2, "leg 3 length scale"), "leg_len_4": (1.0, 0.2, 2.2, "leg 4 length scale"),
 "leg_rot_1": (0.0, -60.0, 60.0, "leg 1 swing about the hip (deg, + = foot forward)"), "leg_rot_2": (0.0, -60.0, 60.0, "leg 2 swing (deg)"), "leg_rot_3": (0.0, -60.0, 60.0, "leg 3 swing (deg)"), "leg_rot_4": (0.0, -60.0, 60.0, "leg 4 swing (deg)"),
 "arm_len_L": (1.0, 0.5, 2.3, "left (-X) arm length scale (only along the arm, never thinner; at most 2.3x)"), "arm_len_R": (1.0, 0.5, 2.3, "right (+X) arm length scale"),
 "cus_show": (0.0, 0.0, 1.0, "1 shows the cushion CUS_Cushion (the cushion actions key it), 0 shrinks it to nothing"), "move_x": (0.0, -30.0, 30.0, "root travels sideways (m, rig-local +X = viewer's right); the scene or an action moves him with it"), "move_y": (0.0, -30.0, 30.0, "root travels forward/back (m, +Y = backwards, -Y = the way he faces)"), "yaw": (0.0, -180.0, 180.0, "whole-body turn about the vertical axis (deg, root bone; + = turns toward the viewer's left)"),
 "hop": (0.0, -0.2, 1.0, "root up/down (m): jumps and landing dips; the cushion squashes when his feet sink into it"), "jump_t": (0.0, 0.0, 1.0, "0..1: root travels from where he stands to the cushion's resting place (cus_dx, cus_dy, cus_dz)"),
 "cus_held": (0.0, 0.0, 1.0, "cushion: 0 = under his feet, 1 = hugged upright in front of him"), "cus_toss": (0.0, 0.0, 1.0, "cushion thrown: 0 = start place, 1 = at the resting place (cus_dx/dy/dz)"),
 "cus_arc": (0.0, 0.0, 1.5, "extra height of the cushion in flight (m)"), "cus_tumble": (0.0, -1440.0, 1440.0, "cushion tumble about its long axis (deg)"),
 "cus_dx": (-0.9, -4.0, 4.0, "resting place of the thrown cushion, relative to his origin: x (m)"), "cus_dy": (0.0, -4.0, 4.0, "resting place: y (m)"), "cus_dz": (0.78, 0.0, 3.0, "resting place: height of the cushion centre (m)"),
 "cus_squash": (0.0, 0.0, 1.0, "manual squash of the cushion (the shape key also squashes by itself when his feet sink in)"),
 "arm_fwd_L": (0.0, -90.0, 90.0, "left arm swing forward (deg)"), "arm_fwd_R": (0.0, -90.0, 90.0, "right arm swing forward (deg)"),
 "talk": (0.0, 0.0, 1.0, "voice envelope 0..1: stretches him up, bobs and sparkles the eyes (no mouth)"),
 "squash": (0.0, -1.0, 1.0, "+1 squashed (short and wide), -1 stretched (tall and thin); volume kept"),
 "lean": (0.0, -25.0, 25.0, "side lean (deg, + = toward viewer's right)"), "nod": (0.0, -25.0, 25.0, "forward tilt (deg, + = forward)"),
 "turn": (0.0, -60.0, 60.0, "body yaw (deg, + = face turns toward the viewer's right)"), "bob": (0.0, -0.05, 0.1, "body up/down (m)"),
}

def build_armature():
    arm = bpy.data.armatures.new("RIG_Claude"); rig = bpy.data.objects.new("RIG_Claude", arm)
    rig["anim_owner"] = "claude"; rig.location = RIG_LOC
    col = bpy.data.collections.new("CLAUDE"); bpy.context.scene.collection.children.link(col); col.objects.link(rig)
    bpy.context.view_layer.objects.active = rig; rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for n, (h, t, p) in BONES.items():
        b = arm.edit_bones.new(n); b.head, b.tail = V(h), V(t); b.roll = 0
        if n in ("eye_L", "eye_R", "glint_L", "glint_R", "blush_L", "blush_R", "body", "squash", "ctrl"): b.align_roll(V((0, -1, 0)))  # local Z = world -Y (toward viewer's back)
    for n, (h, t, p) in BONES.items():
        if p: arm.edit_bones[n].parent = arm.edit_bones[p]
    bpy.ops.object.mode_set(mode='OBJECT')
    for n in ("ctrl", "aim_L", "aim_R"): arm.bones[n].use_deform = False
    for n in ("root",): arm.bones[n].use_deform = False
    rig.show_in_front = True; arm.display_type = 'STICK'
    return rig

def rounded_prism(me, radius, seg=4):
    """replace a box-shaped mesh (eye / glint) by a rounded-corner prism with the same bounding box (corners rounded in the XZ face, depth along Y)."""
    import bmesh
    xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]; zs = [v.co.z for v in me.vertices]
    x0, x1, y0, y1, z0, z1 = min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)
    r = min(radius, (x1 - x0) / 2 - 1e-4, (z1 - z0) / 2 - 1e-4)
    pts = []
    for cx, cz, a0 in ((x1 - r, z1 - r, 0), (x0 + r, z1 - r, 90), (x0 + r, z0 + r, 180), (x1 - r, z0 + r, 270)):
        for k in range(seg + 1):
            a = math.radians(a0 + 90 * k / seg); pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    bm = bmesh.new()
    front = [bm.verts.new((x, y0, z)) for x, z in pts]; back = [bm.verts.new((x, y1, z)) for x, z in pts]
    bm.faces.new(front); bm.faces.new(back)
    n = len(pts)
    for i in range(n): bm.faces.new((front[i], front[(i + 1) % n], back[(i + 1) % n], back[i]))
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mats = list(me.materials)
    bm.to_mesh(me); bm.free()
    me.update()

ROUND = {"CLA_Eye_L": .010, "CLA_Eye_R": .010, "CLA_Glint_L": .005, "CLA_Glint_R": .005, "CLA_Blush_L": .016, "CLA_Blush_R": .016}

def make_parts(rig):
    col = bpy.data.collections["CLAUDE"]
    # the lineup copies are hidden (not evaluated, so their world matrices go stale after a file reload) and the lineup's own jump action moves the source body:
    # unhide the source chain, evaluate at frame 1, read, then restore the visibility
    chain = set()
    for n in list(PARTS):
        o = bpy.data.objects[n]
        while o: chain.add(o); o = o.parent
    saved = {}
    for o in chain:
        try: saved[o] = (o.hide_viewport, o.hide_get()); o.hide_viewport = False; o.hide_set(False)
        except Exception: pass
    bpy.context.scene.frame_set(2); bpy.context.scene.frame_set(1); bpy.context.view_layer.update()
    body = bpy.data.objects[PFX]; origin = body.matrix_world.translation.copy()
    items = {k: v for k, v in PARTS.items()}
    for src_name, (nn, bone) in list(items.items()) + [(k, v) for k, v in BLUSH.items()]:
        src = bpy.data.objects[src_name]
        me = src.data.copy(); me.name = nn
        if src_name in BLUSH:
            M = Matrix.Translation(V((-1 if nn.endswith("_L") else 1, 0, 0)) * 0) @ src.matrix_basis   # blush is parented to the V3B body: local == rig-local
        else:
            M = Matrix.Translation(-origin) @ src.matrix_world
        me.transform(M)
        if nn in ROUND: rounded_prism(me, ROUND[nn])
        o = bpy.data.objects.new(nn, me); o["anim_owner"] = "claude"; col.objects.link(o)
        vg = o.vertex_groups.new(name=bone); vg.add(list(range(len(me.vertices))), 1.0, 'REPLACE')
        m = o.modifiers.new("Armature", 'ARMATURE'); m.object = rig
        o.parent = rig
        o.data.shade_smooth() if False else None
    for o, (hv, hs) in saved.items():
        try: o.hide_viewport = hv; o.hide_set(hs)
        except Exception: pass
    return len(items) + len(BLUSH)

def axis_map(arm, bone, world_axis):
    """(channel index, sign) of the bone's rest-local axis that points along world_axis."""
    M = arm.bones[bone].matrix_local.to_3x3()
    best = max(range(3), key=lambda i: abs(M.col[i].dot(world_axis)))
    return best, (1.0 if M.col[best].dot(world_axis) > 0 else -1.0)

def prop_var(rig, d, name, prop):
    v = d.variables.new(); v.name = name; v.type = 'SINGLE_PROP'
    v.targets[0].id = rig; v.targets[0].data_path = f'pose.bones["ctrl"]["{prop}"]'

def drive(rig, bone, path, idx, expr, props):
    pb = rig.pose.bones[bone]
    fc = pb.driver_add(path, idx); d = fc.driver; d.type = 'SCRIPTED'; d.expression = expr
    for p in props: prop_var(rig, d, p, p)

def setup_controls(rig):
    arm = rig.data; pb = rig.pose.bones
    for n in pb.keys(): pb[n].rotation_mode = 'XYZ' if n in ("body", "arm_L", "arm_R", "eye_L", "eye_R", "squash") else 'QUATERNION'
    c = pb["ctrl"]
    for n, (dv, mn, mx, desc) in PROPS.items():
        c[n] = float(dv); ui = c.id_properties_ui(n); ui.update(default=float(dv), description=desc); ui.update(min=mn, max=mx); ui.update(soft_min=mn, soft_max=mx)
    X, Y, Z = V((1, 0, 0)), V((0, 1, 0)), V((0, 0, 1))
    for fc in list(rig.animation_data.drivers) if rig.animation_data else []: rig.animation_data.drivers.remove(fc)
    for side, hn in (("L", "eye_h_L"), ("R", "eye_h_R")):
        e, g, bl = f"eye_{side}", f"glint_{side}", f"blush_{side}"
        ix, sx = axis_map(arm, e, X); iz, sz = axis_map(arm, e, Z)
        drive(rig, e, "scale", 1, f"eye_open*{hn}*(1+0.08*talk)", ["eye_open", hn, "talk"])      # bone Y runs along the eye height
        drive(rig, e, "scale", ix, "eye_w", ["eye_w"])
        drive(rig, e, "location", ix, f"{sx}*look_x", ["look_x"]); drive(rig, e, "location", 1, "look_y+eye_y", ["look_y", "eye_y"])
        # tilt about the view axis (world Y); mirrored left/right
        iy, sy = axis_map(arm, e, Y)
        drive(rig, e, "rotation_euler", iy, f"{sy}*radians(eye_roll)*{1 if side == 'R' else -1}", ["eye_roll"])
        gx, gsx = axis_map(arm, g, X)
        drive(rig, g, "location", gx, f"{gsx}*look_x", ["look_x"])
        drive(rig, g, "location", 1, f"look_y+eye_y+(eye_open*{hn}-1)*0.04", ["look_y", "eye_y", "eye_open", hn])
        for i in range(3): drive(rig, g, "scale", i, f"glint*(1+0.25*talk)*min(1,eye_open*{hn})", ["glint", "eye_open", hn, "talk"])
        for i in range(3): drive(rig, bl, "scale", i, "max(blush,0.001)", ["blush"])
    for side, sgn in (("L", -1), ("R", 1)):
        a = f"arm_{side}"
        # raise: rotate the tail toward +Z; swing forward: toward -Y. find the channel/sign by probing the rest axes
        Yb = arm.bones[a].matrix_local.to_3x3().col[1]        # bone direction
        for chan_name, target_dir, prop in (("up", Z, f"arm_{side}"), ("fwd", -Y, f"arm_fwd_{side}")):
            # rotation about axis k by +t moves the tail by  k x Yb : pick k among the local axes so that k x Yb ~ target_dir
            M = arm.bones[a].matrix_local.to_3x3()
            best = None
            for i in range(3):
                for s in (1, -1):
                    sc = (s * M.col[i]).cross(Yb).dot(target_dir)
                    if best is None or sc > best[0]: best = (sc, i, s)
            _, i, s = best
            drive(rig, a, "rotation_euler", i, f"{s}*radians({prop})", [prop]) if chan_name == "up" else None
            if chan_name == "fwd": FWD[a] = (i, s)
        # lift the arm away from the wall while it swings up/down so it never sinks into the body (bone Y runs outward)
        drive(rig, a, "location", 1, f"0.055*sin(radians(max({a},0)))+0.03*sin(radians(max(-{a},0)))", [a])
    # forward swing shares the euler with the raise on another channel (they differ)
    for side in "LR":
        a = f"arm_{side}"; i2, s2 = FWD[a]
        fc = rig.animation_data.drivers.find(f'pose.bones["{a}"].rotation_euler', index=i2)
        if fc is None: drive(rig, a, "rotation_euler", i2, f"{s2}*radians(arm_fwd_{side})", [f"arm_fwd_{side}"])
    # hands and feet can move around their own side: arms slide on the side wall (y, z), legs under the body (x, y)
    for side in "LR":
        a = f"arm_{side}"; iy, sy_ = axis_map(arm, a, Y); iz, sz_ = axis_map(arm, a, Z)
        drive(rig, a, "location", iy, f"{sy_}*arm_y_{side}", [f"arm_y_{side}"]); drive(rig, a, "location", iz, f"{sz_}*arm_z_{side}", [f"arm_z_{side}"])
        drive(rig, a, "scale", 1, f"arm_len_{side}", [f"arm_len_{side}"])      # bone Y runs along the arm (the Stretch To constraint, when on, takes over)
    for k in (1, 2, 3, 4):
        l = f"leg_{k}"; ix, sx_ = axis_map(arm, l, X); iy, sy_ = axis_map(arm, l, Y)
        drive(rig, l, "location", ix, f"{sx_}*leg_x_{k}", [f"leg_x_{k}"]); drive(rig, l, "location", iy, f"{sy_}*leg_y_{k}", [f"leg_y_{k}"])
        pb[l].rotation_mode = 'XYZ'
        drive(rig, l, "scale", 1, f"leg_len_{k}", [f"leg_len_{k}"])                       # bone Y runs along the leg (hip -> foot)
        drive(rig, l, "rotation_euler", ix, f"{sx_}*-radians(leg_rot_{k})", [f"leg_rot_{k}"])   # swing about the hip, + = foot forward (-Y)
    # root: hop and the jump to the cushion's resting place (root bone, world axes)
    rx_, rxs = axis_map(arm, "root", X); ry_, rys = axis_map(arm, "root", Y); rz_, rzs = axis_map(arm, "root", Z)
    drive(rig, "root", "location", rx_, f"{rxs}*(jump_t*cus_dx+move_x)", ["jump_t", "cus_dx", "move_x"]); drive(rig, "root", "location", ry_, f"{rys}*(jump_t*cus_dy+move_y)", ["jump_t", "cus_dy", "move_y"])
    pb["root"].rotation_mode = 'XYZ'; drive(rig, "root", "rotation_euler", rz_, f"{rzs}*radians(yaw)", ["yaw"])
    drive(rig, "root", "location", rz_, f"{rzs}*(hop+jump_t*(cus_dz+0.116))", ["hop", "jump_t", "cus_dz"])
    # reach: Stretch To the aim bone (no volume change: the arm gets longer, not thinner), then a limit of 2.3x its length
    for side in "LR":
        pbn = pb[f"arm_{side}"]
        for c in list(pbn.constraints): pbn.constraints.remove(c)
        st = pbn.constraints.new('STRETCH_TO'); st.name = "Aim"; st.target = rig; st.subtarget = f"aim_{side}"; st.volume = 'NO_VOLUME'; st.rest_length = 0.1
        lm = pbn.constraints.new('LIMIT_SCALE'); lm.name = "ReachLimit"; lm.owner_space = 'LOCAL'; lm.use_max_y = True; lm.max_y = REACH_MAX; lm.use_min_y = True; lm.min_y = 0.0
        lm.use_transform_limit = False
        fcs = st.driver_add("influence"); d = fcs.driver; d.type = 'SCRIPTED'; d.expression = f"arm_aim_{side}"; prop_var(rig, d, f"arm_aim_{side}", f"arm_aim_{side}")
    # the aim targets can follow the steering-wheel grips of the car (hands on the wheel); no car in the file = no constraint
    for side, grip in (("L", "CAR_WheelGrip_R"), ("R", "CAR_WheelGrip_L")):
        g = bpy.data.objects.get(grip)
        if not g: continue
        a_ = pb[f"aim_{side}"]
        for c in list(a_.constraints): a_.constraints.remove(c)
        cl = a_.constraints.new('COPY_LOCATION'); cl.name = "WheelGrip"; cl.target = g
        fcs = cl.driver_add("influence"); d = fcs.driver; d.type = 'SCRIPTED'; d.expression = f"aim_follow_{side}"; prop_var(rig, d, f"aim_follow_{side}", f"aim_follow_{side}")
    # squash: volume-keeping scale about the ground
    ih, _ = axis_map(arm, "squash", Z)
    drive(rig, "squash", "scale", ih, "1-0.3*(squash-0.22*talk)", ["squash", "talk"])
    for i in (0, 1, 2):
        if i != ih: drive(rig, "squash", "scale", i, "1/sqrt(1-0.3*(squash-0.22*talk))", ["squash", "talk"])
    # body: bob, lean (about world Y), nod (about world X), turn (about world Z)
    iby, sby = axis_map(arm, "body", Y); ibx, sbx = axis_map(arm, "body", X); ibz, sbz = axis_map(arm, "body", Z)
    drive(rig, "body", "location", ibz, f"{sbz}*(bob+0.012*talk)", ["bob", "talk"])
    drive(rig, "body", "rotation_euler", iby, f"{sby}*radians(lean)", ["lean"])   # lean + = toward viewer's right (+X)
    drive(rig, "body", "rotation_euler", ibx, f"{sbx}*radians(nod)", ["nod"])     # nod + = forward (-Y)
    drive(rig, "body", "rotation_euler", ibz, f"{sbz}*radians(turn)", ["turn"])
FWD = {}

def main():
    cleanup(); fetch_blush()
    rig = build_armature(); n = make_parts(rig); setup_controls(rig)
    return n
result = main()
