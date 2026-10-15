// stage: align <id> — whisper word times -> scene timing (whole frames) -> cue resolution -> work/<id>/{project.json,timeline.json,sync.json,narration.wav}
import { readFileSync, writeFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { validateProject, validateStoryboard } from "./validate.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const W = path.join(ROOT, "work", process.argv[2]);
const MODEL = process.env.WHISPER_MODEL || path.join(ROOT, "../ffmpeg/models/ggml-base.en.bin");
const FPS = 30, LEAD = 0.4, TAIL = 0.6, T = 0.5, MIN_EVENT_GAP = 0.45, FIRST_EVENT = 1.0; // scene lead-in/out, fade length, character timing rules (s)
const COLORS = ["#2EC4B6", "#5B5BD6", "#FF6B6B", "#FFC93C"]; // STYLE.md palette: aqua, indigo, coral, amber
const run = (cmd, args) => { const r = spawnSync(cmd, args, { encoding: "utf8" }); if (r.status) throw new Error(`${cmd} failed: ${r.stderr.slice(-500)}`); };
const norm = (s) => s.toLowerCase().replace(/[^a-z0-9]/g, "");
const warns = [];
const fr = (s) => Math.round(s * FPS) / FPS;

const sb = JSON.parse(readFileSync(`${W}/storyboard.json`));
validateStoryboard(sb);
const tts = JSON.parse(readFileSync(`${W}/tts.json`));
const character = JSON.parse(readFileSync(path.join(ROOT, "character.json")));

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
  const matched = at.map((x) => x !== null);
  for (let i = 0; i < at.length; i++) if (at[i] === null) { // linear interpolation between neighbours
    let a = i - 1, b = i + 1; while (b < at.length && at[b] === null) b++;
    const t0 = a >= 0 ? at[a] : 0, t1 = b < at.length ? at[b] : audioSec;
    at[i] = t0 + ((t1 - t0) * (i - a)) / (b - a);
  }
  return orig.map((w, i) => ({ w, at: +at[i].toFixed(3), matched: matched[i] }));
}

// cue -> index of the first word >= `from` whose normalised text equals the cue; falls back to even spacing (warns)
function resolve(sc, words, list, key = "cue") {
  let from = 0;
  return list.map((it, k) => {
    if (it[key] === undefined) return { ...it, idx: -1, at: it.at };
    const c = norm(it[key]); let idx = words.findIndex((w, i) => i >= from && norm(w.w) === c);
    if (idx < 0) { idx = Math.min(words.length - 1, Math.floor((k * words.length) / list.length)); warns.push(`scene ${sc.id}: cue "${it[key]}" not found after word ${from}; spaced evenly`); }
    else if (!words[idx].matched) warns.push(`scene ${sc.id}: cue "${it[key]}" was interpolated (whisper did not hear it)`);
    from = idx;
    return { ...it, idx, at: words[idx].at };
  });
}

