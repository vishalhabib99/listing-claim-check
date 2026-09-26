"""Run the checker on an eval set and score it against the launch gates in EVAL_PLAN.md."""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from listing_claim_check import check  # noqa: E402

path = Path(sys.argv[1])
rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
by_slice, fails = Counter(), []
passed = Counter()
for r in rows:
    out = check(r["specifics"], r.get("title", ""), r.get("description", ""))
    ok = out["decision"] == r["expected"]
    by_slice[r["slice"]] += 1
    passed[r["slice"]] += ok
    if not ok:
        flagged = [f"{c['status']} {c['attribute']} {c['text']!r}" for c in out["claims"] if c["status"] != "SUPPORTED"]
        planted = (r.get("planted") or {}).get("text")
        fails.append(f"  FAIL {r['id']} [{r['slice']}] expected {r['expected']} got {out['decision']}"
                     + (f" | planted: {planted!r}" if planted else "") + (f" | flagged: {flagged}" if flagged else ""))
    if r["expected"] == "REVIEW" and out["decision"] == "REVIEW" and not all(c["reason"] for c in out["claims"]):
        fails.append(f"  EXPLAIN {r['id']}: a flag has no reason")

print(f"{path.name}: {sum(passed.values())}/{len(rows)} pass")
for s in sorted(by_slice):
    print(f"  {s:13} {passed[s]}/{by_slice[s]}")
hh = by_slice["high_harm"]
miss = hh - passed["high_harm"]
clean = by_slice["clean"] + by_slice["tricky_clean"]
false_review = clean - passed["clean"] - passed["tricky_clean"]
print(f"GATE top harm: {miss}/{hh} high-harm claims marked PUBLISH ({miss / hh:.0%}) — threshold <= 10%: {'PASS' if miss / hh <= 0.10 else 'FAIL'}")
print(f"GATE friction: {false_review}/{clean} clean listings marked REVIEW ({false_review / clean:.0%}) — threshold <= 20%: {'PASS' if false_review / clean <= 0.20 else 'FAIL'}")
print("\n".join(fails))
