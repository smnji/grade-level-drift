# Methodology — Operational Pipeline

**Status:** v0 design ratified 2026-05-04 (post deterministic pivot)
**Last updated:** 2026-05-04

This is the operational spec — the canonical reference for *how the pipeline runs*. The research proposal's Methodology section summarizes and cross-references this document; this is the source of truth.

---

## Pipeline overview

```
[LC: standard text]                                  [Standard text]
       │                                                    │
       ▼                                                    ▼
[Snapshot to data/raw/]                  ┌──── (raw wording) │
       │                                 │                   │
       ▼                                 │                   ▼
[Parent sample n=200]                    │       [Rewriter LLM call] ──► (simplified wording)
       │                                 │                   │
       ▼                                 │                   │
[v0 sub-sample n=60]                     │                   │
       │                                 ▼                   │
       └─────────────► [Generator LLM call: 3 models × 3 prompts × 2 wordings]
                                                   │
                                                   ▼
                                         [Output: 100-250 word explanation]
                                                   │
                                                   ▼
                                  [Deterministic scoring stack]
                                  textstat + AWL/NGSL + spaCy + CLEAR-calibrated
                                                   │
                                                   ▼
                                       [Per-output scores]
                                                   │
                                                   ▼
                                    [Aggregation + drift analysis]
                                                   │
                                                   ▼
                                       [Interactive HTML report]
```

Every artifact at every stage is logged with a `run_id`, the timestamp, and a manifest of inputs (model IDs, prompt-template SHAs, rewriter model + prompt, evaluator stack version, random seeds, dataset snapshot date, parent-sample SHA).

---

## 1. Sampling

### Source

LC Knowledge Graph REST API (cursor-paginated). The client is wrapped in [`src/lc_client.py`](../src/lc_client.py); raw snapshots land in `data/raw/lc/{YYYY-MM-DD}/` with sibling `*.provenance.json` files. The full study will switch to local JSONL exports for full reproducibility.

### Frame

Records where `normalizedStatementType == "Standard"`. This is the leaf-learning-expectation set in CASE-format frameworks; it includes `statementType` values `Standard`, `Component`, and `Content Standard`, and excludes the organizational `Standard Grouping` rows (Strands, Domains, Clusters, Conceptual Categories, Grade-Level headers).

### Parent sample (drawn 2026-05-04)

- Jurisdiction: Multi-State Common Core only (ELA framework `c64961be-…`, Math framework `c6496676-…`).
- n = 100 per subject (200 total), simple random, seed `20260504`.
- Eligible population at draw: 1100 ELA + 597 Math.
- Implementation: `python -m src.snapshot && python -m src.sample`.
- Frozen artifact: [`data/processed/pilot_v1_sample.json`](../data/processed/pilot_v1_sample.json). Self-contained — every item carries its identifier, statement code, grade level, description, and source provenance.

### v0 sub-sample (the actual run)

- n = 30 per subject (60 total), drawn as a deterministic random subset of the parent sample. Seed `20260504`.
- Implementation: `python -m src.sub_sample`.
- Frozen artifact: [`data/processed/v0_subpilot_sample.json`](../data/processed/v0_subpilot_sample.json).
- Why subset, not re-sample: keeps the parent sample as a reusable resource for follow-up runs without re-running snapshots.

### Caveat: HS grade tagging

CCSS HS Math standards carry `gradeLevel = ["9","10","11","12"]` and HS ELA pairs grades (9-10, 11-12) by design. v0 preserves these multi-grade items as drawn; for per-grade analysis we will either (a) drop multi-grade items, (b) treat HS as a single band, or (c) draw a target grade per item. Decision deferred; documented in [`scope.md`](scope.md) "Decisions still open" #2.

## 2. Wording conditions and rewriter

Each standard enters the generation step under two wording conditions:

| Condition | Source |
|---|---|
| **Raw** | Standard description verbatim from the LC API |
| **Simplified** | Standard rewritten by an LLM to ~4th-grade reading level, preserving the learning expectation |

### Rewriter spec

- **Model:** single fixed OpenAI model (logged in run manifest). Same model across all rewrites.
- **Prompt (frozen, SHA-pinned):**
  ```
  Rewrite the following K-12 academic standard so a 4th-grade reader can
  understand it. Preserve the learning expectation exactly — do not change
  what the student is asked to know or do. Simplify only the language:
  shorter sentences, more familiar vocabulary, no jargon. Keep the result
  to 1-3 sentences.

  Standard: {description}
  ```
- **Temperature:** 0 (deterministic).
- **Caching:** each rewrite is computed once per standard, stored at `data/interim/rewrites/{rewriter_model}/{standard_id}.json`, and re-used across all generation cells.
- **Self-measurement:** every rewrite is scored by the same deterministic stack used downstream. The rewriter-induced reading level is a measured covariate, not assumed.

### Why the simplified arm exists

It's an interventional check on H4 ("the model partially mirrors the standard's own register"). If raw and simplified wordings produce different drift signals, that's direct evidence the standard's wording confounds the output's reading level. Without the manipulation, H4 is observational only.

