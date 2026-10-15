// stage: render <id> — silent 16:9 + 9:16 renders from work/<id>/project.json + character clip (audio is added by assemble)
import { readFileSync, existsSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { validateProject } from "./validate.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const W = path.join(ROOT, "work", process.argv[2]);
const project = JSON.parse(readFileSync(`${W}/project.json`));
validateProject(project);
const todo = [["Video", "silent.mp4", "16:9", "char_16x9"], ["VideoVertical", "silent_vertical.mp4", "9:16", "char_9x16"]].filter((x) => existsSync(path.join(W, x[3], `f_${String(project.character.frames).padStart(4, "0")}.png`)));
if (!todo.length) { console.error("ERROR: no character frames in " + W + " (run the performance stage first)"); process.exit(2); }
for (const [comp, out] of todo) { // one after the other: never two Chromes at once; an aspect without a character clip is simply not rendered (draft = 16:9 only)
  const r = spawnSync("npx", ["remotion", "render", "src/index.ts", comp, `${W}/${out}`, `--props=${W}/project.json`, `--public-dir=${W}`, "--muted", "--log=warn", "--concurrency=3"],
    { cwd: path.join(ROOT, "remotion"), stdio: "inherit" });
  if (r.status) { console.error(`ERROR: remotion render of ${comp} failed (exit ${r.status})`); process.exit(r.status); }
}
