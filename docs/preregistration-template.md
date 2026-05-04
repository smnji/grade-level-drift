# Preregistration — {Investigation name}

> **Template usage.** This is the *template*. When ready to freeze the study, copy this file to `docs/preregistration.md` and fill in every field. Then commit, tag the commit `pre-reg-v1`, and submit the form to [AsPredicted](https://aspredicted.org) or [OSF Registries](https://osf.io/registries) for an external timestamp. Cite the AsPredicted ID or OSF DOI in the published writeup. This template file stays unchanged for the next preregistration.

> **Workflow tip.** Filling this form *before* the pilot run forces the design to be specific enough to register. Vague pre-registrations are signs of unresolved methodology decisions; if you can't fill a field crisply, the corresponding methodology section probably has a hole.

---

## 1. Have any data been collected for this study already?

> **Fill in:** Yes/No. If Yes, describe what's been collected — pilot data is fine to disclose, the goal is honesty, not denial. AsPredicted explicitly asks this; lying or evading is grounds for rejection of the pre-registration's standing.

**Answer:** {...}

## 2. What's the main hypothesis being tested?

> **Fill in:** State the hypothesis(es) verbatim from `research-proposal.qmd §4` (or wherever §Hypotheses lives in your repo). Include directions and magnitudes when the literature supports doing so. If you have multiple hypotheses, label them `H1`, `H2`, ..., consistent with the proposal.

**Answer:** {...}

## 3. Describe the key dependent variable(s) and how they will be measured.

> **Fill in:** What's measured, by what instrument, with what scale. For LLM evaluation studies: the outcome scalar (e.g., Δ = predicted_grade − target_grade), the instrument that produces it (e.g., LC Grade Level Appropriateness Evaluator), and any auxiliary variables that contribute to secondary analyses.

**Answer:** {...}

## 4. Conditions / independent variable(s).

> **Fill in:** What varies across conditions. For LLM studies: model identity, prompt template version, decoding parameters (temperature, top_p), sample-strata factors. For experimental studies: treatment vs control assignment.

**Answer:** {...}

## 5. Analysis plan — specific tests, exclusions, and multiple-comparison policy.

> **Fill in:** The exact statistical procedures. Each pre-registered test should specify: the test statistic (e.g., one-sample t-test), the α level (typically 0.05), the multiple-comparison correction (Holm–Bonferroni, FDR, or none), and any pre-defined exclusion rules for outliers or quality failures. Be specific enough that someone could reproduce the analysis from this section alone.

**Answer:** {...}

## 6. Sample size and stop rule.

> **Fill in:** The intended sample size, the allocation across strata if stratified, and the stop rule. Stop rules are: a fixed n (preferred), a calendar deadline, or an observed effect size threshold (rare; defensible only with sequential-design corrections).
>
> Be precise about *how* the number is determined, not *why*. AsPredicted asks specifically that justification can be brief but the exact mechanism must be unambiguous.

**Answer:** {...}

## 7. Anything else worth pre-registering?

> **Fill in:** Secondary analyses you commit to running regardless of the primary outcome; specific cuts you commit to reporting whether or not they're significant; data-quality checks; test-retest characterizations; convergent-validity sub-studies. Anything where, in advance, you want to remove the option to silently abandon the analysis if it doesn't go your way.

**Answer:** {...}

## 8. What's NOT pre-registered.

> **Fill in:** Explicitly enumerate what stays open. Any analysis not listed in §5, §7, or here is **exploratory** and must be labeled as such in the writeup.
>
> This list prevents the post-hoc creep that pre-registration is designed to catch. It is the most-skipped field on AsPredicted forms; do not skip it.

**Answer:** {...}

## 9. Name, date, and external timestamp.

> **Fill in:** Author name(s), today's date in ISO format, the git commit SHA after this file is filled and tagged, and (after submission) the AsPredicted ID or OSF DOI.

**Filled by:** {Author name(s)}
**Date:** {YYYY-MM-DD}
**Git tag:** `pre-reg-v1`
**Commit SHA:** {filled in after `git tag pre-reg-v1`}
**External timestamp:** {AsPredicted ID `#NNNN` or OSF DOI `10.17605/OSF.IO/XXXXX`, after submission}

---

## After submission

- Cite the AsPredicted/OSF ID in any publication or release tied to this study, in the Methodology section.
- Treat this file as **immutable** after submission. Updates require a new pre-registration version (`docs/preregistration-v2.md`, tag `pre-reg-v2`) with explicit notes on what changed and why.
- If a pre-registered analysis cannot be run as specified (e.g., a covariate is unavailable), document the deviation in the writeup and report both the closest feasible analysis and the original plan.
