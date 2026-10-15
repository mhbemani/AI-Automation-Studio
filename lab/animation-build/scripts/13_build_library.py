"""Build lab/animation-library/library_v1.blend from anim_work.blend (headless):
   /Applications/Blender.app/Contents/MacOS/Blender -b lab/animation-build/anim_work.blend --python lab/animation-build/scripts/13_build_library.py
Keeps collections HUMAN, CLAUDE, CAR, PHONE, CUSHION, MAGIC (+ the hidden metarig in REGEN), only CLA_/HUM_/CAR_ actions (fake users, marked as assets),
resets every rig to its default pose and removes all previews/debug objects, lights, cameras and source copies."""
import bpy, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = os.path.join(ROOT, "lab/animation-library/library_v1.blend")
KEEP = ("HUMAN", "CLAUDE", "CAR", "PHONE", "CUSHION", "MAGIC")
sc = bpy.context.scene
# metarig into its own hidden collection
regen = bpy.data.collections.get("REGEN") or bpy.data.collections.new("REGEN")
if "REGEN" not in [c.name for c in sc.collection.children]: sc.collection.children.link(regen)
meta = bpy.data.objects.get("META_Human")
if meta:
    for c in list(meta.users_collection): c.objects.unlink(meta)
    regen.objects.link(meta)
# the Rigify-generated rig lands in the metarig's collection: move it into HUMAN
rh = bpy.data.objects.get("RIG_Human")
if rh:
    for c in list(rh.users_collection): c.objects.unlink(rh)
    bpy.data.collections["HUMAN"].objects.link(rh)
# remove everything outside the kept collections
keepc = KEEP + ("REGEN",)
for o in list(bpy.data.objects):
    cols = [c.name for c in o.users_collection]
    if not any(c in keepc for c in cols) or o.get("anim_debug") or o.name.startswith(("SRC_", "DBG_", "ANIM_")): bpy.data.objects.remove(o)
for c in list(sc.collection.children):
    if c.name not in keepc: sc.collection.children.unlink(c)
for c in list(bpy.data.collections):
    if c.name not in keepc and not c.users: bpy.data.collections.remove(c)
# actions: ours only
for a in list(bpy.data.actions):
    if not a.name.startswith(("CLA_", "HUM_", "CAR_", "PHN_", "MAG_")): bpy.data.actions.remove(a)
# visibility + clean state
for o in bpy.data.objects:
    o.hide_viewport = False; o.hide_render = False; o.hide_set(False)
    if o.animation_data:
        o.animation_data.action = None
        for t in list(o.animation_data.nla_tracks): o.animation_data.nla_tracks.remove(t)
for o in bpy.data.objects:
    if o.name in ("CAR_ctrl", "HUM_PhoneSocket") or o.type == 'ARMATURE': o.hide_render = True
if meta: meta.hide_viewport = True; meta.hide_render = True
for lc in bpy.context.view_layer.layer_collection.children:
    lc.exclude = False
    if lc.name == "REGEN": lc.hide_viewport = True
# rigs: all bone collections visible again, Rigify custom shapes on, everything selectable
for rn in ("RIG_Human", "RIG_Claude"):
    rg = bpy.data.objects[rn]
    if rn == "RIG_Human":
        for c in rg.data.collections_all: c.is_visible = True
        rg.data.show_bone_custom_shapes = True; rg.data.show_names = False
for o in bpy.data.objects: o.hide_select = False
# rigs back to default
import json, mathutils
for rn in ("RIG_Human", "RIG_Claude"):
    r = bpy.data.objects[rn]
    for pb in r.pose.bones: pb.matrix_basis = mathutils.Matrix.Identity(4)
h = bpy.data.objects["RIG_Human"]
for n, m in json.loads(h["neutral_pose"]).items(): h.pose.bones[n].matrix_basis = mathutils.Matrix(m)
c = bpy.data.objects["RIG_Claude"].pose.bones["ctrl"]
for k in c.keys():
    try: c[k] = float(c.id_properties_ui(k).as_dict()["default"])
    except Exception: pass
cc = bpy.data.objects["CAR_ctrl"]
for k, v in dict(distance=0.0, speed=0.0, steer=0.0, door_L=0.0, door_R=0.0, dash_glow=0.0).items(): cc[k] = v
mr = bpy.data.objects["MAG_Root"]
for k, v in dict(fade=0.0, shot=0.0, dist=1.2, size=1.0, wrap=0.0, wrap_to=0.7, spin_rate=1.0, puff=0.0, sparkle=0.0).items(): mr[k] = v
mr.rotation_mode = "XYZ"; mr.rotation_euler = (0, 0, 0)
ph_ = bpy.data.objects["PHN_Phone"]
for k, v in dict(chat_greeting=1.0, chat_typed=0.0, chat_sent=0.0, chat_reply=0.0, screen_glow=1.0, phone_visible=1.0).items(): ph_[k] = v
# scene
sc.render.fps = 24; sc.render.fps_base = 1; sc.frame_start = 1; sc.frame_end = 96; sc.frame_set(1); sc.unit_settings.system = 'METRIC'
sc.camera = None
# assets
TAGS = {"CLA_": "Claude", "HUM_": "Human", "CAR_": "Car", "PHN_": "Phone", "MAG_": "Magic"}
for a in bpy.data.actions:
    a.use_fake_user = True; a.asset_mark()
    a.asset_data.tags.new(next(v for k, v in TAGS.items() if a.name.startswith(k)), skip_if_exists=True)
    kind = "pose" if ("_pose_" in a.name or "_emo" in a.name or "_look_" in a.name) else "loop" if any(x in a.name for x in ("idle", "talk_small", "talk_pulse", "wheel_spin", "sway", "hold_read", "phone_type", "walk_cycle", "walk_texting", "hands_lap", "look_out_window", "gesture", "hold_wheel", "arm_wiggle", "run_cycle", "run_carry", "cushion_jump", "cushion_sit", "cushion_sleep", "happy_stand", "react_giggle")) else "one-shot"
    a.asset_data.tags.new(kind, skip_if_exists=True); a.asset_data.description = f"{a.name} ({kind}); see lab/animation-library/CONTRACT.md"
for cn in KEEP:
    col = bpy.data.collections[cn]; col.asset_mark(); col.asset_data.description = f"{cn} rig with controls (see CONTRACT.md)"
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("@@LIB", OUT, os.path.getsize(OUT), len(bpy.data.objects), len(bpy.data.actions))
