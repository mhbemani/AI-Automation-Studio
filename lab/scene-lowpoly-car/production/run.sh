#!/bin/bash
# run.sh — everything, one step at a time: validate -> build (TTS, Whisper, timeline, envelopes) -> mix -> check
set -euo pipefail
cd "$(dirname "$0")"
[ -x .venv/bin/python ] || { python3 -m venv .venv && .venv/bin/pip install -q kokoro-onnx soundfile; }
.venv/bin/python validate.py
.venv/bin/python -u build.py
./mix.sh
.venv/bin/python check.py | tee checks.txt
