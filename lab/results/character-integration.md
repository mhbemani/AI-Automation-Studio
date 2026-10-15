# Lab result: character-integration (Facet presenter inside the n8n + Remotion pipeline)

**1. Verdict:** Works with caveats. One webhook call turns `storyboard_v2.json` into a 42.2 s 1080p and 9:16 MP4 with the Facet presenter, cue-synced diagrams, captions, transitions and two-pass loudnorm. A **draft** run takes **8m43s** webhook to AWAITING_APPROVAL (target ~8 min: slightly over). A **final** run takes **17m49s**. Visuals and sync were checked from stills and measurements; I cannot hear audio and did not watch the videos in motion.

Note: all work is on branch `<task branch>` in its worktree (`lab/character-integration/`), committed. Other labs were only read. MP4s are git-ignored (`*.mp4`), so the videos exist only on disk in `lab/character-integration/out/` of that worktree.

**2. Commands** (from `lab/character-integration/`; `.env` holds RUNNER_TOKEN, PORT=8788, TTS_DIR, WHISPER_MODEL; it is git-ignored)
```bash
cp -cR <lab>/integration/remotion/node_modules remotion/        # reused, not reinstalled
(set -a; . ./.env; set +a; node runner.mjs &)                    # 127.0.0.1:8788 (8787 is the older lab's runner, left alone)
docker exec -i n8n-postgres-1 psql -U studio -d studio < n8n/migrate_asset_generation.sql   # adds ASSET_GENERATION to the status CHECK (init.sql updated too)
docker cp n8n/workflow.json n8n-n8n-1:/tmp/c.json && docker exec n8n-n8n-1 n8n import:workflow --input=/tmp/c.json
docker exec n8n-n8n-1 n8n publish:workflow --id=chint001 && docker restart n8n-n8n-1
curl -X POST localhost:5678/webhook/character-integration -H 'content-type: application/json' \
  -d '{"topic":"What happens when you click Login?","storyboard":"storyboard_v2.json","preset":"draft"}'   # preset "final" for the release render
# status SCRIPTING -> ASSET_GENERATION -> RENDERING -> AWAITING_APPROVAL; resume URL for approval is in content_items.note (as before)
node stages/stills.mjs <id>                                      # stills of both aspects
<tts venv python> tools/sync_check.py <id>                       # sync measurements
```
Stages (runner, id-only, `POST /run/{tts|align|character|render|assemble}/<id>`; `character` also takes `?preset=draft|final`): `tts.py` (bf_emma, speed 0.95 from storyboard), `align.mjs` (whisper word times, cue resolution, scene timing in whole frames, `timeline.json`, narration track), `character.mjs` (Blender, VP9 alpha), `render.mjs` (Remotion 16:9 then 9:16, never in parallel), `assemble.mjs` (loudnorm, bed, mux). **Global run lock:** a second request while a stage runs gets HTTP 409 `runner busy: stage "tts" of run 7 is still running...` (tested). Errors come back as plain text so n8n puts a readable message in `note` (tested with `storyboard_bad.json`: `tts failed: Error: Invalid storyboard: - scene[0]... action "dance" unknown ...`, status FAILED).

**3. Storyboard v2 schema** (validated strictly in `stages/validate.mjs`: unknown keys, unknown layouts/actions/nodes, non-adjacent packets and cue words absent from the narration all fail before any heavy stage)
```
{ version: 2, topic, series, targetSeconds, bed: "generated"|"none",
  voice: { main: "bf_emma", alt: "af_heart", speed: 0.95 },
  pronunciation: { "API": "A P I", ... },
  scenes: [ {
    id, narration,
    layout: "presenter_center_typography" | "presenter_left_diagram_right" | "presenter_corner_diagram_full",
    // typography layout:
    onScreen: [ { text, cue?: word } ],
    // diagram layouts:
    nodes: [name...], packets: [ { from, to, label, cue?: word } ],      // chain, adjacent nodes only
    focus: [ { node, cue: word, label?: text } ],                          // node highlight (+ status line) while it is talked about
    character: [ { action, at: seconds-after-narration-start | cue: word } ]   // actions: wave talk think point_left point_right celebrate idle enter exit
  } ] }
```
`cue` = word from the Whisper timing (first match at or after the previous cue in that list; not-found falls back to even spacing with a WARN; none were needed in the run: 126/126 words matched). The 3 layouts: character left + diagram right; character centre-bottom + big typography above (no captions in this layout); small character bottom-left + full-width diagram. In 9:16 every layout puts the character in the lower third with content above and captions between.

