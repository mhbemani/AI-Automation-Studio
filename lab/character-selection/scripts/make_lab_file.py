"""Create character_selection_lab.blend: empty lab file with the user's reference asset (static low-poly male) as a baseline.
Run: Blender -b --python lab/character-selection/scripts/make_lab_file.py -- <ref.blend> <out.blend>"""
import bpy, sys
ref, out = sys.argv[sys.argv.index("--")+1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
cols = {n: bpy.data.collections.new(n) for n in ("REF_static_baseline", "CANDIDATES", "TEST_POSES")}
for c in cols.values(): bpy.context.scene.collection.children.link(c)
with bpy.data.libraries.load(ref) as (src, dst):
    dst.objects = src.objects
n = 0
for o in dst.objects:
    if o: cols["REF_static_baseline"].objects.link(o); n += 1
print("imported", n, [(o.name, o.type) for o in dst.objects if o])
bpy.ops.wm.save_as_mainfile(filepath=out)
