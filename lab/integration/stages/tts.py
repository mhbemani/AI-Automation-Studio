# stage: tts <id>  — storyboard -> work/<id>/s<N>.wav (Kokoro, one per scene) + tts.json
import json, re, sys, time, subprocess, pathlib, soundfile as sf
ROOT = pathlib.Path(__file__).resolve().parent.parent
W = ROOT / "work" / sys.argv[1]
sb = json.load(open(W / "storyboard.json"))
r = subprocess.run(["node", "-e", f"import('{ROOT}/stages/validate.mjs').then(m=>m.validateStoryboard(JSON.parse(require('fs').readFileSync('{W}/storyboard.json'))))"], capture_output=True, text=True)
if r.returncode: sys.exit("\n".join(l for l in r.stderr.splitlines() if l.startswith(('Error','Invalid',' - '))))
def respell(t):  # pronunciation respelling, whole words only
    for k, v in sb.get("pronunciation", {}).items(): t = re.sub(rf"\b{re.escape(k)}\b", v, t)
    return t
from kokoro_onnx import Kokoro
M = ROOT.parent / "tts" / "models"
k = Kokoro(str(M / "kokoro-v1.0.int8.onnx"), str(M / "voices-v1.0.bin"))
voice = sb["voice"]["main"]; lang = "en-gb" if voice[0] == "b" else "en-us"
out = []
for s in sb["scenes"]:
    t = time.time(); a, sr = k.create(respell(s["narration"]), voice=voice, speed=1.0, lang=lang)
    sf.write(W / f"s{s['id']}.wav", a, sr)
    out.append(dict(id=s["id"], audioSec=round(len(a) / sr, 3), genSec=round(time.time() - t, 2)))
json.dump(out, open(W / "tts.json", "w"), indent=1); print(out)
