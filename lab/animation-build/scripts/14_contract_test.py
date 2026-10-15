"""Contract test: how a scene uses library_v1.blend. Runs headless on a COPY of the realistic scene (never the original):
  Blender -b lab/animation-build/contract_test/scene_copy.blend --python lab/animation-build/scripts/14_contract_test.py
Appends Claude + the human with their actions, plays an emotion, a blink and a talk pulse (baked from a test envelope) and renders stills."""
import bpy, os, sys, math, time, json
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LIB = os.path.join(ROOT, "animation-library/library_v1.blend"); OUT = os.path.join(ROOT, "animation-build/contract_test")
sys.path.insert(0, os.path.join(ROOT, "animation-build/scripts")); import claude_talk
sc = bpy.context.scene; t0 = time.time()
with bpy.data.libraries.load(LIB, link=False) as (s, d):
    d.collections = ["CLAUDE", "HUMAN", "PHONE", "CUSHION", "MAGIC"]; d.actions = [a for a in s.actions if a.startswith(("CLA_", "HUM_", "PHN_", "MAG_"))]
for c in d.collections:
    if c.name != "PHONE": sc.collection.children.link(c)
    else: sc.collection.children.link(c)
print("@@CT appended", [c.name for c in d.collections], len(d.actions), "actions in %.2fs" % (time.time() - t0))
O = bpy.data.objects
claude, human = O["RIG_Claude"], O["RIG_Human"]
# park them in an open spot of the scene (a real scene would place them in the car seats)
ref = O.get("CHAR_Claude"); base = ref.matrix_world.translation.copy() if ref else sc.camera.location.copy()
# test stage far below the city (the scene's CC0 textures are not next to this copy, so the city renders magenta): a grey floor
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, -100)); floor = bpy.context.active_object; floor.name = "TEST_floor"
fm = bpy.data.materials.new("TEST_floor"); fm.use_nodes = True; fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (.25, .26, .28, 1); floor.data.materials.append(fm)
wd = bpy.data.worlds.new("TEST_world"); wd.use_nodes = True; wd.node_tree.nodes["Background"].inputs[0].default_value = (.08, .09, .1, 1); sc.world = wd
claude.location = (-0.7, 0.0, -100.0); human.location = (0.9, 0.0, -100.0); bpy.context.view_layer.update()
for o in (O.get("CHAR_Claude"), O.get("CHAR_Human")):
    pass
def nla(rig, strips):
    ad = rig.animation_data_create(); ad.action = None
    for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
    for i, (an, st, bl) in enumerate(strips):
        tr = ad.nla_tracks.new(); s_ = tr.strips.new(an, st, bpy.data.actions[an]); s_.blend_type = bl; s_.extrapolation = "HOLD" if i == 0 else "NOTHING"
# talk pulse from a test envelope (24 samples/s, 3 syllables), baked into its own action
env = [0.0] * 4 + [0.9, 1.0, 0.6, 0.1, 0.0, 0.7, 0.95, 0.4, 0.0, 0.0, 0.8, 1.0, 0.5] + [0.0] * 8
claude.animation_data_create(); tmp = bpy.data.actions.new("CLA_talk_baked_TEST"); claude.animation_data.action = tmp
n = claude_talk.bake_talk(claude, env, start_frame=1, fps=24, env_rate=24); claude.animation_data.action = None
print("@@CT baked talk keys:", n)
nla(claude, [("CLA_idle", 1, "REPLACE"), ("CLA_emoeyes_happy", 20, "COMBINE"), ("CLA_emobody_happy", 20, "COMBINE"), ("CLA_blink", 40, "COMBINE"), ("CLA_talk_baked_TEST", 50, "COMBINE")])
nla(human, [("HUM_pose_seated", 1, "REPLACE"), ("HUM_seat_idle", 1, "COMBINE"), ("HUM_emobody_curious", 10, "COMBINE"), ("HUM_look_at_claude", 30, "COMBINE"), ("HUM_talk_small", 30, "COMBINE")])
# camera + light for the test
cam = bpy.data.objects.new("TEST_CAM", bpy.data.cameras.new("TEST_CAM")); sc.collection.objects.link(cam); cam.data.lens = 50
sun = bpy.data.objects.new("TEST_SUN", bpy.data.lights.new("TEST_SUN", 'SUN')); sun.data.energy = 4; sun.rotation_euler = (0.9, 0.2, 0.8); sc.collection.objects.link(sun)
for m in sc.timeline_markers: m.camera = None     # camera-bound markers would switch the camera back during the render
sc.render.engine = 'BLENDER_EEVEE_NEXT'; sc.eevee.taa_render_samples = 8; sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 640, 360, 100
sc.render.image_settings.file_format = "PNG"
import mathutils
def look(loc, tgt):
    cam.location = loc; cam.rotation_euler = (mathutils.Vector(tgt) - mathutils.Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); sc.camera = cam
