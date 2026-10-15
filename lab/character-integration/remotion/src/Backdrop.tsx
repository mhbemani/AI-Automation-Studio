import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { C, rng } from "./theme";

// Continuous stage behind every scene: drifting glows, slowly turning low-poly shards and twinkling dust, so no frame is static.
const shardColors = [C.aqua, C.indigo, C.coral, C.amber];
export const Backdrop: React.FC = () => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const { width: W, height: H } = useVideoConfig();
  const U = Math.min(W, H) / 1080;
  const r = rng(7);
  const shards = Array.from({ length: 16 }, (_, i) => ({ x: r() * W, y: r() * H, s: (70 + r() * 170) * U, a: r() * 360, v: (r() - 0.5) * 8, ph: r() * 6.28, c: shardColors[i % 4], o: 0.05 + r() * 0.07 }));
  const dust = Array.from({ length: 46 }, () => ({ x: r() * W, y: r() * H, s: (2 + r() * 3.5) * U, ph: r() * 6.28, sp: 0.6 + r() * 1.4 }));
  return (
    <AbsoluteFill style={{ background: C.bg }}>
      <AbsoluteFill style={{ background: `radial-gradient(circle at ${30 + 8 * Math.sin(t * 0.25)}% ${28 + 6 * Math.cos(t * 0.2)}%, #1a2456 0%, transparent 55%), radial-gradient(circle at ${72 + 7 * Math.cos(t * 0.22)}% ${75 + 5 * Math.sin(t * 0.3)}%, #2a1f5c 0%, transparent 50%)` }} />
      <svg width={W} height={H} style={{ position: "absolute" }}>
        {shards.map((s, i) => {
          const x = s.x + Math.sin(t * 0.3 + s.ph) * 40 * U, y = s.y + Math.cos(t * 0.25 + s.ph) * 30 * U, a = s.a + t * s.v, k = s.s;
          return <polygon key={i} points={`0,${-k} ${k * 0.9},${k * 0.6} ${-k * 0.8},${k * 0.7}`} transform={`translate(${x} ${y}) rotate(${a})`} fill={s.c} opacity={s.o} />;
        })}
        {dust.map((d, i) => <circle key={i} cx={d.x + Math.sin(t * 0.4 + d.ph) * 12 * U} cy={d.y - ((t * 14 * d.sp * U) % H) + (d.y - ((t * 14 * d.sp * U) % H) < 0 ? H : 0)} r={d.s} fill={C.ink} opacity={0.1 + 0.18 * (0.5 + 0.5 * Math.sin(t * d.sp * 1.5 + d.ph))} />)}
      </svg>
    </AbsoluteFill>
  );
};
