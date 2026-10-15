# Lab result: blender

**1. Verdict:** Works with caveats. Headless `blender -b -P` builds, animates and renders a 5 s 1080p30 scene to MP4 and to alpha. Character *appearance* is slow to get right by script.

**2. What I did** (Blender 4.5.3 LTS was already at `/Applications/Blender.app`; nothing downloaded)
```
B=/Applications/Blender.app/Contents/MacOS/Blender
cd lab/blender
$B -b -P mascot.py -- mp4      # -> out/mascot.mp4 (Eevee, FFmpeg H.264)
$B -b -P mascot.py -- alpha    # -> out/alpha/f_0001..0150.png (RGBA, film_transparent)
ffmpeg -framerate 30 -i out/alpha/f_%04d.png -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 2M out/alpha.webm
```
Optional 3rd arg limits last frame (`-- mp4 3` for a quick test). `mascot.py` builds a blue egg-body robot (head, glowing eyes, ears, antenna, arms, belly), floor, sun + area light, camera. It animates a bounce, a head turn and a right-arm wave over 150 frames.

**3. Output** (`lab/blender/out/`)
- `mascot.mp4`: 1920x1080, 30 fps, 5.0 s, 150 frames, 0.67 MB.
- `alpha.webm`: VP9 with alpha, 1.3 MB. I did not test it in Remotion.
- The PNG sequence was 150 frames, 109 MB. I deleted it to save space; rerun the alpha command to regenerate it.
- The alpha channel is real (corner pixel RGBA = 0,0,0,0). I checked a PNG frame only, not the webm decode.
- I looked at one MP4 frame (t=2.5 s). It reads as a clean flat-shaded 3D mascot.

**4. Measurements**
- Machine: Apple M2, 8 GB RAM, macOS (Darwin 25.6). ffmpeg from Homebrew.
- Eevee (`BLENDER_EEVEE_NEXT`) at 32 samples: MP4 render 106 s wall for 150 frames (~0.7 s/frame, Metal GPU). Alpha PNG render 126 s.
- Blender memory peak was about 110 MB.
- Startup and scene build take about 10 s.
- A 3-frame test MP4 took 11 s wall.

**5. Problems & caveats**
- **Iteration is the real cost.** The first render was a broken close-up. The camera was too tight, and nested parenting under a scaled body distorted the child offsets. The default AgX view transform washed the colours out. Emissive eyes blew out to white.
- I fixed some of this: camera, parenting, view transform to Standard, lower emission and light energy. The final frame still has detached arms (the pivot and cylinder offsets are wrong), a floor that is overexposed near the camera, and eyes that protrude from the head. The mascot is usable as a tech proof, not as a polished brand character.
- Each tweak means a re-render (~1 s/frame) or a low-res test frame. Cheap preview: `-- mp4 3` and a lower resolution.
- Primitives only. `primitive_capsule_add` does not exist in 4.5, so the arms are plain cylinders. `hasattr(bpy.ops.mesh, ...)` returns True even for missing operators.
- MP4 has no alpha. For compositing in Remotion use the PNG sequence (large) or VP9 alpha webm (small; Chrome and Remotion should play it). ProRes 4444 `.mov` also worked in ffmpeg (134 MB for 5 s), but is heavy and Remotion's use of it is unverified.
- Licence: Blender is GPL, and rendered output is free to use. Python scripting needs no add-ons.
- **Rigify/Mixamo assessment (not built):** For simple bounce, head-turn and wave, hierarchy plus keyframes from script is enough. Walking, talking or expressive acting needs a real rig. Rigify (bundled, free) gives a rig, but it works on a modelled mesh and needs manual weight painting, so it is a GUI-assisted step. Mixamo (free Adobe account needed, so check the $0 and no-sign-up rule) auto-rigs and supplies mocap for humanoids only, and the licence terms matter. A non-humanoid mascot gets little from Mixamo. For lip-sync use shape keys (mouth open/close) driven by audio amplitude from script.
- Housekeeping: while checking for stray renders I ran `pkill` on Blender and killed an idle GUI Blender process (not mine). If the user had Blender open, it was closed.

**6. Recommendation**
- Use Blender only for a recurring 3D mascot or hero shots. For explainer visuals Remotion is faster to iterate on. Keep one parametrised `mascot.py` and render short alpha clips (1-5 s) at 540p or 720p for drafts and 1080p for finals.
- Composite as VP9-alpha webm or PNG sequence in Remotion.
- Next experiment: model the mascot once in the Blender GUI (or import a free CC0 glTF), save a `.blend`, and drive only the animation by script (`-b mascot.blend -P anim.py`). Then test the alpha webm inside Remotion (`<OffthreadVideo>` vs PNG sequence) and measure a 720p draft render.
