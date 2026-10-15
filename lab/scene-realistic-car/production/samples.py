"""samples.py — one short sample per candidate voice (dialogue_v2.json voiceCandidates) into samples/, so the creator
can listen and pick. Each voice speaks two of its own character's lines."""
import json, os, shutil
import numpy as np, soundfile as sf, espeakng_loader
from kokoro_onnx import Kokoro, EspeakConfig

LAB = "lab"
d = json.load(open("dialogue_v2.json"))
os.makedirs("samples", exist_ok=True)
esd = "work/espeak-ng-data"   # short path: espeak-ng truncates long data paths (see build.py)
if not os.path.isdir(esd):
    os.makedirs("work", exist_ok=True); shutil.copytree(espeakng_loader.get_data_path(), esd)
k = Kokoro(f"{LAB}/tts/models/kokoro-v1.0.int8.onnx", f"{LAB}/tts/models/voices-v1.0.bin", espeak_config=EspeakConfig(data_path=esd))
TEXT = {s: " ".join(l["text"] for l in d["lines"] if l["speaker"] == s and l["id"] in (5, 7, 6, 12)) for s in ("claude", "human")}
for who, voices in d["voiceCandidates"].items():
    for v in voices:
        a, sr = k.create(TEXT[who], voice=v, speed=1.0, lang="en-gb" if v[0] == "b" else "en-us")
        sf.write(f"samples/{who}_{v}.wav", np.asarray(a, dtype=np.float32), sr)
        print(f"samples/{who}_{v}.wav  {len(a) / sr:.1f} s")
