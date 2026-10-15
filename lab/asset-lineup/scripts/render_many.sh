#!/bin/zsh
# render_many.sh <studio|golden> <draft|final> CAM [CAM ...]  -> lab/asset-lineup/previews/<CAM>_<light>_<preset>.png (one Blender per render)
cd "$(dirname $0)/../../.."
light=$1; preset=$2; shift 2
for c in "$@"; do
  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup lab/asset-lineup/lineup.blend \
    --python lab/asset-lineup/scripts/render_lineup.py -- --camera $c --preset $preset --light $light \
    --out lab/asset-lineup/previews/${c#LU_CAM_}_${light}_${preset}.png 2>&1 | grep -E "rendered|Error|Traceback"
done
