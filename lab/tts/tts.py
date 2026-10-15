import time, json, sys, numpy as np, soundfile as sf
INTRO = ["When you click Login, your browser sends your email and password to the server.",
 "The server checks them against the database, and if they match, it sends back a token.",
 "From then on, your browser shows that token with every request, so you stay signed in."]
JARGON = ["The API returns a JWT over HTTPS, and the user record lives in PostgreSQL."]
SENT = INTRO + JARGON
print("words:", sum(len(s.split()) for s in INTRO), "+", sum(len(s.split()) for s in JARGON))
res = {}
def run(name, gen, sr_fn):
    t = time.time(); parts = []; marks = []; pos = 0.0
    for s in SENT:
        a, sr = gen(s); parts.append(a); marks.append([s, round(pos, 3), round(pos + len(a)/sr, 3)]); pos += len(a)/sr
    el = time.time() - t; audio = np.concatenate(parts)
    sf.write(f"out/{name}.wav", audio, sr)
    res[name] = dict(gen_s=round(el, 2), audio_s=round(pos, 2), rtf=round(el/pos, 3), sentences=marks)
    print(name, res[name]["gen_s"], res[name]["audio_s"], res[name]["rtf"])
import os; os.makedirs("out", exist_ok=True)
which = sys.argv[1:]
if "kokoro" in which:
    from kokoro_onnx import Kokoro
    k = Kokoro("models/kokoro-v1.0.int8.onnx", "models/voices-v1.0.bin")
    k.create("warm up", voice="af_heart", lang="en-us")
    for v in ["af_heart", "af_bella", "am_michael", "bf_emma"]:
        run("kokoro_" + v, lambda s, v=v: k.create(s, voice=v, speed=1.0, lang="en-gb" if v[0]=="b" else "en-us"), None)
if "piper" in which:
    from piper import PiperVoice
    p = PiperVoice.load("models/en_US-lessac-medium.onnx")
    def g(s):
        c = list(p.synthesize(s)); return np.concatenate([x.audio_float_array for x in c]), c[0].sample_rate
    g("warm up"); run("piper_lessac", g, None)
json.dump(res, open(f"out/timings_{'_'.join(which)}.json", "w"), indent=1)
