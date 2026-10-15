// Strict checks with readable messages, before any expensive stage runs. Storyboard v3 (v2 + the scripted `performance` array) + the derived project.json.
export const LAYOUTS = { typography: ["presenter_center_typography"], flow: ["presenter_left_diagram_right", "presenter_corner_diagram_full"] };
export const GESTURES = ["point_at", "track", "present", "beat", "beat_repeat", "nod", "shake_head", "shrug", "lean_in", "press", "point_viewer", "point_self", "scramble", "compare", "offer", "hold_palm", "grip", "open_arms", "wave"];
export const EMOTIONS = ["friendly", "curious", "excited", "playful", "confident", "reassuring", "serious", "thoughtful", "satisfied", "proud", "emphatic", "happy"];
const BEAT_KEYS = ["cue", "at", "atEnd", "gesture", "target", "emotion", "intensity", "hold", "hand"];
const SCENE_KEYS = { typography: ["id", "type", "layout", "narration", "onScreen", "performance"], flow: ["id", "type", "layout", "narration", "nodes", "packets", "focus", "performance"] };
export const TOP_KEYS = ["version", "topic", "series", "targetSeconds", "bed", "voice", "pronunciation", "scenes"];
export const normWord = (s) => s.toLowerCase().replace(/[’‘]/g, "'").replace(/[^a-z0-9']/g, "").replace(/^'+|'+$/g, "");

export function validateStoryboard(sb) {
  const e = [], str = (x) => typeof x === "string" && x.trim();
  if (sb.version !== 3) e.push("version must be 3 (storyboard_v3 schema: v2 + scene.performance)");
  for (const k of Object.keys(sb)) if (!TOP_KEYS.includes(k)) e.push(`unexpected top-level key "${k}"`);
  if (!str(sb.topic)) e.push("topic missing");
  const v = sb.voice || {};
  if (!str(v.main)) e.push("voice.main missing");
  if (v.speed !== undefined && !(v.speed >= 0.6 && v.speed <= 1.3)) e.push("voice.speed must be 0.6..1.3");
  if (sb.bed !== undefined && !["generated", "none"].includes(sb.bed)) e.push('bed must be "generated" or "none"');
  if (!Array.isArray(sb.scenes) || !sb.scenes.length) e.push("scenes must be a non-empty array");
  const ids = new Set();
  (sb.scenes || []).forEach((s, i) => {
    const w = `scene[${i}] (id ${s.id})`;
    if (ids.has(s.id)) e.push(`${w}: duplicate id`); ids.add(s.id);
    if (!str(s.narration)) e.push(`${w}: narration missing`);
    // scene type is implied by layout: typography layouts carry onScreen, diagram layouts carry nodes
    const type = s.layout === "presenter_center_typography" ? "typography" : LAYOUTS.flow.includes(s.layout) ? "flow" : null;
    if (!type) return e.push(`${w}: unknown layout "${s.layout}" (${[...LAYOUTS.typography, ...LAYOUTS.flow].join(" | ")})`);
    for (const k of Object.keys(s)) if (!SCENE_KEYS[type].concat("type").includes(k)) e.push(`${w}: unexpected key "${k}" for a ${type} scene`);
    const words = str(s.narration) ? s.narration.split(/\s+/).map(normWord).filter(Boolean) : [];
    const cueOk = (c, where) => { if (!str(c)) e.push(`${w}: ${where}.cue must be a word`); else if (!words.includes(normWord(c))) e.push(`${w}: ${where}.cue "${c}" is not a word of the narration`); };
    if (type === "typography") {
      if (!Array.isArray(s.onScreen) || !s.onScreen.length) e.push(`${w}: onScreen must be a non-empty list of {text, cue?}`);
      (s.onScreen || []).forEach((l, j) => { if (!str(l.text)) e.push(`${w}: onScreen[${j}].text missing`); if (l.cue !== undefined) cueOk(l.cue, `onScreen[${j}]`); });
    } else {
      const names = s.nodes || [];
      if (names.length < 2) e.push(`${w}: flow needs >= 2 nodes`);
      if (new Set(names).size !== names.length) e.push(`${w}: duplicate node names`);
      if (!Array.isArray(s.packets) || !s.packets.length) e.push(`${w}: flow needs >= 1 packet`);
      (s.packets || []).forEach((p, j) => {
        for (const k of ["from", "to"]) if (!names.includes(p[k])) e.push(`${w}: packet[${j}].${k} "${p[k]}" is not a node`);
        if (Math.abs(names.indexOf(p.from) - names.indexOf(p.to)) !== 1) e.push(`${w}: packet[${j}] must go between adjacent nodes (chain layout)`);
        if (!str(p.label)) e.push(`${w}: packet[${j}] has no label`);
        if (p.cue !== undefined) cueOk(p.cue, `packet[${j}]`);
      });
      (s.focus || []).forEach((f, j) => { if (!names.includes(f.node)) e.push(`${w}: focus[${j}].node "${f.node}" is not a node`); cueOk(f.cue, `focus[${j}]`); });
    }
    // ---- performance script (the authored beats). Cue lookup: first match at or after the previous beat's cue word (same rule as align.mjs).
    if (!Array.isArray(s.performance) || !s.performance.length) e.push(`${w}: performance must be a non-empty list of beats`);
    const nodeNames = type === "flow" ? s.nodes || [] : [];
    let from = 0;
    (s.performance || []).forEach((b, j) => {
      const bw = `${w}: performance[${j}]`;
      for (const k of Object.keys(b)) if (!BEAT_KEYS.includes(k)) e.push(`${bw}: unexpected key "${k}" (${BEAT_KEYS.join(", ")})`);
      const timing = ["cue", "at", "atEnd"].filter((k) => b[k] !== undefined);
      if (timing.length !== 1) e.push(`${bw}: needs exactly one of "cue" (narration word), "at" (seconds from scene start) or "atEnd" (seconds relative to scene end, negative = before the end), got ${timing.length}`);
      if (b.cue !== undefined) {
        if (!str(b.cue)) e.push(`${bw}.cue must be a word`);
        else { const i = words.findIndex((x, ix) => ix >= from && x === normWord(b.cue)); if (i < 0) e.push(`${bw}.cue "${b.cue}" not found in the narration at or after word ${from} ("${words[from] ?? "end"}")`); else from = i; }
      }
      if (b.at !== undefined && !(typeof b.at === "number" && b.at >= 0)) e.push(`${bw}.at must be a number >= 0`);
      if (b.atEnd !== undefined && !(typeof b.atEnd === "number" && b.atEnd <= 0)) e.push(`${bw}.atEnd must be a number <= 0 (seconds before the scene end)`);
      if (!GESTURES.includes(b.gesture)) e.push(`${bw}.gesture "${b.gesture}" unknown (${GESTURES.join(", ")})`);
      if (!EMOTIONS.includes(b.emotion)) e.push(`${bw}.emotion "${b.emotion}" unknown (${EMOTIONS.join(", ")})`);
      if (b.intensity !== undefined && !(typeof b.intensity === "number" && b.intensity >= 0 && b.intensity <= 1)) e.push(`${bw}.intensity must be 0..1`);
      if (b.hold !== undefined && !(typeof b.hold === "number" && b.hold >= 0 && b.hold <= 4)) e.push(`${bw}.hold must be 0..4 seconds`);
      if (b.hand !== undefined && !["L", "R", "auto"].includes(b.hand)) e.push(`${bw}.hand must be L, R or auto`);
      const t = String(b.target ?? ""), m = t.match(/^(viewer|self|diagram|node|text|packet)(?::(.*))?$/);
      if (!m) e.push(`${bw}.target "${t}" unknown (viewer | self | diagram | node:<Name> | text:<index> | packet:<index>)`);
      else {
        const [, kind, arg] = m;
        if (["viewer", "self", "diagram"].includes(kind) && arg !== undefined) e.push(`${bw}.target "${t}" takes no argument`);
        if (kind === "diagram" && type !== "flow") e.push(`${bw}.target "diagram" only exists in diagram scenes`);
        if (kind === "node" && !nodeNames.includes(arg)) e.push(`${bw}.target "${t}": node "${arg}" not in this scene (${nodeNames.join(", ") || "none: typography scene"})`);
        if (kind === "text" && !(type === "typography" && /^\d+$/.test(arg ?? "") && +arg < (s.onScreen || []).length)) e.push(`${bw}.target "${t}": no such onScreen line (this scene has ${type === "typography" ? (s.onScreen || []).length : 0})`);
        if (kind === "packet" && !(type === "flow" && /^\d+$/.test(arg ?? "") && +arg < (s.packets || []).length)) e.push(`${bw}.target "${t}": no such packet (this scene has ${type === "flow" ? (s.packets || []).length : 0})`);
        if (b.gesture === "track" && kind !== "packet") e.push(`${bw}: gesture "track" needs a packet:<index> target`);
      }
    });
  });
  if (e.length) throw new Error("Invalid storyboard:\n - " + e.join("\n - "));
}

export function validateProject(p) {
  const e = [];
  if (!(p.fps > 0) || !(p.durationSec > 0)) e.push("fps/durationSec must be > 0");
  p.scenes.forEach((s, i) => {
    if (!(s.durationSec > 0)) e.push(`scene[${i}]: durationSec must be > 0`);
    if (s.type === "flow") s.packets.forEach((k, j) => {
      if (!s.edges[k.edge]) e.push(`scene[${i}] packet[${j}]: edge ${k.edge} does not exist`);
      if (!(k.at >= 0 && k.at + k.dur <= s.durationSec)) e.push(`scene[${i}] packet[${j}]: runs outside the scene (${k.at}+${k.dur} > ${s.durationSec})`);
    });
    if (s.type === "typography" && s.lines.some((l) => l.at >= s.durationSec)) e.push(`scene[${i}]: a line appears after the scene ends`);
  });
  if (e.length) throw new Error("Invalid project JSON:\n - " + e.join("\n - "));
}
