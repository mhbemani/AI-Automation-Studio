# Lab: integration — first end-to-end pipeline test (NO publishing)

Read `lab/BRIEF.md` and all `lab/results/*.md` first. Follow the BRIEF constraints and output contract (report -> `lab/results/integration.md`). You are lab "integration"; work in `lab/integration/` (reuse and COPY from other labs, never edit them).

## Decisions already made
- Voice: Kokoro `bf_emma` (main), `af_heart` (alternative). Reuse `lab/tts/` setup/models.
- First video has NO 3D character: typography + diagrams only.
- Remotion is the engine; FFmpeg only for final audio/encode; whisper.cpp for word timing.
- Input is `lab/integration/storyboard.json` (3 scenes, ~45s).
- Machine is an M2 with 8 GB RAM: run heavy stages ONE AT A TIME (never Docker + render + TTS concurrently).

## Build (minimal, no frameworks)
1. **Host runner:** tiny Node script, binds 127.0.0.1 only, shared-token header, allowlist of fixed commands (tts, align, render, assemble) taking only a content-item id. No arbitrary shell. n8n reaches it via `host.docker.internal`.
2. **Pipeline stages** (each a plain script working on `work/<id>/`): storyboard.json -> narration WAV (Kokoro, per scene, with pronunciation respelling) -> Whisper word timestamps -> scene timing JSON -> Remotion project JSON -> render silent video -> FFmpeg: add voice, loudnorm -14 LUFS, optional quiet bed, export 1080p MP4 + 9:16.
3. **Remotion:** add a typography scene (kinetic title/bullet reveal), `<Series>` with a fade transition across the 3 scenes, `<Audio>`, styled captions from word timings (not FFmpeg-burned), open-licence font (e.g. Inter via @remotion/google-fonts or bundled), fix the packet-label z-order bug from the remotion report, and validate scene JSON before rendering (fail with a clear message).
4. **n8n:** reuse `lab/n8n/` compose (pin n8n 2.41.7). Workflow: webhook {storyboard path} -> insert content_items row -> call runner stage by stage, updating status (SCRIPTING -> RENDERING -> AWAITING_APPROVAL) -> on failure set a FAILED-style note and stop. Add a Wait/resume webhook for manual APPROVED. Note: if Docker + render is too heavy at 8 GB, say so and propose running n8n natively.
5. **Do NOT** build publishing, Instagram, analytics, Blender, or dashboards.

## Measure and report
Per-stage wall time and peak memory, total time idea->MP4, file sizes, number of manual steps, what broke. Include a quality self-check: render stills at key frames and look at them; list visual flaws honestly (clipping, overflow, timing drift between narration and animation). State clearly what you could not verify (e.g. you cannot hear audio).
Final deliverable: `out/final.mp4`, `out/final_vertical.mp4`, plus the report.
