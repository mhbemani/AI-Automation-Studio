# Lab: performance — fix character flicker + scripted, diagram-synced character performance (phase C)

Read first: `lab/BRIEF.md`, `lab/results/character.md`, `lab/results/character-integration.md`, `lab/results/integration.md`, then the code in `lab/character/` and `lab/character-integration/`.
Constraints: $0, no downloads without asking, never `pkill` processes you did not start, heavy stages one at a time (M2, 8 GB), no publishing. COPY `lab/character-integration/` to `lab/performance/pipeline/` and evolve the copy (and COPY `lab/character/` to `lab/performance/character/` if you change the rig/renderer). Do not edit the older labs. Work in your own worktree, COMMIT your finished work on your branch. Report: `lab/results/performance.md`.

## Creator feedback on the last video (`lab/character-integration/out/final.mp4`)
1. **The character flickers.** Cause unknown.
2. **The character's motions are not synced to the diagrams.** It looks like the first character sample without sound: canned loops (talk, point_right, think) switched at 3-4 cue words per scene, with no relation to what is on screen. The creator wants a **specific script of how the hands, body, head, eyes and mouth move, tied to the narration words, the on-screen text and what the diagram is showing.**
3. Everything else is approved and must stay as is: layouts, placements, backdrop, diagram colours/animations/effects, typography. Only change them if you find a real defect, and list every such change in the report.

Facet is still a placeholder character. Design everything below so a better character can replace it later (see "Rig profile" at the end).

## Part 1 — Flicker: diagnose first, with evidence, then fix
Do NOT guess. Bisect the pipeline and measure at each stage.
Evidence I already have (frame-difference measurement of `lab/character-integration/work/8/char_stage.webm`, decoded with `-c:v libvpx-vp9`): median alpha-channel frame-to-frame difference 0.85, but **5 isolated spike frames** at about frames 280, 440, 789, 921, 1249 (9.3 s, 14.7 s, 26.3 s, 30.7 s, 41.6 s) at 2.5-30x the neighbouring difference, which look like pops (hard switches), plus a constantly non-zero baseline. So the source clip alone already pops. Candidate causes to test (do not assume):
- (a) NLA/action switching: "one-shot that ends early falls back to a `talk` loop", loop restarts with a different phase, 6-frame cross-fades that do not match poses, hard pose resets at action boundaries.
- (b) Eevee render noise between frames at low samples (6 draft / 16 final): soft shadows, light sampling, clearcoat specular on flat facets flipping highlights between frames. Test by rendering 60 frames of a FROZEN pose and measuring frame difference: any non-zero result is render noise. Check Eevee settings (fixed seed, shadow jitter, TAA reprojection, soft-shadow/light-threshold, denoise).
- (c) Facet clearcoat/specular patches near-white on some facets (reported in the character lab): highlights popping on/off as facets rotate a few degrees.
- (d) VP9 alpha encoding (keyframe interval, 4:2:0 chroma, alpha plane quality) causing periodic pulsing. Compare against the lossless PNG sequence.
- (e) Remotion compositing: `OffthreadVideo transparent` extracts frames by timestamp and can duplicate or skip frames or differ in colour from `Html5Video` (the character lab noted this colour difference). Compare Remotion's rendered character region frame by frame against the source clip frames; check frame numbers map 1:1 (same fps, start offset).
- (f) The shadow blob, the crown "secondary motion" bone, or the lagged bones oscillating.
Method: build a small `tools/flicker_check.py` (stdlib + ffmpeg `signalstats`/`tblend` is fine, no numpy installed) that computes per-frame temporal difference over the character bounding region and flags (i) spikes > 2.5x the average of the two neighbours, and (ii) the high-frequency energy of the differences. Run it on: the frozen-pose render, the PNG sequence, the VP9 webm, the Remotion-composited MP4 (character region), and the final MP4. Report where each defect first appears. Fix the root cause(s), then re-run the check and show before/after numbers.
Acceptance: frozen-pose diff ~0; no spike > 2.5x neighbours in the character region of the final composite except at intentional hard moments (list them, e.g. none expected); look at consecutive-frame contact strips around the old spike frames and confirm visually. If Remotion compositing is the cause, consider a frame-exact PNG-sequence/`<Img>` path or `Html5Video` and measure the cost (disk size, render time) honestly. Fix noise by deterministic settings first, more samples only if needed (draft clip time budget: keep draft total under ~10 min).

