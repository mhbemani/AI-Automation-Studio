import React from "react";
import { Easing, Html5Video, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Geo, Place } from "./theme";

export type CharacterCfg = { file: string; framing: { charHeight: number; feetY: number; centerX: number } };

// One continuous clip for the whole video (same fps, starts at frame 0 => in sync with the narration). Only its on-screen position changes per layout.
export const CharacterOverlay: React.FC<{ cfg: CharacterCfg; geos: Geo[]; starts: number[]; T: number }> = ({ cfg, geos, starts, T }) => {
  const { fps, width, height } = useVideoConfig();
  const t = useCurrentFrame() / fps;
  let k = 0; starts.forEach((s, i) => { if (s <= t) k = i; });
  const a = geos[Math.max(0, k - 1)].char, b = geos[k].char;
  const p = k === 0 ? 1 : interpolate(t, [starts[k], starts[k] + T], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  const m = (x: number, y: number) => x + (y - x) * p;
  const pl: Place = { cx: m(a.cx, b.cx), feet: m(a.feet, b.feet), charH: m(a.charH, b.charH) };
  const S = pl.charH / cfg.framing.charHeight; // side of the square clip on screen
  const left = pl.cx - S * cfg.framing.centerX, top = pl.feet - S * cfg.framing.feetY;
  const U = Math.min(width, height) / 1080;
  return (
    <>
      <div style={{ position: "absolute", left: pl.cx - pl.charH * 0.42, top: pl.feet - pl.charH * 0.03, width: pl.charH * 0.84, height: pl.charH * 0.1, borderRadius: "50%", background: "radial-gradient(closest-side, rgba(46,196,182,0.28), transparent)", filter: `blur(${4 * U}px)` }} />
      <Html5Video src={staticFile(cfg.file)} muted style={{ position: "absolute", left, top, width: S, height: S }} />
    </>
  );
};
