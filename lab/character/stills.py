"""Test stills: blender -b facet.blend -P stills.py -- outdir spec [spec...]   spec = action@seconds[:camera[:mouth[:aspect]]]"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stagecfg
a = sys.argv[sys.argv.index("--") + 1:]; outdir = a[0]; os.makedirs(outdir, exist_ok=True)
sc = bpy.context.scene; rig = bpy.data.objects["FacetRig"]; cam = bpy.data.objects["STAGE_camera"]
for spec in a[1:]:
    parts = spec.split(":"); act, t = parts[0].split("@")
    camera = parts[1] if len(parts) > 1 and parts[1] else "full"
    mouth = float(parts[2]) if len(parts) > 2 and parts[2] else None
    aspect = parts[3].replace("x", ":") if len(parts) > 3 else None
    stagecfg.apply(sc, cam, camera, os.environ.get("Q", "draft"), aspect)
    rig.animation_data.action = bpy.data.actions[act]
    sc.frame_set(1 + round(float(t) * 30))
    if mouth is not None: rig.animation_data.action = None   # keep evaluated pose, then override mouth
    if mouth is not None:
        pb = rig.pose.bones["mouth"]; pb.scale = (1, 1, 1)   # placeholder, converted below
        import mathutils
        s = abs((rig.data.bones["mouth"].matrix_local.to_3x3().inverted() @ mathutils.Vector((1, 1, mouth)))[1])
        # mouth bone axes: set via same conversion as the baker
        v = rig.data.bones["mouth"].matrix_local.to_3x3().inverted() @ mathutils.Vector((1, 1, max(mouth, .05)))
        pb.scale = [abs(x) for x in v]; bpy.context.view_layer.update()
    sc.render.filepath = os.path.join(outdir, spec.replace(":", "_").replace("@", "_") + ".png")
    bpy.ops.render.render(write_still=True)
