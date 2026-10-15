// Host runner: POST /run/<stage>/<id>[?storyboard=name.json][&preset=draft|final][&aspects=16:9|16:9,9:16]  header x-runner-token. 127.0.0.1 only, fixed commands only.
// One stage at a time (8 GB machine): a second request while one runs is rejected with 409 and a readable message.
import http from "node:http";
import { spawn, execFileSync } from "node:child_process";
import { copyFileSync, mkdirSync, appendFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const TOKEN = process.env.RUNNER_TOKEN;
if (!TOKEN) { console.error("set RUNNER_TOKEN"); process.exit(1); }
const PORT = +(process.env.PORT || 8787);
const TTS_DIR = process.env.TTS_DIR || path.join(ROOT, "../tts");
const S = (f) => path.join(ROOT, "stages", f);
const STAGES = { // the whole attack surface: stage -> argv builder (only the numeric id and the preset enum are interpolated)
  tts: (id) => [path.join(TTS_DIR, ".venv/bin/python"), S("tts.py"), id],
  align: (id) => ["node", S("align.mjs"), id],
  performance: (id, preset, aspects) => ["node", S("performance.mjs"), id, preset, aspects],
  render: (id) => ["node", S("render.mjs"), id],
  assemble: (id) => ["node", S("assemble.mjs"), id],
};
const PRESETS = ["draft", "final"], ASPECTS = ["16:9", "9:16", "16:9,9:16", "9:16,16:9"];

// system memory used (active + wired + compressed) and swap-outs, sampled while a stage runs
const vm = () => {
  const t = execFileSync("vm_stat", { encoding: "utf8" }), g = (k) => +(t.match(new RegExp(k + ":\\s+(\\d+)"))?.[1] || 0);
  return { usedMB: Math.round(((g("Pages active") + g("Pages wired down") + g("Pages occupied by compressor")) * 16384) / 1048576), swapouts: g("Swapouts") };
};

let busy = null;
http.createServer((req, res) => {
  const u = new URL(req.url, "http://x");
  const [, run, stage, id] = u.pathname.split("/");
  // errors go out as plain text so n8n stores a readable message in content_items.note; success is JSON with the metrics
  const send = (code, o) => { res.writeHead(code, { "content-type": code < 400 ? "application/json" : "text/plain" }); res.end(code < 400 ? JSON.stringify(o) : o.error); };
  if (req.headers["x-runner-token"] !== TOKEN) return send(401, { error: "bad token" });
  if (req.method !== "POST" || run !== "run" || !STAGES[stage] || !/^\d{1,9}$/.test(id || "")) return send(404, { error: "unknown stage or id" });
  const preset = u.searchParams.get("preset") || "draft";
  if (!PRESETS.includes(preset)) return send(400, { error: `preset must be ${PRESETS.join(" or ")}` });
  const aspects = u.searchParams.get("aspects") || (preset === "final" ? "16:9,9:16" : "16:9"); // draft = the 16:9 character clip only, final = both aspects
  if (!ASPECTS.includes(aspects)) return send(400, { error: `aspects must be one of ${ASPECTS.join(" | ")}` });
  const sbName = u.searchParams.get("storyboard"); // plain filename inside this folder, copied once at first stage
  if (sbName && (!/^[\w-]+\.json$/.test(sbName) || !existsSync(path.join(ROOT, sbName)))) return send(400, { error: "storyboard must be an existing plain *.json file next to runner.mjs" });
  if (busy) return send(409, { error: `runner busy: stage "${busy.stage}" of run ${busy.id} is still running (${Math.round((Date.now() - busy.t0) / 1000)} s). Heavy stages run one at a time; retry when it finishes.` });
  busy = { stage, id, t0: Date.now() };
  const W = path.join(ROOT, "work", id);
  mkdirSync(W, { recursive: true });
  if (sbName) copyFileSync(path.join(ROOT, sbName), path.join(W, "storyboard.json"));
  const [cmd, ...args] = STAGES[stage](id, preset, aspects);
  const t0 = Date.now(); let err = "", out = "";
  const base = vm(); let peak = base.usedMB;
  const tick = setInterval(() => { peak = Math.max(peak, vm().usedMB); }, 1000);
  const done = (code, spawnErr) => {
    clearInterval(tick); const end = vm();
    const rss = +(err.match(/(\d+)\s+maximum resident set size/)?.[1] || 0);
    const m = { stage, id, ok: code === 0, wallSec: +((Date.now() - t0) / 1000).toFixed(1), peakRssMB: Math.round(rss / 1048576), sysUsedBaseMB: base.usedMB, sysUsedPeakMB: Math.max(peak, end.usedMB), swapoutPages: end.swapouts - base.swapouts, ...(stage === "performance" ? { preset, aspects } : {}) };
    appendFileSync(path.join(W, "metrics.jsonl"), JSON.stringify(m) + "\n");
    console.log(JSON.stringify(m));
    const all = (spawnErr || out + err).trim().split("\n");
    const key = all.filter((l) => /^(ERROR|Error|Invalid| - )/.test(l.trim()) || /^ - /.test(l));
    busy = null;
    send(code === 0 ? 200 : 500, code === 0 ? { ...m, tail: (out + err).slice(-1500) } : { error: `${stage} failed: ` + (key.length ? key : all.slice(-4)).join(" | ").slice(0, 900) });
  };
  const p = spawn("/usr/bin/time", ["-l", cmd, ...args], { cwd: ROOT });
  p.stdout.on("data", (d) => (out += d)); p.stderr.on("data", (d) => (err += d));
  p.on("error", (e) => done(1, String(e))); p.on("close", (code) => done(code));
}).listen(PORT, "127.0.0.1", () => console.log(`runner on 127.0.0.1:${PORT}`));
