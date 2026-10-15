import bpy
def setup_view(cam_loc=(1.0,-1.9,1.05), cam_tgt=(0.0,0.0,0.88), lens=50, seat=True):
    exec(open("scripts/_cam.py").read(), globals()); exec(open("scripts/rigtest_lib.py").read(), globals())
    studio(); iso("HUM_Body","RIG_Human","ANIM_","ANIM_seat")
    rig = bpy.data.objects["RIG_Human"]; rig.hide_render = True; rig.hide_viewport = False
    for o in bpy.data.objects:
        if o.name in ("HUM_PhoneSocket",) or o.name.startswith("PHN_"): o.hide_viewport = o.hide_render = True
    s = bpy.data.objects.get("ANIM_seat")
    if seat and not s:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0.03, 0.12, 0.2)); s = bpy.context.active_object; s.name = "ANIM_seat"; s.scale = (0.5, 0.55, 0.4); s["anim_debug"] = 1
        m = bpy.data.materials.get("ANIM_seatmat") or bpy.data.materials.new("ANIM_seatmat"); m.diffuse_color = (.12, .12, .14, 1)
        m.use_nodes = True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (.12, .12, .14, 1); s.data.materials.append(m)
        bk = bpy.data.objects.new("ANIM_seatback", s.data); bpy.context.scene.collection.objects.link(bk); bk.location = (0.03, 0.42, 0.65); bk.scale = (0.5, 0.08, 0.7); bk["anim_debug"] = 1
    for n in ("ANIM_seat", "ANIM_seatback"):
        if n in bpy.data.objects: o = bpy.data.objects[n]; o.hide_viewport = o.hide_render = not seat
    cam(cam_loc, cam_tgt, lens)
def nla(strips, rigname="RIG_Human"):
    """strips = [(action, start_frame, blend)] ; first is the base (REPLACE, hold)."""
    rig = bpy.data.objects[rigname]; ad = rig.animation_data_create(); ad.action = None
    for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
    for i, (an, st, bl) in enumerate(strips):
        tr = ad.nla_tracks.new(); s = tr.strips.new(an, st, bpy.data.actions[an]); s.blend_type = bl; s.extrapolation = "HOLD" if i == 0 else "HOLD_FORWARD" if bl == "COMBINE" and False else ("HOLD" if i == 0 else "NOTHING")
def nla_clear(rigname="RIG_Human"):
    ad = bpy.data.objects[rigname].animation_data
    for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
