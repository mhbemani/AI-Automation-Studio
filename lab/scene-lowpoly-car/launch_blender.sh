#!/bin/bash
# Open Blender (GUI) with the live bridge. Usage: launch_blender.sh [scene.blend]
# Blender must stay open; the agent drives it through bridge/bl.py, you can edit freely too.
D="$(cd "$(dirname "$0")" && pwd)"
[ -f "$D/bridge/.token" ] || openssl rand -hex 16 > "$D/bridge/.token"
export BRIDGE_TOKEN="$(cat "$D/bridge/.token")"
exec /Applications/Blender.app/Contents/MacOS/Blender ${1:+"$1"} --python "$D/bridge/studio_bridge.py"
