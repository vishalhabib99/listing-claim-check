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

## Red team (v0.2), bar frozen 2026-09-27 before any attack is written

The two blind sets were written from the plan, so they show the checker handles the listings a spec-reader imagines. The red team tests the listings someone who has **read the code** would write to get an unbacked claim through.

- **Who:** a separate agent that may read everything: code, vocabulary, PRD, this plan and both held-out sets. It writes `evals/redteam.jsonl` in the same format and runs the checker itself.
- **What counts as a hole:** a listing whose text makes a **high-harm** claim (PRD section 4) that the item specifics don't back or that they contradict, and that v0.2 marks **PUBLISH**. The claim must be one a real seller or listing model could plausibly write (no unreadable text, no invisible characters used only to hide a word). The builder confirms each reported hole against the PRD before it counts.
- **Bar:** **0 confirmed high-harm holes** for the red team to count as held. Low-harm holes (color, material) and false REVIEWs on clean listings are recorded but don't block.
- **If the bar fails:** results are published as-is. The fix is a design change, not a pattern per case, followed by a fresh blind set (held-out 3) from a new agent before any new claim is made. The held-out-2 known issue ("no box or charger") is fixed only in that same round.

## Changelog

| Date | Change | Why |
|---|---|---|
| 2026-09-26 | Gates frozen (commit `25dc887`) before any code or cases | Pre-registration |
| 2026-09-26 | `evals/heldout.jsonl` (30 cases) written by a separate agent that read only this plan and the PRD. Committed together with the checker, frozen, before the first run | The builder saw the agent's one-line summary of each planted phrase before the first run. So the vocabulary was frozen at that point, and nothing after it counts as blind |
| 2026-09-26 | **v0.1 first blind run: top-harm gate FAILED**, 2/11 high-harm claims marked PUBLISH (18% > 10%); friction passed, 1/16 (6%). Log: `evals/heldout_first_run.txt` | Both misses were numbers phrased outside the vocabulary ("91% health", "Tabby 26") |
| 2026-09-26 | **v0.2 design change**, not a pattern per miss: any number that no item specific backs → UNSUPPORTED. Also fixed two bugs found in held-out case h14: a 3-word negation window (now up to 5 words, cut at a conjunction), and "genuine black leather" read as an authenticity claim | Same principle as retirement-answer-check: what the source of truth can't back goes to a person. Held-out 1 is **no longer blind** for v0.2; its re-run is in `evals/heldout_after_v02_NOT_BLIND.txt` and isn't reported as a result |
| 2026-09-26 | `evals/heldout2.jsonl`: 30 new cases from a **fresh** agent, reporting slice counts only (the builder didn't see any planted phrases). Committed with v0.2 frozen, before its first run | The blind measurement of v0.2 |