## 3. Prompt template variants

Three variants per generation, varying input token budget systematically:

### S (short, ~50 input tokens, zero-shot, no role)

```
Standard ({grade}): {description}

Explain this to a grade {grade} student in 100-250 words.
```

### M (medium, ~150 input tokens, role + format, zero-shot)

```
You are a teacher writing a short student-facing explanation of a K-12 academic standard.

Standard: {statement_code} (grade {grade})
Description: {description}

Write 100-250 words explaining what this standard means and what the student
is expected to learn. Write at a reading level appropriate for grade {grade}.
Do not include worked examples, problem sets, or follow-up questions.
```

### L (long, ~400 input tokens, role + format + one-shot exemplar)

```
You are a teacher writing a short student-facing explanation of a K-12 academic standard.

Example —
Standard: K.CC.A.1 (grade K)
Description: Count to 100 by ones and by tens.
Explanation: We are learning to count up to 100. We can count one at a time:
1, 2, 3, 4, 5, all the way up to 100. We can also count by tens, jumping ten
numbers at a time: 10, 20, 30, 40, 50, 60, 70, 80, 90, 100. Counting helps us
know how many things there are.

Now write the same kind of explanation for this standard:

Standard: {statement_code} (grade {grade})
Description: {description}

Write 100-250 words. Write at a reading level appropriate for grade {grade}.
Do not include worked examples or follow-up questions.
```

### Notes

- Each template's exact text is captured at run time; the SHA of each is part of the run manifest.
- For multi-grade items (HS Math, HS ELA pairs), `{grade}` is rendered as the grade range (e.g., "9-10" or "9-12"); models receive the same range a real curriculum author would.
- The S/M/L distinction is *prompt-engineering effort* as a controlled experimental variable, not "did we try harder." All three are reasonable choices a real user would make.

## 4. Generation conditions

| Variable | Levels |
|---|---|
| **Models** | `gpt-5.5`, `gpt-5.4`, `gpt-4.1` (3 levels) |
| **Prompt variant** | S, M, L (3 levels) |
| **Wording** | raw, simplified (2 levels) |
| **Standards** | 60 (30 ELA + 30 Math from sub-sample) |

**Total v0 generations:** 3 × 3 × 2 × 60 = **1,080 generations**.

### Generator spec

- **Temperature:** 0 (deterministic). Within-model variance is not a v0 question; can be added later by sweeping temperature on a subset.
- **max_tokens:** 400 (covers 100-250 word target with margin; logged per call).
- **Storage:** raw outputs at `data/generated/{run_id}/{cell_key}.json`. The cell key is `{model}__{prompt}__{wording}__{standard_id}`.
- **Output schema:** the response text, OpenAI usage block (prompt_tokens, completion_tokens, total_tokens), the model ID actually returned (in case OpenAI routes to a versioned variant), the prompt SHA, the wording-condition SHA, the system fingerprint when present, and the wall-clock timestamp.

## 5. Evaluation (deterministic stack — no LLM-as-judge)

Every output is scored by a fully deterministic, open-source stack. No API calls past generation.

### 5.1 Reading level (headline ensemble)

Run via `textstat`:

| Formula | Source |
|---|---|
| Flesch-Kincaid Grade Level | Kincaid et al., 1975 |
| SMOG Index | McLaughlin, 1969 |
| Coleman-Liau | Coleman & Liau, 1975 |
| Automated Readability Index (ARI) | Smith & Senter, 1967 |
| Gunning Fog | Gunning, 1952 |
| Dale-Chall | Dale & Chall, revised 1995 |
| New Dale-Chall | Chall & Dale extended |

**Ensemble grade equivalent:** median across the 7 formulas. Median is more robust than mean to formula-specific outliers (e.g., SMOG and F-K disagree systematically on technical text).

### 5.2 Reading level (calibrated)

