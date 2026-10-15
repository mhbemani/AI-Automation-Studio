// stage: performance <id> <draft|final> [aspects: "16:9" | "16:9,9:16"]
// storyboard_v3 beats + aligned words + narration.wav + on-screen geometry -> solver (per-frame rig channels) -> Blender (pose every frame, RGBA PNG frames) -> work/<id>/char_<aspect>/f_%04d.png
import { readFileSync, existsSync, writeFileSync, rmSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { exportGeometry, ASPECTS } from "./geometry.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const LAB = path.resolve(ROOT, "..");
const id = process.argv[2], preset = process.argv[3] || "draft", aspects = (process.argv[4] || (preset === "final" ? "16:9,9:16" : "16:9")).split(",");
const W = path.join(ROOT, "work", id), BLENDER = process.env.BLENDER || "/Applications/Blender.app/Contents/MacOS/Blender";
const blend = path.resolve(ROOT, process.env.CHARACTER_BLEND || "../character/facet.blend");
for (const a of aspects) if (!ASPECTS[a]) { console.error(`ERROR: unknown aspect "${a}" (${Object.keys(ASPECTS).join(", ")})`); process.exit(2); }
for (const f of [BLENDER, blend, `${W}/narration.wav`, `${W}/project.json`, `${W}/beats.json`, `${W}/words.json`]) if (!existsSync(f)) { console.error(`ERROR: missing ${f} (run align first?)`); process.exit(2); }

const project = JSON.parse(readFileSync(`${W}/project.json`));
writeFileSync(`${W}/geometry.json`, JSON.stringify(await exportGeometry(project)));
const times = {};
for (const a of aspects) {
  const tag = a === "16:9" ? "16x9" : "9x16", perf = `${W}/performance_${tag}.json`, dir = `${W}/char_${tag}`;
  let t0 = Date.now();
  const s = spawnSync("python3", [path.join(LAB, "character/solver.py"), "--work", W, "--aspect", a, "--profile", path.join(LAB, "rig_profile_facet.json"), "--camera-cfg", path.join(ROOT, "character.json"), "--out", perf], { encoding: "utf8" });
  if (s.status) { console.error("ERROR: performance solver failed: " + (s.stderr || s.stdout).split("\n").filter((l) => l.trim()).slice(-3).join(" | ")); process.exit(s.status); }
  console.log(s.stdout.trim()); times[`solve_${tag}`] = (Date.now() - t0) / 1000;
  rmSync(dir, { recursive: true, force: true });
  t0 = Date.now();
  const r = spawnSync(BLENDER, ["-b", blend, "-P", path.join(LAB, "character/render_performance.py"), "--", "--perf", perf, "--camera-cfg", path.join(ROOT, "character.json"), "--preset", preset, "--out", dir], { encoding: "utf8", maxBuffer: 1 << 28 });
  process.stdout.write((r.stdout || "").split("\n").filter((l) => /POSE_SECONDS|RENDER_SECONDS|ERROR/.test(l)).join("\n") + "\n");
  if (r.status || !existsSync(`${dir}/f_${String(project.character.frames).padStart(4, "0")}.png`)) { console.error("ERROR: character render failed: " + ((r.stderr || "") + (r.stdout || "")).split("\n").filter((l) => /Error|ERROR|Traceback/.test(l)).slice(-3).join(" | ")); process.exit(r.status || 2); }
  times[`render_${tag}`] = (Date.now() - t0) / 1000;
}
console.log(`performance done (${preset}; ${aspects.join(" + ")}): ` + JSON.stringify(times));
