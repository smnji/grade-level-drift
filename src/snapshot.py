"""Pull a Learning Commons standards-framework snapshot to disk.

Writes JSONL + a sibling `.provenance.json` to `data/raw/lc/{YYYY-MM-DD}/`. The
raw directory is gitignored (see `data/README.md`); the provenance file
captures everything needed to reconstruct the snapshot from the LC API.

Run directly to snapshot the Multi-State Common Core ELA + Math frameworks:

    python -m src.snapshot
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from src.lc_client import LCClient

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "data" / "raw" / "lc"


@dataclass(frozen=True)
class FrameworkRef:
    slug: str
    framework_uuid: str
    name: str
    subject: str


CC_FRAMEWORKS = [
    FrameworkRef(
        slug="cc-ela",
        framework_uuid="c64961be-d7cb-11e8-824f-0242ac160002",
        name="Common Core State Standards for ELA",
        subject="English Language Arts",
    ),
    FrameworkRef(
        slug="cc-math",
        framework_uuid="c6496676-d7cb-11e8-824f-0242ac160002",
        name="Common Core State Standards for Mathematics",
        subject="Mathematics",
    ),
]


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot_framework(client: LCClient, ref: FrameworkRef, out_dir: Path) -> Path:
    """Fetch all standards in `ref` and write JSONL + provenance to `out_dir`.

    Returns the JSONL path. Idempotent within a day: re-running overwrites
    the same file (raw snapshots are date-keyed; same date = same snapshot
    intent).
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / f"{ref.slug}-standards.jsonl"

    n = 0
    with jsonl_path.open("w", encoding="utf-8") as f:
        for item in client.standards_in_framework(ref.framework_uuid):
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            n += 1

    provenance: dict[str, Any] = {
        "slug": ref.slug,
        "framework_name": ref.name,
        "framework_uuid": ref.framework_uuid,
        "subject": ref.subject,
        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "api_base": client.base_url,
        "endpoint": "/academic-standards",
        "record_count": n,
        "sha256": _sha256_file(jsonl_path),
        "fetched_by": "src/snapshot.py",
    }
    (out_dir / f"{ref.slug}-standards.provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
    )
    return jsonl_path


def main() -> None:
    load_dotenv()
    today = dt.date.today().isoformat()
    out_dir = RAW_DIR / today
    with LCClient() as client:
        for ref in CC_FRAMEWORKS:
            path = snapshot_framework(client, ref, out_dir)
            print(f"  {ref.slug}: {path.relative_to(REPO_ROOT)}")
    print(f"snapshot complete → {out_dir.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
