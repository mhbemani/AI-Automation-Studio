# Lab result: character ("Facet", low-poly gem presenter + Blender stage)

**1. Verdict:** Works with caveats. A 340-triangle flat-shaded gem character with a rigid-part rig, 9 actions, a 3-point stage, amplitude lip sync and a CLI that turns `timeline.json` + a narration WAV into a VP9-alpha `.webm`. A 12 s clip renders in 2m47s (720p) and 6m20s (1080p) on an M2/8 GB. Visual polish is decent, not final (flaws in section 5). I cannot hear audio, so lip sync was judged from stills only.

Note: the harness blocked writes into the base checkout (`lab/...`), so everything lives in this session's worktree (`<worktree>/lab/character/`, report here in `lab/results/character.md`). The SPEC was copied in. Nothing was edited in other labs.

**2. Commands** (Blender 4.5.3 at `/Applications/Blender.app`, ffmpeg from Homebrew)
```bash
B=/Applications/Blender.app/Contents/MacOS/Blender; cd lab/character
./build.sh                                   # rebuilds facet.blend from scratch (~2 s): build_character.py + build_stage.py
python3 lipsync.py narration.wav mouth.json  # optional; render_clip.py also does this itself when given --audio
$B -b facet.blend -P render_clip.py -- --timeline timeline_12s.json --out out/clip \
   --preset draft|final --camera full|half|corner [--aspect 16:9|9:16|1:1] [--audio narration.wav | --mouth mouth.json] \
   [--keep-frames] [--png-only] [--mux-audio]
# stills for checking: $B -b facet.blend -P stills.py -- out/dir talk@0.5 point_right@0.6:half talk@0:half:0.6   (action@sec:camera:mouth:aspect)
python3 sheet.py sheet.png 0b1020 3 560 a.png b.png ...   # contact sheet dev tool (needs PIL)
```
Test narration: `lab/integration/work/3/narration.wav` (Kokoro, 48 kHz mono). Output is `out/clip.webm` (VP9 `yuva420p`, no audio unless `--mux-audio`); frames deleted unless `--keep-frames`; `--png-only` stops after the RGBA PNG sequence. A bad timeline fails before any render: `ERROR: events[0]: unknown action 'dance'. Valid actions: celebrate, enter, exit, idle, point_left, point_right, talk, think, wave` (exit code 2). Also checked: fps must be 30, `t` ascending and `< duration`.

Timeline semantics: an event's action runs until the next event; loops repeat; a one-shot that ends early falls back to a `talk` loop (`exit` holds its last pose); 6-frame cross-fade between actions via NLA (one track per event). Each action is a Blender Action with every channel keyed every frame (needed so NLA blends do not pop).

**3. Output** (`lab/character/`)
- `facet.blend` 280 KB (no external deps), scripts + docs ~38 KB total.
- Style: `STYLE.md` (palette, shape language, proportions, materials, light recipe). Palette: aqua `#2EC4B6`, indigo `#5B5BD6`, coral `#FF6B6B`, amber accent `#FFC93C`, eyes `#141C5C`/`#E8FAFF`.
- Contact sheets (`sheets/`): `actions_navy.png`, `actions_light.png` (9 actions at key pose), `cameras_mouth.png` (full/half/corner + mouth 0.14/0.6/1.0), `timeline_sheet.png` (12 frames of the 12 s clip), `alpha_composite_zoom.png` (navy vs white), `remotion_offthread.png`, `remotion_html5.png`.
- Clips (git-ignored `out/`): `draft_full.webm` 1280x720 2.4 MB, `final_full.webm` 1920x1080 3.3 MB, both 12 s.
- Character: 19 meshes, 342 triangles, 4 materials (crystal, body, accent, eye), colour only via a per-facet colour attribute (value-jittered). 13 bones: root, torso, head, crown (lagged secondary motion), eye_L/R (blink), mouth (scale), arm_L/R, hand_L/R, leg_L/R. Rigid bone-parenting, no weights.
- Actions (30 fps): idle 2 s loop, talk 2 s loop, point_left/right 1.2 s, wave 2 s, celebrate 1.5 s, think 2.4 s loop, enter 1 s, exit 1 s. Eyes shift toward the pointing side / up during think.

