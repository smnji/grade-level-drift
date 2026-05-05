"""Classical readability formulas via `textstat`.

Pure deterministic. Returns a flat dict of grade-equivalent scores plus an
ensemble median. Empty / very-short text returns NaN per formula and a NaN
ensemble.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import textstat

FORMULAS = (
    "flesch_kincaid_grade",
    "smog_index",
    "coleman_liau_index",
    "automated_readability_index",
    "gunning_fog",
    "dale_chall_readability_score",
)


def _safe(fn, text: str) -> float:
    try:
        v = fn(text)
        if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
            return float("nan")
        return float(v)
    except Exception:
        return float("nan")


def score_readability(text: str) -> dict[str, float]:
    if not text or len(text.split()) < 5:
        out = {name: float("nan") for name in FORMULAS}
        out["ensemble_grade_median"] = float("nan")
        return out

    out = {
        "flesch_kincaid_grade": _safe(textstat.flesch_kincaid_grade, text),
        "smog_index": _safe(textstat.smog_index, text),
        "coleman_liau_index": _safe(textstat.coleman_liau_index, text),
        "automated_readability_index": _safe(
            textstat.automated_readability_index, text
        ),
        "gunning_fog": _safe(textstat.gunning_fog, text),
        "dale_chall_readability_score": _safe(
            textstat.dale_chall_readability_score, text
        ),
    }
    vals = [v for v in out.values() if not math.isnan(v)]
    out["ensemble_grade_median"] = float(np.median(vals)) if vals else float("nan")
    return out
