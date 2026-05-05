---
date: 2026-05-04
severity: major
area: methodology
tags: [evaluators, deterministic, no-llm-judge, design-pivot, openai, rewriter, prompts]
title: Deterministic-evaluator pivot — drop LLM-as-judge; multi-model + multi-prompt + wording design
---

Significant methodological pivot today, late in the pre-pilot setup. The v0 design was substantially restructured before the first generation call. Capturing the chain of decisions and the rationale here so the design rationale is auditable.

## What changed

| Dimension | Before | After |
|---|---|---|
| **Generator** | Claude Opus 4.7 (single model) | OpenAI ensemble: `gpt-5.5`, `gpt-5.4`, `gpt-4.1` (3 models, all run on every cell) |
| **Evaluators** | LC's 5 LLM-as-judge evaluators (Gemini + OpenAI backends) | Fully deterministic open-source stack: `textstat` 7-formula ensemble + Coxhead AWL + NGSL + Dale-Chall + spaCy syntactic complexity + optional CLEAR-calibrated regressor |
| **Sample size in v0** | n=200 (the parent sample) | Sub-sample n=60 (30 per subject) drawn from the parent sample |
| **Conditions per standard** | 1 (single model, single prompt, single wording) | 18 (3 models × 3 prompts × 2 wordings) |
| **Total generations in v0** | 200 | 1,080 |
| **Required API keys** | LC + OpenAI + Gemini | LC + OpenAI only |
| **H3 (cross-model)** | Deferred to publication-readiness step | Tested *within* v0, within OpenAI family |
| **H4 mechanism** | Observational only | Observational + interventional (raw vs simplified wording) |

## Decision chain (in order today)

### 1. Sub-pilot reduction (200 → 60)

The user introduced multi-condition design (multiple models, multiple prompts, wording manipulation). At the parent sample size of 200 standards × 18 cells = 3,600 generations, the API budget got large. Reducing to 30 per subject keeps subject parity, gives 1,080 generations, and stays in a reasonable cost envelope (~$15-25). The parent sample stays as a frozen artifact for follow-up runs.

### 2. Drop LLM-as-judge

While probing LC's evaluator repo to see which delegate to OpenAI vs Gemini (the user wanted to skip Gemini), I discovered:

- **Grade Level Appropriateness** (the *primary outcome*) uses `gemini-2.5-pro`.
- **Conventionality** and **Subject Matter Knowledge** use `gemini-3-flash-preview`.
- **Vocabulary** is mixed — uses Gemini for grades 3-4 and `gpt-4.1` for grades 5-12.
- Only **Sentence Structure** uses OpenAI (`gpt-4o`) cleanly.

So "OpenAI-only LC evaluators" does not exist as a coherent subset; the primary outcome itself depends on Gemini.

The user's pushback was deeper: they don't trust LLMs to *measure* reading level. This is methodologically defensible — LLM-as-judge has known instability and self-preference biases, and a study about LLM behavior measured by another LLM has obvious epistemic issues. The pivot to fully deterministic measurement is the right move.

### 3. Deterministic stack design

Once we're going deterministic, the question is *what to measure with*. The design landed on a layered stack:

