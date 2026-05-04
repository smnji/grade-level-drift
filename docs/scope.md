# Scope — Decision Record

**Status:** draft, awaiting ratification
**Last updated:** 2026-05-04

This document fixes the boundaries of the v0 study. Every methodology choice and data pull is checked back against it. Open questions at the bottom resolve before the pilot begins.

## Dimensions to fix

1. Subjects
2. Jurisdictions / standards frameworks
3. Grade bands
4. Models (instruction generators)
5. Output type (what counts as "instruction")
6. Sample size and stratification
7. Evaluators

---

## Subjects

**Proposal.** ELA + Math, both included from v0.

**Rationale.** Math has the deepest LC coverage (15+ states crosswalked) and the cleanest Common Core anchor; ELA is the substrate the literacy evaluators were originally validated on. Together they yield enough variance for cross-subject claims about drift while staying inside what LC supports best.

**Open question.** Whether to add a third subject (Science, given NGSS structure) for triangulation in v1.

## Jurisdictions

**Proposal.** Multi-State / Common Core anchor + 3–5 representative state frameworks (mix of large/small, CC-adopter/non-adopter, geographic spread). Defer 50-state coverage to v1.

**Rationale.** The headline finding is about LLM behavior given a standard, not state-level differences. A small jurisdiction set is enough to show whether drift varies by framework wording.

**Open question.** Confirm the 3–5 candidate states. Candidate set: California, Texas, Florida, Massachusetts, Virginia (mirrors the standards-substrate bootstrap slice for cross-project consistency).

## Grade bands

**Proposal.** Full K-12. Findings reported by grade band (K-2, 3-5, 6-8, 9-12) wherever a band-level cut is informative.

**Rationale.** Drift may differ systematically by band; band-level reporting is cheap and adds explanatory power.

**Open question.** None.

## Models

**Proposal.** Claude (specific model ID pinned per run) for the v0 pilot. Add a second model (GPT-x or Gemini) before publication so cross-model claims (Q2) are answerable.

**Rationale.** A single model is enough to detect "does drift exist" (Q1). Cross-model comparisons require ≥2.

**Open question.** Which second model to add — GPT-4-class, Gemini, or both. Decision driven by access and cost.

## Output type

**Proposal.** Short student-facing explanation: 100–250 words explaining the standard at the target grade level. No worked examples, no problem sets, no multi-turn dialog.

**Rationale.** Different output types (explanation vs lesson plan vs worked example) carry different default registers, which would confound the drift measurement. Pinning one output type isolates the question. Length is constrained to keep evaluator scoring on a comparable token budget across grades.

**Open question.** Whether to vary length by grade (e.g. 75–150 words for K-2, 150–250 for 6-12). Likely yes; needs a brief pilot to choose breakpoints.

## Sample size and stratification

**Proposal.**
- **Pilot (n = 30):** 5 standards per grade band × ELA/Math mix. Used to debug pipeline and check for unforeseen issues.
- **Full study (n ≈ 300):** Stratified random sample by (grade band × subject × jurisdiction). Equal allocation per cell.

**Rationale.** ~25 standards per cell gives reasonable statistical power for medium effect sizes (Cohen's d ≈ 0.5) at α = 0.05. Total cost is bounded by LLM-generation + evaluator API calls.

**Open question.** Stratify by jurisdiction, or treat jurisdiction as an unmodeled covariate in v0?

## Evaluators

**Proposal.** All five of Learning Commons' literacy evaluators on every output:

| Evaluator | Use |
|---|---|
| Grade Level Appropriateness | Primary outcome — direct measure of drift |
| Sentence Structure | Mechanism: complexity contribution |
| Vocabulary | Mechanism: word-tier contribution |
| Conventionality | Quality control — adverse outputs |
| Subject Matter Knowledge | Q8: decoupling check |

**Rationale.** These evaluators are SAP-rubric-anchored, expert-validated against the CLEAR dataset, and free at the inference cost of OpenAI + Gemini calls. Using all five is cheap insurance against discovering at writeup that we needed an extra channel.

**Open question.** None.

---

## Out of scope (explicit)

- Pre-K and postsecondary standards
- Career/technical education (CTE)
- Subjects beyond ELA and Math (v0)
- Lesson plans, worked examples, multi-turn dialog (v0)
- Student outcome data (deferred to a future investigation that pairs evaluator scores with student interaction data)
- Standards in languages other than English (v0)
- Re-implementing reading-level metrics from scratch (we use LC's evaluators verbatim)

## Decisions still open

1. Bootstrap-slice state list — confirm the candidate five.
2. Output length: fixed across grades, or band-tiered?
3. Second model identity (GPT-4-class vs Gemini vs both).
4. Whether jurisdiction is a stratification variable or an unmodeled covariate in v0.

These are resolved before the pilot run begins; resolutions are recorded in `decisions/` ADRs.
