---
date: 2026-05-04
severity: moderate
area: methodology
tags: [pilot, sampling, scope, common-core, ccss]
title: Pilot sampling plan — CC-only, n=100 random per subject, normalizedStatementType filter
---

Drew the pilot sample today. This entry captures the methodology decisions that shaped the draw and the composition observations from the resulting sample. Companion infrastructure entry: [LC cursor pagination fix](2026-05-04-lc-cursor-pagination.md), which surfaced the true universe size and made the sampling decision meaningful.

## Decisions

### 1. Jurisdiction: Multi-State Common Core only (pilot scope)

**Decision.** The pilot draws from CCSS ELA + CCSS Math exclusively. State-specific frameworks (CA, TX, FL, MA, VA candidates) are deferred to the full study.

**Rationale.** The pilot's job is pipeline debugging, prompt-template calibration, and surfacing evaluator behavior — not measuring jurisdiction variance. Stripping jurisdiction reduces a degree of freedom while we work out the rest of the stack. State frameworks come back in for the full study, where the pre-registered analysis explicitly tests for cross-jurisdiction drift.

**scope.md change.** "Jurisdictions" section now distinguishes Pilot (CC-only) from Full study (CC + 3-5 states). Open question #1 (state list) and #4 (jurisdiction stratification) marked as deferred to full study.

### 2. Sample size: n = 100 per subject, simple random

**Decision.** 200 total standards (100 ELA + 100 Math), simple random sample, seed `20260504`.

**Rationale.** Initial scope.md proposal was n=30 (5/band) with stratification — too small to surface evaluator behavior across grade-bands, but stratified to control for grade. Revised proposal trades stratification for size: n=100 per subject is large enough that the (uniformly random) draw will hit every K-12 grade group with non-trivial counts, and small enough that the LLM-generation + evaluator API budget for the pilot stays bounded. Stratification stays the design for the full study; the pilot is explicitly *not* powered for inferential claims.

**Tradeoff acknowledged.** Random sampling can under-represent grade bands with fewer items in the population. K-2 has fewer eligible standards than the upper grades; the resulting sample reflects population proportions, not equal-per-band coverage. This is acceptable for pipeline debugging and a known difference from the full-study design.

### 3. Population frame: `normalizedStatementType == "Standard"`

**Decision.** Sample from items where `normalizedStatementType == "Standard"`, not the narrower `statementType == "Standard"`.

**Rationale.** CASE-format frameworks distinguish:
- `normalizedStatementType == "Standard"` (1100 ELA, 597 Math) — leaf learning expectations, regardless of how the source framework labels them. Includes `Standard`, `Component`, and `Content Standard` rows.
- `normalizedStatementType == "Standard Grouping"` (362 ELA, 226 Math) — Strands, Domains, Clusters, Conceptual Categories, Grade-Level headers. Organizational, not learning expectations.

A "100-250 word student-facing explanation" is a coherent task only for a leaf learning expectation. Sampling from groupings would yield items like "Reading Standards for Literature, Grade 3" with no concrete learning to explain. The narrower `statementType == "Standard"` (393 in Math) drops the `Component` rows, which *are* leaf expectations (e.g., `4.NF.B.4.b` — "Understand a multiple of $\\frac{a}{b}$ as a multiple of $\\frac{1}{b}$..."). So `normalizedStatementType` is the cleaner cut.

**methodology.md change.** §1 frame definition updated.

## Sample composition (informational)

n = 100 per subject (200 total), drawn from `data/raw/lc/2026-05-04/` (snapshots taken same day):

| Subject | Pop after filter | Drawn | Per-grade distribution |
|---|---|---|---|
| ELA | 1100 | 100 | K(4), 1(10), 2(8), 3(7), 4(8), 5(4), 6(9), 7(17), 8(8); HS pairs: 9-10(13), 11-12(10); cross-grade anchors (K-12): 2 |
| Math | 597 | 100 | K(6), 1(3), 2(3), 3(7), 4(12), 5(7), 6(11), 7(8), 8(7); HS (9-12 spanning): 36 |

### Notable structural features (CCSS design, not data quirks)

- **CCSS ELA pairs HS grades.** Reading/Writing/Speaking standards are tagged `["9","10"]` or `["11","12"]` rather than as four single-grade items. This is built into the framework — CCSS authors deliberately pace HS literacy growth over two-year bands.
- **CCSS HS Math has no single-grade tagging.** HS standards carry `gradeLevel = ["9","10","11","12"]` because CCSS leaves HS course sequencing to states. This is the source of the 36 multi-grade Math items in the pilot.
- **Cross-grade ELA anchors.** Two ELA items in the sample have all 13 grades attached. These are likely Speaking & Listening anchor standards or College and Career Readiness anchors.

### Open thread: per-grade analysis with multi-grade items

For Grade Level Appropriateness as the primary outcome, we need a *target grade* per item to compute `Δ = predicted_grade − target_grade`. Multi-grade items don't have a single target. Three handling options for the full study:

- **(a) Drop multi-grade items** from the per-grade analysis. Simple, but loses ~40% of the Math sample at the analysis stage if applied to the pilot.
- **(b) Treat as a band** (e.g., HS = a single bucket). Preserves items but blurs grade-level resolution at HS.
- **(c) Per-item target-grade draw.** For each multi-grade item, randomly pick one of its grades as the target. Preserves resolution at the cost of injecting variance.

Decision deferred to the full-study methodology pass. The pilot will run on all 200 items as drawn; we'll see how the evaluator behaves on multi-grade items as part of pipeline debugging. Captured as scope.md open question #5.

## Artifact

[`data/processed/pilot_v1_sample.json`](../../data/processed/pilot_v1_sample.json) — 200 items, self-contained (each item has identifier, statement code, grade level, description, jurisdiction, source provenance). Re-runnable: `python -m src.snapshot && python -m src.sample`. The sample is committed; the raw snapshots it derives from are gitignored but reconstructable from the LC API given the framework UUIDs and snapshot SHA256 (which is in the manifest).

## Why this is a research-log entry, not an ADR

These decisions are reversible: re-sampling with a different population filter, different seed, or different jurisdiction scope is a five-minute re-run. The full-study sample design — when it gets pre-registered — *will* be ADR-worthy because the pre-reg freeze locks it in. The pilot sample is exploratory by design.
