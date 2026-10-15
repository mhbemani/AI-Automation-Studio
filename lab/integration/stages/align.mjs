// stage: align <id> — whisper word times -> scene timing -> work/<id>/project.json (+ narration.wav)
import { readFileSync, writeFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { validateProject } from "./validate.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const W = path.join(ROOT, "work", process.argv[2]);
const MODEL = path.join(ROOT, "../ffmpeg/models/ggml-base.en.bin");
const LEAD = 0.5, TAIL = 0.7, T = 0.5, FPS = 30; // scene lead-in/out and fade length (s)
const COLORS = ["#38bdf8", "#a78bfa", "#34d399", "#fbbf24"];
const run = (cmd, args) => { const r = spawnSync(cmd, args, { encoding: "utf8" }); if (r.status) throw new Error(`${cmd} failed: ${r.stderr.slice(-500)}`); };
const norm = (s) => s.toLowerCase().replace(/[^a-z0-9]/g, "");

const sb = JSON.parse(readFileSync(`${W}/storyboard.json`));
const tts = JSON.parse(readFileSync(`${W}/tts.json`));

// word times (scene-local seconds): original words, timed from whisper by greedy match, gaps interpolated
function wordTimes(sc, audioSec) {
  run("whisper-cli", ["-m", MODEL, "-f", `${W}/s${sc.id}.wav`, "-ml", "1", "-sow", "-oj", "-of", `${W}/w${sc.id}`, "-np"]);
  const ws = JSON.parse(readFileSync(`${W}/w${sc.id}.json`)).transcription
    .map((x) => ({ n: norm(x.text), at: x.offsets.from / 1000 })).filter((x) => x.n);
  const orig = sc.narration.split(/\s+/);
  let p = 0;
  const at = orig.map((w) => {
    for (let j = p; j < Math.min(p + 4, ws.length); j++) if (ws[j].n === norm(w)) { p = j + 1; return ws[j].at; }
    return null;
  });
  const matched = at.filter((x) => x !== null).length;
  for (let i = 0; i < at.length; i++) if (at[i] === null) { // linear interpolation between neighbours
    let a = i - 1, b = i + 1; while (b < at.length && at[b] === null) b++;
    const t0 = a >= 0 ? at[a] : 0, t1 = b < at.length ? at[b] : audioSec;
    at[i] = t0 + ((t1 - t0) * (i - a)) / (b - a);
  }
  return { words: orig.map((w, i) => ({ w, at: +at[i].toFixed(3) })), matched };
}

let start = 0; const scenes = [], captions = [], audio = [], stats = [];
sb.scenes.forEach((sc, i) => {
  const a = tts.find((x) => x.id === sc.id).audioSec;
  const dur = LEAD + a + TAIL;
  const { words, matched } = wordTimes(sc, a);
  stats.push(`scene ${sc.id}: ${matched}/${words.length} words matched to whisper`);
  const nar = start + LEAD; // global start of this scene's narration
  const local = (k) => LEAD + words[Math.min(words.length - 1, Math.floor((k * words.length) / sc._n))].at; // chunk k start, scene-local
  audio.push({ file: `s${sc.id}.wav`, delayMs: Math.round(nar * 1000) });
  // captions: phrases of <= 5 words, also split after punctuation once >= 3 words
  let cur = [];
  const flush = () => { if (cur.length) captions.push({ at: cur[0].at, words: cur }); cur = []; };
  for (const w of words) { cur.push({ w: w.w, at: +(nar + w.at).toFixed(3) }); if (cur.length >= 5 || (cur.length >= 3 && /[.,!?]$/.test(w.w))) flush(); }
  flush();
  if (sc.type === "typography") {
    sc._n = sc.onScreen.length;
    scenes.push({ type: "typography", durationSec: +dur.toFixed(3), lines: sc.onScreen.map((t, k) => ({ text: t, at: +Math.max(0.3, local(k)).toFixed(3) })) });
  } else {
    sc._n = sc.packets.length;
    const nodes = sc.nodes.map((n, k) => ({ id: n, label: n, at: 0.1 + 0.25 * k, color: COLORS[k % COLORS.length] }));
    const edges = nodes.slice(1).map((n, k) => ({ from: nodes[k].id, to: n.id, at: Math.max(0, n.at - 0.3) }));
    const packets = sc.packets.map((p, k) => {
      const a0 = sc.nodes.indexOf(p.from), a1 = sc.nodes.indexOf(p.to), at = Math.max(nodes.length * 0.25 + 0.4, local(k) - 0.15);
      return { edge: Math.min(a0, a1), reverse: a1 < a0, label: p.label, at: +at.toFixed(3), dur: +Math.min(1.4, dur - at - 0.1).toFixed(3), color: COLORS[(k + 3) % COLORS.length] };
    });
    scenes.push({ type: "flow", durationSec: +dur.toFixed(3), nodes, edges, packets });
  }
  start += dur - T;
});
const durationSec = +(start + T).toFixed(3);
const project = { fps: FPS, transitionSec: T, durationSec, topic: sb.topic, series: sb.series, scenes, captions, audio: "narration.wav" };
validateProject(project);
writeFileSync(`${W}/project.json`, JSON.stringify(project, null, 1));
// narration track: each scene wav delayed to its place on the video timeline
const ins = audio.flatMap((x) => ["-i", `${W}/${x.file}`]);
const fc = audio.map((x, i) => `[${i}]aresample=48000,adelay=${x.delayMs}:all=1[a${i}]`).join(";") + `;${audio.map((_, i) => `[a${i}]`).join("")}amix=inputs=${audio.length}:normalize=0,apad,atrim=0:${durationSec}[o]`;
run("ffmpeg", ["-y", ...ins, "-filter_complex", fc, "-map", "[o]", "-ac", "1", `${W}/narration.wav`]);
console.log(stats.join("\n"), `\nvideo ${durationSec}s`);
