# Git rules

For every agent and for the creator. The pre-commit hook in `.githooks/` enforces the file rules below (`git config core.hooksPath .githooks`, already set in this clone).

## Who pushes, and when
- **Only the creator publishes.** Agents commit locally. Agents never add a remote, create a GitHub repository, push, or force-push on their own.
- If the creator says "push" in a session: push `main` only, with a plain `git push` (tags with `git push --tags` if asked). Before pushing, show the creator `git log --oneline origin/main..` and `git status`.
- After the first public push, published history is never rewritten. A mistake gets a new commit; a leaked secret gets rotated first, then the creator is told.

## Branches and worktrees
- One task = one worktree branch (`.claude/worktrees/` is local only and never committed).
- When the task is finished and verified: update `main` with `git merge --ff-only` (rebase the branch first if needed), then delete the branch and the worktree. Only `main` and the `vN` tags are ever pushed.

## Commits
- Commit after each finished, checked batch. Small commits, one subject line: `area: what changed` (add numbers when there are any, e.g. `animation-build: 113 actions, contract test passes`).
- Write for a human reader of the public history: say what changed, not which session or "brain"/"main agent" did it.
- No `Co-Authored-By` lines, no "Generated with" lines, no names of tools or sessions in commit messages or file contents. Do not change `git config` (the author is the creator's identity).

## What goes in git
Scripts (`.py`, `.sh`, `.ts`, `.tsx`, `.mjs`, `.sql`), workflow JSON, docs and reports (`.md`), `requirements`/`package` files, and small images (stills and sheets). Every file stays **under 5 MB**.

## What never goes in git
| Never commit | Where it lives instead |
|---|---|
| `.blend`, `.fbx`, `.glb`, `.obj` and any file containing BlenderKit (Royalty Free) models | local only; own-made files may be attached to a GitHub Release by the creator |
| Videos longer than a short preview, audio (`.wav`, `.mp3`), archives (`.zip`, `.tar.gz`) | finished videos go to YouTube; README gets a link or a clip (<= 5 MB) in `docs/media/` |
| Model weights (`.onnx`, `.pt`, `.pth`, `.ckpt`, `.safetensors`) | downloaded by a script |
| **Voice samples and trained voice models of the creator or friends** | never leave the machine |
| Secrets: `.env*`, `.token`, `cred*.json`, `credentials*`, keys, API tokens | local only; rotate any secret that was ever staged |
| Downloaded third-party packs (CC0 or not) | fetched by a script (`fetch_assets.py` style) |
| `CLAUDE.md`, `.claude/` | local agent config |

## Portability
- No absolute personal paths (`/Users/<name>/...`) in code or docs: use paths relative to the repo, or `~`/`$HOME`. No agent worktree paths in docs.
- A lab that needs an asset or tool that others cannot get (e.g. a BlenderKit login) says so in its `ASSETS.md` or README.

## Licences
Before using any third-party asset, tool or model, record it in the lab's `ASSETS.md`: name, source URL, licence, date. Only CC0/permissive items may be fetched by script; anything Royalty Free or restricted is never committed or redistributed.

## Before the first public push (creator decides)
1. Secrets and personal-path scan of the whole tree and history.
2. A human-facing README (what it is, how to run the reproducible parts, results), a `LICENSE` for the own code, and a credits/licences section.
3. Decide: publish the full history, or a fresh history from the current tree.
4. Check the stills for anything personal.

## The hook
`.githooks/pre-commit` blocks forbidden file types, files over 5 MB, likely secrets and personal paths. If it blocks a commit, fix the cause. Never use `--no-verify` unless the creator says so.