Optional ridge-regression predictor trained on the [CLEAR corpus](https://github.com/scrosseye/CLEAR-Corpus) — 4,724 expert-rated passages with grade-level scores. Features = the rest of the deterministic stack (formulas + tier composition + syntactic complexity). Output: a single calibrated grade-level prediction per text.

### 5.3 Vocabulary tier

Word-list lookups (case-folded, lemmatized via spaCy):

| Feature | Definition |
|---|---|
| `pct_awl` | % of content tokens in Coxhead's Academic Word List (Tier-2 academic) |
| `pct_ngsl` | % in the New General Service List (Tier-1 general) |
| `pct_off_list` | % in neither (Tier-3 proxy: domain-specific or unknown) |
| `mean_word_length` | Mean characters per content word |
| `type_token_ratio` | Lexical diversity (unique tokens / total tokens) |

### 5.4 Syntactic complexity

Per-output features from the spaCy dependency parse:

| Feature | Definition |
|---|---|
| `mean_dep_depth` | Mean depth of token-to-root dependency path |
| `mean_t_unit_length` | Mean length (in tokens) of T-units (Lu's L2SCA construct) |
| `subord_clause_ratio` | Subordinate clauses per main clause |
| `passive_ratio` | Passive constructions per finite verb |
| `nominalization_ratio` | Nominalized verbs per noun |

### 5.5 Surface

`word_count`, `sentence_count`, `paragraph_count`, `prompt_tokens`, `completion_tokens`. Sanity checks; cost telemetry.

### 5.6 Determinism guarantees

- Every formula and feature is a pure function of the input text and the version-pinned tools (textstat version, spaCy model version, word-list SHAs).
- No random seeds in the scoring path.
- Re-running scoring on the same outputs produces byte-identical scores.

## 6. Analysis

### Primary

- **Outcome variable:** `Δ = ensemble_grade − target_grade` (signed grade-level deviation).
- **Per-band aggregation:** mean and 95% CI of Δ within each grade band, per model.
- **Effect size:** Cohen's d for the deviation against zero, per model and overall.
- **Direction test:** sign test on Δ to detect systematic over- or under-shoot.
- **Calibrated parallel:** the same analyses are repeated using `Δ_cal = predicted_cal − target_grade` from the CLEAR-trained ridge regressor; both reported.

### Cross-model (Q2 / H3 within v0)

- Pearson r and intraclass correlation (ICC) of Δ across the three OpenAI models, per standard.
- **Direction-preservation test:** does `sign(Δ_5.5) == sign(Δ_5.4) == sign(Δ_4.1)` per standard?
- Per-band model-comparison plot.

### Per-standard drift (Q3)

Standards with mean |Δ| > 1.0 across all (model × prompt × wording) cells are flagged as "reliably above-grade" (or below). Their statement-text features (own-text formulas + tier composition + syntactic complexity) are regressed on |Δ| as the H4 observational arm.

### Wording-intervention (Q4 / H4 interventional arm)

For each standard, compute Δ(raw) − Δ(simplified) per (model, prompt). A non-zero mean difference is direct evidence the input register confounds the output register. Paired test (within-standard); also report magnitude.

### Prompt-sensitivity (robustness)

For each (model, standard, wording), compute the spread of Δ across prompt variants S/M/L. A small spread = prompt-robust drift; a large spread = prompt-driven drift. Reported as a per-cell standard deviation and as a between-prompt ANOVA component.

### Cuts

Subject (ELA vs Math), grade band, model, prompt variant, wording condition. The 4-way interaction (grade-band × model × prompt × wording) is the headline analysis cube.

### Multiple-comparison policy

The pre-registered cuts above use Holm–Bonferroni correction. Any post-hoc cut is reported as exploratory in the writeup.

## 7. Reproducibility artifact

For every published v0 run, the following is committed (or released alongside):

- `data/processed/pilot_v1_sample.json` — parent sample (seed + identifiers).
- `data/processed/v0_subpilot_sample.json` — sub-sample.
- `data/interim/rewrites/{rewriter_model}/` — cached simplified wordings.
- `data/generated/{run_id}/` — raw model outputs, one JSON per cell.
- `data/results/{run_id}_scores.parquet` — per-output deterministic-stack scores.
- `data/processed/{run_id}_manifest.json` — model IDs, prompt SHAs, rewriter spec, scoring stack version, dataset snapshot date, seed.
- `reports/{run_id}_report.html` — interactive HTML report (plotly).

Anyone with `OPENAI_API_KEY` (the only key needed) and the public CLEAR corpus can reproduce end-to-end by re-running:

```
python -m src.snapshot
python -m src.sample
python -m src.sub_sample
python -m src.rewrite
python -m src.generate
python -m src.score
python -m src.report
```

API keys are never committed; all secrets in `.env` (gitignored from line 1 of `.gitignore`).

## 8. Limitations and threats to validity

A full treatment with mitigations is in [`research-proposal.qmd`](research-proposal.qmd) §8. Headline threats specific to the deterministic stack:

- **Classical-formula limitations.** Flesch-Kincaid et al. measure surface features (syllables, sentence length); they do not capture register, abstraction, or knowledge demands. v0 is explicitly scoped to reading level only (Q1-Q3); the qualitative dimensions are deferred Q5 territory.
- **Ensemble correlation.** The 7 formulas are not independent — they share inputs (syllable counts, sentence length, word lists). The median across the ensemble is robust to formula-specific outliers but does not eliminate shared bias. Mitigation: report each formula's individual prediction alongside the ensemble.
- **Rewriter-induced register confound.** The simplified wording is produced by an LLM, which has its own register. Mitigation: the comparison of interest is *within-standard* (raw vs simplified), where the rewriter affects both arms similarly; the rewriter output is also scored by the same deterministic stack so we know what reading level we actually achieved.
- **Output-type artifact.** Findings only generalize to the pinned 100–250-word explanation format; other formats (lessons, worked examples) may behave differently.
- **Standards-text confound.** A standard whose own wording is at grade 11 may push the model up regardless of the target grade. v0 addresses this with both the observational H4 arm (regress drift on standard's own grade) and the interventional H4 arm (raw vs simplified wording).
