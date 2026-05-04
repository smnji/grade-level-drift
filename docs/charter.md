# Charter — Grade-Level Drift in LLM-Generated Instruction

Working title for the publication: *Does an LLM Teach a Standard at Its Grade Level?*

This document captures the research question map. Every analysis, scope decision, and deliverable in this repo is checked back against it. Sub-questions deferred to follow-up posts are listed explicitly so the v0 doesn't drift in scope.

## Central research question

**For an LLM asked to generate student-facing instruction for a K-12 academic standard at grade N, does the produced text land at grade N's reading level — or does it systematically drift?**

## v0 anchor sub-questions

The v0 publication answers these three:

1. **Does drift exist?** Direction (above or below target grade) and magnitude.
2. **Is drift consistent across models?** Or does each model carry its own bias?
3. **Are there standards that reliably produce above-grade output across all models — and what do those have in common?** (Vocabulary in the standard? Topic? Abstraction level?)

## Deferred to follow-ups (within the reading-level theme)

4. **Mechanism.** Is the LLM mirroring the standard's reading level, applying a topic-specific default register, or sensitive to prompt phrasing?
5. **Beyond reading level.** Sentence structure, vocabulary tier (Beck), conventionality, cohesion — does the model miss any of these systematically?
6. **Decoupling.** Do reading-level mismatch and subject-matter accuracy come apart?

## Deferred to other investigations in the series

7. **Loop closure.** Does reading-level mismatch correlate with where students get stuck? (Requires student interaction data; deferred to a future investigation in the series.)

## Downstream impact (where findings land)

- AI tutoring product design — model selection, prompt engineering, content QA gates.
- K-12 LLM safety literature — adds a per-standard instructional risk dimension.
- Standards-aligned content generation — informs whether the standard text alone is enough conditioning, or whether grade-level scaffolding must be supplied.
- Methodology contribution — establishes a reusable LC-evaluator-based pipeline for measuring AI educational text quality.
