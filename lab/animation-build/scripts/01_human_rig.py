"""Human rig (milestone 1): append the scan + simple rig, scale to 1.75 m, fit a Rigify metarig, generate,
move the weights to the DEF bones. Idempotent: rebuilds everything it owns (collection HUMAN, objects META_Human,
RIG_Human, HUM_Body). Run in Blender via the bridge, cwd lab/animation-build."""
import bpy, mathutils, os, math
from mathutils import Vector
V = Vector
ROOT = os.environ.get("ANIM_ROOT") or os.path.dirname(os.path.abspath(__import__("bpy").data.filepath))
SRC = os.path.join(ROOT, "snapshots", "character_selection_lab_2026-10-12.blend")
HEIGHT = 1.75

def remove_all(prefixes):
    for o in list(bpy.data.objects):
        if o.name in prefixes or o.get("anim_owner") == "human": bpy.data.objects.remove(o)

def append_source():
    for n in ("HUM_Body", "RIG_Human", "META_Human"):
        o = bpy.data.objects.get(n)
        if o: bpy.data.objects.remove(o)
    for c in list(bpy.data.collections):
        if c.name in ("STEP1_rig", "HUMAN"):
            for o in list(c.objects): bpy.data.objects.remove(o)
            bpy.data.collections.remove(c)
    with bpy.data.libraries.load(SRC, link=False) as (s, d):
        d.objects = ["HUM_Body", "RIG_Human"]
    col = bpy.data.collections.new("HUMAN"); bpy.context.scene.collection.children.link(col)
    for o in d.objects: col.objects.link(o)
    bpy.data.objects["RIG_Human"].name = "SRC_RIG_Human"
    return col

def apply_scale(body, rig):
    body.parent = None   # scale both separately; the body is parented to the new rig later
    ztop = max((body.matrix_world @ v.co).z for v in body.data.vertices)
    s = HEIGHT / ztop
    for o in (body, rig): o.scale = (s, s, s)
    bpy.ops.object.select_all(action='DESELECT')
    for o in (body, rig): o.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return s

def old_bones(rig):
    return {b.name: (V(b.head_local), V(b.tail_local)) for b in rig.data.bones}

def build_metarig(ob):
    """metarig from the default one: keep the body bones, move them onto the scan's skeleton."""
    bpy.ops.object.armature_human_metarig_add()
    m = bpy.context.active_object; m.name = "META_Human"; m.data.name = "META_Human"
    m["anim_owner"] = "human"
    default_z = {b.name: b.matrix_local.to_3x3().col[2].copy() for b in m.data.bones}
    bpy.ops.object.mode_set(mode='EDIT')
    eb = m.data.edit_bones
    keep = {"spine", "spine.001", "spine.002", "spine.003", "spine.004", "spine.005", "spine.006"}
    for side in "LR":
        keep |= {f"{n}.{side}" for n in ("shoulder", "upper_arm", "forearm", "hand", "thigh", "shin", "foot", "toe", "heel.02")}
        for f in ("index", "middle", "ring", "pinky"): keep |= {f"f_{f}.0{i}.{side}" for i in (1, 2, 3)}
        keep |= {f"thumb.0{i}.{side}" for i in (1, 2, 3)}
    for b in list(eb):
        if b.name not in keep: eb.remove(b)
    def put(name, head, tail, zref=None):
        b = eb[name]; b.head = head; b.tail = tail
        z = (default_z.get(name, V((0, -1, 0))))
        d = (tail - head).normalized(); z = z - d * z.dot(d)
        if z.length < 1e-4: z = V((0, -1, 0)) - d * V((0, -1, 0)).dot(d)
        b.align_roll(z.normalized())
    lerp = lambda a, b, t: a.lerp(b, t)
    ob_ = ob
    P, S, C, N, H = (ob_[k] for k in ("pelvis", "spine", "chest", "neck", "head"))
    put("spine", P[0], P[1]); put("spine.001", S[0], S[1])
    put("spine.002", C[0], lerp(C[0], C[1], .5)); put("spine.003", lerp(C[0], C[1], .5), C[1])
    put("spine.004", N[0], lerp(N[0], N[1], .5)); put("spine.005", lerp(N[0], N[1], .5), N[1])
    put("spine.006", H[0], H[1])
    for side in "LR":
        g = lambda n: ob_[f"{n}.{side}"]
        for n in ("shoulder", "upper_arm", "forearm", "hand", "thigh", "shin"): put(f"{n}.{side}", g(n)[0], g(n)[1])
        for f in ("index", "middle", "ring", "pinky"):
            for i in (1, 2, 3): put(f"f_{f}.0{i}.{side}", *g(f"f_{f}.0{i}"))
        for i in (1, 2, 3): put(f"thumb.0{i}.{side}", *g(f"thumb.0{i}"))
        ank, tip = g("foot")
        ball = lerp(ank, tip, .62); ball.z = tip.z
        fl = (tip - ank); fl.z = 0; fl.normalize()
        put(f"foot.{side}", ank, ball); put(f"toe.{side}", ball, tip)
        heel = ank - fl * 0.06; heel.z = 0
        sx = 1 if side == "L" else -1
        put(f"heel.02.{side}", heel - V((0.045 * sx, 0, 0)), heel + V((0.045 * sx, 0, 0)))
        for n in ("thigh", "upper_arm"): pass
        eb[f"shoulder.{side}"].parent = eb["spine.003"]
        eb[f"upper_arm.{side}"].parent = eb[f"shoulder.{side}"]
        for f in ("index", "middle", "ring", "pinky"): eb[f"f_{f}.01.{side}"].parent = eb[f"hand.{side}"]
        eb[f"thumb.01.{side}"].parent = eb[f"hand.{side}"]
        eb[f"thigh.{side}"].parent = eb["spine"]
        for n in ("upper_arm", "forearm", "hand", "thigh", "shin", "foot", "toe"): eb[f"{n}.{side}"].use_connect = n not in ("upper_arm", "thigh")
        for n in ("shoulder",): eb[f"{n}.{side}"].use_connect = False
        eb[f"heel.02.{side}"].parent = eb[f"foot.{side}"]; eb[f"heel.02.{side}"].use_connect = False
        eb[f"f_index.01.{side}"].use_connect = False
        for f in ("index", "middle", "ring", "pinky"):
            for i in (2, 3): eb[f"f_{f}.0{i}.{side}"].use_connect = True
            eb[f"f_{f}.01.{side}"].use_connect = False
        for i in (2, 3): eb[f"thumb.0{i}.{side}"].use_connect = True
        eb[f"thumb.01.{side}"].use_connect = False
    for n in ("spine.001", "spine.002", "spine.003", "spine.005", "spine.006"): eb[n].use_connect = True
    eb["spine.004"].use_connect = False   # Rigify wants the neck chain split from the torso chain (same position)
    bpy.ops.object.mode_set(mode='POSE')
    for pb in m.pose.bones:
        if pb.rigify_type in ("limbs.arm", "limbs.leg"):
            pb.rigify_parameters.segments = 1
    bpy.ops.object.mode_set(mode='OBJECT')
    return m

