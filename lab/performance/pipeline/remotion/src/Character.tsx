import React from "react";
import { Html5Video, Img, OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Geo } from "./theme";
import { charPlace, clipRect } from "./layout";

export type CharacterCfg = { file: string; mode?: "video" | "offthread" | "frames"; dir?: string; dirs?: { "16:9": string; "9:16": string }; frames?: number; framing: { charHeight: number; feetY: number; centerX: number } };

// One continuous clip for the whole video (same fps, starts at frame 0 => in sync with the narration). Only its on-screen position changes per layout.
export const CharacterOverlay: React.FC<{ cfg: CharacterCfg; geos: Geo[]; starts: number[]; T: number }> = ({ cfg, geos, starts, T }) => {
  const { fps, width, height } = useVideoConfig();
  const frame = useCurrentFrame(), t = frame / fps, dir = cfg.dirs ? (width > height ? cfg.dirs["16:9"] : cfg.dirs["9:16"]) : cfg.dir;
  const pl = charPlace(t, geos, starts, T);
  const { left, top, S } = clipRect(pl, cfg.framing);
  const U = Math.min(width, height) / 1080;
  return (
    <>
      <div style={{ position: "absolute", left: pl.cx - pl.charH * 0.42, top: pl.feet - pl.charH * 0.03, width: pl.charH * 0.84, height: pl.charH * 0.1, borderRadius: "50%", background: "radial-gradient(closest-side, rgba(46,196,182,0.28), transparent)", filter: `blur(${4 * U}px)` }} />
      {cfg.mode === "frames" ? <Img src={staticFile(`${dir}/f_${String(Math.min(frame, (cfg.frames ?? 1e9) - 1) + 1).padStart(4, "0")}.png`)} style={{ position: "absolute", left, top, width: S, height: S }} />
        : cfg.mode === "offthread" ? <OffthreadVideo src={staticFile(cfg.file)} muted transparent style={{ position: "absolute", left, top, width: S, height: S }} />
        : <Html5Video src={staticFile(cfg.file)} muted style={{ position: "absolute", left, top, width: S, height: S }} />}
    </>
  );
};
