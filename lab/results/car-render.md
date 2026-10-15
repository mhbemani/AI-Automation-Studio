# car-render: animation from the timeline + first sample video

## 1. Verdict
**Works.** The whole scene is animated by one re-runnable script from `timeline.json` and the two envelopes, and it rendered end to end: `sample_draft.mp4` (960x540, 24 fps, 1335 frames, 55.625 s, 11.6 MB) with `audio_mix.wav`. The draft render took **49 min wall (46 min of rendering)** on the M2/8 GB, with a flat 0.56 GB RSS and no swap growth. A full 1080p render is estimated at **2.7 h**; I rendered only a 10 s 1080p excerpt (32 min). **I cannot hear audio and did not watch the video in real time**: everything below about picture comes from stills and contact sheets, and nothing says the audio sounds right or is in sync beyond the frame/duration numbers.

## 2. What was built (Blender 4.5.3, branch `<task branch>`)
Rebuild chain after any scene edit: `build_city -> build_car -> build_characters -> build_cameras -> build_lighting -> drive_car -> animate` (`python3 bridge/bl.py file scripts/<x>.py` live, or `blender -b scene.blend -P scripts/<x>.py` headless), then `verify_animation.py`. Save the .blend afterwards.
| script | does |
|---|---|
| `scripts/_anim_util.py` | helpers: ANIM_* actions with slots, one-key-per-frame F-curves, the car distance profile |
| `scripts/drive_car.py` (changed) | Follow Path constraint; **keyed** `eval_time`: car rolls in from 15 m behind (out of the EST frame), decelerates at constant rate to a stop at the curb (frame 253), waits to 277, then speed follows a smoothstep 0 -> 8.5 m/s over 3.5 s, cruise |
| `scripts/animate.py` | markers bound to cameras at the 14 shot starts; mirror aim; wheels (spin = distance/0.54 m, front wheels steer); steering wheel (12:1) and Claude's arms (Track-To grip empties on the rim); street human walk + phone typing; Claude body/eye emotions + speech pulse + blinks + mirror glances; seated human; handheld drift; visibility keys. Fixed seeds. |
| `scripts/verify_animation.py` | 15 numeric checks, output in `stills/verify_animation.txt` (15/15 pass) |
| `scripts/render_sequence.py` | headless renderer, presets, `--range/--shots/--frames/--every/--set`, resume, per-frame CSV (`production/out/frame_times_*.csv`) |
| `scripts/tune_presets.py`, `scripts/measure_shots.py` | the tuning table and per-shot timing below |
| `bridge/snapgrid.py` | contact sheets from the live Blender |
Changes to older scripts: `build_cameras.py` now builds the interior at the first interior frame (the seated human is hidden before it), uses the evaluated pose for his eyes, clears camera animation on rebuild, stores the mirror centre, and frames the phone closer (62% of the old distance); `build_characters.py` puts the street human at (1.5,-7.7) facing 100 deg (his frame-1 state).
Animation details: the human walks from the door (frame 13) to the curb (73) at 1.62 m/s using the shipped Walk action (stride measured at 1.6 m per 24-frame cycle; the lowest foot is kept on the ground per frame), stops at x=4.03, looks up and follows the arriving car with his head. The phone text is typed by 24 text objects (one per prefix) keyed on `hide_render` (12 chars/s from frame 109) and a blue "sent" bubble from frame 163; no add-ons. The mirror is re-aimed **every frame** in HUMAN_POV shots at Claude's animated eyes (constant keys at each cut for CLAUDE_POV shots), otherwise the face left the mirror when Claude leaned.

