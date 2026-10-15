# Lab: character — low-poly 3D presenter + Blender stage (asset phase)

Read first: `lab/BRIEF.md`, `lab/results/blender.md`, `lab/results/remotion.md`, `lab/results/integration.md`.
Follow BRIEF constraints ($0, minimal, ask before big downloads/installs, never edit other labs; COPY what you need).
Work in `lab/character/`. Final report: `lab/results/character.md` (BRIEF output contract).
Blender is at `/Applications/Blender.app/Contents/MacOS/Blender` (4.5.3). Do NOT `pkill` Blender or any process you did not start.
Machine: Apple M2, 8 GB RAM. Everything must render comfortably on it. Run heavy things one at a time.

## Goal
Produce a reusable, good-looking **3D presenter character** plus a **stage/lighting setup**, and a CLI that renders short **transparent-background clips** of the character performing named actions, with mouth movement driven by a narration WAV. The clips will later be composited next to Remotion diagrams (next phase, not yours).

## Art direction: faceted "low-poly gem" style
- The user wants hard edges, stone/crystal/jewel-like facets, NOT smooth subdivided surfaces (those are too heavy for this Mac). Think low-poly, gem-cut, flat-shaded.
- Flat shading (no smooth shading, no subdivision modifier, no bevel-heavy meshes). Total character <= ~2,000 triangles.
- Material: a small set (<= 4) of Principled BSDF materials, strong colour per facet group, slight specular/clearcoat so facets catch light like cut stones, low roughness on "crystal" parts, matte on "body". A very subtle emissive on eyes only. Avoid textures/images: colour and geometry only (fast, reproducible).
- Palette: pick ONE coherent palette (3-4 main colours + 1 accent) that reads well on both dark navy (#0b1020) and light backgrounds. Record hex codes in `lab/character/STYLE.md` along with the shape language and proportions so later characters/props match.
- Appeal: friendly, curious teacher. Slightly large head, simple readable silhouette, clear eyes. No uncanny realism. Original design (no copyrighted characters).

## Character design (build it exactly like this, you may refine details)
Name: **"Facet"**. A small gem-bodied creature.
- **Rigid-part rig, no skinning/weight painting.** Each body part is a separate rigid low-poly mesh parented to an armature bone (or bone-constraint). Parts: head (faceted gem, slightly tilted-cut shape), torso (elongated faceted crystal), two arms (upper arm + hand as separate faceted pieces so shoulders can float slightly, Rayman-style gaps are fine and stylistically intended), two short legs/feet OR a hovering base if legs look bad, two eyes (flat emissive facets), a mouth object, optional small crystal "antenna" or crown with secondary motion.
- Armature: simple, named bones (root, torso, head, arm_L/R, hand_L/R, leg_L/R if used), IK not required. Add a **blink** (eyes scale-Y to ~0.1), a **mouth** that opens/closes via scale or a shape key, and an optional secondary-motion bone for the crown/antenna (simple delayed rotation).
- Save the finished asset as `lab/character/facet.blend` (packed, no external deps, committed to git: keep it small, < 5 MB).

## Stage and lighting ("proper setup")
- Build with a script `build_stage.py` + `build_character.py` (idempotent: running them rebuilds from scratch).
- Camera: 1080x1920-safe framing AND 1080x1080 framing configs; render the character with a 35-50 mm equivalent lens, slight three-quarter angle, character occupying ~70% of frame height. Make camera presets: `full`, `half` (waist-up), `corner` (small, for picture-in-picture bottom-left/right).
- Lighting: 3-point setup (soft key area light, cool fill, strong coloured rim/back light) + a very low world light. Shadow catcher ground plane so the character has a soft contact shadow on a TRANSPARENT background. No visible floor. Tune so facets show clearly different brightness (that is what sells the low-poly look).
- Render engine: Eevee (BLENDER_EEVEE_NEXT), 16-32 samples, Standard view transform (AgX washes colours out, we already saw this), film_transparent ON, RGBA PNG. Keep draft (720p) and final (1080p) presets. Measure frame times for both.
- Verify by rendering test stills and LOOKING at them (read the PNGs). Iterate until: arms attached/readable, nothing clipping, eyes not protruding or blown out, no overexposed regions, facets clearly visible. Do not stop at the first render. Describe the visual flaws honestly in the report.

## Animation library (all as Blender Actions on the armature, 30 fps, loopable where noted)
1. `idle` (loop, 2 s): breathing bob, slow head sway, blinks.
2. `talk` (loop, 2 s): subtle body bounce, small hand gestures, head nods. Mouth is NOT keyed here, it is driven separately (below).
3. `point_left` / `point_right` (one-shot, ~1.2 s): arm points toward the screen side where a diagram will be, head looks that way, returns to talk pose.
4. `wave` (one-shot, ~2 s) and `celebrate` (one-shot, ~1.5 s).
5. `think` (one-shot or loop): hand near head, head tilt, eyes look up.
6. `enter` and `exit` (one-shot, ~1 s): slide/hop in from the side and out.
Keep poses readable and exaggerated slightly (squash/stretch via scale is OK on rigid parts). Provide NLA or a simple script API to chain actions on a timeline.

## Narration-driven mouth (lip sync, minimal version)
- Script `lipsync.py` (plain Python, no heavy deps): reads a mono WAV, computes a smoothed amplitude envelope at 30 fps (RMS, attack/release smoothing, threshold), outputs `mouth.json` = per-frame mouth-open values 0..1.
- Blender script applies these as keyframes on the mouth (scale or shape key), plus occasional blinks and slight head nod on emphasised peaks.
- No viseme/phoneme lip sync required; amplitude-driven is enough. State in the report how convincing it looks (from stills at several mouth values; you cannot hear audio, say so).

## CLI contract (this is what the next phase calls)
`render_character.py` / a shell wrapper such that:
`blender -b lab/character/facet.blend -P render_clip.py -- --timeline timeline.json --out out/<name> --preset draft|final --camera full|half|corner [--audio narration.wav]`
- `timeline.json` example: `{"fps":30,"duration":12.0,"events":[{"t":0,"action":"enter"},{"t":1,"action":"talk"},{"t":5.2,"action":"point_right"},{"t":8,"action":"talk"},{"t":11,"action":"exit"}]}`
- Output: PNG sequence (RGBA) then encode a **VP9 alpha .webm** (`libvpx-vp9 -pix_fmt yuva420p`) with FFmpeg, and ALSO keep an option to emit a PNG sequence. Delete intermediate PNGs after encode unless `--keep-frames`.
- Validate the timeline JSON up front (unknown action names must fail with a clear message listing valid actions).
- Test with a 12 s timeline using a real narration WAV (copy one from `lab/integration/work/` or `lab/tts/out/`).

## Checks you must do and report
1. Stills contact sheet of: every action at its key pose, 3 camera presets, 3 mouth values.
2. Render times and peak memory (`/usr/bin/time -l`): draft 720p and final 1080p for a 12 s clip. Target: 12 s draft clip under ~3 min, final under ~10 min. If over, reduce samples/resolution or optimise and report what worked.
3. Alpha check: the webm really has alpha (decode one frame, inspect RGBA corner pixel) AND a quick composite test over a dark navy and a white background with FFmpeg, then LOOK at the frames for halos/fringing.
4. Test the webm inside Remotion if cheap (copy `lab/integration/remotion/` to your folder, add one `<OffthreadVideo transparent>` or PNG-sequence test comp, render one still), and report which method works. If it doesn't work, say exactly what failed.
5. Total .blend and script sizes. No add-ons, no external assets, no downloads beyond what you ask permission for.

## Do NOT
- No smooth/subsurf character, no Cycles, no textures, no add-ons, no Mixamo/accounts, no AI image generation.
- Do not build n8n/runner/Remotion pipeline changes (next phase does that).
- Do not leave background processes running.

## Report must include
Verdict, the exact commands, STYLE.md summary, contact-sheet paths, timings/memory, alpha and Remotion findings, honest list of remaining visual flaws, and recommended next steps.
