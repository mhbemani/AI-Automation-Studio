import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { font } from "./Video";

export type TypoScene = { type: "typography"; durationSec: number; lines: { text: string; at: number }[] };

// kinetic reveal: each line pops in word by word; the previous line dims when the next arrives
export const Typo: React.FC<TypoScene> = ({ lines }) => {
  const f = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const U = Math.min(width, height) / 1080;
  return (
    <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 40%, #1e293b, #0f172a 70%)", fontFamily: font, color: "white", justifyContent: "center", alignItems: "center", padding: `0 ${90 * U}px`, paddingBottom: 140 * U }}>
      {lines.map((l, k) => {
        const nextAt = lines[k + 1]?.at ?? 1e9;
        const dim = interpolate(f / fps, [nextAt, nextAt + 0.5], [1, 0.35], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        const big = k === 0;
        return (
          <div key={k} style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", gap: `0 ${22 * U}px`, margin: `${18 * U}px 0`, opacity: dim, fontSize: (big ? 130 : 96) * U, fontWeight: 800, lineHeight: 1.12, textAlign: "center", color: big ? "white" : "#38bdf8" }}>
            {l.text.split(" ").map((w, i) => {
              const s = spring({ frame: f - (l.at + i * 0.12) * fps, fps, config: { damping: 13 } });
              return <span key={i} style={{ display: "inline-block", opacity: Math.min(1, s * 2), transform: `translateY(${(1 - s) * 50 * U}px) scale(${0.85 + 0.15 * s})` }}>{w}</span>;
            })}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
