"""Checks an AI-written marketplace listing against the seller's item specifics.

Deterministic, no model. Every claim the vocabulary (lexicon.json) recognizes is marked
SUPPORTED, CONTRADICTED or UNSUPPORTED. Any claim that isn't SUPPORTED means REVIEW.
docs/demo/checker.js implements the same rules; tests/test_parity.py keeps them identical.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

LEXICON = json.loads((Path(__file__).resolve().parent / "lexicon.json").read_text(encoding="utf-8"))
_NEG_AFTER = re.compile(LEXICON["negation_after_regex"], re.I)
_CLAUSE_END = re.compile(r"[.!?;,\n]")


def norm(s) -> str:
    return re.sub(r"[^a-z0-9.]", "", str(s).lower())


def _fill(template: str, m: re.Match) -> str:
    return re.sub(r"\$(\d)", lambda g: (m.group(int(g.group(1))) or ""), template).strip().lower()


def _negated(text: str, start: int, end: int) -> bool:
    before = text[max(0, start - 60):start]
    cut = max((b.end() for b in _CLAUSE_END.finditer(before)), default=0)
    words = re.findall(r"[a-z']+", before[cut:].lower())
    breaks = [i for i, w in enumerate(words) if w in LEXICON["clause_break_words"]]
    if breaks:
        words = words[breaks[-1] + 1:]
    words = words[-LEXICON["negation_window_words"]:]
    if any(w in LEXICON["negations_before"] or w.endswith("n't") for w in words):
        return True
    return bool(_NEG_AFTER.match(text[end:end + 30]))


def _context(text: str, start: int, end: int) -> str:
    """The number plus up to two words either side, so the seller sees what it refers to."""
    left = re.findall(r"\S+", text[max(0, start - 30):start])[-2:]
    right = re.findall(r"\S+", text[end:end + 30])[:2]
    return " ".join(left + [text[start:end]] + right) if (left or right) else text[start:end]


def _canon_brand(s: str) -> str:
    s = norm(s)
    return norm(LEXICON["brand_aliases"].get(s, s))


def _model_norm(s: str) -> str:
    words = [w for w in str(s).lower().split() if w not in LEXICON["model_strip_words"]]
    return norm(" ".join(words))


def _judge(det: dict, claimed: str, specifics: dict) -> tuple[str, str]:
    key, compare = det["specific"], det["compare"]
    listed = specifics.get(key)
    if compare in ("true",):
        if listed:
            return "SUPPORTED", f"specifics: {key} = {listed}"
        return "UNSUPPORTED", f"specifics don't record {key}"
    if listed in (None, "", []):
        return "UNSUPPORTED", f"specifics don't say anything about {key}"
    if compare == "equals":
        ok = norm(claimed) == norm(listed)
    elif compare == "contains":
        aliases = LEXICON["color_aliases"]
        ok = norm(aliases.get(claimed, claimed)) in norm(" ".join(aliases.get(w, w) for w in str(listed).lower().split()))
    elif compare == "model":
        ok = _model_norm(claimed) in _model_norm(listed)
    elif compare == "min":
        ok = int(claimed) <= int(listed)
    elif compare == "brand":
        ok = _canon_brand(claimed) == _canon_brand(listed)
    elif compare == "condition":
        ok = listed in LEXICON["condition_allows"][claimed]
    elif compare == "member":
        ok = claimed in [str(x).lower() for x in listed]
    elif compare == "complete":
        items = [str(x).lower() for x in listed]
        ok = "original box" in items and len(items) >= 2
    else:  # pragma: no cover
        raise ValueError(f"unknown compare {compare}")
    return ("SUPPORTED" if ok else "CONTRADICTED"), f"specifics: {key} = {listed}"


def check(specifics: dict, title: str = "", description: str = "") -> dict:
    text = f"{title}\n{description}".strip()
    if not text:
        return {"decision": "REVIEW", "claims": [], "reason": "empty listing"}
    taken: list[tuple[int, int]] = []
    claims, seen = [], set()
    for det in LEXICON["detectors"]:
        for pat in det["patterns"]:
            for m in re.finditer(pat["regex"], text, re.I):
                s, e = m.span()
                if any(s < te and ts < e for ts, te in taken):
                    continue
                taken.append((s, e))
                if _negated(text, s, e):
                    continue
                claimed = _fill(pat["value"], m)
                ident = (det["attribute"], claimed)
                if ident in seen:
                    continue
                seen.add(ident)
                status, why = _judge(det, claimed, specifics)
                claims.append({"attribute": det["attribute"], "claimed": claimed, "text": m.group(0),
                               "status": status, "harm": det["harm"], "reason": why})
    backed = set()
    for v in specifics.values():
        for item in (v if isinstance(v, list) else [v]):
            backed.update(re.findall(r"\d+(?:\.\d+)?", str(item)))
    rule = LEXICON["unbacked_numbers"]
    for m in re.finditer(rule["regex"], text):
        s, e = m.span()
        if any(s < te and ts < e for ts, te in taken) or m.group(0) in backed:
            continue
        taken.append((s, e))
        claims.append({"attribute": "number", "claimed": m.group(0), "text": _context(text, s, e),
                       "status": "UNSUPPORTED", "harm": rule["harm"],
                       "reason": f"the number {m.group(0)} isn't in any item specific"})
    bad = [c for c in claims if c["status"] != "SUPPORTED"]
    return {"decision": "REVIEW" if bad else "PUBLISH", "claims": claims,
            "reason": f"{len(bad)} claim(s) not backed by the item specifics" if bad else
                      "every recognized claim is backed by the item specifics"}
