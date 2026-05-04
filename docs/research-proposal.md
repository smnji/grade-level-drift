# Research Proposal — Grade-Level Drift in LLM-Generated Instruction for K-12 Academic Standards

**Author:** Standards Research Group
**Date:** 2026-05-04 (proposal v0.1)
**Status:** Draft for internal review; pre-registration finalized before pilot run

---

## 1. Abstract

State K-12 academic standards are increasingly used as the conditioning input to AI-mediated tutoring and content-generation systems. A standard like *3.NF.A.1* says "explain a fraction as a quantity formed by parts of a whole" — and the implicit promise of an AI tutor is that it will explain that idea *to a third grader*, in language a third grader can read. Whether large language models (LLMs) actually meet that promise is, surprisingly, an empirical question that the published literature has not directly answered.

This proposal lays out a study to measure **grade-level drift** in LLM-generated instructional text. For a stratified random sample of K-12 academic standards drawn from the Learning Commons (LC) Knowledge Graph (math and English Language Arts, K-12, multiple jurisdictions), we prompt a frontier LLM to generate a short student-facing explanation of each standard targeted at the standard's grade level. We then score each output with five LC literacy evaluators — co-designed with Student Achievement Partners and the Achievement Network and validated against the CLEAR expert-annotated dataset — to obtain a per-output predicted grade level and decomposed complexity ratings. The primary outcome is the signed deviation between predicted and target grade. Adjacent literature on controllable readability (Imperial & Madabushi, 2023; Ribeiro et al., 2023; Trott & Rivière, 2024) predicts compression toward the middle of the grade range, with mean absolute error in the 1-2 grade-level region; this proposal pre-registers that prediction.

The contribution is twofold: an empirical characterization of where, by how much, and for which standards LLMs miss the target reading level; and a reusable open methodology that grounds AI-tutoring quality claims in a measurable, instrument-based outcome rather than vibes. Findings are intended for a public blog publication and an open-source artifact release.

## 2. Background and motivation

### 2.1 The substrate question

State K-12 academic standards function as the *substrate* for AI-mediated learning. They are the structured input into curriculum-generation, item-generation, lesson-planning, and tutoring systems. Treating standards as substrate makes a strong implicit assumption: that an AI system, given a standard at grade N, will produce content that is *appropriate for grade N readers*. The standard's grade level is a hard constraint, not a soft suggestion — a fifth-grader who is handed sixth-grade prose does not silently up-level; they disengage.

The assumption that LLMs satisfy this constraint is widespread but largely unverified. AI-tutoring marketing claims grade-level appropriateness as a default; AI-content-generation pipelines add it as a prompt fragment ("write at a grade 5 reading level") and presume it works. The systematic empirical question — *how often, by how much, and on which kinds of standards do LLMs miss the target?* — has not been answered at scale in the K-12 instructional-text setting.

### 2.2 Why now: the instrument exists

Reading-level measurement has historically been split between quantitative formulas (Flesch-Kincaid, Lexile, Dale-Chall, ATOS) — which capture word/sentence statistics but not meaning, abstraction, or knowledge demand — and expert qualitative judgment, which captures the missing dimensions but does not scale.

Learning Commons has released an evaluator suite that closes this gap for our purposes. Their Grade Level Appropriateness Evaluator, Sentence Structure Evaluator, Vocabulary Evaluator, Conventionality Evaluator, and Subject Matter Knowledge Evaluator are LLM-as-judge instruments grounded in the Student Achievement Partners (SAP) Qualitative Text Complexity rubric and validated against the CLEAR corpus (Crossley et al., 2023). Crucially, the rubric and the underlying corpus were designed for K-12 instructional text — not generic web prose. This is the right instrument for the question.

### 2.3 Why this is the right first study

This study is the first in a planned multi-part investigation of LLM behavior against K-12 standards. It is deliberately the first because:

- **Measurement is well-defined.** Drift between predicted and target grade is a single signed scalar with established analytic conventions.
- **No human-subjects data is required.** No IRB, no consent, no privacy considerations beyond standard secrets handling.
- **The result is publishable in either direction.** A finding of "no systematic drift" disconfirms a widespread informal assumption and is useful; a finding of structured drift is even more useful, with direct implications for prompt engineering, model selection, and content QA pipelines.
- **It establishes the reusable measurement scaffolding** that subsequent studies (entropy, interaction-data-grounded learning outcomes) will build on.

### 2.4 Position in the broader research line

This study is the first in a planned multi-part investigation of LLM behavior against K-12 academic standards. Two follow-up investigations are sketched: one on per-standard model uncertainty and hallucination (using LLM internals and self-consistency to predict where instruction will go wrong), and one that loops in student interaction data to ground reading-level findings in actual learning outcomes. Each builds methodologically on the previous, so getting the measurement scaffolding right here is a load-bearing decision for the entire line.

## 3. Research questions

### 3.1 Central question

**For an LLM asked to generate student-facing instruction for a K-12 academic standard at grade N, does the produced text land at grade N's reading level — or does it systematically drift?**

### 3.2 v0 sub-questions (this study answers these)

1. **Does drift exist?** Direction (above or below target grade) and magnitude.
2. **Is drift consistent across models?** Does each model carry its own bias?
3. **Are there standards that reliably produce above-grade output across all models — and what do those have in common?** (Standard wording reading-level? Topic? Vocabulary tier? Abstraction?)