cw = claude.matrix_world.translation; hw = human.matrix_world.translation
for o in list(O):
    if o.name.startswith(('CHAR_', 'CITY_', 'PROP_')): o.hide_render = True
shots = [("claude_idle_f8", 8, (cw.x, cw.y - 1.6, cw.z + 0.42), (cw.x, cw.y, cw.z + 0.3)), ("claude_happy_f30", 30, (cw.x, cw.y - 1.6, cw.z + 0.42), (cw.x, cw.y, cw.z + 0.3)), ("claude_blink_f42", 42, (cw.x, cw.y - 1.6, cw.z + 0.42), (cw.x, cw.y, cw.z + 0.3)),
         ("claude_talk_peak_f55", 55, (cw.x, cw.y - 1.6, cw.z + 0.42), (cw.x, cw.y, cw.z + 0.3)), ("human_curious_look_f45", 45, (hw.x + 0.5, hw.y - 2.0, hw.z + 1.25), (hw.x, hw.y, hw.z + 0.95))]
for name, f, loc, tgt in shots:
    sc.frame_set(f); look(loc, tgt); sc.render.filepath = os.path.join(OUT, name + ".png")
    t1 = time.time(); bpy.ops.render.render(write_still=True); print("@@CT rendered", name, "%.2fs" % (time.time() - t1))
# phone: the creator's holding pose, the chat reveal on the phone, a walk-texting frame
ph = O["PHN_Phone"]; ph.animation_data_create(); ph.animation_data.action = bpy.data.actions["PHN_chat_reveal"]
nla(human, [("HUM_phone_hold_read", 1, "REPLACE")])
for name, f, loc, tgt in (("human_phone_hold_f40", 40, (hw.x + 0.9, hw.y - 1.2, hw.z + 1.4), (hw.x - 0.1, hw.y - 0.15, hw.z + 1.25)), ("human_phone_chat_f105", 105, (hw.x + 0.9, hw.y - 1.2, hw.z + 1.4), (hw.x - 0.1, hw.y - 0.15, hw.z + 1.25))):
    sc.frame_set(f); look(loc, tgt); sc.render.filepath = os.path.join(OUT, name + ".png"); bpy.ops.render.render(write_still=True); print("@@CT rendered", name)
dg = bpy.context.evaluated_depsgraph_get()
sc.frame_set(55); e = claude.evaluated_get(dg); print("@@CT squash scale at f55", [round(x, 3) for x in e.pose.bones["squash"].scale], "talk=", round(e.pose.bones["ctrl"]["talk"], 3))
# phase 3: the cushion (hugged, then thrown) and the magic ring shot at a target, on the same rigs
nla(claude, [("CLA_cushion_hold_to_throw", 1, "REPLACE")])
sc.frame_set(18); look((cw.x + 0.7, cw.y - 1.8, cw.z + 0.6), (cw.x, cw.y, cw.z + 0.3)); sc.render.filepath = os.path.join(OUT, "claude_cushion_hold_f18.png"); bpy.ops.render.render(write_still=True); print("@@CT rendered claude_cushion_hold_f18")
claude.pose.bones["ctrl"]["cus_show"] = 0.0      # props that no active action keys keep their last value: put the cushion away
nla(claude, [("CLA_magic_cast", 1, "REPLACE")]); nla(O["MAG_Root"], [("MAG_ring_shoot", 8, "REPLACE")])
sc.frame_set(21); look((cw.x + 1.4, cw.y - 2.0, cw.z + 0.9), (cw.x, cw.y - 0.5, cw.z + 0.3)); sc.render.filepath = os.path.join(OUT, "claude_magic_f21.png"); bpy.ops.render.render(write_still=True); print("@@CT rendered claude_magic_f21")
print("@@CT done total %.1fs" % (time.time() - t0))
