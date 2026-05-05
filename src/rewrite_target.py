"""Rewrite each sub-sample standard into a *complete prompt at the standard's
own target grade*.

This is the rewriter for the v0_run2 follow-up. v0_run1 only rewrote the
standard's *description*; the surrounding scaffolding and grade specifier
were always at adult reading level. The prompt-as-sent therefore averaged
+3.19 grade levels above target — and we couldn't separate "model drifts"
from "model matches the prompt's drift". v0_run2 rewrites the entire prompt
(scaffolding + standard wording + grade spec) at the standard's target grade
and asks: when the prompt is on-target, where does the output land?

For each standard the rewriter is asked to produce a self-contained prompt:

- Written at the standard's target grade reading level
- Asks the AI to explain the standard's idea to a student of that grade
- Specifies a 100-250 word target length
- Avoids jargon, technical CCSS identifiers, and instructional metadata

The rewriter is the same model as src/rewrite.py (`gpt-4.1`, temperature 0).
After each rewrite we verify with textstat's ensemble grade; if the rewrite
itself drifted by more than ±1.5 grade levels from target, we retry up to
3 times with a stricter prompt. Cached at
`data/interim/prompts_at_target/{rewriter_model}/{standard_id}.json`.

    python -m src.rewrite_target

Idempotent — re-runs skip cached standards.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

from src.evaluators import score
from src.openai_helpers import (
    REPO_ROOT,
    UsageRollup,
    chat_complete_with_retry,
    make_client,
)

DEFAULT_REWRITER_MODEL = "gpt-4.1"

SUBSAMPLE_PATH = REPO_ROOT / "data" / "processed" / "v0_subpilot_sample.json"
INTERIM_DIR = REPO_ROOT / "data" / "interim" / "prompts_at_target"

MAX_ATTEMPTS = 3
TOLERANCE_GRADES = 1.5

REWRITER_TEMPLATE_BASE = """\
Write a prompt that asks an AI tutor to explain an academic standard to a \
student. The student is in grade {grade_label}. Your prompt itself must be \
written at a reading level appropriate for that grade — short sentences, \
familiar vocabulary, no jargon, no technical curriculum identifiers.

Your prompt should:
- Tell the AI tutor what the student is learning, in words a grade-{grade_label} \
reader would understand.
- Ask the AI tutor to explain the idea in 100 to 250 words at the same reading level.
- Not include the standard's code, the words "standard" or "Common Core", or any \
teacher-facing language.

Concept the student is learning (you must rewrite this in your prompt at the \
right reading level — do not copy the original wording):
{description}

Return only the prompt text, ready to send to the AI tutor. Do not add headings, \
quotes, or commentary.
"""

REWRITER_TEMPLATE_STRICTER = """\
Your previous attempt was at a reading level of {observed_grade:.1f} but I \
need it at grade {grade_label}. Try again — the prompt itself must be \
written at grade {grade_label} reading level. Use very short sentences \
and only words a grade-{grade_label} reader knows.

The prompt should ask an AI tutor to explain a concept to a grade-{grade_label} \
student in 100 to 250 words at that same reading level. Do not include the \
standard's code, the words "standard" or "Common Core", or any teacher-facing \
language.

Concept the student is learning (rewrite this at grade {grade_label}, do not copy):
{description}

