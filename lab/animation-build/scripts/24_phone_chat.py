"""Phase 2 / milestone 2b: the phone's chat UI as properties + drivers, and the actions PHN_chat_reveal (120) and PHN_screen_glow (12).
Properties on PHN_Phone: chat_greeting (1 = greeting shown), chat_typed (0..24 characters typed), chat_sent (0/1), chat_reply (0/1), screen_glow (0..1.5, 1 = normal).
Drivers set hide_viewport/hide_render of the UI objects. Idempotent. Run via bridge."""
import bpy
ph = bpy.data.objects["PHN_Phone"]; O = bpy.data.objects
PROPS = {"chat_greeting": (1.0, 0.0, 1.0, "1 = greeting + avatar visible (before typing)"), "chat_typed": (0.0, 0.0, 24.0, "number of typed characters shown (the PHN_UI_Typed_NN objects)"),
         "chat_sent": (0.0, 0.0, 1.0, "1 = the user's message bubble is shown, placeholder returns"), "chat_reply": (0.0, 0.0, 1.0, "1 = Claude's reply shown"),
         "screen_glow": (1.0, 0.0, 1.5, "screen emission multiplier, 0 = asleep"), "phone_visible": (1.0, 0.0, 1.0, "0 = the whole phone (and its UI) is hidden, 1 = visible")}
for n, (dv, mn, mx, desc) in PROPS.items():
    ph[n] = float(dv); ui = ph.id_properties_ui(n); ui.update(default=float(dv), description=desc); ui.update(min=mn, max=mx); ui.update(soft_min=mn, soft_max=mx)
def hide_driver(o, expr):
    for p in ("hide_viewport", "hide_render"):
        if o.animation_data:
            for fc in list(o.animation_data.drivers):
                if fc.data_path == p: o.animation_data.drivers.remove(fc)
        fc = o.driver_add(p); d = fc.driver; d.type = 'SCRIPTED'; d.expression = expr
        for name in ("chat_greeting", "chat_typed", "chat_sent", "chat_reply"):
            if name in expr:
                v = d.variables.new(); v.name = name; v.type = 'SINGLE_PROP'; v.targets[0].id = ph; v.targets[0].data_path = f'["{name}"]'
for n in ("PHN_UI_Greeting", "PHN_UI_GreetAvatar"): hide_driver(O[n], "1 - (chat_greeting > 0.5)")
hide_driver(O["PHN_UI_Placeholder"], "1 - ((chat_typed < 0.5) + (chat_sent > 0.5) > 0)")
for k in range(1, 25):
    o = O.get(f"PHN_UI_Typed_{k:02d}")
    if o: hide_driver(o, f"1 - (abs(chat_typed - {k}) < 0.5) * (chat_sent < 0.5)")
for n in ("PHN_UI_UserBubble", "PHN_UI_UserText"): hide_driver(O[n], "1 - (chat_sent > 0.5)")
for n in ("PHN_UI_ReplyAvatar", "PHN_UI_ReplyText"): hide_driver(O[n], "1 - (chat_reply > 0.5)")
# whole-phone visibility: the phone root and the screen follow `phone_visible`; the UI objects also need their own state
def vis_driver(o, expr, props):
    for p in ("hide_viewport", "hide_render"):
        if o.animation_data:
            for fc in list(o.animation_data.drivers):
                if fc.data_path == p: o.animation_data.drivers.remove(fc)
        fc = o.driver_add(p); d = fc.driver; d.type = 'SCRIPTED'; d.expression = expr
        for name in props:
            v = d.variables.new(); v.name = name; v.type = 'SINGLE_PROP'; v.targets[0].id = ph; v.targets[0].data_path = f'["{name}"]'
vis_driver(ph, "1 - (phone_visible > 0.5)", ["phone_visible"])
# (children of PHN_Phone inherit its hidden state in the viewport and in renders only if they are hidden themselves, so fold the flag into their drivers)
for o in list(ph.children_recursive):
    if o.animation_data:
        for fc in list(o.animation_data.drivers):
            if fc.data_path in ("hide_viewport", "hide_render") and "phone_visible" not in fc.driver.expression:
                fc.driver.expression = f"({fc.driver.expression}) + (1 - (phone_visible > 0.5)) > 0"
                if not any(v.name == "phone_visible" for v in fc.driver.variables):
                    v = fc.driver.variables.new(); v.name = "phone_visible"; v.type = 'SINGLE_PROP'; v.targets[0].id = ph; v.targets[0].data_path = '["phone_visible"]'
    else: vis_driver(o, "1 - (phone_visible > 0.5)", ["phone_visible"])
# screen glow -> emission strength of the screen material
mat = bpy.data.materials["NEW_MAT_UI_Background"]; em = next(n for n in mat.node_tree.nodes if n.type == 'EMISSION')
s0 = em.inputs["Strength"].default_value
if mat.node_tree.animation_data:
    for fc in list(mat.node_tree.animation_data.drivers): mat.node_tree.animation_data.drivers.remove(fc)
fc = mat.node_tree.driver_add(f'nodes["{em.name}"].inputs[1].default_value'); d = fc.driver; d.type = 'SCRIPTED'; d.expression = f"{s0}*screen_glow"
v = d.variables.new(); v.name = "screen_glow"; v.type = 'SINGLE_PROP'; v.targets[0].id = ph; v.targets[0].data_path = '["screen_glow"]'
def build(name, keys, interp):
    old = bpy.data.actions.get(name)
    if old: bpy.data.actions.remove(old)
    a = bpy.data.actions.new(name); a.use_fake_user = True; ph.animation_data_create().action = a
    for f in sorted(keys):
        for p, val in keys[f].items(): ph[p] = float(val); ph.keyframe_insert(f'["{p}"]', frame=f)
    for fc in a.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = interp
    ph.animation_data.action = None
    for n, (dv, *_) in PROPS.items(): ph[n] = float(dv)
    return a
# chat reveal (120 frames @24): greeting 0-9, typing 12..60 (24 chars, one per 2 frames), send at 66, reply 1.5 s later (f102)
keys = {1: dict(chat_greeting=1, chat_typed=0, chat_sent=0, chat_reply=0), 10: dict(chat_greeting=0, chat_typed=0, chat_sent=0, chat_reply=0)}
for k in range(1, 25): keys[10 + 2 * k] = dict(chat_greeting=0, chat_typed=k, chat_sent=0, chat_reply=0)
keys[66] = dict(chat_greeting=0, chat_typed=24, chat_sent=1, chat_reply=0); keys[102] = dict(chat_greeting=0, chat_typed=24, chat_sent=1, chat_reply=1); keys[120] = dict(keys[102])
build("PHN_chat_reveal", keys, 'CONSTANT')
build("PHN_screen_glow", {1: dict(screen_glow=0.0), 5: dict(screen_glow=1.25), 9: dict(screen_glow=0.95), 12: dict(screen_glow=1.0)}, 'BEZIER')
result = [a.name for a in bpy.data.actions if a.name.startswith("PHN_")]
