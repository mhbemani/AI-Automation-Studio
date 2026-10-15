import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";

export type Scene = {
  title: string; durationSec: number; bg: string; accent: string;
  nodes: { id: string; label: string; sub?: string; at: number; color: string }[];
  edges: { from: string; to: string; at: number }[];
  packets: { edge: number; label: string; at: number; dur: number; color: string; reverse?: boolean }[];
  captions: { text: string; at: number; dur: number }[];
};

const font = "system-ui, -apple-system, 'Helvetica Neue', sans-serif";

export const Flow: React.FC<Scene> = (s) => {
  const f = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = f / fps;
  const vertical = height > width;
  const U = Math.min(width, height) / 1080; // scale unit
  const box = { w: 300 * U, h: 150 * U };
  // evenly space nodes along the main axis (row landscape, column portrait)
  const pos = (i: number) => {
    const n = s.nodes.length;
    return vertical
      ? { x: width / 2, y: height * 0.22 + ((height * 0.52) / (n - 1)) * i }
      : { x: width * 0.15 + ((width * 0.7) / (n - 1)) * i, y: height * 0.48 };
  };
  const P = Object.fromEntries(s.nodes.map((n, i) => [n.id, pos(i)]));
  const pop = (at: number) => spring({ frame: f - at * fps, fps, config: { damping: 14 } });
  const fade = (at: number, dur = 0.5) => interpolate(t, [at, at + dur], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // edge endpoints stop at box borders
  const seg = (e: Scene["edges"][number]) => {
    const a = P[e.from], b = P[e.to];
    const gx = vertical ? 0 : box.w / 2 + 12 * U, gy = vertical ? box.h / 2 + 12 * U : 0;
    return { x1: a.x + gx, y1: a.y + gy, x2: b.x - gx, y2: b.y - gy };
  };

  return (
    <AbsoluteFill style={{ background: s.bg, fontFamily: font, color: "white" }}>
      <div style={{ position: "absolute", top: 70 * U, width: "100%", textAlign: "center", fontSize: 62 * U, fontWeight: 800, padding: `0 ${60 * U}px`, boxSizing: "border-box",
        opacity: fade(0.1), transform: `translateY(${(1 - fade(0.1)) * -30}px)` }}>{s.title}</div>

      <svg width={width} height={height} style={{ position: "absolute" }}>
        {s.edges.map((e, i) => {
          const g = seg(e); const p = interpolate(t, [e.at, e.at + 0.6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
          return <line key={i} x1={g.x1} y1={g.y1} x2={g.x1 + (g.x2 - g.x1) * p} y2={g.y1 + (g.y2 - g.y1) * p} stroke="#475569" strokeWidth={8 * U} strokeLinecap="round" strokeDasharray={`${18 * U} ${14 * U}`} />;
        })}
        {s.packets.map((k, i) => {
          if (t < k.at || t > k.at + k.dur) return null;
          const g = seg(s.edges[k.edge]);
          const raw = interpolate(t, [k.at, k.at + k.dur], [0, 1], { easing: Easing.inOut(Easing.cubic) });
          const p = k.reverse ? 1 - raw : raw;
          const x = g.x1 + (g.x2 - g.x1) * p, y = g.y1 + (g.y2 - g.y1) * p;
          const w = (k.label.length * 17 + 44) * U, h = 52 * U;
          // label sits beside the packet, offset perpendicular to travel
          const lx = vertical ? x + 40 * U : x - w / 2, ly = vertical ? y - h / 2 : y - 90 * U;
          return <g key={i}>
            <circle cx={x} cy={y} r={26 * U} fill={k.color} />
            <circle cx={x} cy={y} r={44 * U} fill={k.color} opacity={0.25} />
            <rect x={lx} y={ly} width={w} height={h} rx={12 * U} fill="#1e293b" stroke={k.color} strokeWidth={3 * U} />
            <text x={lx + w / 2} y={ly + h / 2 + 10 * U} textAnchor="middle" fontSize={28 * U} fontWeight={600} fill="white" fontFamily={font}>{k.label}</text>
          </g>;
        })}
      </svg>

      {s.nodes.map((n, i) => {
        const sc = pop(n.at), { x, y } = P[n.id];
        return <div key={n.id} style={{ position: "absolute", left: x - box.w / 2, top: y - box.h / 2, width: box.w, height: box.h, boxSizing: "border-box",
          transform: `scale(${sc})`, opacity: Math.min(1, sc * 2), background: "#1e293b", border: `${5 * U}px solid ${n.color}`, borderRadius: 28 * U,
          display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", boxShadow: `0 0 ${50 * U}px ${n.color}55` }}>
          <div style={{ fontSize: 46 * U, fontWeight: 800 }}>{n.label}</div>
          {n.sub && <div style={{ fontSize: 28 * U, color: "#94a3b8", marginTop: 6 * U }}>{n.sub}</div>}
        </div>;
      })}

      {s.captions.map((c, i) => {
        const o = Math.min(fade(c.at, 0.4), 1 - fade(c.at + c.dur - 0.4, 0.4));
        return <div key={i} style={{ position: "absolute", bottom: (vertical ? 190 : 110) * U, width: "100%", textAlign: "center", fontSize: 54 * U, fontWeight: 700,
          color: s.accent, opacity: o, transform: `translateY(${(1 - o) * 24}px)` }}>{c.text}</div>;
      })}
    </AbsoluteFill>
  );
};
