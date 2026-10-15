// Fast iteration on the performance: renders ONLY the character for one scene at tiny cost and builds a stills strip taken exactly at every beat's apex frame,
// composited into the real video frame (Remotion) with a cross at the on-screen target and a dot at the measured fingertip.
//   tools/preview_performance <runId> [--scene <1-based scene id>] [--aspect 16:9|9:16] [--res 480] [--samples 4] [--every 3] [--no-clip] [--gesture name]
// output: out/preview/<runId>/<aspect>/  strip_scene<k>.png, one PNG per beat, preview clip frames in work/<runId>/preview_<tag>/
import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync, rmSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
import path from "node:path";

const LAB = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const PIPE = path.join(LAB, "pipeline");
const args = process.argv.slice(2), id = args.find((a) => /^\d+$/.test(a));
const opt = (k, d) => { const i = args.indexOf("--" + k); return i >= 0 ? args[i + 1] : d; };
const aspect = opt("aspect", "16:9"), res = +opt("res", 480), samples = +opt("samples", 4), every = +opt("every", 3), sceneId = opt("scene"), only = opt("gesture");
if (!id) { console.error("usage: preview_performance <runId> [--scene id] [--aspect 16:9|9:16] [--res 480] [--samples 4] [--every 3] [--no-clip] [--gesture name]"); process.exit(2); }
const tag = aspect === "16:9" ? "16x9" : "9x16", W = path.join(PIPE, "work", id), BLENDER = process.env.BLENDER || "/Applications/Blender.app/Contents/MacOS/Blender";
const sh = (cmd, a, o = {}) => { const r = spawnSync(cmd, a, { encoding: "utf8", maxBuffer: 1 << 26, ...o }); if (r.status) { console.error((r.stdout || "") + (r.stderr || "")); process.exit(r.status || 1); } return r.stdout; };
const run = (f) => sh("node", [path.join(PIPE, "stages", f), id], { cwd: PIPE });

if (!existsSync(`${W}/geometry.json`)) run("geometry.mjs");
const camcfg = path.join(PIPE, "character.json"), profile = path.join(LAB, "rig_profile_facet.json"), perfJson = `${W}/performance_${tag}.json`;
console.log(sh("python3", [path.join(LAB, "character/solver.py"), "--work", W, "--aspect", aspect, "--profile", profile, "--camera-cfg", camcfg, "--out", perfJson]).trim());
const perf = JSON.parse(readFileSync(perfJson)), project = JSON.parse(readFileSync(`${W}/project.json`)), geom = JSON.parse(readFileSync(`${W}/geometry.json`))[aspect];
const beats = perf.beats.filter((b) => (!sceneId || String(b.scene) === String(sceneId)) && (!only || b.gesture === only));
if (!beats.length) { console.error("no beats selected"); process.exit(1); }
const sceneFrames = [...new Set(beats.map((b) => b.si))].map((si) => geom.scenes[si]);
const pdir = path.join(W, `preview_${tag}`); rmSync(pdir, { recursive: true, force: true }); mkdirSync(pdir, { recursive: true });
const frames = [...new Set(beats.map((b) => b.apexFrame))].sort((a, b) => a - b);
writeFileSync(`${W}/verify_in_${tag}.json`, JSON.stringify({ frames: frames.map((f) => ({ frame: f, rect: geom.rect[f] })) }));
const common = ["-b", path.join(LAB, "character/facet.blend"), "-P", path.join(LAB, "character/render_performance.py"), "--", "--perf", perfJson, "--camera-cfg", camcfg, "--res", String(res), "--samples", String(samples), "--out", pdir];
const t0 = Date.now();
const o1 = sh(BLENDER, [...common, "--only", frames.join(","), "--verify", `${W}/verify_in_${tag}.json`, "--verify-out", `${W}/verify_${tag}.json`]);
console.log(o1.split("\n").filter((l) => /POSE|VERIFY|RENDER|Error/.test(l)).join("\n"));
if (!args.includes("--no-clip")) { // the preview clip: every Nth frame of the selected scene(s) (frames not rendered are simply missing; the strip only needs the apex frames)
  const a = Math.min(...sceneFrames.map((s) => s.startFrame)), b = Math.max(...sceneFrames.map((s) => s.endFrame));
  const o2 = sh(BLENDER, [...common.slice(0, -2), "--out", pdir + "_clip", "--frames", `${a}-${b}`, "--every", String(every)]);
  console.log("clip:", o2.split("\n").filter((l) => /RENDER/.test(l)).join(" "), `(frames ${a}-${b}, every ${every}) -> ${pdir}_clip`);
}
// composite stills with markers through Remotion (the real layouts/backdrop/diagram, character frames from the preview dir)
const ver = Object.fromEntries(JSON.parse(readFileSync(`${W}/verify_${tag}.json`)).frames.map((r) => [r.frame, r]));
const marks = [];
for (const b of beats) {
  const v = ver[b.apexFrame]; if (b.targetApex) marks.push({ frame: b.apexFrame, x: b.targetApex[0], y: b.targetApex[1], color: "#ffffff", kind: "cross" });
  if (v && b.side) marks.push({ frame: b.apexFrame, x: v["tip_" + b.side][0], y: v["tip_" + b.side][1], color: "#ff00ff", kind: "dot" });
}
const pj = { ...project, character: { ...project.character, mode: "frames", dirs: { "16:9": path.basename(pdir), "9:16": path.basename(pdir) } }, debug: { marks } };
const require = createRequire(path.join(PIPE, "remotion/package.json")), { bundle } = require("@remotion/bundler"), { renderStill, selectComposition } = require("@remotion/renderer");
const serveUrl = await bundle({ entryPoint: path.join(PIPE, "remotion/src/index.ts"), publicDir: W });
const comp = await selectComposition({ serveUrl, id: aspect === "16:9" ? "Video" : "VideoVertical", inputProps: pj });
const out = path.join(LAB, "out/preview", id, tag); mkdirSync(out, { recursive: true });
const files = [];
for (const b of beats) {
  const f = path.join(out, `scene${b.scene}_${String(b.j).padStart(2, "0")}_${b.gesture}_f${b.apexFrame}.png`);
  await renderStill({ composition: comp, serveUrl, output: f, frame: b.apexFrame, inputProps: pj }); files.push({ f, b });
}
writeFileSync(path.join(out, "beats.json"), JSON.stringify(files.map(({ f, b }) => ({ file: path.basename(f), rect: geom.rect[b.apexFrame], ...b }))));
sh("python3", [path.join(LAB, "tools/strip.py"), out, ...files.map((x) => x.f)]);
rmSync(serveUrl, { recursive: true, force: true }); // each bundle copies the whole public dir (the character frames): do not leave them in /tmp
console.log(`stills: ${files.length} beats -> ${out}   (${((Date.now() - t0) / 1000).toFixed(0)} s total)`);
