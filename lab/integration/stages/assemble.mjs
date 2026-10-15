// stage: assemble <id> — voice + loudnorm -14 LUFS (+ optional quiet bed via BED=/path.wav) -> out/<id>/final.mp4 + final_vertical.mp4
import { mkdirSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const id = process.argv[2], W = path.join(ROOT, "work", id), O = path.join(ROOT, "out", process.argv[2]);
mkdirSync(O, { recursive: true });
const bed = process.env.BED; // optional; no music bed is shipped (no CC0 track chosen yet)
const af = bed
  ? "[1:a]volume=0.10[b];[0:a]asplit[v][k];[b][k]sidechaincompress=threshold=0.02:ratio=4[d];[v][d]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]"
  : "[0:a]loudnorm=I=-14:TP=-1.5:LRA=11[a]";
for (const [vid, out] of [["silent.mp4", "final.mp4"], ["silent_vertical.mp4", "final_vertical.mp4"]]) {
  const r = spawnSync("ffmpeg", ["-y", "-i", `${W}/narration.wav`, ...(bed ? ["-stream_loop", "-1", "-i", bed] : []), "-i", `${W}/${vid}`,
    "-filter_complex", af, "-map", `${bed ? 2 : 1}:v`, "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", path.join(O, out)], { stdio: "inherit" });
  if (r.status) process.exit(r.status);
}
