# realistic-car-scene: a second, more realistic setup of the car scene

## 1. Verdict

**Works, with caveats.** A game-style "realistic-leaning" version of the scene is set up, lit and camera-ready:
- a downtown ring road;
- a yellow coupe with an interior I built;
- the human (Oscar) beside Claude;
- a chat-app phone screen;
- 5 cameras with 9:16 variants;
- golden-hour lighting;
- a voiced 71.8 s timeline.

It renders at 1.1–2.3 s per draft frame and 2.8–5.2 s at 1080p, but total memory including GPU buffers peaks at 3.5–4.2 GB, above the 2.5 GB target. The stylised `drive_car.py` runs unchanged. `animate.py` runs after small adaptations, and its walk and seated-human sections need real rework.

## 2. What I did

Built live with the creator in Blender 4.5.3 through the bridge. Branch `<task branch>`, 15 commits.

**Creator decisions** (`lab/scene-realistic-car/SCENE_NOTES.md` has the full list):
- **Look:** "like a game", not photoreal.
- **Assets:** a hybrid policy. The creator lifted the BlenderKit ban for the human (Oscar) and the car (Vulcar Hachura coupe, yellow); everything else is CC0 or built by script.
- **Street:** 13 m wide (parking, lane, lane, parking).
- **Light:** golden-hour look A.
- **Seating: the human sits in the front passenger seat**, a big change from the brief's back-right seat. It fits the 2-door car, puts both faces directly on camera and removes the rear-view mirror problem.
- **Voices:** local Kokoro; ElevenLabs was dropped because its free plan is non-commercial.

**Rebuild:**
- `scripts/fetch_assets.py` gets the CC0 assets (88.8 MB); `ASSETS.md` explains the two BlenderKit files.
- Run the build scripts in order: `import_assets` → `build_city` → `build_car` → `build_characters` → `build_phone` → `drive_car` → `build_cameras` → `build_lighting`, through `bridge/bl.py file`.
- Audio: `production/run.sh` (Kokoro + Whisper → `timeline.json` + envelopes + mix; all checks pass).

## 3. Output

- `lab/scene-realistic-car/scene.blend` (84 MB, not in git, relative paths). Copied to the base checkout `lab/scene-realistic-car/scene.blend`.
- Stills (in git, 2.8 MB): `stills/FINAL_*` (1080p, one per camera), `DRAFT_9frames_lap`, `CAMS_16x9`, `CAMS_9x16`, `LAP_claude_pov_10`, `CONTRACT_animate_sheet`, `PHONE_ui_states`, plus city, car and character sheets.
- Audio (not in git): `production/out/audio_mix.wav` (71.8 s, voices plus generated ambience) and `production/samples/*.wav` (7 voice candidates).

## 4. Measurements

Apple M2, 8 GB. Headless Eevee renders, warm-up frame discarded, GUI Blender open at the same time.

| | Draft 960×540, 16 samples | Final 1920×1080, 32 samples |
|---|---|---|
| Interior shots | 1.77–2.22 s (stylised: 1.76–2.0) | 5.0–5.2 s (stylised: 7.3–8.0 s, with 2 shadow rays) |
| `CAM_EST_Street` | 2.25 s | 4.82 s |
| `CAM_PHONE_CU` | 1.12 s | 2.81 s |
| Blender RSS peak | 1.26 GB | 1.91 GB |
| Total footprint peak, incl. GPU | **3.8 GB** | **4.2 GB** |

- **Memory.** The stylised scene peaked at 1.65–1.94 GB total. What I tried at 1080p:
  - render subdivision capped at 1, plus 1K textures: 3.5 GB;
  - a smaller shadow pool: no real gain;
  - hiding the parked cars: no gain.

  The main driver is not identified.
- **Scale and timing:**
  - Scene: about 1,000 objects. The city draws about 1.05M instanced triangles; the hero car about 205k with smoothing.
  - Audio build: about 1 minute for 14 lines. The Kokoro environment takes 209 MB.

## 5. Problems and caveats

**Licences:**
- Two **BlenderKit Royalty Free** assets (Oscar by Rex Mun, Vulcar Hachura by m awais). They are usable in videos but not redistributable, and the credits are recorded. They required the creator's BlenderKit login and add-on, which go against the brief's original rule; the creator decided this.
- The Vulcar file was saved by Blender 5.0, so it opens with a warning.
- Kokoro is Apache-2.0. Its training data includes some synthetic audio from commercial TTS: a small risk about where the data came from, not a licence restriction.
- The chat screen imitates the Claude app (no real logos). Claude's look resembles Anthropic's mascot, the same caveat as the stylised scene.

**Not verified:**
- I **can't hear audio**: the creator picked the voices by ear.
- I didn't watch anything in motion; all judgements come from stills.
- The seated human's head-turn and tilt signs after the bone mapping are unchecked.
- Oscar's face rig (expressions) is untested.

**Visual flaws:**
- dark streaks on a seat back;
- beige, foggy side windows from inside;
- Oscar's eyes look flat; a loose phone grip with an open left hand at the door;
- Claude's grip arms can point at the camera like a beak;
- bare corner plazas;
- some props more photo-real than the rest.

**Process:**
- The BlenderKit add-on's own import step stalled twice, so the files were copied from its download cache.
- A Blender restart happened mid-session; nothing was lost.

## 6. Honest comparison with the stylised scene

**Better:**
- The city reads as a real place: real street proportions, materials with texture, crosswalks and signals, trees, parked cars, a skyline.
- The car is a believable, attractive vehicle with an interior.
- Faces: the human has a real, expressive animated-film face, and Claude reads clearly in 3/4 view at 25% of the frame instead of a 100 px mirror reflection.
- The opening human is **155 px instead of about 50 px** tall.
- The phone shows a real chat flow.
- The voices are natural lines with real timing.
- The 1080p render is *faster* than the stylised final.

**Worse or riskier:**
- Memory: about 4 GB total vs about 1.9 GB.
- Licences: two Royalty Free assets and a login on the creator's side, instead of all-CC0.
- The back-seat/mirror story beat is gone (by choice).
- More moving parts: the BlenderKit add-on, Rigify posing, a 209 MB Python environment.
- `animate.py` needs a real walk and a Rigify face/pose pass.
- Mixed fidelity: cartoon Oscar, photo-real Poly Haven props, a glossy realistic car.

**Cost:** about one long interactive session. $0 spent.

## 7. Recommendation

Use this scene for the next animation and render step:
1. Animate with Rigify: walk to the curb, get into the front door, face expressions driven by the envelopes, glances from `dialogue_v2.json`.
2. Rewrite `verify_animation.py` for timeline v2.
3. Before any long render:
   - close the GUI;
   - decide on the memory cap (subdivision 1 plus 1K textures) after a side-by-side still comparison;
   - render a 10 s 1080p excerpt and have the creator watch it with sound.

Next experiment worth running: find the memory driver by switching the Eevee features (ray tracing, shadows) off one at a time.
