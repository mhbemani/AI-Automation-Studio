import React from "react";
import { AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { loadFont } from "@remotion/google-fonts/Inter";
import { Typo, TypoScene } from "./Typo";
import { Flow, FlowScene } from "./Flow";
import { Backdrop } from "./Backdrop";
import { CharacterCfg, CharacterOverlay } from "./Character";
import { C, geo } from "./theme";

export const font = `${loadFont("normal", { weights: ["600", "700", "800"], subsets: ["latin"] }).fontFamily}, system-ui, sans-serif`;

type Cap = { at: number; scene: number; words: { w: string; at: number }[] };
export type Mark = { frame: number; x: number; y: number; color?: string; kind?: "cross" | "dot" };
export type Project = { debug?: { marks: Mark[] }; fps: number; transitionSec: number; durationSec: number; character: CharacterCfg; scenes: (TypoScene | FlowScene)[]; captions: Cap[]; audio?: string };

// styled captions from word timings (not burned by FFmpeg): current phrase, current word highlighted. Only in diagram scenes, inside the layout's caption rect.
const Captions: React.FC<{ caps: Cap[]; scenes: Project["scenes"] }> = ({ caps, scenes }) => {
  const { width, height, fps } = useVideoConfig();
  const t = useCurrentFrame() / fps;
  const U = Math.min(width, height) / 1080;
  const i = caps.findLastIndex((c) => c.at - 0.05 <= t);
  if (i < 0) return null;
  const c = caps[i], sc = scenes[c.scene];
  if (sc.type === "typography") return null;
  const end = caps[i + 1]?.at ?? c.words[c.words.length - 1].at + 1.5;
  if (t > end + 0.4) return null;
  const r = geo(sc.layout, width, height).caption;
  return (
    <div style={{ position: "absolute", left: r.x, top: r.y, width: r.w, height: r.h, display: "flex", justifyContent: "center", alignItems: "center" }}>
      <div style={{ fontFamily: font, fontWeight: 800, fontSize: 50 * U, color: "white", background: "rgba(11,16,32,0.8)", border: `${2 * U}px solid ${C.panel2}`, borderRadius: 22 * U, padding: `${12 * U}px ${30 * U}px`, textAlign: "center", maxWidth: "100%", boxSizing: "border-box" }}>
        {c.words.map((w, k) => <span key={k} style={{ color: t >= w.at ? C.amber : C.ink, opacity: t >= w.at ? 1 : 0.7 }}>{w.w}{k < c.words.length - 1 ? " " : ""}</span>)}
      </div>
    </div>
  );
};

// preview tooling only (project.debug is absent in real renders): crosses at the on-screen targets, dots at the measured fingertips
const DebugMarks: React.FC<{ marks?: Mark[] }> = ({ marks }) => {
  const f = useCurrentFrame(), { width, height } = useVideoConfig();
  const ms = (marks || []).filter((m) => m.frame === f);
  if (!ms.length) return null;
  return <svg width={width} height={height} style={{ position: "absolute", left: 0, top: 0 }}>{ms.map((m, i) => m.kind === "dot"
    ? <circle key={i} cx={m.x} cy={m.y} r={9} fill={m.color || "#ff00ff"} stroke="#000" strokeWidth={2} />
    : <g key={i} stroke={m.color || "#ffffff"} strokeWidth={4}><line x1={m.x - 28} y1={m.y} x2={m.x + 28} y2={m.y} /><line x1={m.x} y1={m.y - 28} x2={m.x} y2={m.y + 28} /><circle cx={m.x} cy={m.y} r={18} fill="none" /></g>)}</svg>;
};

export const Video: React.FC<Project> = ({ scenes, captions, transitionSec, fps, audio, character, debug }) => {
  const { width, height } = useVideoConfig();
  const geos = scenes.map((s) => geo(s.layout, width, height));
  return (
    <AbsoluteFill>
      <Backdrop />
      <TransitionSeries>
        {scenes.flatMap((s, i) => [
          ...(i ? [<TransitionSeries.Transition key={`t${i}`} presentation={fade()} timing={linearTiming({ durationInFrames: Math.round(transitionSec * fps) })} />] : []),
          <TransitionSeries.Sequence key={`s${i}`} durationInFrames={Math.round(s.durationSec * fps)}>
            {s.type === "flow" ? <Flow {...s} rect={geos[i].diagram!} /> : <Typo {...s} rect={geos[i].text!} />}
          </TransitionSeries.Sequence>,
        ])}
      </TransitionSeries>
      <CharacterOverlay cfg={character} geos={geos} starts={scenes.map((s) => s.startSec)} T={transitionSec} />
      <Captions caps={captions} scenes={scenes} />
      <DebugMarks marks={debug?.marks} />
      {audio && <Audio src={staticFile(audio)} />}
    </AbsoluteFill>
  );
};
