# listing-claim-check

Checks an AI-written marketplace listing against the seller's own item specifics **before it's published**, and returns **PUBLISH** or **REVIEW** with the exact words behind every unbacked claim.

Marketplaces let sellers generate listings with AI. A model writing sales copy fills gaps with plausible claims: "unlocked", "like new", "genuine leather", "includes the original box". When the item doesn't match, the buyer opens a not-as-described dispute. The item specifics the seller already entered are the source of truth. This checks the copy against them.

**[Try it in your browser →](https://vishalhabib99.github.io/listing-claim-check/)** Runs locally, no account, no tracking.

> Reference build by an AI product manager: [PRD](PRD.md) → [eval plan with gates set first](EVAL_PLAN.md) → build → **blind evals, including a failed first run** → design change → a fresh blind run. Not affiliated with any marketplace.

## What it checks

| Claim | Example it catches | High harm? |
|---|---|---|
| Condition | "Like new" or "barely worn" on an item listed as Used | Yes |
| Authenticity | "100% legit" with no authentication recorded | Yes |
| Model, storage, battery, carrier | "iPhone 14" for a 13 · "256GB" for 128 · "91% battery" for 76 · "works on any network" for a carrier-locked phone | Yes |
| Size, brand, warranty | "Size 11" for a 10 · a brand the specifics don't name · "under warranty" with none recorded | Yes |
| What's included | "Comes with the original box and charger" when only a cable is | Yes |
| **Any number** | A number no item specific backs up ("Tabby 26" for a Tabby 20, "bought in 2023") | Yes |
| Color, material | "Pink" for a blue phone · "leather" for a canvas bag | Low |

Each claim is marked **SUPPORTED**, **CONTRADICTED** (the specifics say otherwise) or **UNSUPPORTED** (the specifics don't say). Anything but SUPPORTED → REVIEW. Negated mentions ("charger not included") aren't claims.

**Deterministic, no model.** It's cheap enough to run on every listing, and every flag points at exact words. The known cost: a claim phrased outside its vocabulary isn't seen, so **PUBLISH means "nothing unbacked was found", not "verified true"**.

## Results

Gates were [set before any code](EVAL_PLAN.md). Each held-out set was written by a separate agent that never saw the code or the vocabulary, and was committed before its first run.

| Run | Top harm: high-harm claims marked PUBLISH (gate ≤ 10%) | Friction: clean listings marked REVIEW (gate ≤ 20%) |
|---|---|---|
| **v0.1**, held-out 1, first run | **2 of 11 (18%): FAIL** | 1 of 16 (6%) |
| **v0.2**, held-out 2 (fresh, blind), first run | **0 of 11: PASS** | 2 of 16 (12%): PASS |

**What changed between them:** v0.1 missed "91% health" and "Tabby 26". Both are numbers phrased outside the vocabulary. Instead of adding a pattern for each miss, v0.2 changed the design: **any number that no item specific backs up goes to REVIEW.** That's the same principle as [retirement-answer-check](https://github.com/vishalhabib99/retirement-answer-check). Two bugs found in the same run were fixed too, which means held-out 1 isn't blind for v0.2, so its re-run isn't reported as a result. Logs: [`evals/heldout_first_run.txt`](evals/heldout_first_run.txt), [`evals/heldout2_first_run.txt`](evals/heldout2_first_run.txt).

**Known issue (v0.2):** "no box **or** charger" isn't read as negating the charger, because "or" ends the negation. Both false REVIEWs on held-out 2 came from this. It's safe-direction friction, not a missed claim. It's left unfixed until a third blind set can measure the fix.

**How much "0 of 11" proves.** It passes the gate on this set, but with 0 misses in 11, the true high-harm miss rate could still be as high as **24%** (one-sided 95% exact bound), above the 10% gate itself. Showing it's under 10% would take **29** high-harm cases in a row with none through.

**Limits:** 60 blind cases in 3 categories (phones, sneakers, handbags), all written by one model family. It hasn't been tested on real listings. Handbag and sneaker model names aren't recognized as model claims (only their numbers are).

## Use it

```bash
pip install git+https://github.com/vishalhabib99/listing-claim-check
```

```python
from listing_claim_check import check
check({"brand": "Nike", "size": "10", "condition": "Used"}, "Nike Dunk Low size 11", "Barely worn.")
# {'decision': 'REVIEW', 'claims': [
#   {'attribute': 'condition', 'text': 'Barely worn', 'status': 'CONTRADICTED', 'reason': 'specifics: condition = Used', ...},
#   {'attribute': 'size', 'text': 'size 11', 'status': 'CONTRADICTED', 'reason': 'specifics: size = 10', ...}, ...]}
```

As an MCP tool, so an AI listing assistant can check its own draft before showing it to the seller:

```bash
claude mcp add listing-claim-check -- uvx --from git+https://github.com/vishalhabib99/listing-claim-check listing-claim-check
```

Run the evals: `python evals/run.py evals/heldout2.jsonl`

## License

MIT
