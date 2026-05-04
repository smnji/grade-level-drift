"""Draw the pilot sample from raw LC framework snapshots.

Filters each subject's snapshot to leaf learning expectations
(`normalizedStatementType == "Standard"`), then takes a deterministic
simple random sample of `n` items per subject. Writes a single
self-contained manifest to `data/processed/pilot_sample_v1.json`.

Run after `src.snapshot` has populated `data/raw/lc/{YYYY-MM-DD}/`:

    python -m src.sample
"""

from __future__ import annotations

import datetime as dt
import json
import random
from pathlib import Path
from typing import Any

from src.snapshot import CC_FRAMEWORKS, RAW_DIR, REPO_ROOT

PROCESSED_DIR = REPO_ROOT / "data" / "processed"

SAMPLE_ID = "pilot_v1"
N_PER_SUBJECT = 100
SEED = 20260504  # today's date as int — reproducible and traceable

POPULATION_FILTER_DESC = "normalizedStatementType == 'Standard'"


def _passes_filter(item: dict[str, Any]) -> bool:
    return item.get("normalizedStatementType") == "Standard"


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _read_provenance(snapshot_dir: Path, slug: str) -> dict[str, Any]:
    return json.loads(
        (snapshot_dir / f"{slug}-standards.provenance.json").read_text(encoding="utf-8")
    )


def _slim(item: dict[str, Any]) -> dict[str, Any]:
    """Carry only the fields the downstream pipeline needs."""
    return {
        "identifier": item.get("identifier"),
        "case_uuid": item.get("caseIdentifierUUID"),
        "statement_code": item.get("statementCode"),
        "statement_type": item.get("statementType"),
        "normalized_statement_type": item.get("normalizedStatementType"),
        "grade_level": item.get("gradeLevel"),
        "description": item.get("description"),
        "jurisdiction": item.get("jurisdiction"),
        "academic_subject": item.get("academicSubject"),
    }


def main() -> None:
    today = dt.date.today().isoformat()
    snapshot_dir = RAW_DIR / today
    if not snapshot_dir.exists():
        raise SystemExit(
            f"No snapshot at {snapshot_dir}. Run `python -m src.snapshot` first."
        )

    rng = random.Random(SEED)
    sources: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []

    for ref in CC_FRAMEWORKS:
        jsonl_path = snapshot_dir / f"{ref.slug}-standards.jsonl"
        provenance = _read_provenance(snapshot_dir, ref.slug)
        all_items = _load_jsonl(jsonl_path)
        eligible = [i for i in all_items if _passes_filter(i)]
        if len(eligible) < N_PER_SUBJECT:
            raise SystemExit(
                f"{ref.slug}: only {len(eligible)} eligible items, need {N_PER_SUBJECT}"
            )
        drawn = rng.sample(eligible, N_PER_SUBJECT)
        for d in drawn:
            slim = _slim(d)
            slim["subject_label"] = ref.subject
            items.append(slim)
        sources.append(
            {
                "subject": ref.subject,
                "framework_slug": ref.slug,
                "framework_name": ref.name,
                "framework_uuid": ref.framework_uuid,
                "snapshot_path": str(jsonl_path.relative_to(REPO_ROOT)),
                "snapshot_sha256": provenance["sha256"],
                "snapshot_fetched_at": provenance["fetched_at"],
                "framework_total": len(all_items),
                "population_size_after_filter": len(eligible),
                "drawn": N_PER_SUBJECT,
            }
        )

    manifest = {
        "sample_id": SAMPLE_ID,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "produced_by": "src/sample.py",
        "seed": SEED,
        "n_per_subject": N_PER_SUBJECT,
        "population_filter": POPULATION_FILTER_DESC,
        "sources": sources,
        "items": items,
    }

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / f"{SAMPLE_ID}_sample.json"
    out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"sample written → {out_path.relative_to(REPO_ROOT)}")
    print(f"  total items: {len(items)}")
    for s in sources:
        print(
            f"  {s['framework_slug']}: drew {s['drawn']} of {s['population_size_after_filter']} eligible"
        )


if __name__ == "__main__":
    main()