### 3.3 Sub-questions deferred to follow-ups

4. **Mechanism.** Is the model mirroring the standard's reading level, applying a topic-specific default register, or sensitive to prompt phrasing?
5. **Beyond reading level.** Sentence structure, vocabulary tier, conventionality, cohesion — orthogonal failure modes.
6. **Decoupling.** Do reading-level mismatch and subject-matter accuracy come apart?
7. **Loop closure with interaction data.** Does reading-level mismatch correlate with where students get stuck? (Deferred to a future investigation that pairs evaluator scores with student interaction data.)

This narrowing is deliberate. v0 establishes the descriptive finding and the measurement scaffolding; mechanism and outcome-grounded follow-ups are higher-investment and depend on having a baseline drift signal to anchor on.

## 4. Hypotheses

The hypotheses below are pre-registered before the pilot run. Effect-size benchmarks follow the K-12 literature (Hill et al., 2008) rather than Cohen's generic conventions, since standardized reading growth is ~0.32 SD per grade in middle grades — Cohen's "small" of 0.2 corresponds to two-thirds of a year of growth, far from negligible in this domain.

**H1 (drift exists, direction).** Mean signed deviation Δ = predicted_grade − target_grade is non-zero. Based on Imperial & Madabushi (2023), Ribeiro et al. (2023), and Trott & Rivière (2024), we predict **compression toward the middle**: positive Δ for low-grade standards (output is above-target) and negative Δ for high-grade standards (output is below-target).

**H2 (magnitude).** Mean absolute |Δ| is in the 1.0–2.0 grade-level range. Tighter than this would constitute strong evidence of grade calibration; wider than this would imply substantial regression-to-mean dynamics.

**H3 (cross-model consistency).** When a second model is added, the *direction* of drift is preserved across models (same compression pattern), but *magnitude* differs by ≥ 0.5 grade levels in at least one band. Equivalently: model choice matters quantitatively but not qualitatively.

**H4 (per-standard predictability).** Standards whose own statement text is at the highest reading level (e.g., 9–12 standards using abstract verbs and Tier-3 vocabulary) will show the smallest |Δ|; standards at K-2 with a high prevalence of Tier-2 academic vocabulary inside the standard wording will show the largest upward drift. Mechanism: the model partially mirrors the input register.

**H5 (null option).** No systematic drift exists; observed |Δ| is statistically indistinguishable from evaluator test-retest variance. This is the disconfirmatory outcome and is reportable on its own merit.

## 5. Literature review

The four themes below frame the empirical and methodological context for studying grade-level drift in LLM-generated instructional text. Where evidence is thin or contested, this is flagged explicitly rather than glossed.

### 5.1 Theme A — Text-complexity and reading-level metrics

Quantitative readability formulas have a century of history but remain contested instruments. **Flesch-Kincaid Grade Level** (Kincaid, Fishburne, Rogers, & Chissom, 1975) and the related **Flesch Reading Ease** combine average sentence length and syllables per word into a grade estimate; the formula was developed for U.S. Navy training manuals and was never validated for narrative or instructional text aimed at children. It remains the default in word processors and many ed-tech pipelines despite well-documented failure modes on short, dialogic, or poetic text (Begeny & Greene, 2014). Relevance: F-K is the most likely "sanity-check" comparator a reviewer will request alongside our SAP-derived evaluators, so we report it even though we do not treat it as ground truth.

**Lexile Framework** (Stenner, Burdick, Sanford, & Burdick, 2006; MetaMetrics) uses word frequency (against a large reference corpus) and sentence length, calibrated through Rasch modeling against a bank of cloze items. Lexile is the dominant metric in U.S. K-12 publishing and is reported on most state assessments. Its main limitation, acknowledged by MetaMetrics, is that it captures quantitative dimensions only — it cannot distinguish a complex idea expressed in short sentences from a simple idea expressed in long ones. Relevance: any cross-walk between our evaluator scores and "industry" reading levels will probably be evaluated by reviewers against Lexile.

**Dale-Chall** (Chall & Dale, 1995) uses a curated list of ~3,000 words familiar to fourth-graders plus average sentence length. **ATOS** (Renaissance Learning, 2000, industry technical report — *grey literature*) underlies the Accelerated Reader program and is calibrated on millions of student reading logs. Both are quantitative and share Lexile's blind spots. Relevance: ATOS is widely used in elementary classroom libraries, so for K-5 standards our outputs are de facto judged against ATOS-shaped intuitions.

The **Student Achievement Partners (SAP) Qualitative Text Complexity rubric** (Student Achievement Partners, 2013, *grey literature / practitioner publication*) emerged from the Common Core State Standards' Appendix A "three-legged stool" model of complexity (quantitative, qualitative, reader-and-task). SAP's rubric operationalizes the qualitative leg across four dimensions: meaning/purpose, structure, language conventionality and clarity, and knowledge demands. It is the rubric our Learning Commons evaluators are derived from. Relevance: this is the conceptual backbone of our scoring instrument; defending the rubric defends our outcome measure.

**Beck's vocabulary tiers** (Beck, McKeown, & Kucan, 2013) classify words as Tier 1 (basic, oral), Tier 2 (high-utility academic), or Tier 3 (domain-specific). Tier 2 vocabulary is the focus of most K-12 instructional planning. Relevance: our Vocabulary Evaluator implicitly encodes this distinction; framing findings in tier language will be legible to educators.

