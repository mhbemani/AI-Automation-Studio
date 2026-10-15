// dev tool: stills.mjs <id> [outdir] [seconds...] — stills of both aspects (default: 4 per scene) from work/<id>/project.json, one bundle + one browser
import { readFileSync, mkdirSync, existsSync, rmSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { createRequire } from "node:module";
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(path.join(ROOT, "remotion/package.json"));
const { bundle } = require("@remotion/bundler"), { renderStill, selectComposition } = require("@remotion/renderer");
const [id, outArg, ...secs] = process.argv.slice(2);
const W = path.join(ROOT, "work", id), out = outArg || path.join(ROOT, "out", id, "stills");
mkdirSync(out, { recursive: true });
const project = JSON.parse(readFileSync(`${W}/project.json`));
const times = secs.length ? secs.map(Number) : project.scenes.flatMap((s) => [0.12, 0.38, 0.62, 0.88].map((k) => +(s.startSec + k * s.durationSec).toFixed(2)));
const serveUrl = await bundle({ entryPoint: path.join(ROOT, "remotion/src/index.ts"), publicDir: W });
for (const [comp, tag, dir] of [["Video", "h", "char_16x9"], ["VideoVertical", "v", "char_9x16"]]) {
  if (!existsSync(path.join(W, dir, "f_0001.png"))) continue; // draft = 16:9 only
  const composition = await selectComposition({ serveUrl, id: comp, inputProps: project });
  for (const t of times) {
    const output = path.join(out, `${tag}_${String(t.toFixed(2)).padStart(6, "0")}.png`);
    await renderStill({ composition, serveUrl, output, frame: Math.min(composition.durationInFrames - 1, Math.round(t * project.fps)), inputProps: project });
  }
}
rmSync(serveUrl, { recursive: true, force: true }); // the bundle copies the public dir (character frames): do not leave it in /tmp
console.log("stills in", out, times.join(" "));
