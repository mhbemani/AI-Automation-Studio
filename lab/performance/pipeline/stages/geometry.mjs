// Shared-layout exporter: runs remotion/src/layout.ts (the SAME functions the Remotion components use) and writes work/<id>/geometry.json,
// per aspect: where the character clip sits on screen every frame, node centres, text-line centres, packet positions every frame.
// usage: node stages/geometry.mjs <id>    (also importable: exportGeometry(project))
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createRequire } from "node:module";
import path from "node:path";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
export const ASPECTS = { "16:9": [1920, 1080], "9:16": [1080, 1920] };

async function loadLayout() { // layout.ts has no React/remotion imports: bundle it with the esbuild that ships with Remotion
  const esbuild = createRequire(path.join(ROOT, "remotion/package.json"))("esbuild");
  const r = esbuild.buildSync({ entryPoints: [path.join(ROOT, "remotion/src/layout.ts")], bundle: true, format: "esm", write: false, platform: "node" });
  return import("data:text/javascript;base64," + Buffer.from(r.outputFiles[0].text).toString("base64"));
}

export async function exportGeometry(project) {
  const L = await loadLayout(), fps = project.fps, T = project.transitionSec, frames = Math.round(project.durationSec * fps), out = {};
  const round = (x) => Math.round(x * 10) / 10;
  for (const [aspect, [W, H]] of Object.entries(ASPECTS)) {
    const geos = project.scenes.map((s) => L.geo(s.layout, W, H)), starts = project.scenes.map((s) => s.startSec);
    const rect = [];
    for (let f = 0; f < frames; f++) { const r = L.clipRect(L.charPlace(f / fps, geos, starts, T), project.character.framing); rect.push([round(r.left), round(r.top), round(r.S)]); }
    const scenes = project.scenes.map((s, i) => {
      const g = geos[i], o = { index: i, layout: s.layout, type: s.type, startFrame: Math.round(s.startSec * fps), endFrame: Math.round((s.startSec + s.durationSec) * fps) };
      if (s.type === "flow") {
        const fl = L.flowLayout(g.diagram, W, H, s.nodes.length), P = Object.fromEntries(s.nodes.map((n, k) => [n.id, fl.pos[k]]));
        o.diagram = [round(g.diagram.x + g.diagram.w / 2), round(fl.rowY)];
        o.nodes = Object.fromEntries(s.nodes.map((n, k) => [n.id, [round(fl.pos[k].x), round(fl.pos[k].y)]]));
        o.nodeBox = [round(fl.bw), round(fl.bh)];
        o.packets = s.packets.map((k) => { // positions for every video frame of the flight
          const ed = s.edges[k.edge], sg = L.edgeSeg(P[ed.from], P[ed.to], fl.bw, fl.bh, fl.U, fl.horiz), a = Math.round((s.startSec + k.at) * fps), b = Math.round((s.startSec + k.at + k.dur) * fps), xy = [];
          for (let f = a; f <= b; f++) { const p = L.packetXY(sg, k.at, k.dur, k.reverse, f / fps - s.startSec); xy.push([round(p.x), round(p.y)]); }
          return { startFrame: a, endFrame: b, from: k.reverse ? ed.to : ed.from, to: k.reverse ? ed.from : ed.to, xy };
        });
      } else {
        const U = Math.min(W, H) / 1080, tl = L.typoLines(s.lines, g.text, U);
        o.text = tl.map((l, k) => ({ cx: round(l.cx), cy: round(l.cy), w: round(l.width), h: round(l.textH), appearFrame: Math.round((s.startSec + s.lines[k].at) * fps) }));
      }
      return o;
    });
    out[aspect] = { width: W, height: H, fps, frames, rect, scenes };
  }
  return out;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const W = path.join(ROOT, "work", process.argv[2]), project = JSON.parse(readFileSync(`${W}/project.json`)), g = await exportGeometry(project);
  writeFileSync(`${W}/geometry.json`, JSON.stringify(g));
  for (const [a, v] of Object.entries(g)) console.log(a, v.frames, "frames;", v.scenes.map((s) => s.type === "flow" ? `flow nodes ${Object.keys(s.nodes).join("/")}` : `text ${s.text.length}`).join(" | "));
}
