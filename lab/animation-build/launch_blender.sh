#!/bin/bash
# Open Blender (GUI) with the live bridge on anim_work.blend. Usage: launch_blender.sh [file.blend]
D="$(cd "$(dirname "$0")" && pwd)"
[ -f "$D/bridge/.token" ] || openssl rand -hex 16 > "$D/bridge/.token"
export BRIDGE_TOKEN="$(cat "$D/bridge/.token")"
F="${1:-$D/anim_work.blend}"
[ -f "$F" ] || F=""
exec /Applications/Blender.app/Contents/MacOS/Blender ${F:+"$F"} --python "$D/bridge/studio_bridge.py"
