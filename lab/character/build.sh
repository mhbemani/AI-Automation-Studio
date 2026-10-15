#!/bin/sh
# Rebuild facet.blend from scratch (character + stage). ~15 s.
cd "$(dirname "$0")"
${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender} -b --factory-startup -P build_character.py -P build_stage.py
