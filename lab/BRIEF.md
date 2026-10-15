# Lab Brief — AI Educational Media Studio

You are one isolated **lab session** in a larger project. A separate "brain" session owns strategy; you only test ONE capability and report back.

## Project in one paragraph
We are building a small AI-assisted studio producing short (30–120s) visual explainer videos about software, AI, backend systems and the internet (working brand: "How Software Actually Works"). Human = creative director and final approver. Claude = ideas/research/script/storyboard (interactively, via Claude Pro / Claude Code, NOT via paid API). n8n = orchestration. Remotion + FFmpeg = deterministic animation and assembly. Blender = optional 3D (e.g. a recurring rigged mascot). Pexels = free stock. Local TTS (Kokoro/Piper) or the user's own voice = narration.

## Hard constraints
- **$0 extra spend.** Only free / open-source tools. No paid APIs, no sign-ups that need a card. If something needs an account or payment, stop and ask.
- Machine: macOS (Apple Silicon assumed; detect chip/RAM with `sysctl -n machdep.cpu.brand_string` and `sysctl -n hw.memsize` and record it).
- Keep it minimal: prove the capability, don't build a framework. Fewest files, no speculative abstractions.
- **Git:** follow `docs/GIT_RULES.md` (commit locally in small batches, never push or add a remote, no files over 5 MB, no secrets, no personal paths).
- Work only inside your own lab folder `lab/<your-lab-name>/`. Do not modify other labs or project docs.
- Don't install heavy things globally without saying so; prefer project-local installs / Docker. Ask before downloading large files (state name, source, size).

## Source docs (read-only context)
- `Sources/ai_educational_media_studio_plan.md` — full vision and plan
- `Sources/free_ai_educational_media_studio_stack.md` — the $0 stack decision (overrides paid providers in the first doc)

## Output contract (required)
When done (or blocked), write `lab/results/<your-lab-name>.md` containing:
1. **Verdict:** works / works with caveats / not viable — one line.
2. **What I did:** exact commands/steps to reproduce from scratch.
3. **Output:** paths of sample outputs (renders, audio, etc.) and their size/duration.
4. **Measurements:** render/generation time, resource use, machine specs.
5. **Problems & caveats:** licences, quality issues, gotchas.
6. **Recommendation:** what the studio should do with this tool, and the next experiment worth running.

Be honest: report failures and quality problems plainly. Keep the report short and factual.
