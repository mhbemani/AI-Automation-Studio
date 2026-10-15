import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { font } from "./Video";
import { C, Rect } from "./theme";
import { lineFont } from "./layout";

export type TypoScene = { type: "typography"; layout: string; startSec: number; durationSec: number; lines: { text: string; at: number }[] };

// kinetic reveal inside its own rect (vertically centred there); no captions in this layout (the text is the caption)
export const Typo: React.FC<TypoScene & { rect: Rect }> = ({ lines, rect, durationSec }) => {
  const f = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = f / fps, U = Math.min(width, height) / 1080;
  const float = Math.sin(t * 0.9) * 6 * U;
  return (
    <AbsoluteFill style={{ fontFamily: font, color: C.ink }}>
      <div style={{ position: "absolute", left: rect.x, top: rect.y + float, width: rect.w, height: rect.h, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", gap: 26 * U }}>
        <div style={{ position: "absolute", width: rect.w * 0.8, height: rect.h * 0.8, borderRadius: "50%", background: `radial-gradient(closest-side, ${C.indigo}${t % 3 > 1.5 ? "40" : "33"}, transparent)`, opacity: 0.7 + 0.3 * Math.sin(t * 1.3), zIndex: -1 }} />
        {lines.map((l, k) => {
          const nextAt = lines[k + 1]?.at ?? 1e9;
          const dim = interpolate(t, [nextAt, nextAt + 0.5], [1, 0.45], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const first = k === 0, { fs, rows } = lineFont(l.text, first, rect.w, U);
          const bar = interpolate(t, [l.at + 0.2, l.at + 0.9], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          return (
            <div key={k} style={{ display: "flex", flexDirection: "column", alignItems: "center", opacity: dim }}>
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", fontSize: fs, fontWeight: 800, lineHeight: 1.1, textAlign: "center", color: first ? C.ink : C.amber }}>
                {rows.map((row, r) => <div key={r} style={{ display: "flex", justifyContent: "center", gap: `0 ${fs * 0.26}px` }}>{row.map((w, i) => {
                  const wi = rows.slice(0, r).reduce((a, x) => a + x.length, 0) + i, s = spring({ frame: f - (l.at + wi * 0.1) * fps, fps, config: { damping: 13 } });
                  return <span key={i} style={{ display: "inline-block", opacity: Math.min(1, s * 2), transform: `translateY(${(1 - s) * 50 * U}px) scale(${0.85 + 0.15 * s})` }}>{w}</span>;
                })}</div>)}
              </div>
              <div style={{ marginTop: 10 * U, height: 8 * U, width: `${bar * 46}%`, borderRadius: 4 * U, background: first ? C.aqua : C.coral, opacity: 0.9 }} />
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
