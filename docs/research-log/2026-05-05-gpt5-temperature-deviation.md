---
date: 2026-05-05
severity: moderate
area: methodology
tags: [openai, gpt-5, temperature, determinism, generation]
title: GPT-5 family rejects custom temperature — accept temperature=1 for those models
---

Discovered while smoke-testing the v0 generation pipeline that the GPT-5 family (`gpt-5.5`, `gpt-5.4`, `gpt-5.1`, ..., plus the o-series reasoning models) rejects two parameters that the methodology assumes:

1. `max_tokens` — replaced by `max_completion_tokens` for these models.
2. `temperature` — only the vendor default (`1.0`) is accepted; passing `temperature=0` returns HTTP 400 (`unsupported_value`).

The error returned by the API is unambiguous:

```
{'error': {'message': "Unsupported value: 'temperature' does not support 0 with this model. Only the default (1) value is supported.", 'type': 'invalid_request_error', 'param': 'temperature', 'code': 'unsupported_value'}}
```

GPT-4.1 still accepts both `max_tokens` and `temperature=0`, so the rewriter (which uses gpt-4.1) is unaffected.

## What this means for the methodology

The pre-pivot methodology stated:

> **Temperature:** 0 (deterministic). Within-model variance is not a v0 question; can be added later by sweeping temperature on a subset.
> ([methodology.md §4 — Generator spec](../methodology.md))

That guarantee no longer holds for the two GPT-5 models in the headline cube. Specifically:

- `gpt-5.5` and `gpt-5.4` cells are generated at temperature=1.0 (model default; not user-controllable).
- `gpt-4.1` cells continue at temperature=0.
- All cells are still single-shot — no sampling-and-aggregation.

Within-model run-to-run variance is therefore non-zero for the GPT-5 cells, where the methodology assumed it was zero. The mean Δ per cell is still measurable, but a re-run of the same cell against `gpt-5.5` will not produce a byte-identical output.

## Decision

Accept the deviation rather than substitute models. The v0 question is "do *frontier OpenAI models* drift?" — substituting older models that happen to support `temperature=0` would weaken the headline more than accepting non-determinism. Mitigations:

- **Document in the run manifest.** The manifest already records the model ID and `system_fingerprint` per call; that's the strongest available pin.
- **Single-call per cell** (no resampling). Within-cell variance is therefore a known but unquantified threat — added below.
- **The cross-model and cross-prompt agreement analyses** average over many cells per (model × condition), so per-cell stochasticity does not bias the aggregate Δ estimate; it adds noise but not direction.
- **A future temperature-sweep follow-up** can probe within-model variance directly on a subset.

## Code change

`src/openai_helpers.py: chat_complete_with_retry` now branches on a `_is_gpt5_family(model)` predicate:

- For `gpt-5*`, `o1*`, `o3*`, `o4*`: passes `max_completion_tokens` only; the `temperature` argument is silently ignored.
- For everything else: passes `max_tokens` and `temperature` as before.

This is the smallest change that lets the existing generator code call all three target models without per-call branching at the call site. The behavior is documented in the helper's docstring with a back-link to this entry.

## Threats to validity to add to the proposal

- **T-NEW (deterministic-temperature deviation).** GPT-5 cells run at the model's default `temperature=1.0`; we cannot pin them lower. This adds within-cell stochastic variance to the Δ measurement for those models. The aggregate Δ per (model × condition × grade-band) is still well-defined as the mean over many cells; per-standard estimates inherit a wider CI than they would under deterministic decoding.

To be reflected in `research-proposal.qmd §8` in the next coherence pass, and in `methodology.md §4` ("Generator spec — Temperature").
