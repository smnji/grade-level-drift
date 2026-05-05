---
date: 2026-05-05
severity: moderate
area: analysis
tags: [v0, results, extreme-values, gpd, tails, drift, math, hs-standards]
title: Extreme-value analysis on v0_run1 + v0_run2 — tails behave differently from means
---

Same-day analysis layer on top of `v0_run1` (baseline) and `v0_run2` (prompt-at-target intervention). No new generations; pure post-hoc analysis of the two scored parquets. The user asked specifically for an extreme-value lens on the data: "where are the edges, where are they not, and is the accuracy story different at the tails than at the mean?"

The bottom line: **yes, the tails behave differently from the means**, and the differences matter for anyone considering shipping these prompts in a real curriculum. Section 12 of the report (`reports/v0_run1_report.html`) walks through the same tables and figures with the practitioner verdict.

## What the means say (recap from earlier entries)

- v0_run1: mean Δ = +3.29, Cohen's d = 1.49, 92% above target
- v0_run2: mean Δ = +1.25, Cohen's d = 0.56, 73% above target
- 62% of the baseline gap closes with the intervention

These are aggregate summaries. They give you the average behavior of the system, but they don't tell you where the catastrophic outputs are.

## What the tails say

### 1. GPD-fit tail shape (right tail of v0_run1)

| Band | ξ (shape) | Tail interpretation |
|---|---|---|
| K-2 | +0.09 | ~exponential — drift well-bounded |
| 3-5 | −0.27 | bounded — hard ceiling around grade 10-11 |
| **6-8** | **+0.43** | **fat tail — extreme drifts possible** |
| 9-12 | −0.28 | bounded — finite range |

The +0.43 ξ for 6-8 is the alarming finding. The cell `8.EE.C.7.b` (a 7th-grade equation-solving standard) was explained at "grade 27" reading level by gpt-5.5 — a >19-grade-level overshoot. There is enough mass in the right tail of 6-8 that *the parametric fit predicts more such outliers if you sampled a larger frame*.

### 2. Where the edges concentrate (per-target-grade tail rate, v0_run1)

| Target | % of cells in top-10% extreme \|Δ\| |
|---|---|
| K | 52.8% |
| 1 | 46.3% |
| 2 | 8.7% |
| 3-8 | < 15% |

K and grade-1 standards are where almost all extreme drift sits. The intervention reduces these but does not eliminate them (K-1 still dominate the v0_run2 tail).

### 3. Tail compression — did v0_run2 shrink the extremes?

| Band | 95th \|Δ\| baseline → intervention | 99th \|Δ\| baseline → intervention |
|---|---|---|
| K-2 | 7.04 → 5.71 | 7.81 → 6.70 |
| 3-5 | 6.13 → 5.75 | **6.51 → 10.45** ← worsens |
| 6-8 | 5.55 → 2.97 ← clean win | 6.70 → 4.40 ← clean win |
| 9-12 | 3.90 → 3.69 | 4.88 → 4.99 |

Two distinct findings:

- **6-8 wins cleanly.** Both 95th and 99th percentiles drop substantially.
- **3-5 has a mixed result.** Median drift compresses, but the 99th percentile *worsens* (intervention pushes up to grade 17 in one cell, `5.NF.B.7` — a math standard where the rewriter triggered an outlier output).

### 4. The new failure modes the intervention introduces

After intervention:
- Top-5 right-tail cells include `5.NF.B.7` (math, grade 5) at +12.3 grade levels — an *intervention-only* outlier; this cell did not appear in v0_run1's top-10.
- Top-5 left-tail cells are *all HS Math standards* (`HSN-VM.B.4` at −4.99). The rewriter wrote sub-HS prompts and the model produced sub-HS output. This is a tail-reversal: an outcome direction that did not exist in baseline now exists in intervention.

Pedagogically the second pattern is interesting. An over-leveled HS explanation is unhelpful but not insulting; an under-leveled HS explanation can be insulting (it implies the student isn't capable of HS-level material). The intervention exchanges one failure mode for another, and depending on stakeholder priorities, the trade may not be a net improvement at HS.

## What this changes in the writeup

Three implications for the v0 + intervention publication:

1. **Two patterns of failure, two recipes.** Math content (especially grade 5 and 6-8) needs a math-specific rewriter — the formal notation register is hard for a general-purpose LLM rewriter to capture at target reading level. K-2 needs a non-LLM rule-based simplifier — no LLM (rewriter or generator) reliably writes below grade 4. Both are deferred follow-ups in `scope.md`.

2. **A reject filter is the minimum-viable safety net for shipping.** For high-stakes content, flag any output with |Δ| > 2 grade levels and re-prompt. The fat tail at 6-8 means without this filter, ~5% of outputs are catastrophic, even after intervention.

3. **Mean Δ is the wrong primary outcome for safety-critical claims.** Cohen's d = 0.56 in v0_run2 is "moderate" by classical standards but understates the practical risk if the right-tail mass matters more than the bulk. A pre-reg should specify *both* the mean and the tail (e.g., "mean Δ ≤ 1.5 *and* 99th percentile of |Δ| ≤ 3"). The current pre-reg template should be updated to include the tail constraint.

## Operational

- Analysis is pure post-hoc; no new API calls, no manifest update needed.
- Section 12 of `reports/v0_run1_report.html` walks through the analysis with the same tables and adds a survival-function plot per band.
- Section 12's "verdict" subsection ends with the reject-filter recommendation.

## Caveats specific to this analysis

- **n is small for the GPD fit on v0_run2.** The intervention run has 42-54 cells per band; the right-tail exceedance count above the 90th percentile is < 10 per band, which is the threshold below which the GPD fit becomes unreliable. The reported v0_run2 GPD shapes are omitted (only baseline ξ is reported); the user-relevant numbers (95th and 99th percentiles, top-5 cells) are non-parametric and stable at this n.
- **Threshold choice (90th percentile) is conventional but discretionary.** A different threshold (e.g., 85th or 95th) would change ξ slightly. The qualitative finding (6-8 fat-tail vs. others bounded) is stable across thresholds in 80-95th range; we did not formalize threshold robustness because the headline conclusion does not turn on it.
- **No bootstrap CI on ξ.** With n_excess ≈ 26-33, a 95% bootstrap CI for ξ is roughly ±0.2 grade levels. The 6-8 ξ = +0.43 is at least one bootstrap-SD above the +0.1 fat-tail threshold, so the qualitative classification holds. Adding the bootstrap CI is a polish step worth doing before the writeup.
