// Pure layout maths (no React, no "remotion" import) shared by the components and by stages/geometry.mjs, so the character is aimed at the REAL on-screen positions.
export type Rect = { x: number; y: number; w: number; h: number };
export type Place = { cx: number; feet: number; charH: number }; // character: centre x, ground line y, height (px)
export type Geo = { diagram?: Rect; text?: Rect; caption: Rect; char: Place };
export type Framing = { charHeight: number; feetY: number; centerX: number };

// Where things go for a layout in a given frame size. 16:9 and 9:16 differ: in 9:16 the character is always in the lower third, content above.
export function geo(layout: string, W: number, H: number): Geo {
  const R = (x: number, y: number, w: number, h: number): Rect => ({ x: x * W, y: y * H, w: w * W, h: h * H });
  if (H > W) {
    const ch = layout === "presenter_left_diagram_right" ? 0.32 : layout === "presenter_corner_diagram_full" ? 0.3 : 0.31;
    const char = { cx: 0.5 * W, feet: 0.985 * H, charH: ch * H };
    const caption = R(0.05, 0.545, 0.9, 0.105);
    return layout === "presenter_center_typography" ? { text: R(0.06, 0.07, 0.88, 0.55), caption, char } : { diagram: R(0.05, 0.06, 0.9, 0.46), caption, char };
  }
  if (layout === "presenter_left_diagram_right") return { diagram: R(0.44, 0.06, 0.54, 0.68), caption: R(0.44, 0.78, 0.54, 0.15), char: { cx: 0.17 * W, feet: 0.965 * H, charH: 0.74 * H } };
  if (layout === "presenter_corner_diagram_full") return { diagram: R(0.05, 0.05, 0.9, 0.66), caption: R(0.21, 0.78, 0.74, 0.15), char: { cx: 0.095 * W, feet: 0.975 * H, charH: 0.36 * H } };
  return { text: R(0.06, 0.05, 0.88, 0.42), caption: R(0.2, 0.8, 0.6, 0.12), char: { cx: 0.5 * W, feet: 0.975 * H, charH: 0.52 * H } };
}

const easeInOutCubic = (x: number) => (x < 0.5 ? 4 * x * x * x : 1 - 4 * (1 - x) * (1 - x) * (1 - x));
const clamp01 = (x: number) => Math.max(0, Math.min(1, x));

// Character placement at time t: it glides from the previous layout's place to the new one during the scene transition.
export function charPlace(t: number, geos: Geo[], starts: number[], T: number): Place {
  let k = 0; starts.forEach((s, i) => { if (s <= t) k = i; });
  const a = geos[Math.max(0, k - 1)].char, b = geos[k].char;
  const p = k === 0 ? 1 : easeInOutCubic(clamp01((t - starts[k]) / T));
  const m = (x: number, y: number) => x + (y - x) * p;
  return { cx: m(a.cx, b.cx), feet: m(a.feet, b.feet), charH: m(a.charH, b.charH) };
}
// Square clip rect on screen (side S) for a place.
export function clipRect(pl: Place, f: Framing) {
  const S = pl.charH / f.charHeight;
  return { left: pl.cx - S * f.centerX, top: pl.feet - S * f.feetY, S };
}

// ---- flow (diagram) scenes
export type Pt = { x: number; y: number };
export function flowLayout(R: Rect, W: number, H: number, n: number) {
  const U = Math.min(W, H) / 1080, horiz = W > H;
  const bw = horiz ? Math.min(R.w * 0.27, 340 * U) : Math.min(R.w * 0.6, 520 * U);
  const bh = horiz ? bw * 0.82 : 220 * U;
  const rowY = R.y + R.h * 0.47;
  const pos: Pt[] = Array.from({ length: n }, (_, i) => horiz ? { x: R.x + bw / 2 + (i * (R.w - bw)) / (n - 1), y: rowY } : { x: R.x + R.w / 2, y: R.y + bh / 2 + (i * (R.h - bh)) / (n - 1) });
  return { U, horiz, bw, bh, rowY, pos };
}
export const edgeSeg = (a: Pt, b: Pt, bw: number, bh: number, U: number, horiz: boolean) => {
  const gx = horiz ? bw / 2 + 16 * U : 0, gy = horiz ? 0 : bh / 2 + 16 * U;
  return { x1: a.x + gx, y1: a.y + gy, x2: b.x - gx, y2: b.y - gy };
};
export const easeInOutCubicT = easeInOutCubic;
// packet centre at time t (clamped to its flight window)
export function packetXY(g: { x1: number; y1: number; x2: number; y2: number }, at: number, dur: number, reverse: boolean | undefined, t: number): Pt {
  const u = easeInOutCubic(clamp01((t - at) / dur)), q = reverse ? 1 - u : u;
  return { x: g.x1 + (g.x2 - g.x1) * q, y: g.y1 + (g.y2 - g.y1) * q };
}

// ---- typography scenes: font size / wrapping per line, and the vertical centre of each text line (flex column, centred in the rect)
export function lineFont(text: string, first: boolean, rectW: number, U: number) {
  const base = first ? 124 : 92;
  const fit = rectW / (text.length * 0.55);
  const fs = fit >= base * U * 0.62 ? Math.min(base * U, fit) : base * U * 0.82;
  const words = text.split(" "), wrapped = fs * text.length * 0.55 > rectW;
  let m = words.length;
  if (wrapped) { let best = 1e9; for (let i = 1; i < words.length; i++) { const d = Math.abs(words.slice(0, i).join(" ").length - words.slice(i).join(" ").length); if (d < best) { best = d; m = i; } } }
  return { fs, wrapped, rows: wrapped ? [words.slice(0, m), words.slice(m)] : [words] };
}
export function typoLines(lines: { text: string }[], R: Rect, U: number) {
  const metrics = lines.map((l, k) => { const f = lineFont(l.text, k === 0, R.w, U); const textH = f.rows.length * f.fs * 1.1; return { ...f, textH, blockH: textH + 10 * U + 8 * U }; });
  const total = metrics.reduce((a, m) => a + m.blockH, 0) + 26 * U * (lines.length - 1);
  let y = R.y + (R.h - total) / 2;
  return metrics.map((m) => { const top = y; y += m.blockH + 26 * U; return { ...m, cx: R.x + R.w / 2, cy: top + m.textH / 2, top, width: Math.max(...m.rows.map((r) => r.join(" ").length)) * m.fs * 0.55 }; });
}
