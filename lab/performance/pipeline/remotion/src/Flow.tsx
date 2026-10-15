import React from "react";
import { AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { font } from "./Video";
import { C, Rect } from "./theme";
import { edgeSeg, flowLayout, packetXY } from "./layout";

export type FlowScene = {
  type: "flow"; layout: string; startSec: number; durationSec: number;
  nodes: { id: string; label: string; at: number; color: string }[];
  edges: { from: string; to: string; at: number }[];
  packets: { edge: number; label: string; at: number; dur: number; color: string; reverse?: boolean }[];
  focus: { node: string; label?: string; at: number; dur: number }[];
};

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const win = (t: number, a: number, b: number, fin = 0.25, fout = 0.4) => interpolate(t, [a, a + fin, b, b + fout], [0, 1, 1, 0], clamp); // 0..1 envelope of a time window

const Icon: React.FC<{ kind: string; s: number; color: string }> = ({ kind, s, color }) => {
  const sw = s * 0.07, p = { fill: "none", stroke: color, strokeWidth: sw, strokeLinejoin: "round", strokeLinecap: "round" } as const;
  return (
    <svg width={s} height={s} viewBox="0 0 64 64">
      {/browser|client|app/i.test(kind) ? <><rect x="6" y="11" width="52" height="42" rx="6" {...p} /><path d="M6 23H58" {...p} /><circle cx="15" cy="17" r="1.5" fill={color} /><circle cx="22" cy="17" r="1.5" fill={color} /><path d="M17 36L27 44L17 52M33 50H47" {...p} transform="translate(0 -8) scale(1)" /></>
        : /data|db|store/i.test(kind) ? <><ellipse cx="32" cy="15" rx="21" ry="8" {...p} /><path d="M11 15V49C11 54 20 58 32 58S53 54 53 49V15M11 32C11 37 20 41 32 41S53 37 53 32" {...p} /></>
        : /api|server/i.test(kind) ? <><rect x="9" y="9" width="46" height="16" rx="4" {...p} /><rect x="9" y="39" width="46" height="16" rx="4" {...p} /><circle cx="19" cy="17" r="2" fill={color} /><circle cx="19" cy="47" r="2" fill={color} /><path d="M32 25V39" {...p} /></>
        : <path d="M32 6L56 22L48 54H16L8 22Z M8 22H56 M32 6L24 54 M32 6L40 54" {...p} />}
    </svg>
  );
};

export const Flow: React.FC<FlowScene & { rect: Rect }> = (s) => {
  const f = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = f / fps, R = s.rect;
  const { U, horiz, bw, bh, rowY, pos } = flowLayout(R, width, height, s.nodes.length);
  const P = Object.fromEntries(s.nodes.map((nd, i) => [nd.id, pos[i]]));
  const idx = (id: string) => s.nodes.findIndex((nd) => nd.id === id);
  const seg = (e: { from: string; to: string }) => edgeSeg(P[e.from], P[e.to], bw, bh, U, horiz);
  const pop = (at: number) => spring({ frame: f - at * fps, fps, config: { damping: 14 } });
  const packetEnd = (k: FlowScene["packets"][number]) => k.at + k.dur;

  // highlight envelope per node: focus windows + packet departure/arrival
  const env = (id: string) => {
    let e = 0;
    for (const x of s.focus) if (x.node === id) e = Math.max(e, win(t, x.at, x.at + x.dur));
    s.packets.forEach((k) => {
      const ed = s.edges[k.edge], src = k.reverse ? ed.to : ed.from, dst = k.reverse ? ed.from : ed.to;
      if (src === id) e = Math.max(e, win(t, k.at, k.at + 0.5, 0.15, 0.3));
      if (dst === id) e = Math.max(e, win(t, packetEnd(k) - 0.15, packetEnd(k) + 0.8, 0.2, 0.4));
    });
    return e;
  };
  const status = (id: string) => { let best: { label: string; v: number } | null = null; for (const x of s.focus) if (x.node === id && x.label) { const v = win(t, x.at, x.at + x.dur, 0.2, 0.3); if (!best || v > best.v) best = { label: x.label, v }; } return best; };
  const lastDir = (ei: number) => { const done = s.packets.filter((k) => k.edge === ei && k.at <= t); return done.length && done[done.length - 1].reverse ? -1 : 1; };
  const dockIndex = (ei: number, pi: number) => s.packets.slice(0, pi).filter((k) => k.edge === ei).length;
  const chipW = (label: string, fs: number) => label.length * fs * 0.56 + fs * 1.8;

  return (
    <AbsoluteFill style={{ fontFamily: font, color: C.ink }}>
      <svg width={width} height={height} style={{ position: "absolute" }}>
        {s.edges.map((e, i) => {
          const g = seg(e), p = interpolate(t, [e.at, e.at + 0.6], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) }), d = lastDir(i);
          const x2 = g.x1 + (g.x2 - g.x1) * p, y2 = g.y1 + (g.y2 - g.y1) * p;
          const dots = [0, 1, 2, 3].map((k) => { let u = (t * 0.16 + k / 4) % 1; if (d < 0) u = 1 - u; return { x: g.x1 + (g.x2 - g.x1) * u, y: g.y1 + (g.y2 - g.y1) * u, o: Math.sin(Math.PI * u) * 0.55 * p }; });
          return <g key={i}>
            <line x1={g.x1} y1={g.y1} x2={x2} y2={y2} stroke={C.indigo} strokeOpacity={0.7} strokeWidth={6 * U} strokeLinecap="round" strokeDasharray={`${16 * U} ${14 * U}`} strokeDashoffset={-d * t * 46 * U} />
            {dots.map((q, k) => <circle key={k} cx={q.x} cy={q.y} r={7 * U} fill={C.aqua} opacity={q.o} />)}
          </g>;
        })}
      </svg>
      {s.nodes.map((nd, i) => {
        const sc = pop(nd.at), { x, y } = pos[i], e = env(nd.id), st = status(nd.id);
        const bob = Math.sin(t * 1.6 + i * 1.7) * 5 * U, breathe = 0.5 + 0.5 * Math.sin(t * 2 + i);
        const fs = Math.min(bh * 0.2, (bw * 0.88) / (Math.max(nd.label.length, 6) * 0.6));
        const sfs = st ? Math.min(bh * 0.15, (bw * 0.9) / (st.label.length * 0.56)) : 0;
        return <div key={nd.id} style={{ position: "absolute", left: x - bw / 2, top: y - bh / 2 + bob, width: bw, height: bh, boxSizing: "border-box", transform: `scale(${sc * (1 + 0.07 * e)})`, opacity: Math.min(1, sc * 2),
          background: `linear-gradient(160deg, ${C.panel2}, ${C.panel})`, border: `${(5 + 2 * e) * U}px solid ${nd.color}`, borderRadius: 26 * U,
          display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 4 * U,
          boxShadow: `0 0 ${(34 + 30 * breathe + 70 * e) * U}px ${nd.color}${e > 0.3 ? "99" : "55"}` }}>
          <Icon kind={nd.label} s={bh * 0.33} color={nd.color} />
          <div style={{ fontSize: fs, fontWeight: 800, lineHeight: 1.1 }}>{nd.label}</div>
          <div style={{ height: bh * 0.14, fontSize: sfs, fontWeight: 600, color: C.amber, opacity: st ? st.v : 0, whiteSpace: "nowrap" }}>{st?.label ?? ""}</div>
        </div>;
      })}
      {/* arrival ripples */}
      <svg width={width} height={height} style={{ position: "absolute" }}>
        {s.packets.map((k, i) => {
          const ed = s.edges[k.edge], dst = P[k.reverse ? ed.from : ed.to], u = (t - packetEnd(k)) / 0.8;
          return u > 0 && u < 1 ? <rect key={i} x={dst.x - bw / 2 - u * 30 * U} y={dst.y - bh / 2 - u * 30 * U} width={bw + u * 60 * U} height={bh + u * 60 * U} rx={(26 + u * 26) * U} fill="none" stroke={k.color} strokeWidth={4 * U} opacity={0.7 * (1 - u)} /> : null;
        })}
      </svg>
      {/* docked log chips, then packets on top of nodes */}
      {s.packets.map((k, i) => {
        if (t < packetEnd(k)) return null;
        const g = seg(s.edges[k.edge]), fs = 22 * U, w = chipW(k.label, fs), di = dockIndex(k.edge, i);
        const x = horiz ? (g.x1 + g.x2) / 2 : g.x1 - 40 * U - w, y = horiz ? rowY + bh / 2 + 36 * U + di * 54 * U : (g.y1 + g.y2) / 2 + (di - 0.5) * 54 * U;
        const lx = horiz ? Math.min(R.x + R.w - w, Math.max(R.x, x - w / 2)) : x, o = interpolate(t, [packetEnd(k), packetEnd(k) + 0.4], [0, 0.9], clamp);
        return <div key={`d${i}`} style={{ position: "absolute", left: lx, top: y - fs, width: w, height: fs * 2, borderRadius: fs, boxSizing: "border-box", background: `${C.panel}`, border: `${2 * U}px solid ${k.color}`, opacity: o, display: "flex", alignItems: "center", justifyContent: "center", fontSize: fs, fontWeight: 600, color: C.ink, whiteSpace: "nowrap" }}>{k.label}</div>;
      })}
      <svg width={width} height={height} style={{ position: "absolute" }}>
        {s.packets.map((k, i) => {
          if (t < k.at || t > packetEnd(k)) return null;
          const g = seg(s.edges[k.edge]);
          const raw = interpolate(t, [k.at, packetEnd(k)], [0, 1], { easing: Easing.inOut(Easing.cubic) });
          const at = (u: number) => { const q = k.reverse ? 1 - u : u; return { x: g.x1 + (g.x2 - g.x1) * q, y: g.y1 + (g.y2 - g.y1) * q }; };
          const { x, y } = at(raw), grow = interpolate(t, [k.at, k.at + 0.15], [0.2, 1], clamp);
          const fs = 32 * U, w = chipW(k.label, fs), h = fs * 1.9;
          const lx = horiz ? Math.min(R.x + R.w - w, Math.max(R.x, x - w / 2)) : Math.min(width - w - 20 * U, x + 44 * U), ly = horiz ? rowY - bh / 2 - 44 * U - h : y - h / 2;
          return <g key={i}>
            {[3, 2, 1].map((j) => { const q = at(Math.max(0, raw - j * 0.035)); return <circle key={j} cx={q.x} cy={q.y} r={(26 - j * 5) * U * grow} fill={k.color} opacity={0.14 * (4 - j)} />; })}
            <circle cx={x} cy={y} r={44 * U * grow} fill={k.color} opacity={0.22} />
            <circle cx={x} cy={y} r={25 * U * grow} fill={k.color} />
            {horiz && <line x1={x} y1={ly + h} x2={x} y2={y - 30 * U} stroke={k.color} strokeOpacity={0.5} strokeWidth={3 * U} strokeDasharray={`${6 * U} ${6 * U}`} />}
            <rect x={lx} y={ly} width={w} height={h} rx={h / 2} fill={C.panel} stroke={k.color} strokeWidth={3 * U} opacity={grow} />
            <text x={lx + w / 2} y={ly + h / 2 + fs * 0.35} textAnchor="middle" fontSize={fs} fontWeight={700} fill={C.ink} fontFamily={font} opacity={grow}>{k.label}</text>
          </g>;
        })}
      </svg>
    </AbsoluteFill>
  );
};
