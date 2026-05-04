# Data Sources — Decision Record

**Status:** decided
**Last updated:** 2026-05-04

## Decision

**Standards data comes from the [Learning Commons Knowledge Graph](https://learningcommons.org/for-developers/#knowledge-graph)**, with the REST API used during the pilot phase and a frozen JSONL snapshot pinned for the published artifact.

## Why

- Multi-state, multi-subject, K-12 standards in a single API surface, anchored on CASE Network 2 (1EdTech).
- License is **CC BY 4.0** — fully redistributable with attribution.
- Comes pre-aligned to Learning Commons' Evaluators, the exact instruments we use for scoring. No alignment layer to build.
- Active maintenance and crosswalks across 15+ states for math.

## Access modes

| Mode | Endpoint / location | Status (2026-05) | Tradeoff |
|---|---|---|---|
| REST API | `https://api.learningcommons.org/knowledge-graph/v0` | Private beta | Live, fast iteration; depends on beta access for reruns |
| MCP server | (via Learning Commons Platform) | Private beta | Convenient for dev exploration; not used in the published pipeline |
| Local JSONL exports | learningcommons.org / GitHub | Public | No auth; reproducible by anyone; pinned for paper |

## Use plan

- **Pilot and dev:** REST API. Faster iteration; key in `.env` (gitignored).
- **Published artifact freeze:** snapshot to JSONL, depend only on JSONL. The snapshot date is recorded in `data/processed/run_manifest.json`. Anyone can rerun the entire pipeline with only a public JSONL download + their own LLM API keys.

This split — beta API for dev, public JSONL for publication — gives us iteration speed now and reproducibility later, without committing to the limitations of either side prematurely.

## Authentication

LC REST API uses `x-api-key` header. The key lives in `.env` (gitignored from the very first commit; see `.gitignore`). The `.env.example` documents the variables expected.

## License and attribution

Knowledge Graph data is CC BY 4.0. The required attribution line is captured per-record in the API response under `attributionStatement` and reproduced in [`attribution.md`](attribution.md). The provenance chain is:

```
state DOEs → 1EdTech CASE Network 2 → Learning Commons Knowledge Graph
```

We surface the chain in any methodology disclosure.

## What we do not commit to the repo

- Bulk standards data — pulled on demand or fetched into `data/raw/` (gitignored). Reproducible from the API or public JSONL.
- API responses containing the key — never written to disk.

## Out of scope (this study)

- Direct state DOE scrapes (deferred; the standards-substrate project handles the fidelity question separately).
- CASE Network direct access (LC already wraps this).
- Commercial standards aggregators (Academic Benchmarks, EdGate) — paid, licensing-restrictive.
- Pre-K, postsecondary, CTE — out per `scope.md`.
