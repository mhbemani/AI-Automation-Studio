"""Contact rule as a Geometry Nodes modifier after the Armature modifier ("HUM_Contact").
For each pair of body parts (part A = vertices mostly on group(s) a, part B = mostly on group(s) b):
  a B-vertex that has gone inside part A's surface (deeper than 2 mm) is pushed back toward A's surface by half the
  depth, and the same for A-vertices inside B -> both surfaces meet in the middle and flatten against each other
  instead of passing through. Each vertex moves at most MAX_PUSH (env MAX_PUSH, default 0.01 m = 1 cm).
Pairs now: thigh vs shin+foot on each leg (back of the knee). More pairs (arm vs chest) can be added to PAIRS.
Run: Blender -b --factory-startup character_selection_lab.blend --python scripts/add_contact.py  (env OUT=)"""
import bpy, os
MAX_PUSH = float(os.environ.get("MAX_PUSH", "0.01"))
CONTACT_RANGE = 0.04  # a vertex counts as pressing into the other part only within 4 cm of its surface
PAIRS = [(["thigh.L"], ["shin.L", "foot.L"]), (["thigh.R"], ["shin.R", "foot.R"])]
if os.environ.get("ARMS") == "1":   # arm vs body (chest/spine/pelvis), and the inner elbow (upper arm vs forearm)
    TORSO = ["chest", "spine", "pelvis"]
    PAIRS += [(TORSO, [f"upper_arm.{s}", f"forearm.{s}"]) for s in "LR"] + [([f"upper_arm.{s}"], [f"forearm.{s}"]) for s in "LR"]
o = bpy.data.objects["HUM_Body"]
ng = bpy.data.node_groups.get("HUM_Contact") or bpy.data.node_groups.new("HUM_Contact", 'GeometryNodeTree')
ng.nodes.clear(); ng.interface.clear()
ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
N, L = ng.nodes, ng.links
gin = N.new("NodeGroupInput"); gout = N.new("NodeGroupOutput")
pos = N.new("GeometryNodeInputPosition")
def weight_sum(names):
    out = None
    for nm in names:
        na = N.new("GeometryNodeInputNamedAttribute"); na.data_type = 'FLOAT'; na.inputs["Name"].default_value = nm
        if out is None: out = na.outputs["Attribute"]
        else:
            m = N.new("ShaderNodeMath"); m.operation = 'ADD'; L.new(out, m.inputs[0]); L.new(na.outputs["Attribute"], m.inputs[1]); out = m.outputs[0]
    return out
def gt(x, t):
    c = N.new("FunctionNodeCompare"); c.data_type = 'FLOAT'; c.operation = 'GREATER_THAN'; L.new(x, c.inputs["A"]); c.inputs["B"].default_value = t; return c.outputs["Result"]
def push_out_of(target_sel, mover_sel):
    """offset field for mover points that are inside the part selected by target_sel"""
    sep = N.new("GeometryNodeSeparateGeometry"); sep.domain = 'POINT'
    L.new(gin.outputs[0], sep.inputs["Geometry"]); L.new(target_sel, sep.inputs["Selection"])
    prox = N.new("GeometryNodeProximity"); prox.target_element = 'FACES'
    L.new(sep.outputs["Selection"], prox.inputs[0])
    snm = N.new("GeometryNodeSampleNearestSurface"); snm.data_type = 'FLOAT_VECTOR'
    nrm = N.new("GeometryNodeInputNormal")
    L.new(sep.outputs["Selection"], snm.inputs["Mesh"]); L.new(nrm.outputs[0], snm.inputs["Value"])
    d = N.new("ShaderNodeVectorMath"); d.operation = 'SUBTRACT'                 # nearest - p
    L.new(prox.outputs["Position"], d.inputs[0]); L.new(pos.outputs[0], d.inputs[1])
    dot = N.new("ShaderNodeVectorMath"); dot.operation = 'DOT_PRODUCT'           # (nearest - p) . n  > 0  => p is inside
    L.new(d.outputs[0], dot.inputs[0]); L.new(snm.outputs["Value"], dot.inputs[1])
    inside = gt(dot.outputs["Value"], 0.002)
    near = N.new("FunctionNodeCompare"); near.data_type = 'FLOAT'; near.operation = 'LESS_THAN'   # only real contacts:
    L.new(prox.outputs["Distance"], near.inputs["A"]); near.inputs["B"].default_value = CONTACT_RANGE  # the parts' surfaces
    both = N.new("FunctionNodeBooleanMath"); both.operation = 'AND'                                    # are open, so far
    L.new(inside, both.inputs[0]); L.new(mover_sel, both.inputs[1])                                    # points can look
    both2 = N.new("FunctionNodeBooleanMath"); both2.operation = 'AND'                                  # "inside" by mistake
    L.new(both.outputs[0], both2.inputs[0]); L.new(near.outputs["Result"], both2.inputs[1]); both = both2
    half = N.new("ShaderNodeVectorMath"); half.operation = 'SCALE'; half.inputs["Scale"].default_value = 0.5
    L.new(d.outputs[0], half.inputs[0])
    ln = N.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'; L.new(half.outputs[0], ln.inputs[0])
    lim = N.new("ShaderNodeMath"); lim.operation = 'DIVIDE'; lim.inputs[0].default_value = MAX_PUSH
    mx = N.new("ShaderNodeMath"); mx.operation = 'MAXIMUM'; mx.inputs[1].default_value = 1e-6; L.new(ln.outputs["Value"], mx.inputs[0])
    L.new(mx.outputs[0], lim.inputs[1])
    mn = N.new("ShaderNodeMath"); mn.operation = 'MINIMUM'; mn.inputs[1].default_value = 1.0; L.new(lim.outputs[0], mn.inputs[0])
    sc = N.new("ShaderNodeVectorMath"); sc.operation = 'SCALE'; L.new(half.outputs[0], sc.inputs[0]); L.new(mn.outputs[0], sc.inputs["Scale"])
    sw = N.new("GeometryNodeSwitch"); sw.input_type = 'VECTOR'
    L.new(both.outputs[0], sw.inputs["Switch"]); L.new(sc.outputs[0], sw.inputs["True"])
    return sw.outputs[0]
total = None
for A, Bn in PAIRS:
    a = gt(weight_sum(A), 0.5); b = gt(weight_sum(Bn), 0.5)
    for off in (push_out_of(a, b), push_out_of(b, a)):
        if total is None: total = off
        else:
            add = N.new("ShaderNodeVectorMath"); add.operation = 'ADD'; L.new(total, add.inputs[0]); L.new(off, add.inputs[1]); total = add.outputs[0]
setp = N.new("GeometryNodeSetPosition")
L.new(gin.outputs[0], setp.inputs["Geometry"]); L.new(total, setp.inputs["Offset"]); L.new(setp.outputs[0], gout.inputs[0])
mod = o.modifiers.get("HUM_Contact") or o.modifiers.new("HUM_Contact", 'NODES')
mod.node_group = ng
# keep it after the Armature modifier
o.modifiers.move(o.modifiers.find("HUM_Contact"), o.modifiers.find("Armature") + 1)   # right after the bones, before the smoothing
print("CONTACT modifier", [m.name for m in o.modifiers], "pairs", len(PAIRS), "max push", MAX_PUSH)
bpy.ops.wm.save_as_mainfile(filepath=os.environ.get("OUT", bpy.data.filepath))
