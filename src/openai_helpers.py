"""Shared OpenAI client helpers — single client, retry-with-backoff, usage rollup.

Used by `src.rewrite` and `src.generate`. Reads `OPENAI_API_KEY` from `.env`.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import APIConnectionError, APIError, APITimeoutError, OpenAI, RateLimitError

REPO_ROOT = Path(__file__).resolve().parents[1]


def make_client() -> OpenAI:
    load_dotenv(REPO_ROOT / ".env")
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY not in env. Add it to .env (gitignored). See .env.example."
        )
    return OpenAI()


@dataclass
class UsageRollup:
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    failures: int = 0
    by_model: dict[str, dict[str, int]] = field(default_factory=dict)

    def record(self, model: str, usage: Any) -> None:
        self.calls += 1
        pt = getattr(usage, "prompt_tokens", 0) or 0
        ct = getattr(usage, "completion_tokens", 0) or 0
        self.prompt_tokens += pt
        self.completion_tokens += ct
        slot = self.by_model.setdefault(
            model, {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0}
        )
        slot["calls"] += 1
        slot["prompt_tokens"] += pt
        slot["completion_tokens"] += ct

    def summary(self) -> str:
        total = self.prompt_tokens + self.completion_tokens
        lines = [
            f"calls={self.calls} failures={self.failures} "
            f"tokens={total:,} (in={self.prompt_tokens:,} out={self.completion_tokens:,})"
        ]
        for model, s in sorted(self.by_model.items()):
            lines.append(
                f"  {model}: {s['calls']} calls, "
                f"{s['prompt_tokens']:,} in, {s['completion_tokens']:,} out"
            )
        return "\n".join(lines)


def chat_complete_with_retry(
    client: OpenAI,
    *,
    model: str,
    messages: list[dict[str, str]],
    temperature: float = 0.0,
    max_tokens: int = 400,
    max_attempts: int = 5,
    initial_backoff: float = 2.0,
) -> dict[str, Any]:
    """Call chat.completions.create with exponential backoff on transient errors.

    Returns a dict with keys: text, model_returned, system_fingerprint,
    prompt_tokens, completion_tokens, finish_reason. Raises on non-transient.
    """
    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            choice = resp.choices[0]
            usage = resp.usage
            return {
                "text": choice.message.content or "",
                "model_returned": resp.model,
                "system_fingerprint": getattr(resp, "system_fingerprint", None),
                "prompt_tokens": getattr(usage, "prompt_tokens", 0) if usage else 0,
                "completion_tokens": getattr(usage, "completion_tokens", 0) if usage else 0,
                "finish_reason": choice.finish_reason,
                "raw_usage": usage,
            }
        except (RateLimitError, APITimeoutError, APIConnectionError) as e:
            last_exc = e
            sleep = initial_backoff * (2 ** (attempt - 1))
            time.sleep(sleep)
        except APIError as e:
            # Some APIErrors are retryable (5xx); some are not (4xx other than rate limit).
            status = getattr(e, "status_code", None)
            if status is not None and 500 <= status < 600:
                last_exc = e
                sleep = initial_backoff * (2 ** (attempt - 1))
                time.sleep(sleep)
            else:
                raise
    raise RuntimeError(f"max_attempts={max_attempts} exhausted; last error: {last_exc!r}")