## Part 2 — Performance script: motion driven by words, text and diagram
Replace "pick a canned action at a few cue words" with a **performance system** made of (A) an authored script and (B) continuous procedural layers, solved per frame into rig poses. No loop restarts, no hard switches: every pose is a blend of layers, so nothing can pop.

### A. The authored script (`storyboard_v3.json`, provided, in `lab/performance/`)
Each scene has a `performance` array of beats. Validate it strictly (unknown keys/gestures/emotions/targets, cue word not found in the narration => clear error before any heavy stage; cue lookup = first match at or after the previous beat's cue, case-insensitive, punctuation/apostrophes normalised; `at` = seconds from scene start; `atEnd` = seconds relative to scene end, negative = before the end). Beat fields: `cue|at|atEnd`, `gesture`, `target`, `emotion`, `intensity` (0..1), optional `hold` seconds, optional `hand` (L|R|auto, auto = the hand on the side of the target, alternating to avoid repeating one arm).
Targets: `viewer` (camera), `self` (the character's chest), `diagram` (diagram centre), `node:<Name>`, `text:<index>` (an `onScreen` line by index), `packet:<index>` (the in-flight packet of this scene; the target MOVES along its path while it flies).
Gesture vocabulary (define each as target-relative hand/arm/head/torso poses; the apex lands on the cue word onset):
`point_at`, `track` (arm and gaze follow a moving packet from launch to arrival), `present` (open-palm sweep toward the diagram), `beat` (small emphasis motion), `beat_repeat` (2-3 rhythmic beats), `nod`, `shake_head`, `shrug`, `lean_in`, `press` (finger "clicks" toward the viewer), `point_viewer`, `point_self`, `scramble` (both hands wiggle), `compare` (hands alternately up/down while looking at the target), `offer` (palm held out with a presented object feel), `hold_palm`, `grip` (hand closes), `open_arms`, `wave`.
Emotions (`friendly, curious, excited, playful, confident, reassuring, serious, thoughtful, satisfied, proud, emphatic, happy`): each is a small set of parameters (eye openness/squint, eye look offset, mouth width/curve bias, head tilt, torso lean, idle speed, gesture amplitude multiplier). They must visibly differ in stills.

### B. Continuous procedural layers (not scripted, always on)
1. **Speech mouth:** amplitude envelope from the narration WAV (existing `lipsync.py`), plus emotion mouth bias; mouth closed in silence, no chatter between words.
2. **Prosody emphasis:** Whisper word timings + energy: stressed words (long duration or loudness peak) trigger a small head nod/torso pulse even where the script has no beat.
3. **Gaze:** eyes + head follow the beat's target; between beats, gaze returns to the viewer at sentence ends and pauses, glances at the diagram when explaining; saccade-like quick eye shifts (not slow glides) with small head follow-through.
4. **Blinks** every 2-5 s (randomised with a fixed seed), also on large gaze shifts.
5. **Idle:** breathing, weight shift, crown/antenna secondary motion with overlap; never frozen.
6. **Anticipation and settle:** every gesture has a lead-in starting 150-250 ms BEFORE the cue so the apex lands on the word onset, a short hold, and an ease-out return. Rules: ease in/out (no linear), never two big gestures within 0.8 s (lower the intensity of the second or merge them), at least one gesture per sentence.

### Aiming at real on-screen targets
Pointing/gaze/track must hit the real position on screen, so the diagram geometry must reach Blender:
- Make the Remotion layout code export (or share one layout function with a Node exporter) a `geometry.json` per aspect: the video-frame pixel rect where the character clip is placed, node centres, `text:<i>` line centres, and packet path positions as a function of time (sampled per frame is fine) for each scene.
- In Blender, convert a target pixel position to a direction from the character (clip-pixel -> camera ray -> aim point on the character's depth plane) and compute shoulder/arm/head/eye rotations analytically (the rig has no IK; rigid parts: aiming a rigid arm toward a point is enough; add bones/extra pivots to the placeholder rig if you need them).
- The layouts differ between 16:9 and 9:16, so pointing directions differ: **render a character clip per aspect** (flag `--aspects`; the draft run defaults to 16:9 only, final renders both). Report the cost.
- Remember `track`: the target moves; sample the packet position per frame.

### Authoring a clip
Single pipeline stage `performance` (replaces/extends the `character` stage; runner allowlist stays id-only; heavy stages still never run concurrently): `storyboard_v3.json` + aligned word times + narration WAV + `geometry.json` => per-frame parameter curves (`performance_<aspect>.json`) => Blender poses every frame (keyframe every frame) => alpha clip => composited by Remotion. Keep `timeline.json` support only if trivially cheap; otherwise drop it.

### Fast iteration (so tuning does not cost 9 minutes)
Provide `tools/preview_performance` that renders **only the character** for one scene at tiny cost (e.g. 480 px, 4 samples, optionally every 3rd frame) AND a stills strip taken exactly at each beat's apex frame, with the on-screen target marked (draw a cross at the target pixel on the composite), so the creator can see the hand/gaze hits the node. Use it during your own tuning (iterate at least 3 times and look at the images).

## Verification (all numeric where possible)
1. Flicker: before/after table (frozen-pose diff, spike count, region energy) for every pipeline stage; root cause stated with evidence.
2. Timing: for each beat, apex frame vs cue-word onset frame (max/mean error in ms; target <= 1-2 frames) from the rendered clip (detect via measurable pose change, e.g. hand position extrema) and from `performance_<aspect>.json`.
3. Aim accuracy: for every `point_at`/`track` beat, angle/pixel error between the hand/gaze direction and the target at the apex (and mid-flight for `track`), reported per beat; target <= ~60 px at 1080p width. Include the marked stills strip.
4. Gesture density: count of beats per second per scene, number of overlapping/too-close gestures (must be 0 after the 0.8 s rule).
5. No regression: re-render stills of all scenes, diff the NON-character regions against the approved video's stills (backdrop, diagrams, typography, captions); they must be unchanged except where you list a fix.
6. Run end-to-end through n8n (draft), then a final render; per-stage times and memory table; draft total <= ~10 min including the performance stage, final as overnight. Loudness: raise the two-pass target so the final lands at -14.0 +/- 0.2 LUFS (it was -14.5).
7. Deliver `out/final.mp4`, `out/final_vertical.mp4`, `out/draft_*`, plus the beat-apex stills strips and the sync/aim reports. State clearly what you could not verify (you cannot hear audio or watch motion in real time).

## Rig profile (so the character can be swapped later)
Document in `performance/RIG_PROFILE.md` the minimal contract a new character `.blend` must satisfy for the performance system: required controls (head aim, eye aim, two arms with reachable hand target, torso lean/twist, mouth open + width, eye openness, optional brows/crown secondary bones), the units/axes the solver drives, the camera object name, and how the solver maps the gesture vocabulary onto them. All Facet-specific numbers (bone names, limb lengths, joint limits, gesture amplitudes) live in one `rig_profile_facet.json`, not scattered in code.

## Do NOT
No publishing, no new character design, no changes to diagram visuals/layouts/colours, no AI-generated imagery, no paid anything, no leftover background processes (say which are still running).

## Report must include
Verdict; flicker root cause + before/after; the performance schema and gesture/emotion tables as implemented; timing and aim numbers; regression results; timings/memory; remaining flaws (honest); what the creator should judge by eye (which files, which seconds); next steps.