**Coh-Metrix** (Graesser, McNamara, Louwerse, & Cai, 2004; McNamara, Graesser, McCarthy, & Cai, 2014) provides ~100 indices of cohesion, including referential overlap, latent semantic analysis-based connectedness, and connective density. Coh-Metrix demonstrated empirically that "easier" text is not always more cohesive — sometimes coherence demands richer connectives — undermining the assumption that simple = appropriate. Relevance: justifies why our evaluator suite is multi-dimensional (sentence structure separate from conventionality separate from knowledge demand) rather than a single scalar.

A useful synthesis is Nelson, Perfetti, Liben, and Liben (2012, *grey literature, SAP-commissioned*): they compared seven quantitative formulas against expert grade-band placements and found inter-formula agreement reasonable in middle grades but poor at K-2 and 11-CCR boundaries — exactly the boundaries where K-12 instructional decisions are highest-stakes. This empirically motivates qualitative supplementation.

### 5.2 Theme B — LLM-as-judge validity

The line of work most cited in our space starts with **Zheng et al. (2023)**, *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena* (NeurIPS 2023 Datasets & Benchmarks). They documented that GPT-4 agreement with human pairwise preferences reached ~85%, comparable to human-human agreement, but identified four systematic biases: position bias (preference for the first-presented response), verbosity bias (preference for longer responses), self-enhancement bias (models prefer their own outputs), and limited reasoning on math/logic. Relevance: every one of these biases is a plausible confound in our design; the verbosity bias in particular is concerning because longer text typically scores as higher grade level, so an LLM judge could conflate "more text" with "higher grade."

**Verga et al. (2024)**, *Replacing Judges with Juries* (arXiv preprint, *clearly marked*), proposed PoLL (Panel of LLM Judges) ensembles using diverse smaller models, showing they reduce intra-model bias and cost relative to a single GPT-4 judge while maintaining or exceeding human-correlation. Relevance: motivates our cross-model robustness check (Claude primary, second model for confirmation) but with the caveat that two large frontier models are not a "diverse panel" in the PoLL sense.

**Kim et al. (2024)**, *Prometheus 2: An Open Source Language Model Specialized in Evaluating Other Language Models* (EMNLP 2024), trained dedicated 7B/8x7B evaluator models on rubric-grounded feedback and showed they approach GPT-4 evaluation performance on direct-assessment tasks. The earlier Prometheus paper (Kim et al., 2024, *ICLR*) emphasized that providing an explicit rubric is the single strongest factor in evaluator-human agreement. Relevance: directly justifies our use of the SAP rubric inside the evaluator prompt; predicts our evaluators should outperform rubric-free judges.

**Wang et al. (2024)**, *Large Language Models are not Fair Evaluators* (ACL 2024), quantified position bias as flipping up to 50% of pairwise judgments under candidate reordering and proposed simple mitigations (multiple-evidence calibration, balanced position calibration). Relevance: our design uses absolute scoring not pairwise comparison, which sidesteps position bias but inherits a different problem — scale-use bias and central-tendency drift, less studied in this literature.

**Panickssery, Bowman, and Feng (2024)**, *LLM Evaluators Recognize and Favor Their Own Generations* (arXiv, *marked preprint*), showed that frontier evaluators score outputs from their own model family higher than equivalent outputs from competitors, even controlling for quality. Relevance: this is the central threat to our cross-model claims — if Claude-as-judge favors Claude-as-generator, our drift estimate is biased toward zero for the same-family condition.

**Educationally-specific LLM-as-judge work is genuinely thin.** Henkel, Hills, Roberts, McGrane, and Boyle (2024, *L@S*) used an LLM judge to evaluate Khan Academy tutor responses and reported moderate-to-good agreement with expert raters on dimensions like correctness and pedagogical appropriateness, but cautioned that agreement collapsed on more subjective dimensions. We are not aware of peer-reviewed work specifically validating LLM judges for grade-level / text-complexity assessment in K-12 contexts — this gap is a contribution opportunity for the present study.

### 5.3 Theme C — LLM register, complexity, and reading-level mismatch

Empirical work on whether LLMs hit a *requested* reading level is surprisingly limited. **Imperial and Madabushi (2023)**, *Flesch or Fumble? Evaluating Readability Standard Alignment of Instruction-Tuned Language Models* (BEA workshop @ ACL), prompted GPT-3.5, GPT-4, and several open models to generate text at specified Flesch-Kincaid grade levels and found systematic compression toward a middle band — outputs targeted for grade 2 came out closer to grade 5, and outputs targeted for grade 12 came out closer to grade 9. This is the closest direct precedent for our "drift" hypothesis. Relevance: predicts the direction (compression toward the middle) and provides a methodological template, though they evaluated free generation, not standards-anchored generation.

**Ribeiro et al. (2023)**, *Generating Summaries with Controllable Readability Levels* (EMNLP 2023), showed that fine-tuning and instruction-tuning both improve readability control but neither achieves tight calibration; mean absolute error in F-K grade remained ~2 grades even for state-of-the-art systems. Relevance: bounds our prior expectation — drift of less than ~1 grade would actually be surprising given this baseline.

**Trott and Rivière (2024)**, *Measuring and Modifying the Readability of English Texts with GPT-4* (*Computers in Human Behavior: Artificial Humans*), found GPT-4 could rewrite texts to be measurably easier or harder but with substantial variance and a strong regression-to-mean effect: extreme target levels were systematically missed. Relevance: same compression pattern, different domain, increases our confidence the effect is real.