- **Headline reading level:** median of 7 classical formulas (F-K, SMOG, Coleman-Liau, ARI, Gunning Fog, Dale-Chall, New Dale-Chall) via `textstat`. Median is more robust than mean to formula-specific outliers.
- **Calibrated reading level:** ridge regression trained on the [CLEAR corpus](https://github.com/scrosseye/CLEAR-Corpus) (the same expert-rated benchmark LC validated against — but open and re-trainable). Features = the rest of the deterministic stack.
- **Vocabulary tier:** Coxhead AWL + NGSL + Dale-Chall lookups → % AWL, % NGSL, % off-list, mean word length, type-token ratio.
- **Syntactic complexity:** spaCy dependency parse → mean dependency depth, T-unit length (L2SCA), subordinate-clause / passive / nominalization ratios.

This stack is fully reproducible offline. No LLM-as-judge anywhere in v0.

### 4. Multi-model design (3 OpenAI models in v0)

Instead of pinning one OpenAI model and replicating across families later, run all 3 OpenAI frontier models in v0 itself. Within-family cross-model comparison answers Q2 inside v0; cross-family replication (Claude, Gemini, open-weights) is the explicit follow-up. This is a tighter design — Q2 isn't deferred.

### 5. Three prompt variants (S/M/L by input token size)

Pinning a single prompt risks measuring "this specific prompt is bad" rather than "the model drifts." Three variants varying input token budget give a built-in robustness check:

- S (~50 tokens): minimal — standard text + grade target + length constraint
- M (~150 tokens): role context + format instructions, zero-shot
- L (~400 tokens): + 1 worked exemplar (one-shot)

If the drift signal is similar across S/M/L, the finding is prompt-robust. If wildly different, we have a prompt-sensitivity finding rather than a model finding.

### 6. Two wording conditions (raw vs simplified)

Interventional H4 check. Each standard is fed in two forms: raw CCSS wording, and a separate-LLM-rewritten "simplified" wording (~4th-grade reading level, preserving the learning expectation). If raw and simplified produce different drift signals on the *same standard*, we have direct evidence the input register confounds the output register.

Acknowledged confound: the rewriter is itself an LLM with its own register. Mitigation: (a) the comparison is *within-standard* (raw vs simplified) where the rewriter affects both arms similarly; (b) the rewriter output is scored by the same deterministic stack so we know what reading level it actually achieved.

## What this commits us to

- **Code:** new modules — `src/sub_sample.py`, `src/rewrite.py`, `src/generate.py`, `src/manifest.py`, `src/evaluators/` (textstat ensemble + AWL/NGSL lookup + spaCy syntax + optional CLEAR-calibrated predictor), `src/score.py`, `src/report.py`.
- **Deps:** add `textstat`, `spacy` (+ `en_core_web_sm`), `scikit-learn`, `plotly`, `pyarrow`. Drop `google-genai`. Keep `openai`.
- **Env:** only `OPENAI_API_KEY` (and `LC_API_KEY` for standards data). Removed `GOOGLE_API_KEY` and `ANTHROPIC_API_KEY` from `.env.example`.
- **Docs touched:** `scope.md`, `methodology.md`, `research-proposal.qmd`, `attribution.md`, `requirements.txt`, `.env.example`. All revised in the same commit pass as this entry.
- **Cost:** ~1,080 generations across 3 OpenAI models. Plus ~60 rewriter calls. Estimate $15-25 total. Bounded.
- **Reproducibility upgrade:** evaluation is now byte-deterministic. Anyone with `OPENAI_API_KEY` and the public CLEAR corpus can re-run end-to-end.

## What this leaves behind (deferred, not abandoned)

- **SAP-rubric qualitative dimensions** (register, abstraction, knowledge demands) that classical formulas cannot capture. These are deferred Q5 ("beyond reading level") territory in the [charter](../charter.md) — and we are not claiming them in v0.
- **Cross-family model replication** (Claude, Gemini, open-weights) — the v0 follow-up.
- **LC's evaluator suite** — a great instrument for a *qualitative* rubric study, but not the right instrument for a *deterministic, reproducible reading-level study*. We use them in some future investigation if the question shifts to qualitative complexity.

## Why this is a research-log entry, not an ADR

It's *severity: major* but the decisions remain reversible by code changes — we could re-introduce the LC evaluators on a future run by adding their prompts back. Once the AsPredicted pre-registration is filed (after v0 results are in), the design becomes ADR-worthy because the freeze locks it in. v0 is exploratory; the freeze is the next milestone.

## Why this is the right pivot, in one sentence

> v0 is *only* about reading level — and reading level has 50 years of validated, deterministic, open-source measurement infrastructure that does not require LLM-as-judge. Using LLM judges to measure LLM outputs is a methodological risk we don't need to take when the deterministic alternative is cleaner, cheaper, faster, and more reproducible.
