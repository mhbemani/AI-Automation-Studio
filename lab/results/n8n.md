# Lab: n8n + PostgreSQL

**1. Verdict:** Works with caveats. n8n 2.41.7 + Postgres 16 run fine in Docker. The webhook → DB insert → local script → DB update flow works, and data persists across restarts. Host-installed tools (FFmpeg/Remotion/Blender) are not reachable from the container without extra setup.

## 2. What I did (reproduce from scratch)
Files are in `lab/n8n/`: `docker-compose.yml`, `init.sql` (the `content_items` table), `work/fake_render.sh`, `workflow.json` (import file), `workflow.exported.json` (CLI export of the live workflow), `cred.json` (Postgres credential, local-only password).
```bash
cd lab/n8n
docker compose up -d        # first run pulls ~1.3 GB; took ~10 min here
# wait ~20s, then load credential + workflow into n8n and activate it
docker cp cred.json n8n-n8n-1:/tmp/cred.json && docker cp workflow.json n8n-n8n-1:/tmp/wf.json
docker compose exec n8n n8n import:credentials --input=/tmp/cred.json
docker compose exec n8n n8n import:workflow --input=/tmp/wf.json
docker compose exec n8n n8n publish:workflow --id=labcontent01
docker compose restart n8n
curl -X POST localhost:5678/webhook/content -H 'content-type: application/json' -d '{"topic":"How DNS works"}'
docker compose exec postgres psql -U studio -c "select * from content_items"
```
- Editor UI is at http://localhost:5678. First visit asks for an owner account (local only, no card needed). The webhook worked without logging in.
- Postgres is also published on host port 5433 (user `studio`, db `studio`).
- `content_items` has the columns you asked for. `status` has a CHECK constraint on IDEA, SCRIPTING, RENDERING, AWAITING_APPROVAL, APPROVED, PUBLISHED.
- Workflow: Webhook (POST `/webhook/content`) → INSERT row as `IDEA` → Execute Command runs `/work/fake_render.sh <id> <topic>` → UPDATE to `RENDERING` and store the script's JSON output in `script`. The response is the final row.
- Compose sets `NODES_EXCLUDE=[]`. n8n 2.x disables the Execute Command node by default, and this turns it back on.
- The script runs inside the n8n container, with `./work` mounted at `/work`.

## 3. Output
- Webhook response (id 1): `{"id":1,"topic":"How DNS works","status":"RENDERING","script":{...},"created_at":...,"updated_at":...}`
- `lab/n8n/work/item_1.json` (92 B) and `item_2.json`, written by the script.
- Workflow exports: `workflow.json`, `workflow.exported.json`.

## 4. Measurements
- Machine: Apple M2, 8 GB RAM. Docker Desktop VM has 1 CPU and ~2.85 GB.
- Docker daemon wasn't running at start; you launched it.
- Webhook round-trip: about 0.1 s for insert + script + update.
- Idle memory: n8n ~377 MiB, Postgres ~25 MiB.
- Images: n8n 1.04 GB, Postgres 288 MB.
- Persistence: `docker compose down` then `up -d` (no `-v`). The row survived, the workflow and credential survived, and the webhook worked straight away. Data lives in the `pgdata` and `n8ndata` volumes. `down -v` would delete them.
- Injection check: a topic of `it's a 'test'; DROP TABLE content_items` was stored verbatim (parameterised query), and the table survived. The shell argument is sanitised in the workflow with a regex (`[^A-Za-z0-9 _-]` stripped).

## 5. Problems & caveats
- **Host tools:** the container is Linux aarch64 and has no ffmpeg (`which ffmpeg` is empty). Host FFmpeg at `/opt/homebrew/bin/ffmpeg` is a macOS binary and can't run in the container. Execute Command reaches only what's in the image or the mounted folder.
- **Reaching the host:** `host.docker.internal` works from the container (I fetched a page from a host HTTP server). Because of that, the clean pattern is:
  - n8n calls a small host runner via the HTTP Request node.
  - The runner is a ~20-line Node script that `spawn`s `ffmpeg`, `npx remotion render` or `blender -b`.
  - It runs under launchd or `npm run`.
  - Bind it to 127.0.0.1, or to all interfaces if the container must reach it (then protect it with a shared token), and only allow a fixed list of commands.
  - I did **not** build or test the runner. I only tested the container-to-host connection.
- **Alternatives:** (a) a custom image that adds ffmpeg, which doesn't help for Remotion/Blender on macOS; (b) n8n installed natively with `npx n8n`, where Execute Command then sees host tools directly, at the cost of not being containerised.
- **Shared folder:** the bind mount `./work:/work` is how renders and JSON move between n8n and the host. It worked, and file ownership was fine.
- **Execute Command risk:** it runs arbitrary shell. Keep n8n bound to localhost and never interpolate raw webhook input into the command (sanitised here).
- **Postgres credential:** importing it through the CLI worked. A credential created in the UI would also do.
- **n8n 2.x:** workflows must be *published* to activate. The old `update:workflow --active` is replaced by `publish:workflow`, and the new setup needs a restart to register the webhook.
- **Licence:** n8n is under the Sustainable Use License (source-available, not OSI open source).
  - It allows use "for your own internal business purposes or for non-commercial or personal use".
  - It forbids reselling n8n or offering it to others as a hosted service.
  - Running it to produce our own videos, including monetised ones, is internal use of our own business and is fine.
  - The `.ee.` files are enterprise-only.
  - Read as of the repo LICENSE.md today, not legal advice.
  - Note this is a different licence from the AGPL/MIT tools elsewhere in the stack.
- The Docker image pull is slow (~10 min). `:latest` is unpinned, so pin a version (2.41.7) for reproducibility.

## 6. Recommendation
- Use n8n + Postgres in Docker as the orchestrator and state store. It's lightweight enough on an 8 GB M2.
- Put all heavy work (Remotion, FFmpeg, Blender, TTS) behind one small host-side runner reached via `host.docker.internal`. Don't try to run those inside the container.
- Next experiment: build that runner (Node, token-protected, allowlisted commands) and have n8n trigger a real FFmpeg command on a file in `work/`. Then add a manual-approval step: a Wait node with a resume webhook, which moves the status to AWAITING_APPROVAL → APPROVED.
