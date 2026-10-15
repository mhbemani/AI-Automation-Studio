// stage: assemble <id> — voice (+ generated quiet bed, ducked under the voice) -> two-pass loudnorm -14 LUFS -> mux into out/<id>/final*.mp4; verifies with ebur128
import { mkdirSync, readFileSync, writeFileSync, existsSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const id = process.argv[2], W = path.join(ROOT, "work", id), O = path.join(ROOT, "out", id);
mkdirSync(O, { recursive: true });
const sb = JSON.parse(readFileSync(`${W}/storyboard.json`)), project = JSON.parse(readFileSync(`${W}/project.json`));
const D = project.durationSec, LUFS = -14, BED_BELOW_VOICE = 22; // LU: bed sits this far under the voice before ducking
const ff = (args, quiet = true) => { const r = spawnSync("ffmpeg", ["-hide_banner", "-y", ...args], { encoding: "utf8", maxBuffer: 1 << 26 }); if (r.status) { console.error("ERROR: ffmpeg failed: " + r.stderr.slice(-400)); process.exit(r.status); } return r.stderr; };
const lufs = (file) => { const e = ff(["-i", file, "-af", "ebur128=peak=true", "-f", "null", "-"]); const s = e.slice(e.lastIndexOf("Summary:")); return { I: +s.match(/I:\s+(-?[\d.]+) LUFS/)[1], LRA: +s.match(/LRA:\s+([\d.]+) LU/)[1], TP: +s.match(/Peak:\s+(-?[\d.]+) dBFS/)[1] }; };

// generated bed (A minor 9 pad, slow tremolo, soft echo): our own synthesis, so no licence question
const chord = [110, 164.81, 220, 261.63, 329.63, 493.88];
ff([...chord.flatMap((f) => ["-f", "lavfi", "-i", `sine=f=${f}:d=${D + 2}:r=48000`]), "-filter_complex",
  `${chord.map((_, i) => `[${i}]`).join("")}amix=inputs=${chord.length}:normalize=0,tremolo=f=0.18:d=0.45,lowpass=f=1400,aecho=0.8:0.7:70|140:0.35|0.2,afade=t=in:d=2.5,afade=t=out:st=${D - 1.5}:d=2.5,atrim=0:${D},pan=mono|c0=c0[o]`, "-map", "[o]", `${W}/bed_raw.wav`]);
const voiceI = lufs(`${W}/narration.wav`).I, bedI = lufs(`${W}/bed_raw.wav`).I, bedGain = (voiceI - BED_BELOW_VOICE - bedI).toFixed(1);

// two-pass loudnorm over the final mix
const mixes = { bed: `[1:a]volume=${bedGain}dB[b];[0:a]asplit[v][k];[b][k]sidechaincompress=threshold=0.02:ratio=3.5:attack=40:release=600[d];[v][d]amix=inputs=2:normalize=0[m]`, nobed: "[0:a]anull[m]" };
const result = {};
for (const [name, mix] of Object.entries(mixes)) {
  const inputs = ["-i", `${W}/narration.wav`, ...(name === "bed" ? ["-i", `${W}/bed_raw.wav`] : [])];
  const p1 = ff([...inputs, "-filter_complex", `${mix};[m]loudnorm=I=${LUFS}:TP=-1.0:LRA=11:print_format=json[o]`, "-map", "[o]", "-f", "null", "-"]);
  const m = JSON.parse(p1.slice(p1.lastIndexOf("{"), p1.lastIndexOf("}") + 1));
  const aud = `${W}/audio_${name}.m4a`;
  let target = LUFS;   // loudnorm lands ~0.5 LU low (its own measurement differs from ebur128 and AAC adds a little): measure the result and correct the target once or twice
  for (let k = 0; k < 3; k++) {
    const ln = `loudnorm=I=${target}:TP=-1.0:LRA=11:measured_I=${m.input_i}:measured_TP=${m.input_tp}:measured_LRA=${m.input_lra}:measured_thresh=${m.input_thresh}:offset=${m.target_offset}:linear=true`;
    ff([...inputs, "-filter_complex", `${mix};[m]${ln},aresample=48000[o]`, "-map", "[o]", "-ar", "48000", "-c:a", "aac", "-b:a", "192k", aud]);
    const err = lufs(aud).I - LUFS; console.log(`loudness ${name}: target ${target.toFixed(2)} -> ${lufs(aud).I} LUFS`);
    if (Math.abs(err) <= 0.1) break; target = +(target - err).toFixed(2);
  }
  for (const [vid, base] of [["silent.mp4", "final"], ["silent_vertical.mp4", "final_vertical"]]) {
    if (!existsSync(`${W}/${vid}`)) continue; // draft renders 16:9 only
    const out = path.join(O, `${base}${name === "bed" ? "" : "_nobed"}.mp4`);
    ff(["-i", `${W}/${vid}`, "-i", aud, "-map", "0:v", "-map", "1:a", "-c", "copy", "-shortest", "-movflags", "+faststart", out]);
    result[path.basename(out)] = lufs(out);
  }
}
writeFileSync(path.join(O, "loudness.json"), JSON.stringify({ target: LUFS, voiceLUFS: voiceI, bedLUFS: bedI, bedGainDb: +bedGain, files: result }, null, 1));
console.log(JSON.stringify(result));
