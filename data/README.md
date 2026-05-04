# data/

Conventions for data handling in this investigation.

## Three commitments

1. **`data/raw/` is immutable.** Files in this directory are never edited in place. If a transformation produces a new view of the data, it lands in `data/interim/` or `data/processed/` as a new file. If raw data is corrupted or stale, re-fetch from the source per [`docs/data-sources.md`](../docs/data-sources.md) — don't patch in place.

2. **Every transformation is provenanced.** Each derived file has a clear lineage: which raw input it came from, which script produced it, when, and (if applicable) which `run_id`. The `data/processed/{run_id}_manifest.json` captures this for analysis runs (schema in [`docs/methodology.md §5`](../docs/methodology.md)); ad-hoc transformations write a sibling `.provenance.json` next to the output file.

3. **Notebooks are exploration; `src/` is canonical.** Anything that's run more than twice or that produces a result we cite belongs in a Python module under `src/`. Notebooks are for one-off exploration, sanity checks, and the final analysis driver — not for production logic.

## Layout

| Subdir | Role | Committed? |
|---|---|---|
| `data/raw/` | Immutable source data — pulled from APIs or downloads | **No** (gitignored) |
| `data/interim/` | Intermediate transformations (cleaned, joined, filtered, etc.) | **No** by default; commit selectively if reproducibility benefits |
| `data/processed/` | Sample frames, run manifests, aggregated results, published artifacts | **Yes** |
| `data/generated/{run_id}/` | Per-run raw outputs (e.g., LLM completions) | **Yes** for published runs; write-once per `run_id` |
| `data/results/{run_id}_scores.parquet` | Per-output scores from measurement instruments | **Yes** for published runs |

## Etiquette

- **Don't `rm` from `data/raw/`.** If raw data is wrong, re-fetch (regenerable by design).
- **Don't overwrite a `run_id`.** New runs get new IDs. The previous artifact stays as evidence of the prior result.
- **Never commit data files containing API keys.** API responses with embedded credentials should be redacted before any commit.
- **Cross-reference `data-sources.md`.** Any access decision (which source, which mode, what license) lives there, not here.
