"""Score every generation + every standard's raw and simplified descriptions.

Reads the generation files in `data/generated/{run_id}/`, the cached rewrites
in `data/interim/rewrites/{rewriter_model}/`, and the sub-sample in
`data/processed/v0_subpilot_sample.json`. Runs the deterministic scoring
stack on each text and writes a per-row parquet at
`data/results/{run_id}_scores.parquet`.

Three row types appear in the parquet:

- `kind="generation"` — one row per cell in the generation cube
- `kind="standard_raw"` — one row per standard (its own raw description)
- `kind="standard_simplified"` — one row per standard (the cached rewrite)

Pure CPU; no API calls. Idempotent except for the `created_at` field.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.evaluators import FEATURE_COLUMNS, score
from src.openai_helpers import REPO_ROOT

SUBSAMPLE_PATH = REPO_ROOT / "data" / "processed" / "v0_subpilot_sample.json"
GENERATED_DIR = REPO_ROOT / "data" / "generated"
REWRITES_DIR = REPO_ROOT / "data" / "interim" / "rewrites"
RESULTS_DIR = REPO_ROOT / "data" / "results"


def numeric_grade(grade_level: list[str] | None) -> float | None:
    """Map a `gradeLevel` field to a numeric target. K → 0, "9-12" → 10.5."""
    if not grade_level:
        return None
    nums: list[float] = []
    for g in grade_level:
        if g == "K":
            nums.append(0.0)
        else:
            try:
                nums.append(float(g))
            except ValueError:
                continue
    if not nums:
        return None
    return sum(nums) / len(nums)


def grade_band(target: float | None) -> str:
    if target is None:
        return "unknown"
    if target <= 2:
        return "K-2"
    if target <= 5:
        return "3-5"
    if target <= 8:
        return "6-8"
    return "9-12"


def _score_with_meta(text: str, meta: dict[str, Any]) -> dict[str, Any]:
    row: dict[str, Any] = dict(meta)
    s = score(text)
    for col in FEATURE_COLUMNS:
        row[col] = s.get(col)
    target = meta.get("target_grade")
    eg = s.get("ensemble_grade_median")
    if target is not None and eg is not None and not (isinstance(eg, float) and pd.isna(eg)):
        row["delta_ensemble"] = float(eg) - float(target)
    else:
        row["delta_ensemble"] = float("nan")
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--rewriter-model",
        default="gpt-4.1",
        help="Rewriter model whose cached simplified wordings to score",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output parquet path (default: data/results/{run_id}_scores.parquet)",
    )
    args = parser.parse_args()

    sub = json.loads(SUBSAMPLE_PATH.read_text(encoding="utf-8"))
    standards = {s["identifier"]: s for s in sub["items"]}

    gen_dir = GENERATED_DIR / args.run_id
    if not gen_dir.exists():
        raise SystemExit(f"no generations at {gen_dir.relative_to(REPO_ROOT)}")
    cell_files = sorted(gen_dir.glob("*.json"))
    if not cell_files:
        raise SystemExit(f"no cell files in {gen_dir.relative_to(REPO_ROOT)}")
    print(f"scoring {len(cell_files)} generations + {len(standards)*2} standard texts")

    rows: list[dict[str, Any]] = []

    # 1) generations
    for i, p in enumerate(cell_files, start=1):
        cell = json.loads(p.read_text(encoding="utf-8"))
        std = standards.get(cell["standard_id"], {})
        target = numeric_grade(cell.get("grade_level") or std.get("grade_level"))
        meta = {
            "kind": "generation",
            "run_id": args.run_id,
            "cell_key": p.stem,
            "model": cell["model"],
            "model_returned": cell.get("model_returned"),
            "prompt_name": cell["prompt_name"],
            "prompt_sha": cell.get("prompt_sha"),
            "wording": cell["wording"],
            "standard_id": cell["standard_id"],
            "statement_code": cell.get("statement_code"),
            "subject": std.get("academic_subject"),
            "grade_level_raw": ",".join(cell.get("grade_level") or []) or None,
            "target_grade": target,
            "grade_band": grade_band(target),
            "prompt_tokens": cell.get("prompt_tokens"),
            "completion_tokens": cell.get("completion_tokens"),
            "finish_reason": cell.get("finish_reason"),
        }
        rows.append(_score_with_meta(cell["output_text"], meta))
        if i % 100 == 0 or i == len(cell_files):
            print(f"  generations: {i}/{len(cell_files)}")

    # 2) raw + simplified standard descriptions (covariates)
    for j, (sid, std) in enumerate(standards.items(), start=1):
        target = numeric_grade(std.get("grade_level"))
        base_meta = {
            "run_id": args.run_id,
            "cell_key": None,
            "model": None,
            "model_returned": None,
            "prompt_name": None,
            "prompt_sha": None,
            "wording": None,
            "standard_id": sid,
            "statement_code": std.get("statement_code"),
            "subject": std.get("academic_subject"),
            "grade_level_raw": ",".join(std.get("grade_level") or []) or None,
            "target_grade": target,
            "grade_band": grade_band(target),
            "prompt_tokens": None,
            "completion_tokens": None,
            "finish_reason": None,
        }

        rows.append(
            _score_with_meta(
                std["description"],
                {**base_meta, "kind": "standard_raw"},
            )
        )

        rewrite_path = REWRITES_DIR / args.rewriter_model / f"{sid}.json"
        if rewrite_path.exists():
            rw = json.loads(rewrite_path.read_text(encoding="utf-8"))
            rows.append(
                _score_with_meta(
                    rw.get("simplified_description") or "",
                    {**base_meta, "kind": "standard_simplified"},
                )
            )

        if j % 20 == 0 or j == len(standards):
            print(f"  standards: {j}/{len(standards)}")

    df = pd.DataFrame(rows)
    df["scored_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    out = Path(args.out) if args.out else RESULTS_DIR / f"{args.run_id}_scores.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"\nwrote {len(df):,} rows → {out.relative_to(REPO_ROOT)}")
    # quick sanity summary
    by_kind = df["kind"].value_counts().to_dict()
    print(f"  rows by kind: {by_kind}")
    gens = df[df["kind"] == "generation"]
    if len(gens):
        print(
            f"  Δ ensemble: mean={gens['delta_ensemble'].mean():.2f} "
            f"median={gens['delta_ensemble'].median():.2f} "
            f"sd={gens['delta_ensemble'].std():.2f} "
            f"min={gens['delta_ensemble'].min():.2f} max={gens['delta_ensemble'].max():.2f}"
        )


if __name__ == "__main__":
    main()
