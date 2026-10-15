// Palette from lab/character/STYLE.md (Facet world): navy stage, aqua / indigo / coral, amber accent.
export const C = { bg: "#0b1020", panel: "#141c3a", panel2: "#1b2550", aqua: "#2EC4B6", indigo: "#5B5BD6", indigoLight: "#7A7AEA", coral: "#FF6B6B", amber: "#FFC93C", ink: "#E8FAFF", dim: "#8d97c4" };

export type { Rect, Place, Geo } from "./layout";
export { geo } from "./layout";

// small deterministic PRNG so ambient motion is identical on every render
export const rng = (seed: number) => () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
