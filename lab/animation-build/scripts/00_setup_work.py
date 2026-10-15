"""Build anim_work.blend inputs: append copies of the sources (never touches the originals).
Idempotent: skips collections already present. Run inside Blender (bridge) from lab/animation-build."""
import bpy, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else os.environ.get("ANIM_ROOT") or os.path.dirname(os.path.abspath(__import__("bpy").data.filepath))
SN = os.path.join(ROOT, "snapshots")
LINEUP = os.path.join(SN, "lineup_2026-10-13.blend")
HUMAN = os.path.join(SN, "character_selection_lab_2026-10-12.blend")

def append_collections(path, names, parent):
    for n in names:
        if n in bpy.data.collections: continue
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            if n in src.collections: dst.collections = [n]
        for c in dst.collections:
            parent.children.link(c)

def main():
    sc = bpy.context.scene
    for o in list(sc.objects):                       # default cube/light/camera only
        if o.name in ("Cube", "Light", "Camera"): bpy.data.objects.remove(o)
    root = bpy.data.collections.get("ANIM_Sources") or bpy.data.collections.new("ANIM_Sources")
    if root.name not in sc.collection.children: sc.collection.children.link(root)
    append_collections(LINEUP, ["LU_V3A_Claude", "LU_V3A_Magic", "LU_NEW_Car", "LU_NEW_Phone_5x"], root)
    append_collections(HUMAN, ["STEP1_rig"], root)
    sc.render.fps = 24; sc.unit_settings.system = 'METRIC'
    return [c.name for c in root.children]
result = main()
