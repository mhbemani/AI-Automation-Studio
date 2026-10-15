// Host runner: POST /run/<stage>/<id>[?storyboard=name.json]  header x-runner-token. 127.0.0.1 only, fixed commands only.
import http from "node:http";
import { spawn } from "node:child_process";
import { copyFileSync, mkdirSync, appendFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const TOKEN = process.env.RUNNER_TOKEN;
if (!TOKEN) { console.error("set RUNNER_TOKEN"); process.exit(1); }
const S = (f) => path.join(ROOT, "stages", f);
const STAGES = { // the whole attack surface: stage -> argv builder (only the numeric id is interpolated)
  tts: (id) => [path.join(ROOT, "../tts/.venv/bin/python"), S("tts.py"), id],
  align: (id) => ["node", S("align.mjs"), id],
  render: (id) => ["node", S("render.mjs"), id],
  assemble: (id) => ["node", S("assemble.mjs"), id],
};

http.createServer((req, res) => {
  const u = new URL(req.url, "http://x");
  const [, run, stage, id] = u.pathname.split("/");
  const send = (code, o) => { res.writeHead(code, { "content-type": "application/json" }); res.end(JSON.stringify(o)); };
  if (req.headers["x-runner-token"] !== TOKEN) return send(401, { error: "bad token" });
  if (req.method !== "POST" || run !== "run" || !STAGES[stage] || !/^\d{1,9}$/.test(id || "")) return send(404, { error: "unknown stage or id" });
  const W = path.join(ROOT, "work", id);
  mkdirSync(W, { recursive: true });
  const sbName = u.searchParams.get("storyboard"); // plain filename inside this folder, copied once at first stage
  if (sbName) {
    if (!/^[\w-]+\.json$/.test(sbName) || !existsSync(path.join(ROOT, sbName))) return send(400, { error: "storyboard must be an existing plain *.json file next to runner.mjs" });
    copyFileSync(path.join(ROOT, sbName), path.join(W, "storyboard.json"));
  }
  const [cmd, ...args] = STAGES[stage](id);
  const t0 = Date.now(); let err = "", out = "";
  const p = spawn("/usr/bin/time", ["-l", cmd, ...args], { cwd: ROOT });
  p.stdout.on("data", (d) => (out += d)); p.stderr.on("data", (d) => (err += d));
  p.on("close", (code) => {
    const rss = +(err.match(/(\d+)\s+maximum resident set size/)?.[1] || 0);
    const m = { stage, id, ok: code === 0, wallSec: +((Date.now() - t0) / 1000).toFixed(1), peakRssMB: Math.round(rss / 1048576) };
    appendFileSync(path.join(W, "metrics.jsonl"), JSON.stringify(m) + "\n");
    console.log(JSON.stringify(m));
    send(code === 0 ? 200 : 500, { ...m, tail: (out + err).slice(-1500) });
  });
}).listen(8787, "127.0.0.1", () => console.log("runner on 127.0.0.1:8787"));