For K-12 specifically, **Stowe et al. (2024)** and contemporaneous work on "controllable text simplification" (e.g., Kew & Ebling, 2022, EACL) consistently show that controllable simplification systems trained on Newsela and OneStopEnglish corpora over-simplify when targeting elementary grades and under-simplify when targeting upper-secondary — but most of this work pre-dates frontier instruction-tuned models. The specifically K-12 instructional-text question is, to our knowledge, **not directly addressed in peer-reviewed literature**. We flag this honestly: our study contributes to a thin evidentiary base.

**Padmakumar and He (2024)**, *Does Writing with Language Models Reduce Content Diversity?* (ICLR 2024), is tangentially relevant — they showed LLM assistance compresses lexical and stylistic variance in human writing, consistent with a "pull toward the mean" mechanism that could explain compression toward a middle grade band.

### 5.4 Theme D — LLMs as educational content generators and tutors

**Henkel, Hills, Roberts, McGrane, and Boyle (2024)**, *Can large language models make the grade? An empirical study evaluating LLMs ability to mark short-answer questions in K-12 education* (L@S 2024), evaluated GPT-4 marking of K-12 short-answer responses against expert markers and found Cohen's κ in the 0.6-0.75 range — "substantial" but below typical inter-human agreement. Relevance: establishes a credibility benchmark for LLM-graded-against-human work in K-12 and provides an effect-size anchor.

**Khan Academy / Khanmigo evaluations** are largely industry-published (*grey literature*). Khan Academy's 2024 impact reports describe pilot deployments but published peer-reviewed evidence is scarce. **Kestin, Miller, Klales, Milbourne, and Ponti (2024)**, *AI Tutoring Outperforms Active Learning* (working paper / preprint, Harvard, *clearly marked*), reported a randomized comparison in a Harvard physics course finding LLM tutoring matched or exceeded active-learning instruction on short-term learning outcomes — a striking but single-context result. Relevance: shows the field is moving toward outcomes-grounded evaluation, but most published evidence remains either model-vs-model or self-reported.

**LearnLM** (Google DeepMind, 2024, *grey literature / technical report*) is an instruction-tuned model line specifically post-trained for pedagogical behaviors; their public report includes human-rater comparisons against GPT-4 on pedagogy-specific rubrics with claimed wins on most dimensions. Relevance: signals that "pedagogical alignment" is treated as a distinct optimization target by frontier labs, supporting our premise that off-the-shelf LLMs are not automatically grade-calibrated.

**Macina et al. (2023)**, *MathDial: A Dialogue Tutoring Dataset with Rich Pedagogical Properties* (EMNLP Findings), and **Wang et al. (2024)**, *Bridging the Novice-Expert Gap via Models of Decision-Making* (ACL), highlighted that LLM tutors frequently give away answers, fail to scaffold, and hallucinate intermediate reasoning steps. Relevance: motivates separating our Subject Matter Knowledge Evaluator from the reading-level evaluators — pedagogical correctness and grade-level appropriateness are genuinely orthogonal failures.

**Pardos and Bhandari (2024)**, *ChatGPT-generated help produces learning gains equivalent to human tutor-authored help* (*Computers and Education: Artificial Intelligence*), is one of the few peer-reviewed comparisons using actual student-outcome data (in an algebra learning system). Relevance: a useful counterpoint to purely model-vs-model evidence and a model for how outcomes-grounded follow-up work to ours might be designed.

Finally, **the standards-alignment literature is sparse**. Most published work on LLM-generated instructional content focuses on Q&A correctness or hallucination rates rather than alignment to specific state K-12 standards. Sonkar, Liu, Mallick, and Baraniuk (2023, NeurIPS) evaluated LLM-generated math hints for correctness but did not score grade-level fit. We flag this gap as a contribution opportunity.

### 5.5 Methodology references

Our design choices draw on established practice in educational measurement and the emerging LLM-evaluation literature.

**Stratified random sampling of educational items.** Stratification by grade and subject is standard in educational measurement; the AERA/APA/NCME *Standards for Educational and Psychological Testing* (AERA, APA, & NCME, 2014) treat representative coverage of the construct domain (here: grade × subject × strand) as a basic validity requirement. Item-sampling designs in studies like NAEP framework documents (NCES, 2022, *grey literature*) use multi-stage stratified sampling across content strands and cognitive complexity levels — we follow that template. For LLM evaluation specifically, **Liang et al. (2023)**, *Holistic Evaluation of Language Models* (TMLR), argued explicitly for stratified scenario sampling to avoid skewed conclusions when a model's failure modes are concentrated in a subdomain.

**LLM evaluation experimental design.** **Zheng et al. (2023)** established the practice of running each evaluation under multiple seeds and reporting variance. **Biderman et al. (2024)**, *Lessons from the Trenches on Reproducible Evaluation of Language Models* (arXiv, *marked preprint*), provided a thorough catalog of reproducibility hazards: prompt sensitivity, decoding-parameter sensitivity, evaluator-version drift, and tokenization edge cases. Our paired design — same standard, multiple prompts, multiple seeds, multiple evaluator runs — mirrors their recommendations.

