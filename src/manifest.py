"""Run-manifest writer.

A run manifest is the single committable artifact that ties a set of model
outputs and per-output scores back to *exactly* the inputs and configuration
that produced them. Required fields are listed in
[docs/methodology.md §7](../docs/methodology.md).

Idempotent: writing the same manifest twice produces byte-identical JSON.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import platform
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from src.evaluators import stack_metadata
from src.openai_helpers import REPO_ROOT
from src.prompts import GENERATOR_PROMPTS, REWRITER_PROMPT

PROCESSED_DIR = REPO_ROOT / "data" / "processed"


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _python_dependency_versions(packages: list[str]) -> dict[str, str | None]:
    from importlib.metadata import PackageNotFoundError, version

    out: dict[str, str | None] = {}
    for p in packages:
        try:
            out[p] = version(p)
        except PackageNotFoundError:
            out[p] = None
    return out


@dataclass
class RunManifest:
    run_id: str
    started_at: str
    sample_path: str
    sample_sha256: str
    rewriter_model: str
    generator_models: list[str]
    seed: int
    n_standards: int
    n_prompt_variants: int
    n_wording_conditions: int
    expected_n_cells: int
    notes: str = ""

    # filled in by helpers below
    prompt_shas: dict[str, str] = field(default_factory=dict)
    rewriter_prompt_sha: str = ""
    scoring_stack: dict[str, Any] = field(default_factory=dict)
    environment: dict[str, Any] = field(default_factory=dict)
    completed_at: str | None = None
    actual_n_cells: int | None = None
    usage: dict[str, Any] | None = None

    @classmethod
    def build(
        cls,
        *,
        run_id: str,
        sample_path: Path,
        rewriter_model: str,
        generator_models: list[str],
        seed: int,
        notes: str = "",
    ) -> "RunManifest":
        sample_data = json.loads(sample_path.read_text(encoding="utf-8"))
        items = sample_data.get("items", [])
        n_standards = len(items)
        m = cls(
            run_id=run_id,
            started_at=dt.datetime.now(dt.timezone.utc).isoformat(),
            sample_path=str(sample_path.relative_to(REPO_ROOT)),
            sample_sha256=_file_sha256(sample_path),
            rewriter_model=rewriter_model,
            generator_models=generator_models,
            seed=seed,
            n_standards=n_standards,
            n_prompt_variants=len(GENERATOR_PROMPTS),
            n_wording_conditions=2,
            expected_n_cells=len(generator_models)
            * len(GENERATOR_PROMPTS)
            * 2
            * n_standards,
            notes=notes,
        )
        m.prompt_shas = {name: spec.sha for name, spec in GENERATOR_PROMPTS.items()}
        m.rewriter_prompt_sha = REWRITER_PROMPT.sha
        m.scoring_stack = stack_metadata()
        m.environment = {
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "packages": _python_dependency_versions(
                [
                    "openai",
                    "textstat",
                    "spacy",
                    "pandas",
                    "numpy",
                    "scipy",
                    "plotly",
                    "pyarrow",
                ]
            ),
        }
        return m

    def mark_complete(
        self, *, actual_n_cells: int, usage: dict[str, Any] | None = None
    ) -> None:
        self.completed_at = dt.datetime.now(dt.timezone.utc).isoformat()
        self.actual_n_cells = actual_n_cells
        if usage is not None:
            self.usage = usage

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write(self, dest: Path | None = None) -> Path:
        dest = dest or PROCESSED_DIR / f"{self.run_id}_manifest.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return dest


def default_run_id(prefix: str = "v0") -> str:
    """`v0_20260505_142233` — UTC timestamp slug."""
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Write a run manifest stub")
    parser.add_argument("--run-id", default=default_run_id())
    parser.add_argument(
        "--sample",
        default=str(PROCESSED_DIR / "v0_subpilot_sample.json"),
    )
    parser.add_argument("--rewriter-model", default="gpt-4.1")
    parser.add_argument(
        "--generator-models",
        default="gpt-5.5,gpt-5.4,gpt-4.1",
        help="Comma-separated list",
    )
    parser.add_argument("--seed", type=int, default=20260504)
    parser.add_argument("--notes", default="manifest stub")
    args = parser.parse_args()

    m = RunManifest.build(
        run_id=args.run_id,
        sample_path=Path(args.sample),
        rewriter_model=args.rewriter_model,
        generator_models=[s.strip() for s in args.generator_models.split(",") if s.strip()],
        seed=args.seed,
        notes=args.notes,
    )
    out = m.write()
    print(f"wrote stub manifest → {out.relative_to(REPO_ROOT)}")
    print(json.dumps(m.to_dict(), indent=2, sort_keys=True))
