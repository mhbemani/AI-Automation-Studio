"""validate.py [dialogue.json] — strict check of the dialogue file; exits 1 with every problem listed."""
import json, sys

SPEAKERS = {"claude", "human"}


def validate(d):
    err = []
    allowed = d.get("emotionsAllowed")
    if not isinstance(allowed, list) or "neutral" not in allowed:
        err.append("emotionsAllowed must be a list that contains 'neutral'")
        allowed = []
    for s in SPEAKERS:
        v = d.get("voices", {}).get(s)
        if not v or not v.get("voice") or not isinstance(v.get("speed"), (int, float)) or not 0.5 <= v["speed"] <= 2:
            err.append(f"voices.{s}: needs 'voice' and 'speed' in 0.5..2")
    if not isinstance(d.get("gapBetweenLinesSec"), (int, float)) or not 0 <= d["gapBetweenLinesSec"] <= 3:
        err.append("gapBetweenLinesSec must be a number in 0..3")
    if not isinstance(d.get("pronunciation", {}), dict) or not all(isinstance(k, str) and isinstance(v, str) and v.strip() for k, v in d.get("pronunciation", {}).items()):
        err.append("pronunciation must map words to non-empty strings")
    intro = d.get("intro")
    if not isinstance(intro, list) or not intro:
        err.append("intro must be a non-empty list")
        intro = []
    for i, s in enumerate(intro):
        where = f"intro[{i}]"
        for k in ("shot", "camera", "action"):
            if not isinstance(s.get(k), str) or not s[k].strip():
                err.append(f"{where}: '{k}' must be a non-empty string")
        if not isinstance(s.get("durationSec"), (int, float)) or not 0.5 <= s["durationSec"] <= 30:
            err.append(f"{where}: durationSec must be a number in 0.5..30")
        if "phoneText" in s and (not isinstance(s["phoneText"], str) or not s["phoneText"].strip()):
            err.append(f"{where}: phoneText must be a non-empty string")
    if sum("phoneText" in s for s in intro) != 1:
        err.append("intro: exactly one shot must carry phoneText")
    lines = d.get("lines")
    if not isinstance(lines, list) or not lines:
        err.append("lines must be a non-empty list")
        lines = []
    ids = [l.get("id") for l in lines]
    if len(set(ids)) != len(ids):
        err.append("lines: ids must be unique")
    for i, l in enumerate(lines):
        where = f"lines[{i}] (id {l.get('id')})"
        if l.get("speaker") not in SPEAKERS:
            err.append(f"{where}: speaker {l.get('speaker')!r} not in {sorted(SPEAKERS)}")
        if l.get("emotion") not in allowed:
            err.append(f"{where}: emotion {l.get('emotion')!r} not in emotionsAllowed")
        if not isinstance(l.get("text"), str) or not l["text"].strip():
            err.append(f"{where}: text must be non-empty")
    return err


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "dialogue_v2.json"
    problems = validate(json.load(open(path)))
    if problems:
        print(f"{path}: {len(problems)} problem(s)\n  " + "\n  ".join(problems))
        sys.exit(1)
    # self-check: a broken copy must fail on each injected fault
    bad = json.load(open(path))
    bad["lines"][0]["speaker"] = "robot"; bad["lines"][1]["emotion"] = "angry"; bad["lines"][2]["text"] = " "; del bad["intro"][0]["durationSec"]
    assert len(validate(bad)) == 4, validate(bad)
    print(f"{path}: OK")
