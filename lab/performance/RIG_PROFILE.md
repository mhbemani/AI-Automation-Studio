# Rig profile: what a replacement character must provide

The performance system (`character/solver.py` + `character/render_performance.py`) knows the character only through (1) a `.blend` that satisfies the contract below and (2) one JSON, `rig_profile_facet.json`. No bone name, limb length, joint limit or gesture amplitude is hard-coded in the code. To swap Facet for a better character: build the new `.blend`, copy `rig_profile_facet.json` to `rig_profile_<name>.json`, adjust the numbers, point `performance.mjs` / `character.json` at them (env `CHARACTER_BLEND`; profile path in `stages/performance.mjs`).

## Conventions
- Blender units, **Z up, the character faces -Y**, screen-right = +X (the camera sits at azimuth 24 deg towards +X, see `character.json` -> `camera`).
- The solver outputs, per bone and per video frame, **world-aligned** values relative to the parent bone: rotation as a quaternion (w,x,y,z), location (x,y,z), scale (x,y,z). `rigpose.py` converts them to bone-local with the bone's rest basis (`M^-1 * q * M`), so the rig does not need any particular bone roll. All bones that are driven must be at rest in a pose where their rest basis is what you want "zero rotation" to mean (T-less hanging arms, head looking -Y).
- The camera object is `STAGE_camera` (framing from `character.json`, clip is square 1:1, 50 mm / 36 mm sensor). The solver re-creates that camera mathematically (`Cam` in `solver.py`) to aim at pixels; if you change lens/sensor edit `geometry.camera` in the profile. The FK of the solver was checked against the evaluated Blender rig: fingertip positions agree within 3 px at 1080p.
- Frames are keyed on **every** frame (no NLA, no actions switching): `render_performance.py` keyframes each channel at every frame.

## Required controls (Facet bone names in brackets)
| control | what the solver drives | notes |
|---|---|---|
| root `[root]` | location (x,y,z) hop/lean-in, scale (squash for breathing) | legs counter-translate in x,y so feet stay planted |
| torso `[torso]` | rotation: lean (+x = forward), twist (z), roll (y); pivot `geometry.torsoPivot` | children: head, arms |
| head aim `[head]` | rotation yaw (z), pitch (x, + = look down), roll (y); pivot `geometry.headPivot` | `viewer.headYaw`: yaw that makes the character face the camera at rest (22 deg for the 24 deg camera) |
| eye aim `[eye_L, eye_R]` | location (x right, z up) in the head frame, +-`limits.eyeShift`; scale z = openness (blink, squint); rotation about y = squint arch | eyes are surface facets, so gaze is mostly the head, the eyes make the quick saccade |
| arms `[arm_L, arm_R]` | rotation swinging the whole arm about the shoulder (`geometry.shoulder`, length `armLen`); location z = shoulder rise (shrug) | rest direction is straight down (0,0,-1) |
| hands `[hand_L, hand_R]` | rotation relative to the arm about the wrist (length `handLen`); scale = fist | **reachable hand target**: the hand TIP (bone tail) is what is aimed; two rigid links, no IK in the rig, `solver.ik2` is a closed-form 2-link IK |
| mouth `[mouth_L, mouth_R]` (parent `mouth`, which stays at identity) | scale z = open, scale x = width, rotation about y = smile curve (+-`mouth.smileTilt` deg, opposite sign per half) | two half-shapes meeting at the centre; a single-shape mouth needs a blend-shape or a second control for the smile |
| brows `[brow_L, brow_R]` (optional) | location z = raise, rotation about y = tilt (inner end up = worried) | |
| crown / antenna `[crown]` (optional) | rotation, driven by a 2nd-order spring on the head motion (overlap / follow-through) | any secondary bone can be added to `spring` |
| legs `[leg_L, leg_R]` | location only (keeps the feet planted when the root moves) | |

## How the gesture vocabulary maps onto the controls
Gestures are data in `rig_profile_facet.json` -> `gestures`: keyframe tables `[tau, value]` relative to the cue-word onset (the **apex**, tau = 0), `"H"` = hold end. Parts: `arms.M|O|B` (main hand chosen from the target side / alternation / busy hand, other hand, both), `head`, `torso`, `root`, `shoulder`, `face`.
- Arm modes: `aim` (straight arm, direction solved so that the **finger ray hits the target pixel**; `phi` = how far the arm reaches toward the camera), `pose` (spherical `[theta from hanging down, psi 0 outward / 90 forward]`), `ik` (hand tip at a point in the torso frame).
- Targets are pixels in the video frame: `viewer`, `self` (chest), `diagram`, `node:<Name>`, `text:<i>`, `packet:<i>` (moving, sampled per frame) from `geometry.json`, which `stages/geometry.mjs` exports from the SAME layout functions Remotion uses (`remotion/src/layout.ts`).
- Always-on layers (not scripted): speech mouth from the narration amplitude, prosody nods, gaze (saccade eyes, slower head, back to the viewer at sentence ends and pauses), blinks, idle breathing / weight shift / head drift, crown and hand follow-through springs.
- Emotions (`emotions`): 12 parameter sets (eye openness, squint, eye-look offset, smile, mouth width, brow raise/tilt, head roll/pitch, torso lean, idle speed, gesture amplitude).

## A new character must satisfy
1. Bone names (or edit `bones` + `rigpose.py` lookup) and rest orientation as above; armature object name `armature` in the profile; camera object `STAGE_camera`.
2. Numbers to measure for the new model and put in the profile: `geometry` (shoulder position, `armLen`, `handLen`, torso/head pivots, `eyeMid`, `chest`, rest arm/hand angles), `limits`, `mouth`, `emotions` amplitudes, and re-tune gesture key values if the proportions differ (arms shorter = smaller `phi`).
3. Run `character/render_performance.py` on a 10-frame check, then `tools/verify_performance.py` (aim miss in px and timing from the evaluated rig) and `tools/preview_performance` (stills strip with target crosses) before trusting it.