Return only the prompt text. No headings, no quotes, no commentary.
"""


def cache_path(model: str, standard_id: str) -> Path:
    return INTERIM_DIR / model / f"{standard_id}.json"


def _grade_label(grade_level: list[str] | None) -> str:
    """A short label for grade banding. Numbers used for the textstat target."""
    if not grade_level:
        return "K-12"
    if len(grade_level) == 1:
        return grade_level[0]
    return f"{grade_level[0]}-{grade_level[-1]}"


def _numeric_target(grade_level: list[str] | None) -> float:
    """Target grade for textstat verification (mean across multi-grade bands)."""
    if not grade_level:
        return 6.0
    nums: list[float] = []
    for g in grade_level:
        nums.append(0.0 if g == "K" else float(g))
    return sum(nums) / len(nums)


def rewrite_one(
    client: Any,
    *,
    model: str,
    standard: dict[str, Any],
    usage: UsageRollup,
) -> dict[str, Any]:
    grade_label = _grade_label(standard.get("grade_level"))
    target_grade = _numeric_target(standard.get("grade_level"))
    description = standard["description"]

    attempts: list[dict[str, Any]] = []
    chosen_text: str | None = None
    chosen_observed: float | None = None
    chosen_attempt = 0

    for attempt in range(1, MAX_ATTEMPTS + 1):
        if attempt == 1 or chosen_text is None:
            prompt = REWRITER_TEMPLATE_BASE.format(
                grade_label=grade_label, description=description
            )
        else:
            prompt = REWRITER_TEMPLATE_STRICTER.format(
                grade_label=grade_label,
                description=description,
                observed_grade=chosen_observed if chosen_observed is not None else 99.9,
            )
        resp = chat_complete_with_retry(
            client, model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0, max_tokens=600,
        )
        usage.record(model, resp["raw_usage"])
        text = resp["text"].strip()
        observed = float(score(text)["ensemble_grade_median"])
        attempts.append({"attempt": attempt, "text": text, "observed_grade": observed})
        if (
            chosen_text is None
            or abs(observed - target_grade) < abs((chosen_observed or 99.0) - target_grade)
        ):
            chosen_text = text
            chosen_observed = observed
            chosen_attempt = attempt
        if abs(observed - target_grade) <= TOLERANCE_GRADES:
            break

    return {
        "standard_id": standard["identifier"],
        "statement_code": standard.get("statement_code"),
        "grade_level": standard.get("grade_level"),
        "target_grade": target_grade,
        "rewriter_model": model,
        "rewriter_model_returned": resp["model_returned"],
        "system_fingerprint": resp["system_fingerprint"],
        "raw_description": description,
        "prompt_at_target": chosen_text,
        "prompt_at_target_observed_grade": chosen_observed,
        "chose_attempt": chosen_attempt,
        "attempts": attempts,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_REWRITER_MODEL)
    args = parser.parse_args()

    if not SUBSAMPLE_PATH.exists():
        raise SystemExit(
            f"Sub-sample missing at {SUBSAMPLE_PATH.relative_to(REPO_ROOT)}."
        )

    sub = json.loads(SUBSAMPLE_PATH.read_text(encoding="utf-8"))
    standards = sub["items"]
    out_dir = INTERIM_DIR / args.model
    out_dir.mkdir(parents=True, exist_ok=True)

    client = make_client()
    usage = UsageRollup()

    cached = 0
    written = 0
    in_tolerance = 0
    for i, std in enumerate(standards, start=1):
        path = cache_path(args.model, std["identifier"])
        if path.exists():
            cached += 1
            existing = json.loads(path.read_text(encoding="utf-8"))
            if abs(existing.get("prompt_at_target_observed_grade", 99) - existing["target_grade"]) <= TOLERANCE_GRADES:
                in_tolerance += 1
            continue
        rec = rewrite_one(client, model=args.model, standard=std, usage=usage)
        path.write_text(
            json.dumps(rec, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        written += 1
        within = abs(rec["prompt_at_target_observed_grade"] - rec["target_grade"]) <= TOLERANCE_GRADES
        if within:
            in_tolerance += 1
        marker = "✓" if within else "!"
        print(
            f"  {marker} [{i:2d}/{len(standards)}] {std.get('statement_code'):<14s} "
            f"target={rec['target_grade']:.1f}  observed={rec['prompt_at_target_observed_grade']:.1f}  "
            f"attempt={rec['chose_attempt']}/{MAX_ATTEMPTS}"
        )

    print()
    print(
        f"prompt-at-target rewrites: cached={cached} written={written} "
        f"of {len(standards)}"
    )
    print(f"  within ±{TOLERANCE_GRADES} of target: {in_tolerance}/{len(standards)}")
    print(usage.summary())


if __name__ == "__main__":
    main()