**4. Measurements** (Apple M2, 8 GB; `/usr/bin/time -l`; 12 s = 360 frames, 12-event timeline with narration lip sync)
| preset | res / samples | render | encode | total wall | peak RSS | peak footprint | webm |
|---|---|---|---|---|---|---|---|
| draft | 1280x720 / 16 | 160 s | 7 s | 2m48s | 504 MB | 1.42 GB | 2.4 MB |
| final | 1920x1080 / 32 | 367 s | 12 s | 6m20s | 854 MB | 1.60 GB | 3.3 MB |
Both within the targets (<3 min, <10 min); draft is close to the limit. (One run was slower while another Blender job overlapped; do not run two at once.) Stills take 0.5-3 s.
- **Alpha:** `ffprobe` shows `alpha_mode=1`. Decoding with `-c:v libvpx-vp9` (ffmpeg's native vp9 decoder drops alpha) gives corner pixel RGBA = (0,0,0,0), body pixel alpha 255. Composited over `#0b1020` and `#ffffff` and zoomed: no dark or light halo or fringing seen; edges are slightly soft on white (4:2:0 chroma), crown tips look a bit hot but not clipped.
- **Remotion** (cloned `lab/integration/remotion/node_modules`, tiny test project `remotion-test/`, still at frame 165): both `<OffthreadVideo transparent>` and `<Html5Video>` of the alpha webm render with transparency intact over a navy panel. OffthreadVideo colours look a little darker/duller than Html5Video. (The character appears cropped at the right edge in the test: my wrapper's `left: 960` offset a 1920-wide video, a test layout bug, not a failure.) I rendered stills only, not a full video.
- Lip sync (`lipsync.py`, stdlib only, ffmpeg fallback for non 16-bit WAV): 26 s of narration -> 791 values, mean open 0.44, 8 blinks, 9 head nods on peaks. From stills at mouth = 0.14 / 0.6 / 1.0 the mouth reads clearly as closed slit / open / wide open. I could not hear audio or watch motion, so how convincing it looks in sync is **unverified**. It is amplitude only: no visemes.

**5. Problems, flaws and caveats**
- No real shadow catcher in Eevee Next (the object flag makes the ground visible). Substitute: a procedural soft dark blob parented to the root bone. It does not shrink or shift when the character hops, and it is faint on dark backgrounds.
- Highlights: head/hand facets and the central crown spike still get near-white specular patches on some frames (clear-coat reflecting key/rim). Reduced, not removed.
- Eyes sit on a slanted lower-head facet and look slightly side-on; mouth is on a downward-facing facet, so it reads best at half/full framing. Mouth/eyes have no emotion beyond squint (celebrate), blink and glance.
- Arm/hand gaps are intentional but the wave arm overlaps the head, and the think hand sits at the cheek rather than a clear chin pose. Hands are single gems: "pointing" reads by arm direction only.
- Squash/stretch is minimal (celebrate only). No foot IK: feet slide during enter/exit.
- Corner preset (1:1) was widened after the last still; not re-rendered after that tweak. Portrait 9:16 still rendered once (`talk_0.5_full__9x16`), not inspected for arm-raise clipping.
- Frames were checked from stills and contact sheets, not by watching the webm in motion.
- `facet.blend1` backup is git-ignored. Blender is GPL; output is free to use. No downloads, add-ons, accounts or textures.

**6. Recommendation**
- Adopt Facet as the recurring presenter: the rebuild-from-script workflow made iterating cheap (still in ~3 s) and the CLI contract is ready for the integration phase. Use `draft` for review, `final` for release; render the character clip once per video and composite as VP9 alpha.
- Next: (1) call `render_clip.py` from `runner.mjs` with timeline events derived from storyboard cues (point_left/right on diagram side), then composite with Html5Video/OffthreadVideo in Remotion and watch a full clip in motion; (2) fix remaining visuals (specular clipping, hop-aware shadow, better think/wave poses, a few more expressions via eye/mouth shapes); (3) if time per video matters, drop final samples to 24 or render at 30 fps only the frames the camera sees; (4) add a `--lipsync-only` quick preview and keyword-anchored cues.
