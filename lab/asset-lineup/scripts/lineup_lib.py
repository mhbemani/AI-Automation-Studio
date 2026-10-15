"""Shared helpers for the asset lineup (imported by build_lineup.py, refresh_human.py, render_lineup.py).
All source files are read-only: we only append from them into the lineup file."""
import bpy, bmesh, math, os, json, hashlib, subprocess, datetime
from pathlib import Path
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

HERE = Path(__file__).resolve().parent
LAB = HERE.parent                                   # lab/asset-lineup
MAIN = Path(os.environ.get("LU_MAIN_REPO", str(Path(__file__).resolve().parents[3]) if "__file__" in globals() else os.getcwd()))
SRC_NEW = MAIN / "lab/scene-realistic-car/scene.blend"
SRC_OLD = MAIN / "lab/scene-lowpoly-car/scene.blend"
SRC_HUMAN = MAIN / ".claude/worktrees/optimistic-wilson-150cb0/lab/character-selection/character_selection_lab.blend"
SNAP = LAB / "snapshots/human_snapshot.blend"
OUT = LAB / "lineup.blend"

PLINTH_H = 0.12          # plinth top is at z = PLINTH_H for every asset
ROW_Y = {"NEW": 4.3, "OLD": -4.3}


# ---------------------------------------------------------------- small utils
def git_info(path):
    try:
        rel = Path(path).resolve().relative_to(MAIN)
        h = subprocess.run(["git", "-C", str(MAIN), "log", "-1", "--format=%h", "--", str(rel)],
                           capture_output=True, text=True).stdout.strip()
        if h:
            return h
    except Exception:
        pass
    p = Path(path)
    mt = datetime.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M") if p.exists() else "?"
    return f"untracked (gitignored); file mtime {mt}"


def sha1(path):
    return hashlib.sha1(Path(path).read_bytes()).hexdigest()[:12]


def mat_simple(name, color, rough=0.6, metal=0.0, emit=None):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = 1.0
    return m


def new_mesh_obj(name, bm, mat, coll):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    if mat:
        me.materials.append(mat)
    coll.objects.link(o)
    return o


def box_obj(name, w, d, h, loc, mat, coll):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= w; v.co.y *= d; v.co.z *= h
    o = new_mesh_obj(name, bm, mat, coll)
    o.location = loc
    return o


def cyl_obj(name, r, h, loc, mat, coll, seg=32):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r, radius2=r, depth=h)
    o = new_mesh_obj(name, bm, mat, coll)
    o.location = loc
    return o


def text_obj(name, body, size, loc, rot, mat, coll, align="CENTER", parent=None):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.align_x = align
    cu.align_y = "CENTER"
    cu.materials.append(mat)
    o = bpy.data.objects.new(name, cu)
    o.location = loc
    o.rotation_euler = rot
    coll.objects.link(o)
    if parent:
        o.parent = parent
    return o


def subtree(root, objs):
    kids = {}
    for o in objs:
        kids.setdefault(o.parent, []).append(o)
    out, stack = [], [root]
    while stack:
        n = stack.pop()
        out.append(n)
        stack.extend(kids.get(n, []))
    return out


# ------------------------------------------------------ bounds, tris, textures
def world_bbox(objs):
    """World-space (min, max) of the evaluated render-visible geometry of objs."""
    dg = bpy.context.evaluated_depsgraph_get()
    lo = Vector((1e9, 1e9, 1e9)); hi = Vector((-1e9, -1e9, -1e9))
    found = False
    for o in objs:
        if o.type not in {"MESH", "CURVE", "SURFACE"} or o.hide_render:
            continue
        e = o.evaluated_get(dg)
        mw = e.matrix_world
        for c in e.bound_box:
            p = mw @ Vector(c)
            lo = Vector(map(min, lo, p)); hi = Vector(map(max, hi, p)); found = True
    return (lo, hi) if found else (Vector(), Vector())


def tri_count(objs):
    """Evaluated triangles of render-visible meshes (same method as lab/tools/polycount.py)."""
    dg = bpy.context.evaluated_depsgraph_get()
    cache, total = {}, 0
    for o in objs:
        if o.type != "MESH" or o.hide_render:
            continue
        key = (o.data.name, tuple((m.type, getattr(m, "levels", 0), getattr(m, "render_levels", 0)) for m in o.modifiers))
        if key not in cache:
            e = o.evaluated_get(dg)
            me = e.to_mesh(); me.calc_loop_triangles(); cache[key] = len(me.loop_triangles); e.to_mesh_clear()
        total += cache[key]
    return total


def textures_of(objs):
    seen = {}
    def walk(nt):
        for n in nt.nodes:
            if n.bl_idname == "ShaderNodeTexImage" and n.image:
                seen[n.image.name] = tuple(n.image.size)
            elif n.bl_idname == "ShaderNodeGroup" and n.node_tree:
                walk(n.node_tree)
    for o in objs:
        for s in getattr(o, "material_slots", []):
            if s.material and s.material.use_nodes:
                walk(s.material.node_tree)
    return seen


