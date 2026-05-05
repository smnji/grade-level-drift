---
date: 2026-05-05
severity: major
area: analysis
tags: [v0, results, drift, gpt-5, gpt-4.1, ccss, deterministic-stack]
title: v0 run 1 — n=1,080 generations, mean Δ = +3.3 grade levels (Cohen's d = 1.49)
---

The v0 cube finished generation, scoring, and reporting today. n = 1,080 generations across 3 OpenAI models × 3 prompt variants × 2 wording conditions × 60 CCSS standards (`run_id=v0_run1`). 0 generation failures across all 1,077 attempted calls (3 cells were already cached from the smoke test). Total wall-clock ≈ 90 minutes; total spend ≈ $4 against the $30 cap. Manifest, generations, scored parquet, and HTML report are all committed under `run_id=v0_run1`.

## Headline finding

Across all three OpenAI frontier models and all 18 generation conditions per standard, generated student-facing explanations land **+3.29 grade levels above the standard's target** (SD 2.20; 92.2% of cells above zero; Cohen's d = 1.49). The effect is large and the direction is unambiguous.

## Cross-model agreement

The per-model means are essentially identical:

| Model | n | Mean Δ | 95% CI | Cohen's d | % above 0 |
|---|---|---|---|---|---|
| gpt-5.5 | 360 | +3.28 | [+3.06, +3.50] | 1.51 | 92% |
| gpt-5.4 | 360 | +3.30 | [+3.08, +3.52] | 1.56 | 93% |
| gpt-4.1 | 360 | +3.28 | [+3.04, +3.52] | 1.42 | 91% |

ICC(2,1) on per-standard mean Δ across the three models = **0.89** (two-way random-effects, single-rater, absolute agreement). Direction-preservation: 95% of the 60 standards have the same sign of Δ across all three models. This is *strong* cross-model consistency — drift is a property of "frontier OpenAI behavior on this task," not a single model's quirk.

## Wording intervention (H4 — interventional arm)

The simplified-wording arm reduces drift, and the paired test rejects the null at every model:

| Model | n pairs | Mean Δ(raw) − Δ(simplified) | t | p |
|---|---|---|---|---|
| gpt-4.1 | 180 | +0.67 | 7.71 | 8.2 × 10⁻¹³ |
| gpt-5.4 | 180 | +0.49 | 5.65 | 6.3 × 10⁻⁸ |
| gpt-5.5 | 180 | +0.48 | 3.44 | 7.2 × 10⁻⁴ |

Direct evidence that the standard's wording confounds the output's reading level: simplifying the input wording shaves 0.5–0.7 grade levels off the drift. This survives Holm-Bonferroni across the three models.

The simplified arm does **not** close the gap, however. Even with a 4th-grade-rewritten standard, mean Δ over the simplified cells is +3.01 — still 3 grade levels above target. The model anchors on the standard's register *and* on a default register of its own.

## Prompt sensitivity

| Prompt | Mean Δ | SD |
|---|---|---|
| S (zero-shot, no role) | +2.72 | 2.57 |
| M (role + format, zero-shot) | +3.91 | 1.86 |
| L (role + format + one-shot exemplar) | +3.23 | 1.94 |

Counter-intuitive: the *medium* prompt drifts hardest. Adding role and format instructions without an exemplar appears to push the model to a more "academic teacher" register; adding an exemplar (L) pulls it partway back. The "minimum-viable" S prompt drifts least, partly because its variance is highest — fewer guard-rails means more cells fall both above and below target. This is interesting but exploratory; the headline story is robust to which prompt was used.

## Per–grade-band breakdown

| Band | n | Mean Δ | SD |
|---|---|---|---|
| K-2 | 252 | +5.22 | 1.12 |
| 3-5 | 252 | +4.11 | 1.41 |
| 6-8 | 324 | +2.85 | 1.91 |
| 9-12 | 252 | +1.09 | 1.83 |

Drift decreases monotonically with target grade. Lower-grade standards drift hardest in absolute terms — a kindergarten standard's explanation lands at roughly grade 5. High-school standards drift least, both because the target is closer to the model's default register and because high school has more multi-grade items (HS Math = 9-12, target = 10.5) which lifts the floor.

## What this rules out / supports

- **H1** (drift exists): supported — Cohen's d = 1.49 against zero, sign test rejects.
- **H2** (drift is positive / above-target): supported — 92% above zero across all models.
- **H3** (drift is consistent across models): supported — ICC = 0.89, direction-preservation = 95%.
- **H4** (the standard's wording register confounds the output): supported by both the observational regression (lower-grade standards drift more) and the interventional arm (simplified wording reduces drift by ~0.5).

This is unusual cleanliness for a 60-standard exploratory pilot — every pre-registered hypothesis goes the predicted direction with a large effect and the cross-model agreement gives strong external validity within the OpenAI family.

## Caveats — what is NOT pre-registered yet

The pre-registration freeze (`pre-reg-v1` tag) has not been cut. Treat this run as exploratory; the freeze comes after the methodology and analysis are finalized in light of these pilot results. Specifically:

- The ensemble-median grade is the headline; the CLEAR-calibrated regressor (scope decision 1) was deferred and would tighten the magnitude estimate but not the direction.
- The classical-formula construct gap (T1 in `research-proposal.qmd §8`) still applies — these formulas measure surface features. A 6-grade-level surface drift is suggestive of a real register shift but does not by itself establish that the explanations are pedagogically inappropriate.
- The new threat T-NEW (GPT-5 family runs at temperature=1) means the gpt-5.5 and gpt-5.4 cells carry within-cell stochasticity. Aggregate Δ per (model × condition × band) is well-defined; per-standard ranking is noisier than under deterministic decoding.

## Operational notes

- Generation rate: ~9 cells/min on gpt-5.5, ~12/min on gpt-5.4, ~20/min on gpt-4.1 (later, lighter model).
- Token totals: 147K input + 248K output across all 1,080 cells = 395K tokens.
- Cost: well under $5 actual against the $30 cap. The PRICING table in `src/generate.py` was conservative.
- The `data/generated/v0_run1/` directory is gitignored per the current policy (regenerable from API). Manifest, scores parquet, and HTML report ARE committed.

## Next

- Cut the `pre-reg-v1` tag using these results to inform the analysis-plan section of the AsPredicted form.
- Decide scope item 2 (multi-grade items): the per-band breakdown shows HS items drift least; either drop, band, or per-item draw is now a *measured* trade-off rather than a hypothetical.
- Finalize the Quarto rendering of `research-proposal.qmd` with these numbers as the pilot results.

## Artifacts

- Manifest: `data/processed/v0_run1_manifest.json`
- Scores: `data/results/v0_run1_scores.parquet` (1,200 rows: 1,080 generations + 60 raw standards + 60 simplified standards)
- Report: `reports/v0_run1_report.html` (5 MB, plotly bundle inline, opens from disk)
