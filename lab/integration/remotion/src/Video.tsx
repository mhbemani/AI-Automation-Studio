import React from "react";
import { AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { loadFont } from "@remotion/google-fonts/Inter";
import { Typo, TypoScene } from "./Typo";
import { Flow, FlowScene } from "./Flow";

export const font = `${loadFont("normal", { weights: ["600", "800"], subsets: ["latin"] }).fontFamily}, system-ui, sans-serif`;

type Cap = { at: number; words: { w: string; at: number }[] };
export type Project = { fps: number; transitionSec: number; durationSec: number; scenes: (TypoScene | FlowScene)[]; captions: Cap[]; audio?: string };

// styled captions from word timings (not burned by FFmpeg): current phrase, current word highlighted
const Captions: React.FC<{ caps: Cap[] }> = ({ caps }) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const { width, height } = useVideoConfig();
  const U = Math.min(width, height) / 1080, vertical = height > width;
  const i = caps.findLastIndex((c) => c.at - 0.05 <= t);
  if (i < 0) return null;
  const c = caps[i], end = caps[i + 1]?.at ?? c.words[c.words.length - 1].at + 1.5;
  if (t > end + 0.4) return null;
  return (
    <div style={{ position: "absolute", left: 0, right: 0, bottom: (vertical ? 260 : 90) * U, display: "flex", justifyContent: "center", padding: `0 ${80 * U}px` }}>
      <div style={{ fontFamily: font, fontWeight: 800, fontSize: 58 * U, color: "white", background: "rgba(15,23,42,0.82)", borderRadius: 22 * U, padding: `${14 * U}px ${34 * U}px`, textAlign: "center", maxWidth: "100%", boxSizing: "border-box", whiteSpace: "pre-wrap" }}>
        {c.words.map((w, k) => <span key={k} style={{ color: t >= w.at ? "#fbbf24" : "white", opacity: t >= w.at ? 1 : 0.75 }}>{w.w}{k < c.words.length - 1 ? " " : ""}</span>)}
      </div>
    </div>
  );
};

export const Video: React.FC<Project> = ({ scenes, captions, transitionSec, fps, audio }) => (
  <AbsoluteFill style={{ background: "#0f172a" }}>
    <TransitionSeries>
      {scenes.flatMap((s, i) => [
        ...(i ? [<TransitionSeries.Transition key={`t${i}`} presentation={fade()} timing={linearTiming({ durationInFrames: Math.round(transitionSec * fps) })} />] : []),
        <TransitionSeries.Sequence key={`s${i}`} durationInFrames={Math.round(s.durationSec * fps)}>
          {s.type === "flow" ? <Flow {...s} /> : <Typo {...s} />}
        </TransitionSeries.Sequence>,
      ])}
    </TransitionSeries>
    <Captions caps={captions} />
    {audio && <Audio src={staticFile(audio)} />}
  </AbsoluteFill>
);