## 3. Swap contract for placeholders
Keep these names, parents and pivots, then re-run the chain from `build_characters`:
- **Claude** (`CHAR_Claude`, owner "claude"): body origin at the bottom centre on the seat (0.48,-0.1,0.93 car-local, 0.6x0.5x0.8 m); children `_Eye_L/R` (pivot at the eye's bottom, scaled in Z for blinks, tilted about Y), `_Arm_L/R` (pivot at the shoulder, hanging along -Z, they get a Track-To to `CAR_WheelGrip_*`). Body pose is driven by position/rotation/scale of the body object, so a rigged replacement needs one root object with that behaviour, or `animate.py` section 4 must be pointed at its bones.
- **Seated human** `CHAR_Human` + `CHAR_Human_Mesh`, **street human** `CHAR_Human_Street` + `_Mesh`: the Quaternius 48-bone armature (Hips, Spine/Spine1/Spine2, Neck, Head, Left/RightArm, ForeArm, UpLeg, Leg, Foot...) with Euler XYZ poses (seated) and quaternions (street). Bone axes (measured): Head/Neck/Spine X = nod forward, Y = turn left, Z = tilt to his right. A different rig needs those names or an edit of the pose tables. The street human must keep the Walk action's facing (-Y in armature space) and ankle height 0.062 m at rest.
- **Phone**: `PROP_Phone` parented to the street human's `RightHand` bone, screen facing its -Y, `PROP_Phone_Screen`.
- **Car**: `CAR_Exterior` facing local -Y with the Follow Path constraint, wheels `CAR_Wheel_*` with pivots at the wheel centres, axle along local X, radius 0.54 m, wheelbase 2.38 m (constants `WHEEL_R`, `WHEELBASE` in `animate.py`), `CAR_SteeringWheel` (tilt -70 deg about X, spin about its own axis), `CAR_RearViewMirror` and its glass/probe.
- **Cameras** `CAM_*` as before; `CAM_PHONE_CU` is parented to `CHAR_Human_Street` relative to its frame-1 state.

## 4. Animation verification (`stills/verify_animation.txt`, 15/15)
Markers equal the 14 shot starts and cameras exactly; the active camera is correct at the first and last frame of every shot; mirror keys at all 11 interior cuts; car identical at (5,-2) for frames 253-277 and still at 252 (step < 0.01 m); the rear door and the human have the same x (4.03), 2.07 m apart across the curb (the curb gap is by design); max acceleration 3.69 m/s2, max jerk 6.5 m/s3, no negative speed, 8.5 m/s at the end; the car is on the lane polyline (offset 0.00 m) at 7 sample frames with 0.0 m arclength error; 359.8 m driven in 44.1 s (the first corner is at frames ~771-870, seen in `stills/ANIM_corner.jpg`); the seated human is hidden at frame 276 and shown at 277, the street human and phone the other way; typed character count matches the formula at 6 test frames.

## 5. Render tuning (Eevee Next, headless; frames 230 EST, 700 HUMAN_POV, 620 CLAUDE_POV; error = mean abs pixel difference vs a 128-sample, 4-ray, 8-step reference)
Big finding: the old `light_threshold` of 0.05 made the 132 street lamps drop out and the whole picture bluer and darker (error 12 vs reference). **0.005 costs about +7% time** and fixes it. Ray-tracing resolution scale 1 vs 2 changes the mirror content; scale 1 costs nothing here, so both presets use 1. Denoise on matters (turning it off triples the error).
| draft 960x540 | s/frame (EST/HUM/CLA) | error |
|---|---|---|
| 4 samples | 0.88 / 0.60 / 0.58 | 2.6 / 2.2 / 1.8 |
| 8 | 1.34 / 1.04 / 0.97 | 1.8 / 1.4 / 1.2 (slightly grainy) |
| **16 (chosen)** | 2.27 / 1.96 / 1.76 | 1.3 / 0.9 / 0.8 (clean) |
| 24 | 3.20 / 2.85 / 2.53 | 1.1 / 0.7 / 0.7 |
| 32 | 4.12 / 3.76 / 3.30 | 1.0 / 0.5 / 0.6 |
| 16, 2 shadow rays | 2.35 / 2.02 / 1.82 | 0.9 / 0.8 / 0.7 |
| 16, denoise off | 2.19 / 1.85 / 1.67 | 3.3 / 3.1 / 2.5 |
| reference 128 samples | 17.0 / 16.4 / 14.4 | 0 |
| final 1920x1080 | EST / HUM / CLA | error |
|---|---|---|
| 24 | 5.0 / 5.6 / 5.3 | 1.0 / 0.6 / 0.6 |
| 32 | 6.5 / 7.3 / 6.8 | 0.9 / 0.5 / 0.6 |
| 48 | 9.5 / 10.7 / 9.8 | 0.8 / 0.4 / 0.5 |
| 64 | 13.9 / 15.4 / 13.7 | 0.8 / 0.3 / 0.4 |
| **32 + 2 shadow rays, 6 steps (chosen)** | 7.5 / 8.0 / 7.3 | 0.6 / 0.4 / 0.4 |
| reference 128 | 31.2 / 35.4 / 32.7 | 0 |
Quality loss honestly: the draft shows light grain on flat walls at 16 samples and is soft because of 960 px; the mirror face stays crisp in both (`stills/DRAFT_vs_FINAL_mirror_f620.jpg`; the draft there is upscaled to 1080p, which is why it looks softer). I did not compare finals against anything but the reference numbers and my own look at three stills (`stills/FINAL_1080p_f*.jpg`).

## 6. Timing and memory (8 spread frames per shot at draft, 3 per shot at final; warm-up frame discarded)
| shot | camera | frames | draft s/frame (min-max) | final s/frame |
|---|---|---|---|---|
| S01 | EST | 96 | 0.86 (0.83-0.90) | 4.08 |
| S02 | PHONE | 84 | 0.81 (0.80-0.86) | 4.23 |
| S03 | EST | 96 | 2.05 (1.47-2.24) | 6.64 |
| S04 | HUMAN_POV | 53 | 1.93 | 7.89 |
| S05 | CLAUDE_POV | 139 | 1.70 | 6.89 |
| S06 | HUMAN_POV | 131 | 1.87 | 7.68 |
| S07 | CLAUDE_POV | 55 | 1.67 | 6.88 |
| S08 | HUMAN_POV | 161 | 2.07 | 7.59 |
| S09 | CLAUDE_POV | 47 | 1.52 | 6.39 |
| S10 | HUMAN_POV | 174 | 2.35 | 8.93 |
| S11 | CLAUDE_POV | 58 | 1.55 | 6.57 |
| S12 | HUMAN_POV | 94 | 2.52 | 8.88 |
| S13 | CLAUDE_POV | 46 | 1.58 | 6.84 |
| S14 | HUMAN_POV | 101 | 2.70 | 9.58 |
| **estimate for 1335 frames** | | | **41.8 min** (1.88 s mean) | **2.70 h** (7.28 s mean) |
- **Measured full draft render: 2933 s wall since launch (2792 s inside Blender, 2757 s summed frame times = 46 min), 2.07 s/frame mean, 11% above the estimate** (it also includes scene load and PNG writes). Per-200-frame means: 0.90, 2.22, 2.02, 2.16, 2.46, 2.36, 2.48 s. The rise follows the shots (interior HUMAN_POV late in the video is heavier, S14 2.7 s); I cannot separate thermal throttling from that: the M2 stayed in the same range for an hour, so no clear throttling showed, but I did not read temperatures.
- Memory: peak RSS 0.56 GB (flat from the first to the last frame), peak footprint 1.65 GB (draft) and 1.88-1.94 GB (final) including GPU buffers. `vm_stat` before/after: free pages 107.7k -> 104.9k (16 KB pages), pageouts +4.2k, swapouts 29.7k (cumulative on the machine), swap used 239 MB both times: no swap growth. Blender alone used about 100% of one CPU core plus GPU (Metal) time; I did not sample GPU utilisation.
- Disk: draft PNG 0.54 MB/frame, 718 MB for 1335 frames; the 1080p PNG 1.97 MB/frame (472 MB for 240 frames), about 2.6 GB for a full final sequence. `sample_draft.mp4` 11.6 MB; the 10 s 1080p excerpt 6.9 MB.
- 1080p excerpt (frames 440-679, covers the cuts at 469 and 600): 1932 s wall, 8.02 s/frame mean (7.0 for the first 40, 8.6 for the last 40).

## 7. Output
- `lab/scene-lowpoly-car/production/out/sample_draft.mp4`: H.264 yuv420p CRF 18, AAC 192k, faststart. ffprobe (`ffprobe_sample_draft.txt`): 55.625 s video and audio, 1335 frames, 24 fps. Loudness of the video's audio -13.9 LUFS = the source `audio_mix.wav`.
- `production/out/sample_final_excerpt_1080p.mp4`: frames 440-679, audio 18.33-28.33 s of the mix. Three final stills `stills/FINAL_1080p_f230/f620/f700.jpg`.
- Both MP4s and the final `scene.blend` (33 MB, not committed) are also copied to the base checkout `lab/scene-lowpoly-car/` (`scene.blend`, `production/out/`); the previous base `scene.blend` is `backups/scene_before_car_render.blend` there.
- Stills in git: `stills/ANIM_*.jpg` (14-shot sheet, emotions sheet, corner, intro, phone), `DRAFT_contact_sheet.jpg`, `DRAFT_cut_f330.jpg`, `DRAFT_cut_f1037.jpg`, `DRAFT_vs_FINAL_mirror_f620.jpg`. The two cut strips (3 consecutive frames) show clean hard cuts with the correct camera and a face in the mirror on both sides.

## 8. Cost options for the final render (not implemented)
Estimated for 1335 frames at 7.3 s: 2.7 h.
- Render the EST/PHONE shots (S01, S02: 180 frames at 4.1 s) at lower samples and the static EST camera frames once: saves little (about 5 min).
- Drop to 24 samples (5.3 s/frame): 2.0 h, error 1.0 vs 0.6.
- **Render the final at 12 fps and let FFmpeg duplicate frames** only for S02 (phone) and the static EST shots: the typing is 2-frame steps anyway; saves about 10 min.
- Render only the shots that changed after edits (`--shots`, resume skips existing frames): the biggest practical saving while iterating.
- Cut the mirror cost: the planar probe is the only extra pass; interior shots are 1.7-2.7 s vs 0.85 s for the PHONE shot at draft, i.e. roughly 1 s of that is probe + interior lights.
- Metal GPU is already used; headless without the GUI saved about 1.2 GB (no measurement of the GUI-on case, since the creator closed it first), so keep the GUI closed for long renders.

## 9. Visual flaws I see (critical)
- **The human's face is a static texture**: no mouth, no expression change; reactions are head/body only and subtle (about 5 deg). His speech reads weakly.
- **Claude's face is visible only in the 100 px mirror** in HUMAN_POV; the eyes are blocks, so emotions read mainly from the body tilt. On the emotion sheet happy/proud/amused squints are similar to each other; curious and excited push the eyes to the mirror edge. The body gain (1.8x) is already cartoonish at the extremes (roll up to -14 deg). Claude's `surprised` was only checked in the preview sheet; the timeline never uses it for Claude.
- Eye "curves" are tilted squashed boxes, not curved shapes.
- Foot sliding while the human walks (stride from the clip vs. constant root speed; ramps help), and the walk is only about 50 px tall in the EST frame: his stop at the curb is hard to see. The seated hands rest in the air above the thighs (not checked from any camera: neither interior camera sees them).
- Claude's arms may not reach the wheel exactly while it turns (Track-To rotates but cannot stretch); not visible in the sampled stills.
- The orange car shell shows as large bars in every HUMAN_POV frame, the front-passenger headrest fills the bottom, and the white rear window in the mirror is blown out.
- Repetitive: the human's listening nod is the same shape at every Claude line; blink timing is random but the same pattern every render.
- The PHONE shot: the hand is large and blocky and the background is a flat wall/sidewalk blur. The sent-bubble blue looked pale in the viewport; in the render it is fine.
- Not checked: flicker of lights/shadows between consecutive frames beyond 3-frame strips at two cuts; the corner shot frame by frame (4 stills only).

## 10. What I could not verify
Audio quality and lip/gesture timing against the sound; real-time playback of the MP4; temperatures; GPU utilisation numbers; that the creator's Blender window state matches (it was closed by the creator before Part 2, and I did not reopen it); the 9:16 variant with the new animation.

## 11. Recommendations
1. Watch the draft with sound and note any pacing problem before spending 2.7 h on the final.
2. Render finals per shot (`--shots`) as they are approved; keep 32 samples + 2 shadow rays.
3. Improve readability: give Claude a visible face in HUMAN_POV (move the camera a little toward the mirror line or enlarge the mirror) and give the human a second face texture (smile / surprise) swapped at his emotion keys.
4. Replace the human's seated hands pose and add a door-closing/entering beat at the cut.
5. Cut render cost by lowering the planar probe cost (probe only needed in interior shots; already so) and by caching nothing else: the draft is already about 0.8x real-time on this machine (46 min for 56 s).
