# Switch the render between 16:9 (1920x1080) and 9:16 (1080x1920, Shorts/Reels). Re-runnable.
# Cameras with a "v916" = (lens, shift_x, shift_y) property get it in 9:16; 16:9 restores the lens
# saved in "lens169" and zero shift. Set ASPECT before running.
import bpy

ASPECT = globals().get("ASPECT", "16:9")   # "16:9" | "9:16" (set it with bl.py exec first)

r = bpy.context.scene.render
r.resolution_x, r.resolution_y = (1920, 1080) if ASPECT == "16:9" else (1080, 1920)
for c in [o for o in bpy.data.objects if o.type == "CAMERA" and "v916" in o]:
    d = c.data
    if "lens169" not in c: c["lens169"] = d.lens
    d.lens, d.shift_x, d.shift_y = (c["lens169"], 0, 0) if ASPECT == "16:9" else tuple(c["v916"])
result = (ASPECT, r.resolution_x, r.resolution_y)
