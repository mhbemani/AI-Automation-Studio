import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import { font } from "./Video";

export type FlowScene = {
  type: "flow"; durationSec: number;
  nodes: { id: string; label: string; at: number; color: string }[];
  edges: { from: string; to: string; at: number }[];
  packets: { edge: number; label: string; at: number; dur: number; color: string; reverse?: boolean }[];
};

export const Flow: React.FC<FlowScene> = (s) => {
  const f = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = f / fps;
  const vertical = height > width;
  const U = Math.min(width, height) / 1080;
  const box = { w: 300 * U, h: 150 * U };
  const pos = (i: number) => {
    const n = s.nodes.length;
    return vertical
      ? { x: width / 2, y: height * 0.2 + ((height * 0.5) / (n - 1)) * i }
      : { x: width * 0.15 + ((width * 0.7) / (n - 1)) * i, y: height * 0.42 };
  };
  const P = Object.fromEntries(s.nodes.map((n, i) => [n.id, pos(i)]));
  const pop = (at: number) => spring({ frame: f - at * fps, fps, config: { damping: 14 } });
  const seg = (e: FlowScene["edges"][number]) => {
    const a = P[e.from], b = P[e.to];
    const gx = vertical ? 0 : box.w / 2 + 12 * U, gy = vertical ? box.h / 2 + 12 * U : 0;
    return { x1: a.x + gx, y1: a.y + gy, x2: b.x - gx, y2: b.y - gy };
  };
  const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

  return (
    <AbsoluteFill style={{ background: "#0f172a", fontFamily: font, color: "white" }}>
      <svg width={width} height={height} style={{ position: "absolute" }}>
        {s.edges.map((e, i) => {
          const g = seg(e); const p = interpolate(t, [e.at, e.at + 0.6], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
          return <line key={i} x1={g.x1} y1={g.y1} x2={g.x1 + (g.x2 - g.x1) * p} y2={g.y1 + (g.y2 - g.y1) * p} stroke="#475569" strokeWidth={8 * U} strokeLinecap="round" strokeDasharray={`${18 * U} ${14 * U}`} />;
        })}
      </svg>
      {s.nodes.map((n) => {
        const sc = pop(n.at), { x, y } = P[n.id];
        return <div key={n.id} style={{ position: "absolute", left: x - box.w / 2, top: y - box.h / 2, width: box.w, height: box.h, boxSizing: "border-box",
          transform: `scale(${sc})`, opacity: Math.min(1, sc * 2), background: "#1e293b", border: `${5 * U}px solid ${n.color}`, borderRadius: 28 * U,
          display: "flex", alignItems: "center", justifyContent: "center", boxShadow: `0 0 ${50 * U}px ${n.color}55` }}>
          <div style={{ fontSize: 46 * U, fontWeight: 800 }}>{n.label}</div>
        </div>;
      })}
      {/* packets last = on top of nodes */}
      <svg width={width} height={height} style={{ position: "absolute" }}>
        {s.packets.map((k, i) => {
          if (t < k.at || t > k.at + k.dur) return null;
          const g = seg(s.edges[k.edge]);
          const raw = interpolate(t, [k.at, k.at + k.dur], [0, 1], { easing: Easing.inOut(Easing.cubic) });
          const p = k.reverse ? 1 - raw : raw;
          const x = g.x1 + (g.x2 - g.x1) * p, y = g.y1 + (g.y2 - g.y1) * p;
          const w = (k.label.length * 17 + 44) * U, h = 52 * U;
          // keep label inside the frame
          const lx = Math.min(width - w - 20 * U, Math.max(20 * U, vertical ? x + 40 * U : x - w / 2)), ly = vertical ? y - h / 2 : y - 90 * U;
          return <g key={i}>
            <circle cx={x} cy={y} r={26 * U} fill={k.color} />
            <circle cx={x} cy={y} r={44 * U} fill={k.color} opacity={0.25} />
            <rect x={lx} y={ly} width={w} height={h} rx={12 * U} fill="#1e293b" stroke={k.color} strokeWidth={3 * U} />
            <text x={lx + w / 2} y={ly + h / 2 + 10 * U} textAnchor="middle" fontSize={28 * U} fontWeight={600} fill="white" fontFamily={font}>{k.label}</text>
          </g>;
        })}
      </svg>
    </AbsoluteFill>
  );
};