**4. Timings and memory** (Apple M2, 8 GB; Docker n8n + Postgres running throughout; wall seconds per stage from the runner)
| stage | draft run (id 7) | final run (id 8) | peak RSS of largest process | system used peak (active+wired+compressed; base ~5.2-5.7 GB) |
|---|---|---|---|---|
| tts (Kokoro, 6 scenes) | 34.6 s | 36.0 s | 409-552 MB | 6.1 GB |
| align (6x whisper + timing) | 3.4 s | 3.3 s | 376 MB | 6.2 GB |
| character (Blender, 1267 frames, 1:1 clip) | 243.8 s | 626 s | 357 / 550 MB | 6.6 GB |
| render (16:9 + 9:16, 1267 frames each) | 229.5 s | 391 s | 669 MB | 6.1-6.5 GB |
| assemble (2-pass loudnorm, bed, 4 muxes) | 9.6 s | 11.1 s | 105 MB | 5.6 GB |
| **webhook -> AWAITING_APPROVAL** | **523 s (8m43s)** | **1069 s (17m49s)** | | |
Swap: 39k pages swapped out during the draft character stage (about 600 MB), 15k in the final run; no failure, no OOM. Draft = 720x720 clip, 6 samples; final = 1080x1080, 16 samples (`character.json` `quality`; I lowered samples from the character lab's 16/32 because 6 vs 16 samples looked the same at 720 and halved the time: 0.34 -> 0.16 s/frame). **Draft is realistic** (about 9 min, slightly above the 8 min target; the Blender stage is ~half). **Final is realistic as an overnight/background job**, not for iteration (18 min).

**5. Sync numbers** (`sheets/sync_report.json`, measured on the delivered files by `tools/sync_check.py`)
- Narration words: Whisper on the final MP4's audio vs intended times: mean 163 ms, p95 400, **max 730 ms**, 126/126 matched. The same test on the clean `narration.wav` gives mean 168 / max 750 ms, so this is Whisper token-timing jitter (it ran on whole-file vs per-scene audio), not a pipeline offset (signed mean +46 ms). Audio placement itself is `adelay` in whole ms, so by construction it is exact; this measurement cannot show better than Whisper's resolution.
- Packet launches (frame where the packet colour first appears vs intended cue time, 6/6 found): max |drift| **200 ms** by this detector. Positive 100 ms = the packet grows from small, so my detector triggers late; negative -167/-200 ms = contamination by same-colour elements (ripples/docked chips). Renderer mapping is "visible when t >= at", so true drift is at most 1 frame (33 ms) by construction; the measurement is not that precise.
- Character events (silhouette change onset after each of 19 timeline events): 12 found, max lag **167 ms**, mean 67 ms; 7 had no clear onset (talk -> talk transitions are too subtle). Lag is expected from the 6-frame cross-fade.
- **Mouth vs narration loudness** (dark mouth pixels in the clip vs lipsync envelope): best lag **0 frames**, correlation 0.74 (0.68/0.70 at +-1 frame). Clip frames 1267 = video frames 1267 (same fps, starts at frame 0).
- So: worst measured drift 200 ms (detector-limited), real expected <= 1 frame for visuals, which was not proven more tightly.

**6. Loudness:** two-pass `loudnorm` (linear) then ebur128 on the finished files: **-14.5 LUFS integrated, LRA 1.9, true peak -1.5 dBTP** (target -14: 0.5 LU low; all four files identical). Bed: generated pad (our own sine synthesis, no licence issue), set 22 LU under the voice and ducked with `sidechaincompress ratio 3.5`. I could not listen; judge it by ear. `final_nobed.mp4` is the same video with voice only.

**7. Output** (`lab/character-integration/out/` in the worktree; git-ignored)
- `final.mp4` 1920x1080 30 fps 42.2 s 20.2 MB (final preset, with bed); `final_nobed.mp4`; `final_vertical.mp4` 1080x1920 19.4 MB (and `final_vertical_nobed` in `out/8/`)
- `draft_16x9.mp4`, `draft_vertical.mp4` (draft preset, run 7)
- Committed: `sheets/contact_16x9.png` (24 stills), `sheets/contact_9x16.png`, `sync_report.json`, `loudness.json`, metrics, `timeline.json`. Full still sets are in `out/8/stills/`.

**8. Character swap contract.** The creator calls Facet a placeholder. To swap in a better character change only: (1) `character.json` (`blend` path, `camera` framing, `framing` = where the character stands inside the square clip, `quality`); (2) the `.blend` itself must keep what `lab/character/render_clip.py` expects: armature object `FacetRig` (bones root, torso, head, eye_L, eye_R, mouth, arms...), actions `idle talk point_left point_right wave think celebrate enter exit` at 30 fps, camera object `STAGE_camera`. Remotion only sees a transparent square VP9 clip (`char_stage.webm`) and the `framing` numbers. `stages/render_char.py` is the only glue (it registers the camera preset without editing the character lab). Env `CHARACTER_BLEND` overrides the file.

**9. Visual review.** Stills of every scene in both aspects, two fix rounds. Fixed: arm of the pointing character touching the diagram; 9:16 diagram drawn as a small horizontal strip (now a vertical chain); packet label colliding with a docked chip in 9:16; two packets overlapping on one edge; orphan word wrapping in 9:16 typography; text height jump. Checked the character edges on navy: no dark/light halos seen at draft or final.
Remaining flaws (honest):
- Character clip is 720 px at draft, upscaled about 1.4x: soft. Final is sharp. Character itself is the weak placeholder (specular patches, flat expressions, feet slide when moving between layouts).
- Typography scenes leave a gap between the text and the character; single-line moments look high.
- Left layout: diagram is small and sits in the upper half; the lower half has only docked chips and captions.
- Packet in flight covers only 52%, 69%, 56% of the three flow scenes (target "most"); docked log chips, pulses and drifting dots fill the gaps but the first diagram scene, with one packet, still has a calm stretch.
- Docked chips and status text are small (26 px at 1080p).
- Backdrop shards are low-opacity and may feel busy or plain; judge by eye.
- Loudness 0.5 LU below -14.
- Duration 42 s (spec ~45; text could be a little longer).

**10. Not verified:** audio (voice, pronunciation, bed, ducking) was never heard; motion smoothness (character blending, hand-offs between layouts, transitions) was never watched in real time; the 9:16 stills were skimmed at small size; packet drift precision as noted above.

**11. What to watch by eye** (`out/final.mp4` first, then `out/final_vertical.mp4`; `out/final_nobed.mp4` to compare the bed)
1. Do the mouth and the voice feel in sync, and is the pointing at the right moments (scenes 2-4)?
2. Does the character glide between layouts at scene changes (about 6 s, 16 s, 31 s) without looking odd?
3. Does each packet leave when its word is spoken ("sends", "looks", "hash", "shows", "signature")?
4. Is the character readable and likeable, or is it distracting (this decides if the placeholder must be replaced first)?
5. Does the bed help or annoy; is the voice clear over it?
6. 9:16: is the lower-third character too big, do captions sit well between diagram and character?
7. Anything that feels static; any flicker at the cross-fades.

**12. Recommendation / next**
- Judge the character first; replace via the contract above before polishing anything else.
- Speed: draft at ~9 min is dominated by Blender; options: render only on `final`, cache the clip when the timeline is unchanged, or render at 24 fps-equivalent frames. Not needed yet.
- Listen to audio; consider raising the loudnorm target by 0.5 LU.
- Then: Pexels/b-roll scene type, per-scene "Layout" variety, and the publishing phase.

**Left running:** my runner (stopped at the end of the session), n8n and Postgres containers (not mine; I restarted n8n once to publish the new workflow `chint001`; the older workflow `integ001` and its runner on :8787 are untouched). The shared lab DB constraint was altered (ASSET_GENERATION added); rows 5-8 are test runs (5,6 FAILED tests, 7 draft, 8 final, both AWAITING_APPROVAL).
