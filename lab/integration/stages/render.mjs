// stage: render <id> — silent 16:9 + 9:16 renders from work/<id>/project.json (audio is added by assemble)
import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { validateProject } from "./validate.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const W = path.join(ROOT, "work", process.argv[2]);
validateProject(JSON.parse(readFileSync(`${W}/project.json`)));
for (const [comp, out] of [["Video", "silent.mp4"], ["VideoVertical", "silent_vertical.mp4"]]) {
  const r = spawnSync("npx", ["remotion", "render", "src/index.ts", comp, `${W}/${out}`, `--props=${W}/project.json`, `--public-dir=${W}`, "--muted", "--log=warn"],
    { cwd: path.join(ROOT, "remotion"), stdio: "inherit" });
  if (r.status) process.exit(r.status);
}