**Statistics for detecting drift.** Our primary outcome is a signed deviation (evaluator score minus target grade), supporting both directional (compression) and magnitude tests. Effect-size conventions follow **Cohen (1988)** for *d* and **Hedges and Olkin (1985)** for the small-sample-corrected *g*. In education research specifically, **Hill, Bloom, Black, and Lipsey (2008)** in *Child Development Perspectives* recommended interpreting effect sizes against empirical benchmarks (the average grade-to-grade growth on standardized reading assessments is ~0.32 SD in middle grades), which is the reference frame we use rather than Cohen's generic "small/medium/large" labels — these substantially under-call effects in education contexts.

For inter-rater agreement when comparing evaluator runs, **Cohen's κ** (Cohen, 1960) for categorical agreement and **intraclass correlation (ICC)** following **Shrout and Fleiss (1979)** and **Koo and Li (2016)** for continuous scores are standard. We will report ICC(2,k) for our evaluator-as-rater consistency across seeds, since the evaluator is treated as a fixed instrument applied to a random sample of items. **McHugh (2012)** provides commonly-cited interpretive bands for κ in clinical and educational contexts.

**SAP/CLEAR provenance.** The SAP Qualitative Text Complexity rubric (Student Achievement Partners, 2013, *grey literature*) was developed to operationalize Common Core Appendix A's qualitative dimension and has been used in dozens of state-level curriculum review processes. The **CLEAR corpus** (CommonLit Ease of Readability) was released by **Crossley, Heintz, Choi, Batchelor, Karimi, and Malatinszky (2023)** in *Behavior Research Methods*: ~5,000 excerpts from grades 3-12 paired with expert pairwise complexity judgments, designed specifically to support training and validation of computational readability models. Learning Commons' evaluators were calibrated against CLEAR pairwise judgments, which gives them external validation against an expert-annotated dataset — an important feature relative to evaluators validated only against another LLM. We cite the CLEAR paper as primary justification for evaluator validity and the SAP rubric documentation as primary justification for construct validity.

## 6. Methodology

The full operational specification is in [`methodology.md`](methodology.md); this section summarizes the design and adds the pre-registration commitments and statistical-power considerations.

### 6.1 Design overview

A **paired between-standards, within-model** design. Each sampled standard at target grade N is fed through the pipeline once per (model, prompt-version, seed) condition, producing one instructional text per condition. Each text is scored by all five LC evaluators. The unit of analysis is (standard × condition × evaluator). Drift is operationalized as the signed difference Δ = predicted_grade − target_grade for the Grade Level Appropriateness Evaluator; the other four evaluators contribute decompositional and quality-control signal.

### 6.2 Data and sampling

