"""Rewrite each sub-sample standard at a simplified (~4th-grade) reading level.

Idempotent: re-running skips standards already cached. Each rewrite is a single
OpenAI call at temperature 0; results are cached at
`data/interim/rewrites/{rewriter_model}/{standard_id}.json`.

    python -m src.rewrite                 # default rewriter model
    python -m src.rewrite --model gpt-4.1 # override

The default rewriter is the most stable available frontier model so simplified
wordings are consistent across runs. Identity goes in the run manifest.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

from src.openai_helpers import REPO_ROOT, UsageRollup, chat_complete_with_retry, make_client
from src.prompts import REWRITER_PROMPT

DEFAULT_REWRITER_MODEL = "gpt-4.1"

SUBSAMPLE_PATH = REPO_ROOT / "data" / "processed" / "v0_subpilot_sample.json"
INTERIM_DIR = REPO_ROOT / "data" / "interim" / "rewrites"


def cache_path(model: str, standard_id: str) -> Path:
    return INTERIM_DIR / model / f"{standard_id}.json"


def rewrite_one(
    client: Any,
    *,
    model: str,
    standard: dict[str, Any],
    usage: UsageRollup,
) -> dict[str, Any]:
    prompt_text = REWRITER_PROMPT.render(description=standard["description"])
    messages = [{"role": "user", "content": prompt_text}]
    try:
        resp = chat_complete_with_retry(
            client,
            model=model,
            messages=messages,
            temperature=0.0,
            max_tokens=400,
        )
    except Exception as e:
        usage.failures += 1
        raise
    usage.record(model, resp["raw_usage"])
    return {
        "standard_id": standard["identifier"],
        "statement_code": standard.get("statement_code"),
        "rewriter_model": model,
        "rewriter_model_returned": resp["model_returned"],
        "rewriter_prompt_sha": REWRITER_PROMPT.sha,
        "system_fingerprint": resp["system_fingerprint"],
        "raw_description": standard["description"],
        "simplified_description": resp["text"].strip(),
        "prompt_tokens": resp["prompt_tokens"],
        "completion_tokens": resp["completion_tokens"],
        "finish_reason": resp["finish_reason"],
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        default=DEFAULT_REWRITER_MODEL,
        help=f"OpenAI model for rewriting (default: {DEFAULT_REWRITER_MODEL})",
    )
    args = parser.parse_args()

    if not SUBSAMPLE_PATH.exists():
        raise SystemExit(
            f"Sub-sample missing at {SUBSAMPLE_PATH.relative_to(REPO_ROOT)}. "
            "Run `python -m src.sub_sample` first."
        )

    sub_sample = json.loads(SUBSAMPLE_PATH.read_text(encoding="utf-8"))
    standards = sub_sample["items"]
    out_dir = INTERIM_DIR / args.model
    out_dir.mkdir(parents=True, exist_ok=True)

    client = make_client()
    usage = UsageRollup()

    cached = 0
    written = 0
    for i, std in enumerate(standards, start=1):
        path = cache_path(args.model, std["identifier"])
        if path.exists():
            cached += 1
            continue
        record = rewrite_one(client, model=args.model, standard=std, usage=usage)
        path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written += 1
        if written % 5 == 0 or i == len(standards):
            print(
                f"[{i}/{len(standards)}] {std.get('statement_code')!r}: written → "
                f"{path.relative_to(REPO_ROOT)}"
            )

    print()
    print(f"rewriter complete. cached={cached} written={written} of {len(standards)}")
    print(usage.summary())


if __name__ == "__main__":
    main()
