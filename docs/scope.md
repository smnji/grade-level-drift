# Scope — Decision Record

**Status:** v0 design ratified 2026-05-04 (post deterministic pivot); pre-registration freeze pending
**Last updated:** 2026-05-04

This document fixes the boundaries of the v0 study. Every methodology choice and data pull is checked back against it. Open questions at the bottom resolve before the pre-registration freeze.

## Dimensions to fix

1. Subjects
2. Jurisdictions / standards frameworks
3. Grade bands
4. Models (instruction generators)
5. Output type (what counts as "instruction")
6. Sample size and stratification
7. Prompt variants (input-token-size dimension)
8. Wording conditions (raw vs simplified standards)
9. Evaluators (deterministic stack)

---

## Subjects

**Proposal.** ELA + Math, both included from v0.

**Rationale.** Math has the deepest LC coverage (15+ states crosswalked) and the cleanest Common Core anchor; ELA is the substrate the deterministic readability formulas have the longest validation history on. Together they yield enough variance for cross-subject claims about drift.

**Open question.** Whether to add a third subject (Science, given NGSS structure) for triangulation in v1.

## Jurisdictions

**v0 (decided 2026-05-04).** Multi-State Common Core only — both subjects drawn from the CCSS frameworks (ELA UUID `c64961be-…`, Math UUID `c6496676-…`). State frameworks deferred until v0 results are in.

**Future-study proposal.** CCSS anchor + 3–5 representative state frameworks (mix of large/small, CC-adopter/non-adopter, geographic spread). Defer 50-state coverage to a later investigation.

**Rationale.** The headline finding is about LLM behavior given a standard, not state-level differences. A small jurisdiction set is enough to show whether drift varies by framework wording. CC-only for v0 strips the jurisdiction dimension entirely while we establish the pipeline; jurisdiction variance returns in a follow-up.

**Open question (deferred).** Confirm the 3–5 candidate states. Candidate set: California, Texas, Florida, Massachusetts, Virginia.

## Grade bands

**Proposal.** Full K-12. Findings reported by grade band (K-2, 3-5, 6-8, 9-12) wherever a band-level cut is informative.

**Rationale.** Drift may differ systematically by band; band-level reporting is cheap and adds explanatory power.

**Open question.** None.

## Models (instruction generators)

**v0 (decided 2026-05-04).** Three OpenAI frontier models, run on every (standard × prompt × wording) cell:

| Model | Why included |
|---|---|
| `gpt-5.5` | Newest frontier (April 2026 release); represents current state of the art |
| `gpt-5.4` | Stable frontier (~6 weeks older); within-family contrast against 5.5 |
| `gpt-4.1` | Code-favored specialist; broadly used; tests whether the drift pattern depends on the GPT-5 family vs the GPT-4 family |

**Rationale.** Within-family cross-model comparison answers Q2 ("is drift consistent across models?") inside v0 rather than deferring it to a follow-up. Three models is a tractable budget at the v0 sample size (n=30 sub-pilot), and it lets us state the finding as a property of the OpenAI frontier rather than of one model in isolation.

**Cross-family replication (Claude, Gemini, open-weights)** is deferred to a follow-up investigation, framed as "rather than re-running the entire pipeline for each model family in v0, replicate the interesting findings on other families later."

**Open question.** None for v0.

## Output type

**Proposal.** Short student-facing explanation: 100–250 words explaining the standard at the target grade level. No worked examples, no problem sets, no multi-turn dialog.

**Rationale.** Different output types (explanation vs lesson plan vs worked example) carry different default registers, which would confound the drift measurement. Pinning one output type isolates the question.

**Open question.** Whether to vary length by grade. Provisionally fixed at 100–250 across grades for v0; band-tiered length is a follow-up.

## Sample size and stratification

**Pilot sample (drawn 2026-05-04).** n = 100 per subject (200 total), simple random, seed `20260504`, drawn from CCSS only. Frozen at [`data/processed/pilot_v1_sample.json`](../data/processed/pilot_v1_sample.json). This is the *parent sample*.

**v0 sub-pilot (decided 2026-05-04, the actual run).** n = 30 per subject (60 total), drawn as a deterministic random subset of the parent sample. Seed `20260504`. Frozen at [`data/processed/v0_subpilot_sample.json`](../data/processed/v0_subpilot_sample.json) once drawn.

**Rationale for the sub-pilot.** v0 is a multi-condition design (3 models × 3 prompts × 2 wordings = 18 conditions per standard). At n=30 standards × 18 conditions = 540 generations, the API + compute budget is bounded. Larger n in v0 multiplies linearly; we can scale to the full 200-standard parent sample after v0 establishes which conditions matter.

