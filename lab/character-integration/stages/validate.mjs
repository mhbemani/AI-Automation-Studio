// Strict checks with readable messages, before any expensive stage runs. Storyboard v2 + the derived project.json.
export const LAYOUTS = { typography: ["presenter_center_typography"], flow: ["presenter_left_diagram_right", "presenter_corner_diagram_full"] };
export const ACTIONS = ["celebrate", "enter", "exit", "idle", "point_left", "point_right", "talk", "think", "wave"]; // actions in facet.blend (render_clip.py re-checks)
const SCENE_KEYS = { typography: ["id", "type", "layout", "narration", "onScreen", "character"], flow: ["id", "type", "layout", "narration", "nodes", "packets", "focus", "character"] };

export function validateStoryboard(sb) {
  const e = [], str = (x) => typeof x === "string" && x.trim();
  if (sb.version !== 2) e.push("version must be 2 (storyboard_v2 schema)");
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
    const words = str(s.narration) ? s.narration.toLowerCase().replace(/[^a-z0-9\s']/g, "").split(/\s+/).map((x) => x.replace(/[^a-z0-9]/g, "")) : [];
    const cueOk = (c, where) => { if (!str(c)) e.push(`${w}: ${where}.cue must be a word`); else if (!words.includes(c.toLowerCase().replace(/[^a-z0-9]/g, ""))) e.push(`${w}: ${where}.cue "${c}" is not a word of the narration`); };
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
    (s.character || []).forEach((c, j) => {
      if (!ACTIONS.includes(c.action)) e.push(`${w}: character[${j}].action "${c.action}" unknown (${ACTIONS.join(", ")})`);
      if ((c.at === undefined) === (c.cue === undefined)) e.push(`${w}: character[${j}] needs exactly one of "at" (seconds after narration start) or "cue"`);
      if (c.at !== undefined && !(c.at >= 0)) e.push(`${w}: character[${j}].at must be >= 0`);
      if (c.cue !== undefined) cueOk(c.cue, `character[${j}]`);
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