def close_hood(body):
    """fill the 10 open edges at the back of the neck (faces only, no new vertices: weights and shape keys stay valid)."""
    import bmesh
    bm = bmesh.new(); bm.from_mesh(body.data)
    edges = [e for e in bm.edges if e.is_boundary]
    n = len(edges)
    if n:
        bmesh.ops.holes_fill(bm, edges=edges, sides=12)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(body.data); bm.free()
    return n

def smooth(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)

def generate(m):
    bpy.ops.object.select_all(action='DESELECT'); m.select_set(True); bpy.context.view_layer.objects.active = m
    for o in list(bpy.data.objects):
        if o.name.startswith("RIG_Human"): bpy.data.objects.remove(o)
    m.data.rigify_rig_basename = "RIG_Human"
    bpy.ops.pose.rigify_generate()
    rig = bpy.data.objects["RIG_Human"]; rig["anim_owner"] = "human"
    for c in list(rig.users_collection): c.objects.unlink(rig)
    bpy.data.collections["HUMAN"].objects.link(rig)
    return rig

def transfer_weights(body, rig, ob, meta):
    """old bone groups -> DEF-* groups. chest/neck are split in two by height, foot gives some to the toe.
    The old groups stay as OLD_<name> (the HUM_Contact node tree reads them; they match no bone so they do not deform)."""
    me = body.data
    old = {g.index: g.name for g in body.vertex_groups}
    data = [{old[g.group]: g.weight for g in v.groups if g.group in old} for v in me.vertices]
    skip = {"KNEE_SMOOTH", "ARM_SMOOTH"}
    for g in list(body.vertex_groups):
        if g.name not in skip and not g.name.startswith("OLD_"): g.name = "OLD_" + g.name
    mb = meta.data.bones
    zc0, zc1 = ob["chest"][0].z, ob["chest"][1].z; zn0, zn1 = ob["neck"][0].z, ob["neck"][1].z
    new = {}
    def add(vi, grp, w):
        if w > 1e-5: new.setdefault(grp, {})[vi] = new.get(grp, {}).get(vi, 0) + w
    plain = {"pelvis": "DEF-spine", "spine": "DEF-spine.001", "head": "DEF-spine.006"}
    feet = {}
    for side in "LR":
        ank, tip = ob[f"foot.{side}"]
        ball = ank.lerp(tip, .62); ball.z = tip.z
        fl = (tip - ank); fl.z = 0; fl.normalize(); feet[side] = (ball, fl)
    for v in me.vertices:
        z = v.co.z; vi = v.index
        for name, w in data[v.index].items():
            if name in skip: continue
            if name in plain: add(vi, plain[name], w)
            elif name == "chest":
                t = smooth((z - zc0) / (zc1 - zc0)); add(vi, "DEF-spine.002", w * (1 - t)); add(vi, "DEF-spine.003", w * t)
            elif name == "neck":
                t = smooth((z - zn0) / (zn1 - zn0)); add(vi, "DEF-spine.004", w * (1 - t)); add(vi, "DEF-spine.005", w * t)
            elif name.startswith("foot."):
                side = name[-1]; ball, fl = feet[side]
                f = smooth(((v.co - ball).dot(fl)) / 0.04)
                add(vi, f"DEF-foot.{side}", w * (1 - f)); add(vi, f"DEF-toe.{side}", w * f)
            else: add(vi, "DEF-" + name, w)
    for g, d in new.items():
        vg = body.vertex_groups.new(name=g)
        for vi, w in d.items(): vg.add([vi], min(1.0, w), 'REPLACE')
    # contact node tree reads the groups by name
    ng = bpy.data.node_groups.get("HUM_Contact")
    if ng:
        for n in ng.nodes:
            if n.type == "INPUT_ATTRIBUTE":
                nm = n.inputs["Name"].default_value
                if nm and not nm.startswith("OLD_"): n.inputs["Name"].default_value = "OLD_" + nm
    for mod in body.modifiers:
        if mod.type == 'ARMATURE': mod.object = rig
        if mod.type == 'CORRECTIVE_SMOOTH': pass
    body.parent = rig; body.matrix_parent_inverse = mathutils.Matrix.Identity(4)
    return len(new)

