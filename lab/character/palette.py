"""Facet palette (see STYLE.md). Hex sRGB -> linear for vertex colours."""
PAL = {
    "head": "#2EC4B6", "head2": "#1FA39A", "head3": "#6FE3D4",     # aqua-teal crystal
    "body": "#5B5BD6", "body2": "#4747B8", "body3": "#7A7AEA",     # indigo stone
    "limb": "#7A7AEA", "limb2": "#5B5BD6",
    "hand": "#FF6B6B", "hand2": "#E64A5A",                          # coral
    "foot": "#FF6B6B", "foot2": "#E64A5A",
    "accent": "#FFC93C", "accent2": "#FFAE1A",                      # amber
    "eye": "#141C5C", "eyehl": "#E8FAFF", "mouth": "#2A0F2E",
}
def srgb(h):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)
