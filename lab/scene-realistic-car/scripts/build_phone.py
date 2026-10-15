# Phone screen: a chat UI in the spirit of the Claude mobile app (warm off-white theme, input bar at the bottom,
# the user's message as a bubble on the right, Claude's reply as plain text with a small orange avatar on the left).
# No real logos: the avatar is a plain orange disc. Children of PROP_Phone_Screen (screen-local: x across, z up,
# the visible face is -Y). Re-runnable: rebuilds objects tagged cs_owner "phone_ui".
# States (custom props on PROP_Phone, applied by set_state(); the animate step keys hide_render per object):
#   0 new chat (greeting)   1 typing: PROP_UI_Typed_NN shows the first NN characters in the input bar
#   2 sent: the message bubble   3 Claude's reply below it
# Run with STATE / CHARS set to preview: python3 bridge/bl.py exec 'STATE=1; CHARS=12' then file scripts/build_phone.py
import bpy, bmesh, math
from mathutils import Vector, Matrix

MESSAGE = "Claude, I wanna go home."
REPLY = "On my way! I'll be there in about two minutes."
GREETING = "How can I help you today?"
STATE = globals().get("STATE", 3); CHARS = globals().get("CHARS", len(MESSAGE))

for o in [o for o in bpy.data.objects if o.get("cs_owner") == "phone_ui" and not o.get("user_locked")]:
    bpy.data.objects.remove(o)
scr = bpy.data.objects["PROP_Phone_Screen"]; phone = bpy.data.objects["PROP_Phone"]; PROPS = bpy.data.collections["06_PROPS"]
old = bpy.data.objects.get("PROP_Phone_Text")
if old: bpy.data.objects.remove(old)            # the v1 static message is replaced by this UI
W, H, FACE = 0.068, 0.138, -0.0012               # screen size; UI sits just in front of the screen face (local -Y)

def emit_mat(name, color, strength=1.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial"); e = nt.nodes.new("ShaderNodeEmission")
    e.inputs[0].default_value = (*color, 1); e.inputs[1].default_value = strength; nt.links.new(e.outputs[0], o.inputs[0])
    m.diffuse_color = (*color, 1); return m
BG = emit_mat("MAT_UI_Background", (0.93, 0.91, 0.86), 1.2)          # warm off-white
BAR = emit_mat("MAT_UI_InputBar", (1.0, 1.0, 0.99), 1.3)
BUBBLE = emit_mat("MAT_UI_UserBubble", (0.86, 0.83, 0.76), 1.2)
ORANGE = emit_mat("MAT_UI_Orange", (0.85, 0.38, 0.22), 1.3)
TEXT = emit_mat("MAT_UI_Text", (0.09, 0.08, 0.07), 1.0)
GREY = emit_mat("MAT_UI_TextGrey", (0.48, 0.46, 0.43), 1.0)
LINE = emit_mat("MAT_UI_Divider", (0.8, 0.78, 0.73), 1.1)
scr.data.materials.clear(); scr.data.materials.append(BG)

def plate(name, x0, x1, z0, z1, m, depth=0.0004, power=6, y=0.0):
    """Flat rounded rectangle (superellipse) in screen space."""
    cx, cz, hx, hz = (x0 + x1) / 2, (z0 + z1) / 2, (x1 - x0) / 2, (z1 - z0) / 2
    bm = bmesh.new(); N = 48; e = 2 / power
    ring = [(math.copysign(abs(math.cos(t)) ** e, math.cos(t)) * hx, math.copysign(abs(math.sin(t)) ** e, math.sin(t)) * hz)
            for t in (2 * math.pi * i / N for i in range(N))]
    vs = [bm.verts.new((cx + a, FACE - y, cz + b)) for a, b in ring]
    f = bm.faces.new(vs); f.normal_update()
    if f.normal.y > 0: f.normal_flip()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(m)
    o = bpy.data.objects.new(name, me); o["cs_owner"] = "phone_ui"; PROPS.objects.link(o)
    o.parent = scr; o.matrix_parent_inverse = Matrix(); return o

def text(name, body, x, z, size, m, align="LEFT", width=None, y=0.0003):
    cu = bpy.data.curves.new(name, "FONT"); cu.body = body; cu.size = size; cu.align_x = align; cu.align_y = "CENTER"
    if width: cu.text_boxes[0].width = width; cu.text_boxes[0].x = {"LEFT": 0, "CENTER": -width / 2, "RIGHT": -width}[align]
    cu.materials.append(m)
    o = bpy.data.objects.new(name, cu); o["cs_owner"] = "phone_ui"; PROPS.objects.link(o)
    o.parent = scr; o.matrix_parent_inverse = Matrix()
    o.location = (x, FACE - y - 0.0004, z); o.rotation_euler = (math.radians(90), 0, 0); return o

# header
text("PROP_UI_Title", "Claude", 0.0, H - 0.012, 0.0052, TEXT, align="CENTER")
plate("PROP_UI_Divider", -W / 2 + 0.003, W / 2 - 0.003, H - 0.0185, H - 0.018, LINE, power=2)
# state 0: greeting
g = [plate("PROP_UI_GreetAvatar", -0.004, 0.004, 0.084, 0.092, ORANGE, power=2),
     text("PROP_UI_Greeting", GREETING, 0.0, 0.074, 0.0042, TEXT, align="CENTER")]
# input bar + placeholder + send button
plate("PROP_UI_InputBar", -W / 2 + 0.003, W / 2 - 0.003, 0.006, 0.020, BAR, power=5)
ph = text("PROP_UI_Placeholder", "Reply to Claude...", -W / 2 + 0.006, 0.013, 0.0036, GREY)
plate("PROP_UI_Send", W / 2 - 0.0125, W / 2 - 0.0055, 0.0095, 0.0165, ORANGE, power=2, y=0.0002)
text("PROP_UI_SendArrow", "↑", W / 2 - 0.009, 0.0131, 0.0045, BAR, align="CENTER", y=0.0004)
typed = [text(f"PROP_UI_Typed_{n:02d}", MESSAGE[:n] + "|", -W / 2 + 0.006, 0.013, 0.0034, TEXT) for n in range(1, len(MESSAGE) + 1)]
# state 2: the user's bubble (right), state 3: Claude's reply (left, plain text with avatar)
bub = [plate("PROP_UI_UserBubble", -0.004, W / 2 - 0.004, 0.083, 0.101, BUBBLE, power=5),
       text("PROP_UI_UserText", MESSAGE, W / 2 - 0.007, 0.092, 0.0037, TEXT, align="RIGHT", width=0.032)]
rep = [plate("PROP_UI_ReplyAvatar", -W / 2 + 0.004, -W / 2 + 0.010, 0.069, 0.075, ORANGE, power=2),
       text("PROP_UI_ReplyText", REPLY, -W / 2 + 0.012, 0.066, 0.0037, TEXT, width=0.048)]

def set_state(state, chars):
    show = lambda objs, v: [setattr(o, a, not v) for o in objs for a in ("hide_render", "hide_viewport")]
    show(g, state == 0); show(bub, state >= 2); show(rep, state >= 3); show([ph], state == 0 or state >= 2)
    for n, o in enumerate(typed, 1): show([o], state == 1 and n == chars)
    phone["ui_state"], phone["ui_chars"] = state, chars
set_state(STATE, CHARS)
result = {"ui_objects": len([o for o in bpy.data.objects if o.get("cs_owner") == "phone_ui"]), "state": STATE, "chars": CHARS}
