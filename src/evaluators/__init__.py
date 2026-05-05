"""Deterministic scoring stack — single entry point.

Combines readability formulas, vocabulary tier features, syntactic complexity
features, and surface counts into a single flat dict per text. Pure function
of the input text and the version-pinned tools (textstat version, spaCy
model version, embedded wordlist SHAs); no API calls, no random seeds.

Usage:

    from src.evaluators import score, score_batch
    s = score("Some text.")
    rows = score_batch(["text 1", "text 2"])

`SCORING_STACK_VERSION` is bumped any time the feature set, formula
selection, or aggregation rule changes. The version string is recorded in
the run manifest so that downstream artifacts can be tied to the exact
scoring contract that produced them.
"""

from __future__ import annotations

import hashlib
import re
from importlib.metadata import PackageNotFoundError, version as _pkg_version
from pathlib import Path
from typing import Any, Iterable

from src.evaluators.readability import score_readability
from src.evaluators.syntax import score_syntax
from src.evaluators.vocabulary import score_vocabulary

SCORING_STACK_VERSION = "v0.1"

WORDLISTS_DIR = Path(__file__).parent / "wordlists"


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _try_pkg_version(name: str) -> str | None:
    try:
        return _pkg_version(name)
    except PackageNotFoundError:
        return None


def _spacy_model_version() -> str | None:
    try:
        import spacy

        nlp = spacy.load("en_core_web_sm")
        return getattr(nlp.meta, "get", lambda *_: None)("version") or nlp.meta.get(
            "version"
        )
    except Exception:
        return None


def stack_metadata() -> dict[str, Any]:
    """Identifying metadata for the scoring stack — committed to the run manifest."""
    return {
        "scoring_stack_version": SCORING_STACK_VERSION,
        "textstat_version": _try_pkg_version("textstat"),
        "spacy_version": _try_pkg_version("spacy"),
        "spacy_model": "en_core_web_sm",
        "spacy_model_version": _spacy_model_version(),
        "awl_sha256": _file_sha256(WORDLISTS_DIR / "awl.txt"),
        "ngsl_sha256": _file_sha256(WORDLISTS_DIR / "ngsl.txt"),
    }


def _surface_counts(text: str) -> dict[str, float]:
    if not text or not text.strip():
        return {"word_count": 0.0, "sentence_count": 0.0, "paragraph_count": 0.0}
    paragraphs = [p for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    # crude sentence split — used only for surface telemetry; the spaCy parse
    # in syntax.py is the authoritative sentence count.
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]
    words = re.findall(r"[A-Za-z][A-Za-z'\-]*", text)
    return {
        "word_count": float(len(words)),
        "sentence_count": float(len(sentences)),
        "paragraph_count": float(len(paragraphs)),
    }


def score(text: str) -> dict[str, float]:
    """Score a single text. Returns a flat dict of features.

    Empty / very-short inputs return NaN for every feature except surface
    counts (which return 0).
    """
    out: dict[str, float] = {}
    out.update(_surface_counts(text))
    out.update(score_readability(text))
    out.update(score_vocabulary(text))
    out.update(score_syntax(text))
    return out


def score_batch(texts: Iterable[str]) -> list[dict[str, float]]:
    return [score(t) for t in texts]


# canonical column order — useful when materializing as a dataframe
FEATURE_COLUMNS: list[str] = [
    # surface
    "word_count",
    "sentence_count",
    "paragraph_count",
    # readability
    "flesch_kincaid_grade",
    "smog_index",
    "coleman_liau_index",
    "automated_readability_index",
    "gunning_fog",
    "dale_chall_readability_score",
    "ensemble_grade_median",
    # vocabulary
    "pct_awl",
    "pct_ngsl",
    "pct_off_list",
    "mean_word_length",
    "type_token_ratio",
    "n_content_tokens",
    # syntax
    "mean_dep_depth",
    "mean_t_unit_length",
    "subord_clause_ratio",
    "passive_ratio",
    "nominalization_ratio",
    "n_sentences",
    "n_tokens",
]


def _smoke_test() -> None:
    """Run a 3-passage smoke test against known grade levels and print results."""
    import json

    samples = [
        (
            "kindergarten",
            "We can count to one hundred. We count one, two, three, four, five. "
            "Counting helps us know how many things there are.",
        ),
        (
            "grade-5",
            "Read the passage carefully and identify the main idea. Then explain how "
            "the author supports the main idea with specific details and examples from the text.",
        ),
        (
            "grade-12",
            "The intricate epistemological frameworks underpinning contemporary discourse "
            "necessitate rigorous methodological scrutiny across heterogeneous academic "
            "disciplines, particularly when interrogating the validity of inferential claims "
            "drawn from observational data alone.",
        ),
    ]
    print("--- stack metadata ---")
    print(json.dumps(stack_metadata(), indent=2))
    print()
    for label, txt in samples:
        s = score(txt)
        print(f"--- {label} ---")
        print(
            f"  ensemble_grade={s['ensemble_grade_median']:.2f}  fk={s['flesch_kincaid_grade']:.2f}  "
            f"smog={s['smog_index']:.2f}  fog={s['gunning_fog']:.2f}"
        )
        print(
            f"  pct_awl={s['pct_awl']:.2%}  pct_ngsl={s['pct_ngsl']:.2%}  "
            f"pct_off={s['pct_off_list']:.2%}  ttr={s['type_token_ratio']:.2f}  "
            f"mean_word_len={s['mean_word_length']:.2f}"
        )
        print(
            f"  dep_depth={s['mean_dep_depth']:.2f}  tu_len={s['mean_t_unit_length']:.2f}  "
            f"subord={s['subord_clause_ratio']:.2f}  passive={s['passive_ratio']:.2f}  "
            f"nom={s['nominalization_ratio']:.2f}"
        )
