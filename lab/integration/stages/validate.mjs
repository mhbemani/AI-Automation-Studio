// Fails with a readable message before any expensive stage runs.
export function validateStoryboard(sb) {
  const e = [];
  if (!Array.isArray(sb.scenes) || !sb.scenes.length) e.push("scenes must be a non-empty array");
  (sb.scenes || []).forEach((s, i) => {
    const w = `scene[${i}] (id ${s.id})`;
    if (typeof s.narration !== "string" || !s.narration.trim()) e.push(`${w}: narration missing`);
    if (s.type === "typography") {
      if (!Array.isArray(s.onScreen) || !s.onScreen.length || s.onScreen.some((t) => typeof t !== "string" || !t.trim())) e.push(`${w}: onScreen must be non-empty strings`);
    } else if (s.type === "flow") {
      const names = s.nodes || [];
      if (names.length < 2) e.push(`${w}: flow needs >= 2 nodes`);
      if (new Set(names).size !== names.length) e.push(`${w}: duplicate node names`);
      (s.packets || []).forEach((p, j) => {
        for (const k of ["from", "to"]) if (!names.includes(p[k])) e.push(`${w}: packet[${j}].${k} "${p[k]}" is not a node`);
        if (Math.abs(names.indexOf(p.from) - names.indexOf(p.to)) !== 1) e.push(`${w}: packet[${j}] must go between adjacent nodes (chain layout)`);
        if (!p.label) e.push(`${w}: packet[${j}] has no label`);
      });
    } else e.push(`${w}: unknown type "${s.type}" (typography | flow)`);
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
