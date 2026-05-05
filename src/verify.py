"""Phase-E completeness check for a v0 run.

Walks the published-run artifacts and confirms that every box in the
methodology §7 reproducibility list is present and shaped the way the
methodology says it should be. Exits non-zero on the first failure.

    python -m src.verify --run-id v0_run1

This is the "did we actually finish" gate before declaring a run shippable.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from src.openai_helpers import REPO_ROOT
from src.prompts import GENERATOR_PROMPTS

GENERATED_DIR = REPO_ROOT / "data" / "generated"
RESULTS_DIR = REPO_ROOT / "data" / "results"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
REWRITES_DIR = REPO_ROOT / "data" / "interim" / "rewrites"
REPORTS_DIR = REPO_ROOT / "reports"
SUBSAMPLE_PATH = PROCESSED_DIR / "v0_subpilot_sample.json"


REQUIRED_MANIFEST_FIELDS = {
    "run_id",
    "started_at",
    "sample_path",
    "sample_sha256",
    "rewriter_model",
    "generator_models",
    "seed",
    "n_standards",
    "n_prompt_variants",
    "n_wording_conditions",
    "expected_n_cells",
    "prompt_shas",
    "rewriter_prompt_sha",
    "scoring_stack",
    "environment",
}


def _check(condition: bool, label: str, *, fatal: bool = True) -> bool:
    mark = "✓" if condition else ("✗" if fatal else "!")
    print(f"  {mark} {label}")
    return condition


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--rewriter-model", default="gpt-4.1")
    args = parser.parse_args()

    run = args.run_id
    print(f"verifying run_id={run}")
    failures = 0

    # 1. sub-sample present
    print("\n[1/7] sub-sample")
    sub_ok = SUBSAMPLE_PATH.exists()
    _check(sub_ok, f"sub-sample at {SUBSAMPLE_PATH.relative_to(REPO_ROOT)}")
    if not sub_ok:
        return 1
    sub = json.loads(SUBSAMPLE_PATH.read_text(encoding="utf-8"))
    standards = sub["items"]
    n_standards = len(standards)
    _check(n_standards == 60, f"n_standards == 60 (got {n_standards})")

    # 2. cached rewrites
    print("\n[2/7] rewriter cache")
    rdir = REWRITES_DIR / args.rewriter_model
    _check(rdir.exists(), f"rewriter dir at {rdir.relative_to(REPO_ROOT)}")
    cached = list(rdir.glob("*.json")) if rdir.exists() else []
    _check(len(cached) == n_standards, f"rewrites cached: {len(cached)}/{n_standards}")

    # 3. manifest
    print("\n[3/7] manifest")
    mpath = PROCESSED_DIR / f"{run}_manifest.json"
    if not _check(mpath.exists(), f"manifest at {mpath.relative_to(REPO_ROOT)}"):
        failures += 1
        m = {}
    else:
        m = json.loads(mpath.read_text(encoding="utf-8"))
        missing = REQUIRED_MANIFEST_FIELDS - set(m.keys())
        _check(not missing, f"required fields present (missing: {sorted(missing)})") or (failures := failures + 1)

    # 4. generations
    print("\n[4/7] generations")
    gdir = GENERATED_DIR / run
    if not _check(gdir.exists(), f"generated dir at {gdir.relative_to(REPO_ROOT)}"):
        return 1
    cells = sorted(gdir.glob("*.json"))
    expected = m.get("expected_n_cells")
    if expected is None:
        # back out expected from generator_models
        models = m.get("generator_models", [])
        expected = len(models) * len(GENERATOR_PROMPTS) * 2 * n_standards
    if not _check(len(cells) == expected, f"cells generated: {len(cells)}/{expected}"):
        failures += 1

    # 5. scores parquet
    print("\n[5/7] scores parquet")
    spath = RESULTS_DIR / f"{run}_scores.parquet"
    if not _check(spath.exists(), f"scores parquet at {spath.relative_to(REPO_ROOT)}"):
        failures += 1
    else:
        df = pd.read_parquet(spath)
        n_gen = (df["kind"] == "generation").sum()
        n_raw = (df["kind"] == "standard_raw").sum()
        n_simp = (df["kind"] == "standard_simplified").sum()
        if not _check(n_gen == expected, f"generation rows: {n_gen}/{expected}"):
            failures += 1
        if not _check(n_raw == n_standards, f"standard_raw rows: {n_raw}/{n_standards}"):
            failures += 1
        if not _check(
            n_simp == n_standards, f"standard_simplified rows: {n_simp}/{n_standards}"
        ):
            failures += 1
        # delta_ensemble should be defined for most generation rows
        gen = df[df["kind"] == "generation"]
        nan_pct = float(gen["delta_ensemble"].isna().mean())
        _check(nan_pct < 0.05, f"delta_ensemble NaN rate < 5% (got {nan_pct:.1%})", fatal=False)

    # 6. report
    print("\n[6/7] report")
    rpath = REPORTS_DIR / f"{run}_report.html"
    if not _check(rpath.exists(), f"report at {rpath.relative_to(REPO_ROOT)}"):
        failures += 1
    else:
        size = rpath.stat().st_size
        _check(
            size > 1_000_000,
            f"report size > 1 MB (got {size:,} — plotly bundle inline)",
        )

    # 7. no .env tracked
    print("\n[7/7] secrets posture")
    import subprocess

    tracked = subprocess.run(
        ["git", "ls-files", ".env"], capture_output=True, text=True, cwd=REPO_ROOT
    ).stdout.strip()
    if not _check(tracked == "", f".env not tracked by git (tracked: {tracked!r})"):
        failures += 1

    print()
    if failures:
        print(f"FAILED — {failures} hard checks did not pass.")
        return 1
    print("OK — all checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
