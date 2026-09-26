"""The web demo (docs/checker.js) and the Python checker must give identical results."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from listing_claim_check import check

ROOT = Path(__file__).resolve().parents[1]
LEX = ROOT / "src/listing_claim_check/lexicon.json"
NODE = shutil.which("node")


def _cases():
    rows = []
    for f in sorted((ROOT / "evals").glob("*.jsonl")):
        rows += [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
    extra = {"brand": "Apple", "model": "iPhone 13 Pro", "condition": "Used", "storage": "128GB", "carrier": "Verizon",
             "battery_health": 86, "includes": ["cable"], "authenticity_verified": False}
    for text in ["Charger not included. No scratches and comes with the charger.", "Bought in 2023, 2 day shipping, 8GB RAM",
                 "Genuine black leather, 100% legit, iPhone 14, Galaxy S23 Ultra, 91% battery", ""]:
        rows.append({"specifics": extra, "title": "", "description": text})
    return rows


@pytest.mark.skipif(NODE is None, reason="node not installed")
def test_js_matches_python():
    cases = _cases()
    script = ("const C=require(process.argv[1]);const L=require(process.argv[2]);"
              "const cs=JSON.parse(require('fs').readFileSync(0,'utf8'));"
              "console.log(JSON.stringify(cs.map(c=>C.check(L,c.specifics,c.title||'',c.description||''))));")
    out = subprocess.run([NODE, "-e", script, str(ROOT / "docs/checker.js"), str(LEX)],
                         input=json.dumps(cases), capture_output=True, text=True, check=True).stdout
    for case, js in zip(cases, json.loads(out)):
        assert js == check(case["specifics"], case.get("title", ""), case.get("description", "")), case.get("id", case)


def test_demo_copy_of_lexicon_is_current():
    assert json.loads((ROOT / "docs/lexicon.json").read_text()) == json.loads(LEX.read_text()), \
        "cp src/listing_claim_check/lexicon.json docs/lexicon.json"
