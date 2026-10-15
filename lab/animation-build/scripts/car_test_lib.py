import bpy, math
from mathutils import Vector as V
def carset(**kw):
    c = bpy.data.objects["CAR_ctrl"]
    for k, v in kw.items(): c[k] = float(v)
    c.update_tag(); bpy.context.view_layer.update()
def carreset(): carset(distance=0, speed=0, steer=0, door_L=0, door_R=0)
def evobj(n): return bpy.data.objects[n].evaluated_get(bpy.context.evaluated_depsgraph_get())
def rot(n): return tuple(round(math.degrees(x), 2) for x in evobj(n).rotation_euler)
def wpos(n): return V(evobj(n).matrix_world.translation)