def smooth_weights(body, repeat=3, factor=0.5):
    """relax the deform weights of the large joints (armpit, hip, spine) so poses stretch less; fingers/hands/toes are left alone."""
    bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); bpy.context.view_layer.objects.active = body
    keep_hard = ("DEF-f_", "DEF-thumb", "DEF-hand", "DEF-toe")
    for i, g in enumerate(body.vertex_groups):
        g.lock_weight = g.name.startswith(keep_hard) or not g.name.startswith("DEF-")
    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
    bpy.ops.object.vertex_group_smooth(group_select_mode='ALL', factor=factor, repeat=repeat, expand=0.0)
    bpy.ops.object.vertex_group_normalize_all(group_select_mode='BONE_DEFORM', lock_active=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    for g in body.vertex_groups: g.lock_weight = False

PAIR = {"torso": None}
def copy_neutral_pose(src, rig):
    """put the new FK controls into the old rig's neutral pose, using armature-space deltas (works across different bone rolls)."""
    order = []
    mp = {"spine": "spine_fk.001", "chest": "spine_fk.002", "neck": "neck", "head": "head"}
    for side in "LR":
        for n in ("shoulder", "upper_arm", "forearm", "hand"):
            mp[f"{n}.{side}"] = n if n == "shoulder" else f"{n}_fk"
        for n in ("thigh", "shin", "foot"): mp[f"{n}.{side}"] = f"{n}_fk"
        for f in ("index", "middle", "ring", "pinky"):
            for i in (1, 2, 3): mp[f"f_{f}.0{i}.{side}"] = f"f_{f}.0{i}"
        for i in (1, 2, 3): mp[f"thumb.0{i}.{side}"] = f"thumb.0{i}"
    # shoulder / finger controls have side suffix
    def newname(old, ctl):
        return ctl + ("." + old[-1] if old[-1] in "LR" and not ctl.endswith((".L", ".R")) and ctl not in ("neck", "head") and "spine" not in ctl else "")
    def depth(b):
        d = 0
        while b.parent: b = b.parent; d += 1
        return d
    pairs = []
    for old, ctl in mp.items():
        nn = newname(old, ctl)
        if old in src.pose.bones and nn in rig.pose.bones: pairs.append((old, nn))
    pairs.sort(key=lambda p: depth(src.data.bones[p[0]]))
    for rb in ("upper_arm_parent.L", "upper_arm_parent.R", "thigh_parent.L", "thigh_parent.R"):
        if rb in rig.pose.bones: rig.pose.bones[rb]["IK_FK"] = 1.0   # FK mode
    bpy.context.view_layer.update()
    missing = []
    for old, nn in pairs:
        sp, sb = src.pose.bones[old], src.data.bones[old]
        delta = sp.matrix @ sb.matrix_local.inverted()
        nb = rig.data.bones[nn]
        rig.pose.bones[nn].matrix = delta @ nb.matrix_local
        bpy.context.view_layer.update()
    import json
    st = {pb.name: [list(r) for r in pb.matrix_basis] for pb in rig.pose.bones if pb.matrix_basis != mathutils.Matrix.Identity(4)}
    rig["neutral_pose"] = json.dumps(st)
    return len(pairs)

def main():
    col = append_source()
    body, rig = bpy.data.objects["HUM_Body"], bpy.data.objects["SRC_RIG_Human"]
    closed = close_hood(body)
    s = apply_scale(body, rig)
    ob = old_bones(rig)
    src = rig
    m = build_metarig(ob)
    new = generate(m)
    n = transfer_weights(body, new, ob, m)
    smooth_weights(body)
    for o in (m, src): o.hide_viewport = True
    k = copy_neutral_pose(src, new)
    return s, n, k, closed
result = main()
