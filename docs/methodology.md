# Methodology — Operational Pipeline

**Status:** draft, paired with `scope.md` and `research-proposal.md`
**Last updated:** 2026-05-04

This is the operational spec — the canonical reference for *how the pipeline runs*. The research proposal's Methodology section summarizes and cross-references this document; this is the source of truth.

---

## Pipeline overview

```
[LC: standard text]
       │
       ▼
[Prompt template]
       │
       ▼
[LLM: instruction text]
       │
       ▼
[LC Evaluators × 5]
       │
       ▼
[Per-output scores]
       │
       ▼
[Aggregation + drift analysis]
```

Every artifact produced at every stage is logged with a `run_id`, the timestamp, and the manifest of inputs (model IDs, prompt-template hash, evaluator versions, random seed, dataset snapshot date).

---

## 1. Sampling

- **Source:** LC Knowledge Graph REST API for v0 pilot; switch to local JSONL exports before publication freeze for reproducibility.
- **Frame:** records where `statementType = "Standard"`. Excludes domains, clusters, and cluster headings.
- **Strata:** (grade band) × (subject) × (jurisdiction). Equal allocation per cell.
- **Seed:** the random seed and full sampled `caseIdentifierUUID` list are committed under `data/processed/sample_v{N}.json`.

Why stratified: the central question is whether drift varies *by grade*, so grade band must be balanced. Subject and jurisdiction are added strata to catch interaction effects that an unstratified random sample would underpower.

## 2. Prompt template

The template is single-version-pinned per run; the SHA of the template file is part of the run manifest.

```
You are explaining a K-12 academic standard to a student in grade {grade}.

Standard: {statementCode} — {description}

Write a clear, accurate explanation of what this standard means and what
students should be able to do, written at a reading level appropriate for
grade {grade}. Aim for {length_low}–{length_high} words. Do not include
worked examples or practice problems.
```

- `{length_low}, {length_high}` follow the band-tiered length proposal in `scope.md`.
- No exemplars (zero-shot only) for v0 — adding few-shot is a Q5/Q6 mechanism check, deferred.
- Standard wording is fed verbatim from the LC API (no normalization).

## 3. Generation

- **Model:** Claude — exact model ID and version pinned in `data/processed/run_manifest.json`.
- **Temperature:** 0 for primary runs (deterministic). A separate variability run at temperature 0.7 with N=5 samples per standard characterizes within-model variance.
- **Decoding params:** `top_p`, `max_tokens`, stop sequences — all logged.
- **Storage:** raw outputs at `data/generated/{run_id}/{standard_id}.txt`. Outputs are write-once; overwriting requires a new `run_id`.

## 4. Evaluation

Every output is scored by all five LC literacy evaluators:

| Evaluator | What it returns | Drift signal |
|---|---|---|
| Grade Level Appropriateness | Predicted grade level for the text | **Primary outcome** — `predicted_grade − target_grade` |
| Sentence Structure | SAP-rubric ordinal score (slightly → exceedingly complex) | Decomposes drift into syntactic complexity contribution |
| Vocabulary | SAP-rubric ordinal score | Decomposes drift into lexical contribution |
| Conventionality | Quality flag | QC: filters degenerate/off-topic outputs from analysis |
| Subject Matter Knowledge | Accuracy score | Q8: reading-level vs subject-matter decoupling |

- **Backend:** LC's evaluators delegate to OpenAI and Gemini (LLM-as-judge). Both API keys must be set.
- **Determinism:** evaluators are not deterministic across runs — every score is logged with the evaluator version, the backend model ID, and the timestamp.
- **Test-retest:** for a 10-standard subset, evaluators are run 3× to characterize within-evaluator variance. This is the noise floor against which drift is measured.

## 5. Analysis

### Primary

- **Outcome variable:** `Δ = predicted_grade − target_grade` (signed grade-level deviation).
- **Per-band aggregation:** mean and 95% CI of Δ within each grade band.
- **Effect size:** Cohen's d for the deviation against zero.
- **Direction test:** sign test on Δ to detect systematic over- or under-shoot.

### Secondary

- **Per-standard drift:** standards with mean Δ exceeding ±1 grade level are flagged for the "reliably above-grade" analysis (Q3).
- **Cross-model agreement (when 2nd model added):** intraclass correlation (ICC) and Pearson r of Δ across models.
- **Mechanism (deferred to follow-up):** mirror the analysis with the standard's own predicted grade level as a covariate (Q4); rerun with prompt variants (Q6).

### Cuts

- Grade band, subject, jurisdiction — primary cuts.
- Standard length, vocabulary density of the standard text — exploratory.

### Multiple-comparison policy

Pre-registered cuts above use Holm–Bonferroni correction. Any post-hoc cut is reported as exploratory in the writeup.

## 6. Reproducibility artifact

For every published study, the following is committed (or released alongside):

- `data/processed/sample_v{N}.json` — sample frame and seed.
- `data/processed/run_manifest.json` — model IDs, prompt-template SHA, evaluator versions, dataset snapshot date.
- `data/generated/{run_id}/` — raw LLM outputs (CC BY 4.0).
- `data/results/{run_id}_scores.parquet` — per-output evaluator scores.
- `notebooks/{run_id}_analysis.ipynb` — analysis driver.

API keys are never committed; all secrets in `.env` (gitignored).

## Limitations and threats to validity

A full treatment is in `research-proposal.md`. Headline threats:

- **Judge-generator family overlap.** If an evaluator's backend shares a base model with the instruction-generator, scores may be biased by self-preference.
- **Single-instrument dependence.** All reading-level conclusions ride on LC's Grade Level Appropriateness Evaluator; if its calibration is off, all our deltas inherit the error. Mitigation: convergent-validity check against Flesch-Kincaid + Lexile-API on a sub-sample.
- **Output-type artifact.** Findings only generalize to the pinned 100–250-word explanation format; other formats (lessons, worked examples) may behave differently.
- **Standards-text confound.** A standard whose own wording is at grade 11 (e.g. "Apply concepts of statistical variability...") may push the model up regardless of the target grade — a Q4 mechanism question we cannot fully isolate in v0.
