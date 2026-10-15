# Lab: character-integration — 3D presenter inside the video pipeline (phase B)

**Prerequisite:** lab "character" is finished (`lab/results/character.md`, `lab/character/facet.blend`, `render_clip.py`, `STYLE.md`). Do not start before it exists. Read it and `lab/results/integration.md`, `lab/BRIEF.md` first.
Follow BRIEF constraints ($0, minimal, ask before big downloads, never edit other labs: COPY `lab/integration/` into `lab/character-integration/` and evolve the copy). Report: `lab/results/character-integration.md`.
Machine: Apple M2, 8 GB. Heavy stages strictly one at a time. Never `pkill` processes you did not start.

## Goal
Take the first video ("What happens when you click Login?") from the flat test version to a **designed 3D-presenter version**: the faceted character "Facet" presents next to animated diagrams, with narration, captions and transitions, through the same n8n + host-runner pipeline. Still NO publishing.

## What changes versus the integration lab
1. **Storyboard v2** (`storyboard_v2.json`, you write it, schema-validated): ~45 s. Each scene gets: `narration`, `layout` (`presenter_left_diagram_right`, `presenter_center_typography`, `presenter_corner_diagram_full`), `character` events (`action` + time offset within the scene, e.g. `point_right`, `think`, `celebrate`), and per-packet **cue words** (`"cue": "token"` = the packet starts when that narrated word begins, taken from Whisper word timings; fall back to even spacing and warn if the word isn't found). Expand the narration to hit 40-50 s at a natural pace (Kokoro `bf_emma`, speed ~0.95), keeping it accurate and tight: hook, the request, the password-hash check, the token, why it matters (sessions vs token one-liner), payoff. Keep pronunciation respellings.
2. **New runner stage `character`:** allowlisted, id-only like the others. Inputs from `work/<id>/`: narration WAV and a generated `timeline.json` (derived from storyboard character events + aligned scene times). It calls the Blender CLI from lab "character" (draft preset by default, `final` via a query flag), writing `char_<camera>.webm` (VP9 alpha). Memory rule: it must not run concurrently with render; add a **global run lock** in the runner (reject or queue second request with a clear message).
3. **Remotion compositing:** layouts above; character clip placed via the method lab "character" found to work (OffthreadVideo transparent or PNG sequence). Clip and scene timing must stay in sync (same fps, same start offsets). Mouth-sync comes from the narration audio already, so the character clip must be rendered against the final aligned narration WAV.
4. **Visual fixes from the integration report:** vertically centre typography; a caption-free typography layout (no caption/typography collision); flow scene must show packets for most of its duration (stagger them across the scene by cue words, keep node highlights/pulses active while a node is being talked about); more motion on idle diagram elements (subtle ambient motion) so no frame feels static; consistent palette from `lab/character/STYLE.md` for backgrounds, nodes and typography; 9:16 layout puts the character in the lower third, diagram above.
5. **Audio:** two-pass loudnorm to -14 LUFS (verify with ebur128), optional quiet CC0/generated bed with gentle ducking (`sidechaincompress ratio 3-4`), no copyrighted music.
6. **n8n:** same workflow shape with the new stage added between align and render (SCRIPTING -> ASSET_GENERATION -> RENDERING -> AWAITING_APPROVAL). Add `ASSET_GENERATION` to the status CHECK via migration SQL (keep `init.sql` updated). Failure at any stage sets a FAILED status with a readable note. Keep the manual approval resume URL.

## Verification you must do
- Run the full pipeline through the n8n webhook; capture per-stage wall time and peak memory; total webhook-to-AWAITING_APPROVAL time on this machine. Report whether draft/final presets are realistic for a 45 s video (target: draft run under ~8 min total).
- Render stills for every scene in both aspects, view them, and fix: clipping, overflow, empty/static frames, character overlapping diagrams, caption collisions, halos on alpha edges. Iterate at least twice on what you find. List remaining flaws honestly.
- Check sync numerically: for each cue/character event compare intended time vs actual frame time (report max drift in ms).
- Deliver `out/final.mp4` (1080p), `out/final_vertical.mp4` (9:16), and `out/draft_*.mp4` if used.
- State what you could not verify (you cannot hear audio; you did not watch motion in real time).

## Do NOT
No publishing, no Instagram/analytics/dashboards, no second character, no AI-generated imagery, no paid anything, no leftover background processes (stop runner/containers you started unless told otherwise, and say which are still up).

## Report must include
Verdict, commands, the storyboard v2 schema, timings/memory table, sync drift numbers, contact sheet paths, remaining flaws, what the creator should judge by eye, and recommended next steps.