- **Source.** LC Knowledge Graph (REST API for the pilot; public JSONL snapshot for the published artifact).
- **Frame.** Records with `statementType = "Standard"` (excluding clusters and domain headings).
- **Strata.** (Grade band: K-2, 3-5, 6-8, 9-12) × (Subject: ELA, Math) × (Jurisdiction: 3-5 anchor states + Multi-State / CCSS).
- **Pilot sample (n = 30).** 5 standards per band × ELA/Math mix; jurisdiction balanced opportunistically.
- **Full study sample (n ≈ 300).** Equal allocation per cell. ~25 per stratum, supports detection of medium effect sizes (Cohen's d ≈ 0.5) at α = 0.05 with > 0.85 power for primary tests.
- **Random seed.** Pinned and recorded per run; the full sampled `caseIdentifierUUID` list is committed to `data/processed/sample_v{N}.json`.

### 6.3 Generation conditions

- **Primary condition.** Single frontier model (Claude, model ID pinned), temperature 0, single pinned prompt template, one sample per standard.
- **Variability condition.** Same model, temperature 0.7, N=5 samples per standard, on a 50-standard subset. Characterizes within-model variance — the noise floor against which between-condition effects are measured.
- **Cross-model condition.** Second model (selection in scope-decision phase: GPT-4-class or Gemini), temperature 0, full sample. Required for H3.

### 6.4 Scoring

Each generated output is scored by all five LC literacy evaluators. Each evaluator is run **3× on a 30-standard test-retest subset** to characterize within-evaluator stability; the rest of the sample receives a single evaluator run, with stability inferred from the subset.

Scores are stored as `(run_id, standard_id, model, prompt_version, seed, evaluator, score, evaluator_version, evaluator_backend)`. No score is overwritten; rerunning produces a new `run_id`.

### 6.5 Statistical analysis

**Primary analyses (pre-registered).**

1. Mean signed Δ within each grade band, with 95% confidence intervals. Single-sample *t*-test against zero per band; Holm-Bonferroni corrected across bands.
2. Direction-of-drift test: sign test on Δ aggregated within (low: K-5) and (high: 6-12) groups, expecting positive Δ in low and negative Δ in high under H1.
3. Mean |Δ| overall and per band, with 95% CI; tested against the H2 prediction of 1.0–2.0 grade levels.

**Secondary analyses.**

4. Cross-model agreement (when 2nd model added): ICC(2,1) and Pearson r of Δ across models.
5. Per-standard drift profile: standards with mean |Δ| > 1.0 across all conditions are identified; their statement-text features (length, F-K, vocabulary tier composition) are regressed on |Δ| as a Q3 / H4 exploratory analysis.
6. Decomposition: Sentence Structure and Vocabulary scores regressed on Δ, to attribute drift to syntactic vs lexical contributions.

**Exploratory cuts.** Anything else (jurisdiction × Δ interactions, subject × Δ interactions beyond ELA-vs-Math main effect, etc.) is reported as exploratory and not used for headline claims.

### 6.6 Pre-registration commitments

Before the full study run begins, the following are frozen and recorded in a tagged commit:

- The sample frame and seed.
- The prompt template (SHA recorded).
- Model IDs and decoding parameters.
- Evaluator versions and backend model IDs.
- The five primary analyses listed above with their specific test statistics and α levels.
- The H1-H4 predictions, in advance of seeing results.

The pilot (n=30) runs *before* this freeze and is allowed to influence the freeze (e.g., adjusting output length, refining prompt). The full study runs after.

## 7. Reproducibility

This study is designed so a reader with no privileged access can replicate the entire pipeline.

- **Standards data.** Public JSONL snapshot pinned at the time of publication. The snapshot date and file hashes are recorded in `data/processed/run_manifest.json`. The REST API is used during dev for speed but is not on the published reproduction path.
- **Code.** Open-source MIT-licensed (on public release). Includes the LC client, sampling, prompt template, generation driver, evaluation driver, and analysis notebook.
- **Generated artifacts.** All generated instruction texts, all evaluator scores, the complete run manifest, and the analysis notebook are released alongside the publication. Storage: a release artifact attached to the corresponding GitHub release tag.
- **External dependencies the reader needs.** An Anthropic API key (or the alternate model's key), an OpenAI API key, and a Google API key — the latter two for LC's evaluator backends. Costs are estimable from the run manifest and are reported in the paper.
- **Determinism.** Generation at temperature 0 plus pinned model IDs is reproducible up to provider drift. Evaluators are not deterministic, so test-retest variance is reported as part of the headline finding rather than swept under the rug.

The dual-license posture (MIT for code, CC BY 4.0 for data and prose; see [`LICENSE.md`](../LICENSE.md)) ensures all pieces can be vendored, cited, and remixed. Attribution requirements for upstream artifacts (LC, SAP, ANet, CLEAR, 1EdTech, state DOEs) are listed in [`attribution.md`](attribution.md) and reproduced in any publication.

## 8. Threats to validity

The threats below are surfaced from the literature review (§5) and from our own pre-mortem. Each is paired with a planned mitigation; some cannot be fully mitigated and remain as honest limitations.

**T1 — Self-preference and judge-generator architectural overlap.** Panickssery et al. (2024) showed evaluators favor their own family's generations. If LC's evaluator backends share architecture with our instruction generator, our drift estimate is biased toward zero for that condition. *Mitigation.* The cross-model condition partly addresses this. We pre-register a check: if the 2nd-model drift differs systematically from the primary-model drift, and the difference aligns with judge-family overlap, we flag the bias explicitly.

**T2 — Single-instrument dependence.** All headline claims ride on LC's Grade Level Appropriateness Evaluator. If its calibration is off, our deltas inherit the error. *Mitigation.* Convergent-validity check on a 50-standard subset against Flesch-Kincaid (always available) and Lexile (subject to API access). If correlation is r > 0.6 we treat divergence as expected qualitative-vs-quantitative differences; if r < 0.4 we treat it as a calibration concern requiring further investigation before publication.

**T3 — Output-type artifact.** Findings only generalize to the pinned 100–250-word explanation format. *Mitigation.* Acknowledged in scope.md and disclosed in the paper. A future study extends to lesson plans and worked examples.

**T4 — Standards-text confound.** A standard whose own wording is at grade 11 may push the model up regardless of the target grade. *Mitigation.* H4 explicitly tests this; if the standard's own F-K explains > 50% of |Δ| variance, the headline claim shifts from "LLMs drift" to "LLMs mirror the standard's register." Both are publishable; the framing changes.

**T5 — Verbosity-grade conflation in the evaluator.** Zheng et al. (2023) identified verbosity bias in LLM judges. If LC's Grade Level Appropriateness Evaluator scores longer text as higher-grade simply because it is longer, our pinned word-count range insulates against this within bands but not across them. *Mitigation.* Token-count distributions are reported per band; if outputs systematically lengthen with target grade, we pre-register a regression check controlling for token count.

**T6 — Convergent validity gap.** No published work demonstrates convergent validity between LC's evaluators and Lexile, F-K, or expert raters outside the CLEAR validation. *Mitigation.* T2's cross-walk check addresses this directly; we treat the cross-walk as a side-finding rather than a primary outcome.

**T7 — Multi-dimensionality of grade level.** SAP treats complexity as four qualitative dimensions; Lexile collapses to one. Whether our five evaluators are orthogonal facets or highly collinear is empirical. *Mitigation.* A factor analysis on the evaluator score matrix is run as a methodological subsidiary analysis and reported.

**T8 — Human-baseline ceiling.** Inter-rater agreement among expert teachers on grade-band placement is ~ICC 0.6-0.75 (Crossley et al., 2023; Nelson et al., 2012). Our evaluator cannot exceed inter-human agreement and remain interpretable. *Mitigation.* We report the human-baseline ICC alongside our evaluator's test-retest ICC explicitly.

**T9 — Prompt-sensitivity dominance.** Biderman et al. (2024) and Wang et al. (2024) repeatedly show that prompt variation can exceed model variation. *Mitigation.* The variability condition (multiple seeds, single prompt) characterizes within-prompt variance. A focused prompt-sensitivity sub-study with 3 prompt variants on a 30-standard subset characterizes between-prompt variance. If between-prompt > between-model, our cross-model claim is reported as "model-and-prompt-dependent" rather than "model-dependent."

**T10 — Provider drift.** Frontier model APIs evolve; the same model ID may produce subtly different outputs months apart. *Mitigation.* All generation timestamps are logged. Reruns of the published study, if attempted later, are expected to show provider-drift effects; we report this as a limitation of any LLM-based artifact.

## 9. Ethics and responsible disclosure

- **Human subjects.** The v0 study uses no student data, no human-rated content, and no PII. Standards text is public CC BY 4.0 material; LLM outputs are generated by the research team. No IRB review is required for v0.
- **Responsible AI disclosure.** Published artifacts disclose the full LLM stack (instruction generator + evaluator backends), API access dates, and known biases of each instrument. The paper includes an explicit statement that the evaluators are LLM-as-judge and inherit the biases documented in §5.2.
- **Misuse considerations.** Findings are cite-able in either direction: a "drift exists" finding could be used to argue that AI tutors are unsafe for K-12; a "no drift" finding could be used to argue the opposite. We mitigate over-claiming by publishing both the raw artifacts (per-standard scores, generated text) and the prose, so any claim can be cross-checked against the data.
- **Attribution and IP.** All upstream artifacts (LC, SAP, ANet, CLEAR, 1EdTech, state DOEs) are credited per [`attribution.md`](attribution.md). No proprietary content is included in the released artifacts.

## 10. Deliverables and timeline

| Phase | Deliverable | Target date |
|---|---|---|
| Pilot setup | `lc_client` working end-to-end; pilot sample (n=30) generated and scored; pipeline issues resolved | T+1 week |
| Pre-registration freeze | Sample frame, prompt, model IDs, evaluator versions, primary analyses, hypotheses — all committed and tagged | T+2 weeks |
| Full study run | Generation and scoring complete for n ≈ 300 across primary + cross-model conditions | T+3 weeks |
| Analysis | Notebooks for primary, secondary, and exploratory analyses; per-standard drift profiles; decomposition results | T+4 weeks |
| Internal review | Methodology + results reviewed against this proposal; threats-to-validity check; pre-publication adjustments only on exploratory analyses (primary remains pre-registered) | T+5 weeks |
| Blog publication | Public post; repo opened to MIT/CC-BY 4.0 license; release artifact attached to a tagged GitHub release | T+6 weeks |
| Follow-up | Per-standard entropy and hallucination proposal opened in a sibling repo | T+8 weeks |

T = pilot kickoff date. The 6-week-to-publication cadence aligns with the publishing-order plan in the parent question bank.

## 11. References

AERA, APA, & NCME. (2014). *Standards for educational and psychological testing*. American Educational Research Association.

Beck, I. L., McKeown, M. G., & Kucan, L. (2013). *Bringing words to life: Robust vocabulary instruction* (2nd ed.). Guilford Press.

Begeny, J. C., & Greene, D. J. (2014). Can readability formulas be used to successfully gauge difficulty of reading materials? *Psychology in the Schools, 51*(2), 198-215.

Biderman, S., Schoelkopf, H., Sutawika, L., Gao, L., Tow, J., Abbasi, B., Aji, A. F., Ammanamanchi, P. S., Black, S., Clive, J., DiPofi, A., Etxaniz, J., Fattori, B., Forde, J. Z., Foster, C., Hsu, J., Jaiswal, M., Lee, W. Y., Li, H., ... Wang, A. (2024). Lessons from the trenches on reproducible evaluation of language models. *arXiv preprint arXiv:2405.14782*. [preprint]

Chall, J. S., & Dale, E. (1995). *Readability revisited: The new Dale-Chall readability formula*. Brookline Books.

Cohen, J. (1960). A coefficient of agreement for nominal scales. *Educational and Psychological Measurement, 20*(1), 37-46.

Cohen, J. (1988). *Statistical power analysis for the behavioral sciences* (2nd ed.). Lawrence Erlbaum.

Crossley, S., Heintz, A., Choi, J. S., Batchelor, J., Karimi, M., & Malatinszky, A. (2023). A large-scaled corpus for assessing text readability. *Behavior Research Methods, 55*(2), 491-507.

Graesser, A. C., McNamara, D. S., Louwerse, M. M., & Cai, Z. (2004). Coh-Metrix: Analysis of text on cohesion and language. *Behavior Research Methods, Instruments, & Computers, 36*(2), 193-202.

Hedges, L. V., & Olkin, I. (1985). *Statistical methods for meta-analysis*. Academic Press.

Henkel, O., Hills, L., Roberts, B., McGrane, J., & Boyle, A. (2024). Can large language models make the grade? An empirical study evaluating LLMs ability to mark short answer questions in K-12 education. In *Proceedings of the 11th ACM Conference on Learning @ Scale (L@S '24)*. ACM.

Hill, C. J., Bloom, H. S., Black, A. R., & Lipsey, M. W. (2008). Empirical benchmarks for interpreting effect sizes in research. *Child Development Perspectives, 2*(3), 172-177.

Imperial, J. M., & Madabushi, H. T. (2023). Flesch or fumble? Evaluating readability standard alignment of instruction-tuned language models. In *Proceedings of the 18th Workshop on Innovative Use of NLP for Building Educational Applications (BEA)* at ACL 2023.

Kestin, G., Miller, K., Klales, A., Milbourne, T., & Ponti, G. (2024). *AI tutoring outperforms active learning* (Working paper). Harvard University. [preprint / working paper]

Kew, T., & Ebling, S. (2022). Target-level sentence simplification as controlled paraphrasing. In *Proceedings of EACL 2022*.

Kim, S., Suk, J., Longpre, S., Lin, B. Y., Shin, J., Welleck, S., Neubig, G., Lee, M., Lee, K., & Seo, M. (2024). Prometheus 2: An open source language model specialized in evaluating other language models. In *Proceedings of EMNLP 2024*.

Kincaid, J. P., Fishburne, R. P., Rogers, R. L., & Chissom, B. S. (1975). *Derivation of new readability formulas for Navy enlisted personnel* (Research Branch Report 8-75). Naval Technical Training Command.

Koo, T. K., & Li, M. Y. (2016). A guideline of selecting and reporting intraclass correlation coefficients for reliability research. *Journal of Chiropractic Medicine, 15*(2), 155-163.

LearnLM Team, Google DeepMind. (2024). *LearnLM: Improving Gemini for learning* (Technical report). Google DeepMind. [grey literature]

Liang, P., Bommasani, R., Lee, T., Tsipras, D., Soylu, D., Yasunaga, M., Zhang, Y., Narayanan, D., Wu, Y., Kumar, A., Newman, B., Yuan, B., Yan, B., Zhang, C., Cosgrove, C., Manning, C. D., Ré, C., Acosta-Navas, D., Hudson, D. A., ... Koreeda, Y. (2023). Holistic evaluation of language models. *Transactions on Machine Learning Research*.

Macina, J., Daheim, N., Chowdhury, S. P., Sinha, T., Kapur, M., Gurevych, I., & Sachan, M. (2023). MathDial: A dialogue tutoring dataset with rich pedagogical properties grounded in math reasoning problems. In *Findings of EMNLP 2023*.

McHugh, M. L. (2012). Interrater reliability: The kappa statistic. *Biochemia Medica, 22*(3), 276-282.

McNamara, D. S., Graesser, A. C., McCarthy, P. M., & Cai, Z. (2014). *Automated evaluation of text and discourse with Coh-Metrix*. Cambridge University Press.

National Center for Education Statistics. (2022). *NAEP reading framework*. U.S. Department of Education. [grey literature]

Nelson, J., Perfetti, C., Liben, D., & Liben, M. (2012). *Measures of text difficulty: Testing their predictive value for grade levels and student performance* (Report to the Gates Foundation). Student Achievement Partners. [grey literature]

Padmakumar, V., & He, H. (2024). Does writing with language models reduce content diversity? In *Proceedings of ICLR 2024*.

Panickssery, A., Bowman, S. R., & Feng, S. (2024). LLM evaluators recognize and favor their own generations. *arXiv preprint arXiv:2404.13076*. [preprint]

Pardos, Z. A., & Bhandari, S. (2024). ChatGPT-generated help produces learning gains equivalent to human tutor-authored help on mathematics skills. *Computers and Education: Artificial Intelligence, 6*, 100244.

Renaissance Learning. (2000). *The ATOS readability formula for books and how it compares to other formulas* (Technical report). Renaissance Learning. [grey literature]

Ribeiro, L. F. R., Bansal, M., & Dreyer, M. (2023). Generating summaries with controllable readability levels. In *Proceedings of EMNLP 2023*.

Shrout, P. E., & Fleiss, J. L. (1979). Intraclass correlations: Uses in assessing rater reliability. *Psychological Bulletin, 86*(2), 420-428.

Sonkar, S., Liu, N., Mallick, D., & Baraniuk, R. G. (2023). CLASS: A design framework for building intelligent tutoring systems based on learning science principles. In *Findings of EMNLP 2023*.

Stenner, A. J., Burdick, H., Sanford, E. E., & Burdick, D. S. (2006). How accurate are Lexile text measures? *Journal of Applied Measurement, 7*(3), 307-322.

Stowe, K., Sourati, Z., Edward, A., Kapanipathi, P., & Forbus, K. (2024). Controllable text simplification with LLMs: A multi-dimensional analysis. In *Proceedings of NAACL 2024*.

Student Achievement Partners. (2013). *Qualitative measures rubric for literary and informational text*. Student Achievement Partners / Achieve the Core. [grey literature]

Trott, S., & Rivière, P. (2024). Measuring and modifying the readability of English texts with GPT-4. *Computers in Human Behavior: Artificial Humans, 2*(2), 100090.

Verga, P., Hofstätter, S., Althammer, S., Su, Y., Piktus, A., Arkhangorodsky, A., Xu, M., White, N., & Lewis, P. (2024). Replacing judges with juries: Evaluating LLM generations with a panel of diverse models. *arXiv preprint arXiv:2404.18796*. [preprint]

Wang, P., Li, L., Chen, L., Cai, Z., Zhu, D., Lin, B., Cao, Y., Liu, Q., Liu, T., & Sui, Z. (2024). Large language models are not fair evaluators. In *Proceedings of ACL 2024*.

Zheng, L., Chiang, W.-L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z., Li, Z., Xing, E. P., Gonzalez, J. E., Stoica, I., & Hashimoto, T. (2023). Judging LLM-as-a-judge with MT-Bench and Chatbot Arena. In *Advances in Neural Information Processing Systems 36 (NeurIPS 2023) Datasets and Benchmarks Track*.
