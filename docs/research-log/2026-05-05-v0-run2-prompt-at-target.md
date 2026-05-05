---
date: 2026-05-05
severity: major
area: analysis
tags: [v0, results, intervention, prompt-engineering, drift, gpt-5, gpt-4.1]
title: v0_run2 — rewriting the whole prompt at target grade closes 62% of the +3.3 grade-level gap
---

Same-day follow-up to [`2026-05-05-v0-run1-results.md`](2026-05-05-v0-run1-results.md). The reframe in v0_run1's report section 3a observed that prompt mean − target = +3.19 grade levels and output mean − target = +3.29 grade levels — implying that ~all of the headline drift might be a property of the prompt rather than the model. The natural intervention is to rewrite the *entire* prompt — scaffolding, standard wording, grade specifier — at the standard's own target grade, and re-run the cube. The user explicitly raised this and asked for the experiment.

This entry records that follow-up run. **The deferred intervention from `scope.md` "Out of scope (explicit)" was performed in-scope today** — see "Why we ran it now" below.

## Design

| Knob | v0_run1 (baseline) | v0_run2 (intervention) |
|---|---|---|
| Standards | 60 (CCSS, drawn 2026-05-04) | same 60 |
| Models | gpt-5.5, gpt-5.4, gpt-4.1 | same 3 |
| Prompt templates | S, M, L | S only (the at-target rewrite *is* the prompt) |
| Wording conditions | raw, simplified | at_target (whole prompt rewritten at standard's target grade) |
| Cells | 60 × 3 × 3 × 2 = 1,080 | 60 × 3 × 1 × 1 = 180 |
| Rewriter | gpt-4.1 (rewrites standard's *description* only at ~grade 4) | gpt-4.1 (rewrites *whole prompt* at standard's *own* target grade, with textstat verification + retry) |
| Cost | ≈ $4 | ≈ $1 |

The new rewriter (`src/rewrite_target.py`) drafts a self-contained student-facing prompt at the standard's target grade, scores it with the deterministic stack, and retries up to 3 times with a stricter instruction if the rewrite drifted by > ±1.5 grade levels. The chosen rewrite per standard is the closest of the up-to-3 attempts.

A new wording condition `at_target` was added to `src/generate.py`: in this condition the cached rewritten prompt is sent to the model directly, bypassing the S/M/L templates entirely.

## Headline result

| | v0_run1 (baseline) | v0_run2 (intervention) |
|---|---|---|
| n cells | 1,080 | 180 |
| **Mean Δ** | **+3.29** | **+1.25** |
| SD Δ | 2.20 | 2.23 |
| Cohen's d | 1.49 | 0.56 |
| % above target | 92% | 73% |

**Mean Δ dropped from +3.29 to +1.25 — a 2.04-grade-level reduction (62% of the baseline gap).** Cohen's d fell from "very large" (1.49) to "moderate" (0.56). The fraction of cells above target dropped from 92% to 73%.

Paired t-test (v0_run1 [S, raw] vs v0_run2 [S, at_target] on the same 60 standards × 3 models, n=171 pairs after dropping incomplete cells): mean reduction = +1.87 grade levels, t = 9.13, p = 2.0 × 10⁻¹⁶. The intervention effect is rock-solid by every conventional standard.

## Per model

| Model | v0_run1 Δ | v0_run2 Δ | Reduction |
|---|---|---|---|
| gpt-5.5 | +3.28 | +0.77 | -2.51 |
| gpt-5.4 | +3.30 | +1.58 | -1.72 |
| gpt-4.1 | +3.28 | +1.35 | -1.93 |

gpt-5.5 — the model with the most reasoning capacity — closes the gap most (down to within +0.77 of target). All three models converge near target.

## Per grade band — where does the intervention work, and where does it overshoot?

| Band | v0_run1 Δ | v0_run2 Δ | Reduction |
|---|---|---|---|
| K-2 | +5.22 | +3.10 | -2.12 |
| 3-5 | +4.11 | +2.03 | -2.08 |
| 6-8 | +2.85 | +1.02 | -1.83 |
| 9-12 | +1.09 | **−0.85** | -1.94 |

Notable:

- **K-2 still drifts +3.1 grade levels** even after the intervention. Reason: the rewriter (gpt-4.1) cannot *itself* write at K-2 reading level. Its output for K-2 targets caps around grade 4 (the same central-tendency issue we documented for the generator). The model dutifully matches that grade-4 prompt, producing grade-4-ish output — too hard for K-2.
- **9-12 now undershoots by 0.85 grade levels.** When the rewriter writes a HS-level prompt below adult register (e.g., grade 8 instead of grade 11), the model produces output below target. This is *direct* evidence that the model is responsive to the prompt's reading level — when the prompt drops below target, output drops below target.

## Coupling — does the rewriter's drift predict the model's drift?

Pearson r(rewriter drift from target, model output Δ from target) = **0.58**. When the rewriter overshoots (or undershoots) target, the model's output overshoots (or undershoots) by a correlated amount. This is the cleanest single piece of evidence that the model is *responsive* to the prompt's reading level — what was ambiguous in v0_run1's r=0.30 (because all v0_run1 prompts were at adult register, leaving little prompt-level variance) becomes clear when prompt grade is varied across K-12.

## Interpretation — updated story

v0_run1 + v0_run2 together tell a 3-part story:

1. **The headline drift is real and large** (+3.3 grade levels in baseline, Cohen's d = 1.49).
2. **It is mostly inherited from prompt design, not generator capability** — when we rewrite the whole prompt at target, drift shrinks from +3.3 to +1.3, a 62% reduction. The model is responsive to the prompt's reading level (r = 0.58).
3. **The remaining ~+1.3 gap has two sources, both worth surfacing:**
   - **Rewriter limits.** The rewriter (gpt-4.1) itself drifts at the extremes — can't go below ~grade 4 for K-2 standards, can't go above ~grade 9 for HS standards. A better rewriter (or a non-LLM rule-based simplifier — currently deferred per scope.md §Wording conditions) is the next bottleneck.
   - **Cell-level variance.** SD = 2.23 in v0_run2; even with a perfectly on-target prompt, individual cells span several grade levels. Some of that is the model's residual default register reasserting itself.

Practitioner take: **most of the "AI can't generate at the right reading level" finding is actually "we don't write our prompts at the right reading level"** — which is fixable. But the fix is bottlenecked by *another* LLM's drift behavior, so the practical recipe is "rewrite your prompt manually at target grade" or "use a non-LLM simplifier like Lexile-tier text generators." The model itself is more capable of register control than the v0_run1 framing suggested.

## Why we ran it now (rather than waiting for a separate publication)

Originally deferred to a follow-up study after the pre-reg freeze (per `docs/scope.md` "Out of scope (explicit)" and the v0_run1 log entry's "Out of scope for v0" section). The user re-evaluated mid-session: without v0_run2, the v0_run1 finding's practical implication ("just rewrite your prompts") is unsubstantiated speculation. Running the 60 × 3 = 180-cell pilot took ~15 minutes wall-clock and ~$1 against the $5 cap, and the result reframes the whole writeup. The deferral was the wrong call given the cost ratio.

This entry, the new section in `reports/v0_run1_report.html`, and the v0_run2 manifest + scores parquet are the artifact of the corrected decision.

## Caveats specific to v0_run2

- **n is smaller** — 180 cells vs v0_run1's 1,080 — because we did not re-run the S/M/L × raw/simplified factors. The intervention contrast we care about (raw S vs at_target S) is well-powered (n=171 pairs, p ≈ 10⁻¹⁶), but the v0_run2 cube cannot be sliced as finely as v0_run1.
- **The rewriter's own drift is a confound** — we *think* the residual gap is partly the rewriter, but we can't separate "rewriter's drift" from "generator's residual register" without a non-drifting rewriter. A rule-based simplifier (deferred) would resolve it.
- **gpt-5.5 had 9 cells return empty text initially** — the at-target prompts pushed gpt-5.5 to spend its full 400-token budget on internal reasoning before producing output. Re-ran with `--max-tokens 1500` to recover; final n=180, 0 NaN. This is itself a small finding about gpt-5.5's reasoning behavior on register-controlled prompts and may belong as a footnote in the writeup.
- **at_target only ran the S template.** M and L templates would inject more scaffolding; the rewriter would have to compress more text at target grade. Probably worth a small follow-up if the writeup needs robustness across prompt sizes.

## Artifacts

- `data/processed/v0_run2_manifest.json`
- `data/results/v0_run2_scores.parquet` (660 rows: 180 generations + 360 prompts + 60 standard_raw + 60 standard_simplified)
- `data/interim/prompts_at_target/gpt-4.1/{standard_id}.json` × 60 (cached rewritten prompts with attempts log)
- `reports/v0_run1_report.html` — section 11 contains the v0_run2 comparison
- `src/rewrite_target.py` — the new rewriter
- `src/generate.py` — extended with `at_target` wording condition
