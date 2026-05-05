# grade-level-drift

Investigating whether LLM-generated K-12 instruction lands at the target standard's grade level — or systematically drifts.

This is the first investigation in a multi-part series. The full research plan, literature review, and methodology live in [`docs/research-proposal.qmd`](docs/research-proposal.qmd).

## Central question

**For an LLM asked to generate student-facing instruction for a K-12 academic standard at grade N, does the produced text land at grade N's reading level — or does it systematically drift?**

## Why this matters

If LLM tutors and content generators systematically miss the target reading level, every downstream claim about "AI-personalized learning" inherits that miss. Reading-level drift is also the cleanest first measurement to take: the instruments exist (50+ years of validated open-source readability formulas — Flesch-Kincaid, SMOG, Coleman-Liau, Dale-Chall — combined with vocabulary-tier and dependency-parsing features, optionally calibrated against the open [CLEAR expert-rated corpus](https://github.com/scrosseye/CLEAR-Corpus)), no student-interaction data is required, and the result is publishable in either direction.

## Layout

| Path | What |
|---|---|
| [`docs/`](docs/) | Charter, scope, methodology, data-source decisions, attribution, research log, and the full research proposal |
| [`src/`](src/) | Python modules: LC API client, sampling, generation, evaluation, analysis |
| [`data/`](data/) | Local data (most contents gitignored — regenerable from the API or JSONL exports) |
| [`notebooks/`](notebooks/) | Exploratory and pilot analyses |

Start at [`docs/research-proposal.qmd`](docs/research-proposal.qmd) for the full picture, or [`docs/charter.md`](docs/charter.md) for the question map.

## Quickstart (once dependencies are installed)

```bash
cp .env.example .env  # then fill in API keys (OPENAI_API_KEY, LC_API_KEY)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python -c "from src.lc_client import LCClient; print(LCClient().list_frameworks()[:3])"
```

## Reproducing a v0 run end-to-end

```bash
# 1. snapshot + sample (LC API; cached locally after the first run)
python -m src.snapshot
python -m src.sample
python -m src.sub_sample

# 2. generation cube (OpenAI API — ~$10-25 wall-clock cost)
python -m src.rewrite                          # 60 cached simplified wordings
python -m src.generate --run-id v0_run1        # 1,080 cells, idempotent on cell_key

# 3. deterministic scoring + interactive report (no API calls)
python -m src.score --run-id v0_run1
python -m src.report --run-id v0_run1
open reports/v0_run1_report.html
```

Full operational spec: [`docs/methodology.md`](docs/methodology.md). Each run pins a manifest at `data/processed/{run_id}_manifest.json` capturing model IDs, prompt SHAs, evaluator versions, and dataset SHA — that file is the reproducibility contract.

## Status

**v0 pilot + intervention complete (2026-05-05).**

- **v0_run1 (baseline):** n = 1,080 generations × 3 OpenAI frontier models × 3 prompt variants × 2 wording conditions × 60 CCSS standards. Headline: mean Δ = **+3.29 grade levels above target** (Cohen's d = 1.49; 92% of cells above zero). Cross-model ICC(2,1) = 0.89; direction-preservation = 95%.
- **The reframe:** the prompt itself sits +3.19 grade levels above target. The model is mostly inheriting the prompt's register, not adding drift on top of it (population-mean residual = +0.10).
- **v0_run2 (intervention):** 180 generations, same 60 standards × 3 models, with the *whole prompt* rewritten at each standard's target grade. Headline: mean Δ = **+1.25** (Cohen's d = 0.56; 73% above zero). Paired t-test reduction +1.87 grade levels, t = 9.13, p ≈ 10⁻¹⁶. **62% of the baseline gap closes** when the prompt is at-target; the residual ~+1.3 is bottlenecked by the rewriter's own drift at extreme grade bands.

See [`docs/research-log/2026-05-05-v0-run1-results.md`](docs/research-log/2026-05-05-v0-run1-results.md), [`docs/research-log/2026-05-05-v0-run2-prompt-at-target.md`](docs/research-log/2026-05-05-v0-run2-prompt-at-target.md), and [`reports/v0_run1_report.html`](reports/v0_run1_report.html) (§11 contains the intervention comparison). Pre-registration freeze (`pre-reg-v1`) is the next milestone.

## Data and methodology dependencies

This work builds on:

- **Learning Commons Knowledge Graph** — academic standards data, CC BY 4.0
- **`textstat`** (MIT) — classical readability formula ensemble (Flesch-Kincaid, SMOG, Coleman-Liau, ARI, Gunning Fog, Dale-Chall)
- **spaCy** (MIT) — dependency parsing for syntactic complexity features
- **Coxhead's Academic Word List** + **New General Service List** — open vocabulary-tier references
- **CLEAR corpus** — expert-rated grade-level benchmark for optional ridge-regression calibration

Full attribution in [`docs/attribution.md`](docs/attribution.md). Evaluation is fully deterministic; no LLM-as-judge in v0.

## License

Private during research; intended public-release posture is MIT (code) + CC BY 4.0 (data and prose). See [`LICENSE.md`](LICENSE.md).
