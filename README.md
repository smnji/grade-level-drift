# grade-level-drift

Investigating whether LLM-generated K-12 instruction lands at the target standard's grade level — or systematically drifts.

This is the first investigation in a multi-part series. The full research plan, literature review, and methodology live in [`docs/research-proposal.md`](docs/research-proposal.md).

## Central question

**For an LLM asked to generate student-facing instruction for a K-12 academic standard at grade N, does the produced text land at grade N's reading level — or does it systematically drift?**

## Why this matters

If LLM tutors and content generators systematically miss the target reading level, every downstream claim about "AI-personalized learning" inherits that miss. Reading-level drift is also the cleanest first measurement to take: the instrument exists ([Learning Commons' Grade Level Appropriateness Evaluator](https://docs.learningcommons.org/evaluators/literacy-evaluators/grade-level-appropriateness-evaluator/about-this-evaluator)), no student-interaction data is required, and the result is publishable in either direction.

## Layout

| Path | What |
|---|---|
| [`docs/`](docs/) | Charter, scope, methodology, data-source decisions, attribution, research log, and the full research proposal |
| [`src/`](src/) | Python modules: LC API client, sampling, generation, evaluation, analysis |
| [`data/`](data/) | Local data (most contents gitignored — regenerable from the API or JSONL exports) |
| [`notebooks/`](notebooks/) | Exploratory and pilot analyses |

Start at [`docs/research-proposal.md`](docs/research-proposal.md) for the full picture, or [`docs/charter.md`](docs/charter.md) for the question map.

## Quickstart (once dependencies are installed)

```bash
cp .env.example .env  # then fill in API keys
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -c "from src.lc_client import LCClient; print(LCClient().list_frameworks()[:3])"
```

## Status

Pre-pilot. Repo initialized 2026-05-04. Charter, scope, methodology, and full research proposal complete. Pilot run pending resolution of the four open decisions in [`docs/scope.md`](docs/scope.md#decisions-still-open).

## Data and methodology dependencies

This work builds on:

- **Learning Commons Knowledge Graph** — academic standards data, CC BY 4.0
- **Learning Commons Evaluators** — literacy evaluation instruments, MIT licensed, co-designed with Student Achievement Partners and the Achievement Network

Full attribution in [`docs/attribution.md`](docs/attribution.md).

## License

Private during research; intended public-release posture is MIT (code) + CC BY 4.0 (data and prose). See [`LICENSE.md`](LICENSE.md).
