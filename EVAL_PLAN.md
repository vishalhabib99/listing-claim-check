# Eval plan: listing-claim-check

**Decision:** publish v0.1 as a public reference build. **Decision owner:** Vishal Habib (delegated). **Thresholds frozen 2026-09-26, before the first run.**

## Test sets

| Set | Who writes it | Used for |
|---|---|---|
| `evals/dev.jsonl` | The builder, while building | Development. It will be overfit, so it isn't reported as a result |
| `evals/heldout.jsonl` | **A separate agent that never sees the vocabulary or the code**, only this plan and the input format. Committed before its first run | The reported result |

Each case has the item specifics, the listing text, the expected decision, and for planted errors the planted claim and its harm level.

**Slices:** clean (every claim supported), high-harm planted (one unsupported or contradicted claim in a high-harm attribute), low-harm planted (color or material), and tricky clean (negations such as "no box included", and near-misses such as "genuine leather" on a real leather item).

## Launch gates

| Gate | Metric (held-out, first run) | Threshold | Blocking? |
|---|---|---|---|
| Top harm | High-harm planted claims marked PUBLISH | **≤ 10%** | **Yes** |
| Seller friction | Clean listings (including tricky clean) marked REVIEW | ≤ 20% | Yes |
| Explainability | REVIEW decisions citing the claim words and the specific they conflict with | 100% | Yes |
| Release gate | [mcp-trust-check](https://github.com/vishalhabib99/mcp-trust-check) on the MCP server | SHIP | Yes |

**Why ≤ 10% and not 0 (unlike retirement-answer-check):** here a miss costs a return and a refund, not a regulatory breach. Existing buyer protections still apply, and today's baseline is no check at all, so every AI-invented claim gets through. The gate is set by the harm, not by what's easy to hit.

**If a gate fails:** the result is published as-is, with the first-run log. The fix is a design change, not a pattern added for each missed case.

## Changelog

| Date | Change | Why |
|---|---|---|
| 2026-09-26 | Gates frozen (commit `25dc887`) before any code or cases | Pre-registration |
| 2026-09-26 | `evals/heldout.jsonl` (30 cases) written by a separate agent that read only this plan and the PRD. Committed together with the checker, frozen, before the first run | The builder saw the agent's one-line summary of each planted phrase before the first run. So the vocabulary was frozen at that point, and nothing after it counts as blind |
| 2026-09-26 | **v0.1 first blind run: top-harm gate FAILED**, 2/11 high-harm claims marked PUBLISH (18% > 10%); friction passed, 1/16 (6%). Log: `evals/heldout_first_run.txt` | Both misses were numbers phrased outside the vocabulary ("91% health", "Tabby 26") |
| 2026-09-26 | **v0.2 design change**, not a pattern per miss: any number that no item specific backs → UNSUPPORTED. Also fixed two bugs found in held-out case h14: a 3-word negation window (now up to 5 words, cut at a conjunction), and "genuine black leather" read as an authenticity claim | Same principle as retirement-answer-check: what the source of truth can't back goes to a person. Held-out 1 is **no longer blind** for v0.2; its re-run is in `evals/heldout_after_v02_NOT_BLIND.txt` and isn't reported as a result |
| 2026-09-26 | `evals/heldout2.jsonl`: 30 new cases from a **fresh** agent, reporting slice counts only (the builder didn't see any planted phrases). Committed with v0.2 frozen, before its first run | The blind measurement of v0.2 |
