# Lab report: remotion

**Verdict:** Works. A JSON-driven "Browser → API → Database → response" scene renders headless to 1080p MP4 (and 9:16) in ~16 s per 15 s video on an M2. Minor layout caveat below.

## What I did
```bash
cd lab/remotion
npm i remotion @remotion/cli react react-dom typescript @types/react   # remotion 4.0.533, react 19.3, node v26
npm run render            # → out/flow-16x9.mp4  (comp "Flow", 1920x1080)
npm run render:vertical   # → out/flow-9x16.mp4  (comp "FlowVertical", 1080x1920)
# stills for checking: npx remotion still src/index.ts Flow out/x.png --frame=165 --props=scenes/request-flow.json
```
Files (5 source files, no framework):
- `scenes/request-flow.json`: the whole scene: `title`, `durationSec`, colours, `nodes[]` (label/sub/at/color), `edges[]` (from/to/at), `packets[]` (edge, label, at, dur, reverse, color), `captions[]` (text/at/dur). All times in seconds.
- `src/Flow.tsx`: the one reusable component. Springs nodes in, draws edges, moves packets with eased interpolation, fades captions. Auto-lays out nodes in a row (landscape) or column (portrait) from the canvas aspect, and scales everything by `min(w,h)/1080`.
- `src/Root.tsx`: two `<Composition>`s sharing the component. `calculateMetadata` sets the frame count from `durationSec`, so the JSON controls the video length.
- `src/index.ts`, `package.json`, `tsconfig.json` (`tsc` passes).

Swap the JSON with `--props=scenes/other.json`. No code edits are needed to change elements, labels, timing or length.

## Output
- `lab/remotion/out/flow-16x9.mp4`: 1920x1080, 30 fps, 15.0 s, h264, 822 kB
- `lab/remotion/out/flow-9x16.mp4`: 1080x1920, 30 fps, 15.0 s, h264, 830 kB
- Check stills: `out/still-h.png`, `still-h2.png`, `still-v.png`, `still-v2.png`. I looked at the stills and the layout is correct in both aspects. I did not watch the MP4s in motion.

## Measurements
- Machine: Apple M2, 8 GB RAM (8589934592 B), macOS (Darwin 25.6), node v26.0.0.
- First render: 140 s wall, 32 s user CPU, peak RSS ~758 MB. This includes the one-time Chrome Headless Shell download and the first bundle, so don't count it as render cost.
- Warm renders: 15.5 s (16:9) and 16.6 s (9:16) wall, about 1:1 realtime (450 frames). CPU was 160–190% (default concurrency).
- Output is ~0.8 MB per 15 s for flat vector-style content.

## Problems & caveats
- **Licence:** Remotion is free for individuals (personal or commercial), teams of up to 3 people, and non-profits. A Company License is required from 4 people. Checked via context7 against LICENSE.md and the licence FAQ. We qualify at $0. Re-check if the studio ever has 4+ people or contractors, because headcount is aggregated across everyone who operates the codebase. The docs also name tiers "Remotion for Creators" and "Remotion for Automators" for the paid Company License. They state that automation (n8n triggering renders) is the Automators tier, but only for companies that need a paid licence. That is a licence-text point to confirm with Remotion if the studio grows.
- The first render downloads Chrome Headless Shell (size not measured). It is cached afterwards. `npm` also warned that esbuild's postinstall is not allow-listed, but renders worked anyway.
- **Layout bug (minor, not fixed):** packet labels are in the SVG layer under the node boxes, so a label can be clipped by a node when the packet is near it (visible at frame 165 and in the portrait still). A fix is to move the packets into a layer above the nodes, or to offset labels further from the line.
- Long titles wrap in portrait (fine) but a very long caption could overflow; there is no auto-fit text.
- Fonts are system-ui only. A custom font would need `@remotion/google-fonts` or a bundled file, and I have not tested that.
- Layout is limited to an evenly spaced linear chain. Branching or fan-out diagrams would need explicit `x,y` per node.

## Recommendation
- Adopt Remotion for the deterministic scene layer. It is cheap, fast (~realtime) and the JSON contract works as intended.
- **Claude writing scene JSONs from a storyboard:** easy. The schema is flat, with seconds-based times and string ids. Claude can map "A asks B, B asks C, data returns" to nodes, edges and packets, and set `at` from narration timestamps. The risks are timing and overlap errors, which are cheap to catch by rendering stills at a few frames. A JSON-schema or zod validation step before render would catch typos in edge indices and ids (not built).
- **Primitives needed next, in priority order:**
  1. A typography scene: kinetic title or bullet reveal, big-number or stat, and quote.
  2. A transition between scenes, e.g. `@remotion/transitions` fade or slide, plus a `<Series>` wrapper so one project JSON lists multiple scenes.
  3. An audio track: `<Audio>` with narration from TTS. Scene `at` times should then be derived from word or sentence timestamps.
  4. Branching layouts (explicit coordinates), a node icon set (SVG), a code or terminal snippet scene, and a caption/subtitle track from a transcript.
  5. Fix the label z-order.
- **Next experiment:** a 2–3 scene video built from a single project JSON (typography intro → flow scene → outro) with a Kokoro or Piper narration track and transitions. Time the full pipeline, with n8n triggering `npx remotion render --props`.
