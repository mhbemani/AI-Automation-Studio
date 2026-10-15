"""Bridge-side helpers for magic tests: setm(**props) on MAG_Root, scene() = studio + camera, rigs at origin."""
import bpy
def setm(**kw):
    r = bpy.data.objects["MAG_Root"]
    for k, v in kw.items(): r[k] = float(v)
    for o in bpy.data.objects:
        if o.name.startswith("MAG_"): o.update_tag()
    bpy.context.view_layer.update()
def mag_reset(): setm(fade=0, shot=0, dist=1.2, size=1, wrap=0, wrap_to=0.7, spin_rate=1, puff=0, sparkle=0)
