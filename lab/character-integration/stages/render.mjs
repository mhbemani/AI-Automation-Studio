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
if (!existsSync(path.join(W, project.character.file))) { console.error(`ERROR: character clip ${project.character.file} missing in ${W} (run the character stage first)`); process.exit(2); }
for (const [comp, out] of [["Video", "silent.mp4"], ["VideoVertical", "silent_vertical.mp4"]]) { // one after the other: never two Chromes at once
  const r = spawnSync("npx", ["remotion", "render", "src/index.ts", comp, `${W}/${out}`, `--props=${W}/project.json`, `--public-dir=${W}`, "--muted", "--log=warn", "--concurrency=3"],
    { cwd: path.join(ROOT, "remotion"), stdio: "inherit" });
  if (r.status) { console.error(`ERROR: remotion render of ${comp} failed (exit ${r.status})`); process.exit(r.status); }
}