# ------------------------------------------------------------ placement
def clear_anim(objs):
    """Bake the current evaluated values (already flushed to the datablock) and unhook the actions
    so placement is not overridden; actions are kept with a fake user."""
    for o in objs:
        ad = o.animation_data
        if ad and ad.action:
            ad.action.use_fake_user = True
            ad.action = None


def detach(o):
    mw = o.matrix_world.copy()
    o.parent = None
    o.matrix_parent_inverse = Matrix.Identity(4)
    o.matrix_world = mw


def settle(objs=None):
    bpy.context.view_layer.update()


def yaw_to(root, objs, forward_from, forward_to, target_dir):
    """Rotate root about Z (around the asset's bbox centre) so the horizontal vector forward_from->forward_to
    points along target_dir."""
    v = Vector(forward_to) - Vector(forward_from); v.z = 0
    cur = math.atan2(v.y, v.x); want = math.atan2(target_dir[1], target_dir[0])
    lo, hi = world_bbox(objs); c = (lo + hi) / 2
    R = Matrix.Translation(c) @ Matrix.Rotation(want - cur, 4, "Z") @ Matrix.Translation(-c)
    root.matrix_world = R @ root.matrix_world
    settle()


def put_on_plinth(root, objs, xy, top=PLINTH_H):
    lo, hi = world_bbox(objs)
    c = (lo + hi) / 2
    root.matrix_world = Matrix.Translation((xy[0] - c.x, xy[1] - c.y, top - lo.z)) @ root.matrix_world
    settle()


def centre_of(o):
    return o.matrix_world.translation.copy()


def dup_hierarchy(objs, root, coll, suffix):
    """Linked duplicate of a hierarchy (shared mesh/curve data)."""
    m = {o: o.copy() for o in objs}
    for o, n in m.items():
        n.name = o.name + suffix
        n.parent = m.get(o.parent)
        n.matrix_parent_inverse = o.matrix_parent_inverse.copy()
        n.animation_data_clear()
        coll.objects.link(n)
    return m[root], list(m.values())


# --------------------------------------------------------------- lighting
def apply_light(preset, scene=None):
    """Switch the lighting preset: 'studio' (neutral) or 'golden' (realistic scene's sunset sky + sun)."""
    sc = scene or bpy.context.scene
    assert preset in ("studio", "golden"), preset
    def walk(lc):
        for c in lc.children:
            if c.name == "LU_LIGHT_Studio":
                c.exclude = preset != "studio"
            elif c.name == "LU_LIGHT_Golden":
                c.exclude = preset != "golden"
            walk(c)
    walk(sc.view_layers[0].layer_collection)
    sc.world = bpy.data.worlds["LU_World_Studio" if preset == "studio" else "LU_World_Golden"]
    sc["lineup_light"] = preset


# --------------------------------------------------------------- cameras
def make_camera(name, coll, lens=50.0):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start = 0.05
    cd.clip_end = 400
    o = bpy.data.objects.new(name, cd)
    coll.objects.link(o)
    return o


def look_at(cam, eye, target):
    cam.location = eye
    d = Vector(target) - Vector(eye)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def corners(lo, hi):
    return [Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]


def fit_camera(cam, lo, hi, az_deg, el_deg, margin=0.06, lens=None, aim_shift=(0, 0, 0)):
    """Place cam on the sphere around the box centre at azimuth az (0 = looking along +Y from -Y... see below) and elevation el,
    at the smallest distance that keeps every box corner inside the frame. az=-90 means camera on the -Y side."""
    sc = bpy.context.scene
    if lens:
        cam.data.lens = lens
    sc.camera = cam
    c = (lo + hi) / 2 + Vector(aim_shift)
    az = math.radians(az_deg); el = math.radians(el_deg)
    d = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
    pts = corners(lo, hi)
    def ok(dist):
        look_at(cam, c + d * dist, c)
        bpy.context.view_layer.update()
        for p in pts:
            v = world_to_camera_view(sc, cam, p)
            if v.z <= 0 or not (margin <= v.x <= 1 - margin and margin <= v.y <= 1 - margin):
                return False
        return True
    a, b = 0.5, 400.0
    for _ in range(40):
        m = (a + b) / 2
        if ok(m): b = m
        else: a = m
    ok(b)
    return b


# --------------------------------------------------------------- human
HUMAN_NAMES = ("HUM_Body", "RIG_Human")


def append_human(src, coll):
    """Append HUM_Body + RIG_Human (+ materials, modifier node group) from the snapshot of the selection lab file."""
    with bpy.data.libraries.load(str(src), link=False) as (df, dt):
        dt.objects = [n for n in df.objects if n in HUMAN_NAMES]
    objs = [o for o in dt.objects if o]
    for o in objs:
        o.name = "LU_NEW_" + o.name
        if o.data:
            o.data.name = "NEW_" + o.data.name
        coll.objects.link(o)
    rig = next(o for o in objs if o.type == "ARMATURE")
    for pb in rig.pose.bones:       # rest pose
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
    return rig, objs
