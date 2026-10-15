// stage: character <id> <draft|final> — Blender renders the character clip (VP9 alpha) against the final aligned narration.wav and timeline.json
import { readFileSync, existsSync, statSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const id = process.argv[2], preset = process.argv[3] || "draft", W = path.join(ROOT, "work", id);
const cfg = JSON.parse(readFileSync(path.join(ROOT, "character.json")));
const BLENDER = process.env.BLENDER || "/Applications/Blender.app/Contents/MacOS/Blender";
const blend = path.resolve(ROOT, process.env.CHARACTER_BLEND || cfg.blend);
for (const f of [BLENDER, blend, `${W}/narration.wav`, `${W}/timeline.json`]) if (!existsSync(f)) { console.error(`ERROR: missing ${f} (run align first?)`); process.exit(2); }
const out = path.join(W, cfg.file.replace(/\.webm$/, "")); // render_clip writes <out>.webm
const r = spawnSync(BLENDER, ["-b", blend, "-P", path.join(ROOT, "stages/render_char.py"), "--", "--camera-cfg", path.join(ROOT, "character.json"),
  "--timeline", `${W}/timeline.json`, "--audio", `${W}/narration.wav`, "--out", out, "--preset", preset, "--camera", cfg.camera.name, "--aspect", cfg.camera.aspect],
  { encoding: "utf8", maxBuffer: 1 << 26 });
process.stdout.write((r.stdout || "").split("\n").filter((l) => /RENDER_SECONDS|ENCODE_SECONDS|ERROR/.test(l)).join("\n") + "\n");
if (r.status || !existsSync(out + ".webm")) { console.error("ERROR: character render failed: " + ((r.stderr || "") + (r.stdout || "")).split("\n").filter((l) => /ERROR|Error/.test(l)).slice(-3).join(" | ")); process.exit(r.status || 2); }
console.log(`${out}.webm ${(statSync(out + ".webm").size / 1e6).toFixed(2)} MB preset ${preset}`);
