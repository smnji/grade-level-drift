"""Generate the v0 cube — 60 standards × 3 models × 3 prompts × 2 wordings.

Each cell makes one chat-completion call at temperature 0 and writes a JSON
record to `data/generated/{run_id}/{cell_key}.json`. The cell key is
`{model}__{prompt}__{wording}__{standard_id}`.

Idempotent: re-running skips cells whose output file already exists, so
interrupts (rate limits, disk full, Ctrl-C) are recoverable. The same
`--run-id` continues an incomplete run; a new `--run-id` starts fresh.

Cost guard: `--max-cost-usd` aborts before issuing a call whose projected
cumulative cost would exceed the cap. The estimate uses a per-model rate
table (see PRICING below) — adjust it at the CLI if those rates are stale.

CLI:

    python -m src.generate \\
        --run-id v0_run1 \\
        --models gpt-5.5,gpt-5.4,gpt-4.1 \\
        --rewriter-model gpt-4.1 \\
        --max-cost-usd 25.0
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path
from typing import Any

from src.manifest import RunManifest, default_run_id
from src.openai_helpers import REPO_ROOT, UsageRollup, chat_complete_with_retry, make_client
from src.prompts import GENERATOR_PROMPTS, render_grade

SUBSAMPLE_PATH = REPO_ROOT / "data" / "processed" / "v0_subpilot_sample.json"
GENERATED_DIR = REPO_ROOT / "data" / "generated"
REWRITES_DIR = REPO_ROOT / "data" / "interim" / "rewrites"
PROMPTS_AT_TARGET_DIR = REPO_ROOT / "data" / "interim" / "prompts_at_target"

# Approximate per-call USD cost. Used only for the --max-cost-usd guard, not
# for billing. Update when OpenAI pricing changes; the guard is conservative
# (rounds to call-grain rather than per-token).
PRICING: dict[str, float] = {
    # Rough $/call assuming ~150 input + ~250 output tokens per cell at the
    # vendor's published per-token rates (mid-2026). Conservative — used only
    # to gate large runs, not to bill anything.
    "gpt-5.5": 0.015,
    "gpt-5.4": 0.010,
    "gpt-5.1": 0.008,
    "gpt-4.1": 0.003,
    "gpt-4o": 0.003,
    "gpt-4o-mini": 0.0008,
    "_default": 0.015,
}


def cell_key(model: str, prompt: str, wording: str, standard_id: str) -> str:
    return f"{model}__{prompt}__{wording}__{standard_id}"


def cell_path(run_id: str, key: str) -> Path:
    return GENERATED_DIR / run_id / f"{key}.json"


def load_simplified(rewriter_model: str, standard_id: str) -> str | None:
    p = REWRITES_DIR / rewriter_model / f"{standard_id}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8")).get("simplified_description")


def load_prompt_at_target(rewriter_model: str, standard_id: str) -> str | None:
    p = PROMPTS_AT_TARGET_DIR / rewriter_model / f"{standard_id}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8")).get("prompt_at_target")


def estimate_cell_cost(model: str) -> float:
    return PRICING.get(model, PRICING["_default"])


def render_user_prompt(
    *,
    prompt_name: str,
    standard: dict[str, Any],
    description: str,
    wording: str = "raw",
    rewriter_model: str | None = None,
) -> str:
    """Render the user message that will be sent to the model.

    For wording ∈ {raw, simplified} the rendered prompt is the S/M/L template
    with `description` substituted in. For wording == "at_target" the prompt
    is the *cached pre-rendered prompt at the standard's target grade* — the
    S/M/L template is bypassed entirely; the same cached prompt is used
    regardless of `prompt_name` so the v0_run2 cube has 1 effective template.
    """
    if wording == "at_target":
        if rewriter_model is None:
            raise ValueError("at_target wording requires rewriter_model")
        text = load_prompt_at_target(rewriter_model, standard["identifier"])
        if text is None:
            raise FileNotFoundError(
                f"prompt-at-target missing for {standard.get('statement_code')!r} "
                f"({standard['identifier']}). Run `python -m src.rewrite_target` first."
            )
        return text
    spec = GENERATOR_PROMPTS[prompt_name]
    grade = render_grade(standard.get("grade_level"))
    return spec.render(
        grade=grade,
        description=description,
        statement_code=standard.get("statement_code") or standard.get("identifier"),
    )


def generate_one(
    client: Any,
    *,
    model: str,
    prompt_name: str,
    wording: str,
    standard: dict[str, Any],
    description: str,
    usage: UsageRollup,
    max_tokens: int = 400,
    rewriter_model: str | None = None,
) -> dict[str, Any]:
    user = render_user_prompt(
        prompt_name=prompt_name,
        standard=standard,
        description=description,
        wording=wording,
        rewriter_model=rewriter_model,
    )
    messages = [{"role": "user", "content": user}]
    resp = chat_complete_with_retry(
        client,
        model=model,
        messages=messages,
        temperature=0.0,
        max_tokens=max_tokens,
    )
    usage.record(model, resp["raw_usage"])
    return {
        "model": model,
        "model_returned": resp["model_returned"],
        "prompt_name": prompt_name,
        "prompt_sha": GENERATOR_PROMPTS[prompt_name].sha,
        "wording": wording,
        "standard_id": standard["identifier"],
        "statement_code": standard.get("statement_code"),
        "grade_level": standard.get("grade_level"),
        "description_used": description,
        "system_fingerprint": resp["system_fingerprint"],
        "output_text": resp["text"].strip(),
        "prompt_tokens": resp["prompt_tokens"],
        "completion_tokens": resp["completion_tokens"],
        "finish_reason": resp["finish_reason"],
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }


def iter_cells(
    standards: list[dict[str, Any]],
    *,
    models: list[str],
    prompt_names: list[str],
    wordings: list[str],
):
    """Deterministic order: model (outer) → prompt → wording → standard."""
    for m in models:
        for p in prompt_names:
            for w in wordings:
                for s in standards:
                    yield m, p, w, s


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default=default_run_id())
    parser.add_argument(
        "--models",
        default="gpt-5.5,gpt-5.4,gpt-4.1",
        help="Comma-separated OpenAI model IDs",
    )
    parser.add_argument(
        "--rewriter-model",
        default="gpt-4.1",
        help="Rewriter model used to produce the simplified-wording arm",
    )
    parser.add_argument(
        "--prompts",
        default="S,M,L",
        help="Comma-separated prompt variant names (S,M,L)",
    )
    parser.add_argument(
        "--wordings",
        default="raw,simplified",
        help="Comma-separated wording conditions",
    )
    parser.add_argument("--max-tokens", type=int, default=400)
    parser.add_argument("--max-cost-usd", type=float, default=25.0)
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="If set, only attempt this many new cells (for dev / cost tests)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the cells that would be generated without making any API calls",
    )
    args = parser.parse_args()

    if not SUBSAMPLE_PATH.exists():
        raise SystemExit(
            f"Sub-sample missing at {SUBSAMPLE_PATH.relative_to(REPO_ROOT)}. "
            "Run `python -m src.sub_sample` first."
        )

    sub_sample = json.loads(SUBSAMPLE_PATH.read_text(encoding="utf-8"))
    standards = sub_sample["items"]
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    prompt_names = [p.strip() for p in args.prompts.split(",") if p.strip()]
    for p in prompt_names:
        if p not in GENERATOR_PROMPTS:
            raise SystemExit(f"unknown prompt name: {p!r}")
    wordings = [w.strip() for w in args.wordings.split(",") if w.strip()]
    for w in wordings:
        if w not in {"raw", "simplified", "at_target"}:
            raise SystemExit(
                f"unknown wording: {w!r} (must be raw|simplified|at_target)"
            )

    out_dir = GENERATED_DIR / args.run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # Manifest stub up front, even if the run is interrupted later
    manifest = RunManifest.build(
        run_id=args.run_id,
        sample_path=SUBSAMPLE_PATH,
        rewriter_model=args.rewriter_model,
        generator_models=models,
        seed=sub_sample.get("seed", 0),
        notes="generated by src.generate",
    )
    manifest.write()

    # If simplified arm requested, every standard must have a cached rewrite
    if "simplified" in wordings:
        missing = [
            s["identifier"]
            for s in standards
            if load_simplified(args.rewriter_model, s["identifier"]) is None
        ]
        if missing:
            raise SystemExit(
                f"{len(missing)} standards missing simplified rewrites for model "
                f"{args.rewriter_model!r}. Run `python -m src.rewrite "
                f"--model {args.rewriter_model}` first.\n"
                f"  first 3 missing: {missing[:3]}"
            )
    # at_target requires the prompt-at-target cache
    if "at_target" in wordings:
        missing = [
            s["identifier"]
            for s in standards
            if load_prompt_at_target(args.rewriter_model, s["identifier"]) is None
        ]
        if missing:
            raise SystemExit(
                f"{len(missing)} standards missing prompt-at-target rewrites for model "
                f"{args.rewriter_model!r}. Run `python -m src.rewrite_target "
                f"--model {args.rewriter_model}` first.\n"
                f"  first 3 missing: {missing[:3]}"
            )

    total_planned = len(models) * len(prompt_names) * len(wordings) * len(standards)
    cells_to_call: list[tuple[str, str, str, dict[str, Any]]] = []
    cells_skipped = 0
    for m, p, w, s in iter_cells(
        standards, models=models, prompt_names=prompt_names, wordings=wordings
    ):
        key = cell_key(m, p, w, s["identifier"])
        if cell_path(args.run_id, key).exists():
            cells_skipped += 1
            continue
        cells_to_call.append((m, p, w, s))

    if args.limit is not None:
        cells_to_call = cells_to_call[: args.limit]

    projected_cost = sum(estimate_cell_cost(m) for m, _, _, _ in cells_to_call)
    print(
        f"run_id={args.run_id} models={models} prompts={prompt_names} "
        f"wordings={wordings} standards={len(standards)}"
    )
    print(
        f"planned={total_planned} already_done={cells_skipped} "
        f"to_call={len(cells_to_call)} projected_cost≈${projected_cost:.2f} "
        f"(cap=${args.max_cost_usd:.2f})"
    )

    if args.dry_run:
        for m, p, w, s in cells_to_call[:10]:
            print(f"  DRYRUN {cell_key(m, p, w, s['identifier'])}")
        if len(cells_to_call) > 10:
            print(f"  ... and {len(cells_to_call) - 10} more")
        return

    if projected_cost > args.max_cost_usd:
        raise SystemExit(
            f"projected cost ${projected_cost:.2f} > cap ${args.max_cost_usd:.2f}. "
            "Raise --max-cost-usd or reduce scope."
        )

    if not cells_to_call:
        print("nothing to do — all cells already generated.")
        return

    client = make_client()
    usage = UsageRollup()
    written = 0
    started = time.time()
    for i, (m, p, w, s) in enumerate(cells_to_call, start=1):
        if w == "raw":
            description = s["description"]
        elif w == "simplified":
            description = load_simplified(args.rewriter_model, s["identifier"])
            if description is None:
                raise SystemExit(
                    f"simplified rewrite missing for {s['identifier']!r} (model "
                    f"{args.rewriter_model!r})"
                )
        else:  # at_target — description field is a copy of the standard for record
            description = s["description"]
        key = cell_key(m, p, w, s["identifier"])
        try:
            record = generate_one(
                client,
                model=m,
                prompt_name=p,
                wording=w,
                standard=s,
                description=description,
                usage=usage,
                max_tokens=args.max_tokens,
                rewriter_model=args.rewriter_model,
            )
        except Exception as e:
            usage.failures += 1
            print(f"  ✗ {key}: {type(e).__name__}: {e}", file=sys.stderr)
            continue

        cell_path(args.run_id, key).write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        written += 1

        if written % 25 == 0 or i == len(cells_to_call):
            elapsed = time.time() - started
            rate = written / elapsed if elapsed else 0.0
            print(
                f"[{i}/{len(cells_to_call)}] {key}  elapsed={elapsed:.0f}s "
                f"rate={rate:.2f}/s  {usage.summary().splitlines()[0]}"
            )

    # Re-build manifest with completion data and rewrite
    manifest.mark_complete(
        actual_n_cells=cells_skipped + written,
        usage={
            "calls": usage.calls,
            "failures": usage.failures,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "by_model": usage.by_model,
        },
    )
    manifest.write()
    print()
    print(
        f"generation complete. written={written} skipped={cells_skipped} "
        f"failures={usage.failures} of {total_planned}"
    )
    print(usage.summary())


if __name__ == "__main__":
    main()
