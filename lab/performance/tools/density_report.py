#!/usr/bin/env python3
"""density_report.py <work dir> <aspect>: gesture density per scene and the 0.8 s rule after toning down (must be 0 too-close big pairs)."""
import json, sys
W, asp = sys.argv[1], sys.argv[2]; tag = "16x9" if asp == "16:9" else "9x16"
p = json.load(open(f"{W}/performance_{tag}.json")); proj = json.load(open(f"{W}/project.json")); R = 0.8
out = {"scenes": [], "rule_seconds": R}
for i, sc in enumerate(proj["scenes"]):
    bs = [b for b in p["beats"] if b["si"] == i]; n = len(bs); dur = sc["durationSec"]
    big = [b for b in bs if (b.get("amp_i") or 0) > 0.5]
    close_all = sum(1 for a, b in zip(bs, bs[1:]) if b["apex"] - a["apex"] < R)
    close_big = sum(1 for a, b in zip(big, big[1:]) if b["apex"] - a["apex"] < R)
    out["scenes"].append({"scene": i + 1, "beats": n, "durationSec": round(dur, 2), "beatsPerSec": round(n / dur, 2), "bigBeats": len(big), "pairsCloserThan0.8s_any": close_all, "pairsCloserThan0.8s_big": close_big,
                          "tonedDown": sum(1 for b in bs if b.get("reduced")), "autoAdded": sum(1 for b in bs if b.get("auto"))})
out["total_close_big_pairs"] = sum(s["pairsCloserThan0.8s_big"] for s in out["scenes"]); out["total_close_pairs_any"] = sum(s["pairsCloserThan0.8s_any"] for s in out["scenes"])
json.dump(out, open(f"{W}/density_report_{tag}.json", "w"), indent=1)
for s in out["scenes"]: print("scene %(scene)d: %(beats)d beats in %(durationSec)s s = %(beatsPerSec)s/s, big %(bigBeats)d, toned down %(tonedDown)d, auto-added %(autoAdded)d, pairs <0.8 s: any %(pairsCloserThan0.8s_any)d, big %(pairsCloserThan0.8s_big)d" % s)
print("too-close BIG pairs after the rule:", out["total_close_big_pairs"], "| all pairs closer than 0.8 s (second one is toned down):", out["total_close_pairs_any"])
