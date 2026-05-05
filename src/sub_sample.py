"""Draw the v0 sub-pilot sample from the parent pilot sample.

The parent sample (`data/processed/pilot_v1_sample.json`) contains 100
standards per subject. v0 runs on a deterministic random subset of 30 per
subject (60 total). Re-running with the same seed produces the identical
sub-sample.

    python -m src.sub_sample
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import random
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"

PARENT_PATH = PROCESSED_DIR / "pilot_v1_sample.json"
OUT_PATH = PROCESSED_DIR / "v0_subpilot_sample.json"

SUB_SAMPLE_ID = "v0_subpilot"
N_PER_SUBJECT = 30
SEED = 20260504


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    if not PARENT_PATH.exists():
        raise SystemExit(
            f"Parent sample missing at {PARENT_PATH.relative_to(REPO_ROOT)}. "
            "Run `python -m src.snapshot && python -m src.sample` first."
        )

    parent = json.loads(PARENT_PATH.read_text(encoding="utf-8"))
    parent_sha = _file_sha256(PARENT_PATH)

    rng = random.Random(SEED)
    items: list[dict[str, Any]] = []
    per_subject_summary: list[dict[str, Any]] = []

    for subject in ("English Language Arts", "Mathematics"):
        subject_pool = [i for i in parent["items"] if i["academic_subject"] == subject]
        if len(subject_pool) < N_PER_SUBJECT:
            raise SystemExit(
                f"{subject}: only {len(subject_pool)} eligible in parent, "
                f"need {N_PER_SUBJECT}"
            )
        drawn = rng.sample(subject_pool, N_PER_SUBJECT)
        items.extend(drawn)
        per_subject_summary.append(
            {
                "subject": subject,
                "parent_pool_size": len(subject_pool),
                "drawn": N_PER_SUBJECT,
            }
        )

    manifest = {
        "sample_id": SUB_SAMPLE_ID,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "produced_by": "src/sub_sample.py",
        "seed": SEED,
        "n_per_subject": N_PER_SUBJECT,
        "n_total": N_PER_SUBJECT * 2,
        "parent_sample": {
            "path": str(PARENT_PATH.relative_to(REPO_ROOT)),
            "sha256": parent_sha,
            "sample_id": parent.get("sample_id"),
            "created_at": parent.get("created_at"),
        },
        "per_subject": per_subject_summary,
        "items": items,
    }

    OUT_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"sub-sample written → {OUT_PATH.relative_to(REPO_ROOT)}")
    print(f"  total items: {len(items)}")
    for s in per_subject_summary:
        print(f"  {s['subject']}: drew {s['drawn']} of {s['parent_pool_size']}")


if __name__ == "__main__":
    main()
