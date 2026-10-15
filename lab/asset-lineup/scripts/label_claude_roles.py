"""Mark V3-A as the main Claude and V3-B / V3-C as emotion samples (labels + custom property lineup_role; object names unchanged).
Reads IN.blend, writes OUT.blend:  Blender -b --factory-startup IN.blend --python lab/asset-lineup/scripts/label_claude_roles.py -- OUT.blend"""
import bpy, sys
out = sys.argv[sys.argv.index("--") + 1]
ROLES = {
    "V3A": ("main", "MAIN  Claude", "main face: eyes lower + highlight"),
    "V3B": ("emotion", "EMOTION  happy / shy", "sample: highlight + blush"),
    "V3C": ("emotion", "EMOTION  excited", "sample: big soft eyes + blush"),
    "V3":  ("reference", "V3  first version", "reference: plain mascot face"),
}
for tag, (role, name, sub) in ROLES.items():
    root = bpy.data.objects[f"LU_{tag}_CHAR_Claude"]; root["lineup_role"] = role
    bpy.data.objects[f"LU_Label_{tag}_Claude_name"].data.body = name
    bpy.data.objects[f"LU_Label_{tag}_Claude_src"].data.body = sub
bpy.ops.wm.save_as_mainfile(filepath=out, copy=False)
print("saved", out)