let startF = 0; const scenes = [], captions = [], audio = [], stats = [], events = [], intended = { packets: [], focus: [], character: [], lines: [], words: [] };
sb.scenes.forEach((sc, si) => {
  const a = tts.find((x) => x.id === sc.id).audioSec;
  const durF = Math.round((LEAD + a + TAIL) * FPS), dur = durF / FPS, start = startF / FPS;
  const words = wordTimes(sc, a);
  stats.push(`scene ${sc.id}: ${words.filter((w) => w.matched).length}/${words.length} words matched to whisper, ${dur.toFixed(2)} s`);
  const nar = start + LEAD; // global start of this scene's narration
  audio.push({ file: `s${sc.id}.wav`, delayMs: Math.round(nar * 1000) });
  // captions: phrases of <= 5 words, also split after punctuation once >= 3 words
  let cur = [];
  const flush = () => { if (cur.length) captions.push({ at: cur[0].at, scene: si, words: cur }); cur = []; };
  for (const w of words) { cur.push({ w: w.w, at: +(nar + w.at).toFixed(3) }); intended.words.push({ scene: sc.id, w: w.w, at: +(nar + w.at).toFixed(3) }); if (cur.length >= 5 || (cur.length >= 3 && /[.,!?]$/.test(w.w))) flush(); }
  flush();
  // character events (global times; the clip is rendered against the final aligned narration)
  for (const e of resolve(sc, words, sc.character || [])) events.push({ action: e.action, t: nar + e.at, scene: sc.id, cue: e.cue });
  const layout = sc.layout;
  if (layout === "presenter_center_typography") {
    const lines = resolve(sc, words, sc.onScreen);
    lines.forEach((l, k) => { if (l.cue === undefined) l.at = (k * a) / lines.length; });
    const mapped = lines.map((l) => ({ text: l.text, at: +Math.max(0.2, LEAD + l.at).toFixed(3) }));
    mapped.forEach((l) => intended.lines.push({ scene: sc.id, text: l.text, at: +(start + l.at).toFixed(3) }));
    scenes.push({ type: "typography", layout, startSec: start, durationSec: dur, lines: mapped });
  } else {
    const nodes = sc.nodes.map((n, k) => ({ id: n, label: n, at: 0.1 + 0.2 * k, color: COLORS[k % COLORS.length] }));
    const edges = nodes.slice(1).map((n, k) => ({ from: nodes[k].id, to: n.id, at: Math.max(0, n.at - 0.2) }));
    const pk = resolve(sc, words, sc.packets);
    const packets = pk.map((p, k) => {
      const a0 = sc.nodes.indexOf(p.from), a1 = sc.nodes.indexOf(p.to), at = LEAD + p.at;
      const next = pk[k + 1] ? LEAD + pk[k + 1].at : dur - TAIL * 0.5; // packets on one edge never overlap       // keep the packet moving until the next one launches (coverage), 0.9-3.2 s
      const d = +Math.min(3.2, Math.max(0.9, next - at - 0.05), dur - at - 0.1).toFixed(3);
      intended.packets.push({ scene: sc.id, label: p.label, at: +(start + at).toFixed(3) });
      return { edge: Math.min(a0, a1), reverse: a1 < a0, label: p.label, at: +at.toFixed(3), dur: d, color: COLORS[(k + 3) % COLORS.length] };
    });
    const fc = resolve(sc, words, sc.focus || []).map((f, k, all) => {
      const at = LEAD + f.at, nextSame = all.slice(k + 1).find((g) => g.node === f.node);
      intended.focus.push({ scene: sc.id, node: f.node, at: +(start + at).toFixed(3) });
      return { node: f.node, label: f.label, at: +at.toFixed(3), dur: +Math.min(2.2, nextSame ? LEAD + nextSame.at - at : 2.2, dur - at).toFixed(3) };
    });
    scenes.push({ type: "flow", layout, startSec: start, durationSec: dur, nodes, edges, packets, focus: fc });
  }
  startF += durF - Math.round(T * FPS);
});
const totalF = startF + Math.round(T * FPS), durationSec = totalF / FPS;

// character timeline: enter first, never closer than MIN_EVENT_GAP, never before FIRST_EVENT, strictly < duration
events.sort((x, y) => x.t - y.t);
const tl = [{ t: 0, action: "enter" }];
for (const e of events) {
  const t = fr(Math.max(e.t, FIRST_EVENT, tl[tl.length - 1].t + MIN_EVENT_GAP));
  if (t >= durationSec - 0.3) { warns.push(`character event ${e.action} (scene ${e.scene}) dropped: too close to the end`); continue; }
  if (t - e.t > 0.05 && e.t >= FIRST_EVENT) warns.push(`character event ${e.action} (scene ${e.scene}, cue ${e.cue ?? "at"}) delayed ${(1000 * (t - e.t)).toFixed(0)} ms by the min-gap rule`);
  tl.push({ t, action: e.action }); intended.character.push({ scene: e.scene, action: e.action, intended: +e.t.toFixed(3), used: t });
}
writeFileSync(`${W}/timeline.json`, JSON.stringify({ fps: FPS, duration: durationSec, events: tl }, null, 1));

const project = { fps: FPS, transitionSec: T, durationSec, topic: sb.topic, series: sb.series, character, scenes, captions, audio: "narration.wav" };
validateProject(project);
writeFileSync(`${W}/project.json`, JSON.stringify(project, null, 1));
writeFileSync(`${W}/sync.json`, JSON.stringify(intended, null, 1));
// narration track: each scene wav delayed to its place on the video timeline
const ins = audio.flatMap((x) => ["-i", `${W}/${x.file}`]);
const fc = audio.map((x, i) => `[${i}]aresample=48000,adelay=${x.delayMs}:all=1[a${i}]`).join(";") + `;${audio.map((_, i) => `[a${i}]`).join("")}amix=inputs=${audio.length}:normalize=0,apad,atrim=0:${durationSec}[o]`;
run("ffmpeg", ["-y", ...ins, "-filter_complex", fc, "-map", "[o]", "-ac", "1", `${W}/narration.wav`]);
// flow coverage: share of each flow scene with a packet in flight
for (const s of scenes) if (s.type === "flow") {
  let covered = 0; for (let t = 0; t < s.durationSec; t += 0.05) if (s.packets.some((p) => t >= p.at && t <= p.at + p.dur)) covered += 0.05;
  stats.push(`flow scene (${s.layout}): packet in flight ${(100 * covered / s.durationSec).toFixed(0)}% of ${s.durationSec.toFixed(1)} s`);
}
console.log(stats.join("\n"), `\n${warns.map((w) => "WARN " + w).join("\n")}\nvideo ${durationSec}s, ${tl.length} character events`);