**Full study (after v0).** Strata: (grade band × subject × jurisdiction). Equal allocation per cell. n ≈ 300, frozen at the AsPredicted pre-registration tag. Pre-reg can also tighten the condition matrix based on v0 findings (e.g., drop a model or a prompt variant if it's redundant).

**Caveat (CCSS HS grade tagging).** HS Math standards carry `gradeLevel = ["9","10","11","12"]` and HS ELA pairs grades (9-10, 11-12) by design. v0 preserves multi-grade items as drawn; per-grade analysis options (drop, band, per-item target-grade draw) are documented in the [pilot-sampling log entry](research-log/2026-05-04-pilot-sampling-plan.md) and resolved at pre-registration.

## Prompt variants (input-token-size dimension)

**v0 (decided 2026-05-04).** Three prompt templates per generation, varying input token budget systematically:

| Variant | Token budget (input) | Includes |
|---|---|---|
| **S** (short) | ~50 tokens | Just the standard text + grade target + length constraint |
| **M** (medium) | ~150 tokens | + role context (teacher), explicit format instructions, no examples |
| **L** (long) | ~400 tokens | + 1 worked exemplar of a (different) standard explained at a (different) grade level (one-shot) |

All three pin everything else (temperature 0, model, output length 100-250 words). Each standard generated under all three variants per model per wording condition.

**Rationale.** Prompt sensitivity is the most plausible failure mode of "this model drifts." If drift behavior is wildly different across the three variants, we have a prompt-quality finding rather than a model finding. If similar, the model claim is robust to prompt phrasing within reasonable bounds.

**Open question.** None for v0. Prompt-engineering deeper sweeps (system-prompt variations, persona, chain-of-thought) deferred to follow-up.

## Wording conditions (raw vs simplified standards)

**v0 (decided 2026-05-04).** Two conditions per standard:

| Condition | Description |
|---|---|
| **Raw** | Standard fed verbatim from the LC API |
| **Simplified** | Same standard rewritten by a separate LLM call to a 4th-grade reading level (instruction: preserve the learning expectation; simplify the language) |

The wording rewriter uses one fixed model + prompt; the rewriter identity is logged in the run manifest. Each rewrite is cached (deterministic seed) so the rewriter is run once per standard and re-used across generations.

**Rationale.** This is an interventional check on H4 ("the model partially mirrors the standard's own register"). If raw and simplified wordings produce different drift signals — same learning content, different register — we have direct evidence that the standard's wording confounds the output's reading level. Without this manipulation, H4 is observational only.

**Caveat acknowledged.** The rewriter is itself an LLM, which introduces *its own* register confound. Mitigation: (a) characterize the rewriter's output reading level using the same deterministic stack, so we know what reading level we actually achieved; (b) treat the rewriter-induced register as a measured covariate, not as a perfectly clean intervention; (c) the comparison of interest is *within-standard* (raw vs simplified) where the rewriter's bias affects both arms similarly.

**Open question.** None for v0. Deterministic rule-based simplifiers (synonym substitution + sentence splitting) are the next logical step but a substantial separate engineering effort; deferred.

## Evaluators (deterministic stack — no LLM-as-judge)

**v0 (decided 2026-05-04).** Every output is scored by a fully deterministic, open-source evaluation stack. No LLM-as-judge is used in v0. The pivot from LC's LLM-based evaluators is documented in the [deterministic-pivot log entry](research-log/2026-05-04-deterministic-evaluator-pivot.md).

| Layer | Instrument | What it returns | Drift signal |
|---|---|---|---|
| **Reading level (headline)** | `textstat` ensemble: Flesch-Kincaid, SMOG, Coleman-Liau, ARI, Gunning Fog, Dale-Chall, New Dale-Chall | Per-formula grade equivalent + median | Primary Δ = ensemble_grade − target_grade |
| **Reading level (calibrated)** | Ridge regression trained on CLEAR corpus, features = the deterministic stack | Single calibrated grade-level prediction | Secondary Δ_cal = predicted − target; expected to be tighter than ensemble |
| **Vocabulary tier** | Word-list lookups (Coxhead AWL, NGSL, Dale-Chall) | % AWL, % NGSL, % off-list (Tier-3 proxy), mean word length, type-token ratio | Decomposes drift into lexical contribution |
| **Syntactic complexity** | spaCy dependency parse | Mean dependency depth, T-unit length, subordinate-clause ratio, passive ratio, nominalization ratio | Decomposes drift into syntactic contribution |
| **Surface features** | Counters | Word count, sentence count, paragraph count, token count (input + output) | Sanity-check + cost tracking |

**Rationale.** Determinism beats LLM-as-judge on reproducibility, transparency, and cost. Classical readability formulas have known and stable biases (documented for 50+ years); LLM judges have biases we'd need to characterize ourselves and would change with every model version. Coxhead's AWL and the NGSL provide a principled tier system; spaCy's parser provides L2SCA-style syntactic complexity. The CLEAR-trained ridge regressor calibrates the ensemble against expert ratings — the same calibration anchor LC's evaluators used.

**What we lose vs LC's LLM evaluators.** The qualitative dimensions in the SAP rubric — register, abstraction, knowledge demands — that classical formulas literally cannot measure. v0 is *only* about reading level (Q1-Q3); the SAP-qualitative dimensions live in deferred Q5 ("beyond reading level"). We are not claiming what we are not measuring.

**Open question.** None for v0.

---

## Out of scope (explicit)

- Pre-K and postsecondary standards
- Career/technical education (CTE)
- Subjects beyond ELA and Math (v0)
- Lesson plans, worked examples, multi-turn dialog (v0)
- Student outcome data (deferred to a future investigation that pairs evaluator scores with student interaction data)
- Standards in languages other than English (v0)
- LLM-as-judge evaluation (rejected on reproducibility grounds; see deterministic-pivot log entry)
- SAP-rubric qualitative dimensions (register, abstraction, knowledge demands) — these are deferred Q5 territory
- Cross-family model replication (Claude, Gemini, open-weights) — deferred follow-up

## Decisions still open

1. **CLEAR-calibrated predictor: train and ship in v0, or defer to writeup time?** Either way, raw textstat ensemble is the headline; calibrated predictor is a tightening overlay. Defaulting to: train in v0, report both ensemble and calibrated values.
2. **Per-grade analysis with multi-grade items (HS Math span; HS ELA pairs).** Drop, band, or per-item target-grade draw? Affects analysis, not generation. Resolve before the writeup.
3. **Stop rule and inferential framing.** v0 is exploratory by design (no pre-reg yet); the AsPredicted form is the next milestone after v0 produces results.

The pre-registration freeze comes after v0; design holes that survive scope.md surface in the form. See [`preregistration-template.md`](preregistration-template.md) for the field schema.
