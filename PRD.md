# PRD: listing-claim-check

**Owner:** Vishal Habib · **Status:** v0.1 reference build · **Date:** 2026-09-26

## 1. Problem and user

- **User:** the product manager for AI listing tools on a marketplace, and the trust & safety team that handles "item not as described" disputes.
- **Job to be done:** "Let sellers publish AI-written listings fast, without the AI inventing attributes the item doesn't have."
- **Today:** marketplaces let sellers generate titles and descriptions with AI from a photo or a few details. A language model writing sales copy will fill gaps with plausible claims: "unlocked", "genuine leather", "includes original box", "like new". When the item doesn't match, the buyer opens a not-as-described dispute. That costs a return, a refund, the seller's rating, and buyer trust in AI-written listings in general.
- **The source of truth already exists:** the seller's structured **item specifics** (condition, brand, model, storage, size, what's included). The check is whether every claim in the AI text is backed by them.

## 2. Scope (v0.1)

- **Categories:** smartphones, sneakers, handbags.
- **Input:** the item specifics (JSON) plus the AI-written title and description.
- **Output:** **PUBLISH** or **REVIEW**. For each detected claim: SUPPORTED, CONTRADICTED (the specifics say something different) or UNSUPPORTED (the specifics say nothing about it), with the words that triggered it.
- **Not in scope:** photos; pricing; policy violations such as prohibited items; writing or rewriting listings.

## 3. Autonomy

| Action | Level |
|---|---|
| Mark PUBLISH | Acts alone, only when every detected claim is supported |
| Mark REVIEW | Acts alone. The seller sees exactly which words to fix or which specific to add |
| Rewrite the listing | Never. The seller decides |

## 4. Top-harm error

**A claim that would cause a not-as-described dispute, marked PUBLISH.** High-harm attributes: condition (for example "like new" on a used item), authenticity, model, storage, carrier lock, battery health, size, brand, warranty, and what's included.

## 5. Design

Deterministic, with no model: a vocabulary of claim patterns per attribute, matched against the text and compared with the item specifics. Negated mentions ("no box", "not unlocked") don't count as claims. Overlapping matches go to the more specific pattern ("genuine leather" is a material, not an authenticity claim).

**Why no model in v0.1:** it has to be cheap enough to run on every listing, and explainable enough to show the seller the exact words. The known cost: claims phrased outside the vocabulary are invisible to it. The blind held-out eval measures how often that happens, and that number decides whether v0.2 needs a model layer, the same path retirement-answer-check took.

## 6. Success metrics (for a real deployment)

- **Primary:** not-as-described dispute rate on AI-written listings, compared with a holdout group that has no check.
- **Guardrail:** share of AI listings sent to REVIEW (seller friction), and time to publish.

## 7. Evals and launch gates

See [EVAL_PLAN.md](EVAL_PLAN.md). Gates are set before the first run.

## 8. Rollout

Shadow mode (flag, don't block) → show REVIEW reasons to sellers in one category → all three categories. **Kill switch:** everything publishes as it does today.

**Shadow-mode exit rule (set before shadow mode starts).** Bar: high-harm claims get through less than 10% of the time (the launch gate), at 95% confidence (one-sided exact binomial). A miss is a high-harm claim the checker would have published (marked PUBLISH), as judged by the reviewer. Each run uses one fixed checker version. The run exits when the number of reviewed cases reaches the count for the misses so far:

| Misses so far | Exit at this many reviewed cases |
|---|---|
| 0 | 37 |
| 1 | 55 |
| 2 | 71 |
| 3 | 87 |
| 4 or more | The run fails. Fix the checker and start a new run |

- **Why not stop at the first clean count:** taken alone, 0 misses in 29 meets the bar. But checking at each row in turn gives the checker four chances to pass, and a checker whose true rate is exactly 10% would then exit about 10% of the time instead of 5%. The counts above are set so the whole schedule, all four chances together, stays at 5% (exact, summed over every path a run can take). The price is 8 more cases on a clean run.
- **A miss doesn't restart the count.** If a miss leads to a change in the checker, that's a new version and a new run starting from 0, and the stopped run stays in the report with its count and its misses. Restarting would keep only the runs that happened to finish clean.
- **The result covers only what the run sampled**, which is live traffic. Blind-set and red-team results are bounds on other populations and are reported next to it, not merged into it. A clean shadow run here says nothing about a seller who is trying to get past the checker: the v0.2 red team got 22 of 22 in-scope attacks through.
- The continuation rule came out of [a reader's review](https://dev.to/arhancanli/comment/3g81b) of the "0 of N" write-up.
