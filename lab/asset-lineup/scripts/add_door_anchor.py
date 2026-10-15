"""Create the hinge anchor of a door from the vertices you selected on the body, and make the door stick to it.
Reads the selected vertices of LU_NEW_CAR_Ext_Body (edit selection saved in the file), takes their centre, and on that side
(+x = Door_L, -x = Door_R):  creates one tiny Empty  LU_NEW_CAR_DoorAnchor_<side>  (parent: car root, size 1 cm, nothing else),
moves the door's pivot (origin) onto it without moving any geometry, and adds a Copy Location constraint so the door follows the anchor.
Reads IN.blend, writes OUT.blend (never the input):
  Blender -b --factory-startup IN.blend --python lab/asset-lineup/scripts/add_door_anchor.py -- OUT.blend"""
import bpy, bmesh, sys
from mathutils import Vector, Matrix
out = sys.argv[sys.argv.index("--") + 1]
P = lambda n: bpy.data.objects["LU_NEW_CAR_" + n]
root, body = P("Exterior"), P("Ext_Body")
if body.mode != "OBJECT":
    bpy.context.view_layer.objects.active = body; bpy.ops.object.mode_set(mode="OBJECT")
inv = root.matrix_world.inverted()
sel = [inv @ (body.matrix_world @ v.co) for v in body.data.vertices if v.select]
print("selected body vertices:", len(sel))
HINGE = {1: Vector((0.9893, -0.82, 2.62)), -1: Vector((-0.9893, -0.82, 2.62))}   # where make_doors.py put each door's pivot (doors closed, in place)
for sx, side in ((1, "L"), (-1, "R")):                      # put both doors back in place first (they may have been moved aside while editing)
    dd = P("Door_" + side)
    if (dd.location - HINGE[sx]).length > 1e-3:
        print(side, "door was moved aside by", tuple(round(x, 3) for x in (dd.location - HINGE[sx])), "- putting it back")
        dd.location = HINGE[sx]
bpy.context.view_layer.update()
for sx, side in ((1, "L"), (-1, "R")):
    pts = [p for p in sel if p.x * sx > 0]
    if not pts: continue
    c = sum(pts, Vector()) / len(pts)
    name = f"LU_NEW_CAR_DoorAnchor_{side}"
    a = bpy.data.objects.get(name) or bpy.data.objects.new(name, None)
    if a.name not in bpy.context.scene.collection.all_objects: body.users_collection[0].objects.link(a)
    a.empty_display_type = "PLAIN_AXES"; a.empty_display_size = 0.01
    a.parent = root; a.matrix_parent_inverse = Matrix.Identity(4); a.location = c
    d = P("Door_" + side)
    # move the door's origin onto the anchor, keeping every vertex (and the inner panel) where it is
    kids = [(k, k.matrix_world.copy()) for k in d.children]
    for k, _ in kids: k.parent = None
    H_old = d.location.copy(); delta = c - H_old
    for v in d.data.vertices: v.co -= delta
    d.location = c
    bpy.context.view_layer.update()
    for k, mw in kids:
        k.matrix_world = mw; k.parent = d; k.matrix_parent_inverse = d.matrix_world.inverted()
    for con in [x for x in d.constraints if x.type == "COPY_LOCATION"]: d.constraints.remove(con)
    cl = d.constraints.new("COPY_LOCATION"); cl.target = a; cl.name = "StickToAnchor"; cl.owner_space = "WORLD"; cl.target_space = "WORLD"
    d.constraints.move(len(d.constraints) - 1, 0)
    d["anchor"] = name
    print(side, "anchor at root-local", tuple(round(x, 4) for x in c), "from", len(pts), "vertices; door pivot moved by", tuple(round(x, 4) for x in delta))
bpy.ops.wm.save_as_mainfile(filepath=out, copy=False)
print("saved", out)
