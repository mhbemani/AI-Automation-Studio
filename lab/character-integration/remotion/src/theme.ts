// Palette from lab/character/STYLE.md (Facet world): navy stage, aqua / indigo / coral, amber accent.
export const C = { bg: "#0b1020", panel: "#141c3a", panel2: "#1b2550", aqua: "#2EC4B6", indigo: "#5B5BD6", indigoLight: "#7A7AEA", coral: "#FF6B6B", amber: "#FFC93C", ink: "#E8FAFF", dim: "#8d97c4" };

export type Rect = { x: number; y: number; w: number; h: number };
export type Place = { cx: number; feet: number; charH: number }; // character: centre x, ground line y, height (px)
export type Geo = { diagram?: Rect; text?: Rect; caption: Rect; char: Place };

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

// small deterministic PRNG so ambient motion is identical on every render
export const rng = (seed: number) => () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
