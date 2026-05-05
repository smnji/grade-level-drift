"""Vocabulary-tier features.

Lookups are case-folded and matched on spaCy lemmas, so an inflected form
(`analysing`, `analyses`) maps to its headword (`analyse`) and the AWL/NGSL
headword files do not need to enumerate inflectional variants.

Returned features (flat dict, all NaN if input is empty / has no alphabetic
content tokens):

- `pct_awl` — fraction of content tokens whose lemma is in the AWL
- `pct_ngsl` — fraction whose lemma is in the NGSL
- `pct_off_list` — fraction in neither (Tier-3 proxy)
- `mean_word_length` — mean characters per content token (raw orth, not lemma)
- `type_token_ratio` — unique lowercased lemmas / total content tokens
- `n_content_tokens` — denominator (surfaced for downstream weighting)
"""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path
from typing import Iterable

WORDLISTS_DIR = Path(__file__).parent / "wordlists"


def _load_set(path: Path) -> frozenset[str]:
    if not path.exists():
        raise FileNotFoundError(f"missing wordlist: {path}")
    words: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        w = line.strip().lower()
        if not w or w.startswith("#"):
            continue
        words.add(w)
    return frozenset(words)


@lru_cache(maxsize=1)
def awl_set() -> frozenset[str]:
    return _load_set(WORDLISTS_DIR / "awl.txt")


@lru_cache(maxsize=1)
def ngsl_set() -> frozenset[str]:
    return _load_set(WORDLISTS_DIR / "ngsl.txt")


@lru_cache(maxsize=1)
def _spacy_nlp():
    import spacy

    try:
        return spacy.load("en_core_web_sm", disable=["ner"])
    except OSError as e:
        raise RuntimeError(
            "spaCy model 'en_core_web_sm' not installed. Run: "
            "python -m spacy download en_core_web_sm"
        ) from e


def _content_tokens(doc) -> list:
    return [t for t in doc if t.is_alpha and not t.is_space]


def _nan_result() -> dict[str, float]:
    return {
        "pct_awl": float("nan"),
        "pct_ngsl": float("nan"),
        "pct_off_list": float("nan"),
        "mean_word_length": float("nan"),
        "type_token_ratio": float("nan"),
        "n_content_tokens": 0.0,
    }


def score_vocabulary(text: str) -> dict[str, float]:
    if not text or not text.strip():
        return _nan_result()
    nlp = _spacy_nlp()
    awl, ngsl = awl_set(), ngsl_set()
    doc = nlp(text)
    toks = _content_tokens(doc)
    n = len(toks)
    if n == 0:
        return _nan_result()

    in_awl = 0
    in_ngsl = 0
    char_total = 0
    lemma_set: set[str] = set()
    for t in toks:
        lemma = t.lemma_.lower() if t.lemma_ else t.text.lower()
        char_total += len(t.text)
        lemma_set.add(lemma)
        if lemma in awl:
            in_awl += 1
        elif lemma in ngsl:
            in_ngsl += 1
        # off-list: lemma in neither set; counted by subtraction below

    in_either = in_awl + in_ngsl
    return {
        "pct_awl": in_awl / n,
        "pct_ngsl": in_ngsl / n,
        "pct_off_list": (n - in_either) / n,
        "mean_word_length": char_total / n,
        "type_token_ratio": len(lemma_set) / n,
        "n_content_tokens": float(n),
    }


def score_vocabulary_batch(texts: Iterable[str]) -> list[dict[str, float]]:
    return [score_vocabulary(t) for t in texts]


if __name__ == "__main__":
    samples = [
        ("kindergarten", "We can count to one hundred. We count one, two, three, four, five."),
        (
            "grade-7",
            "Verify the meaning of an unfamiliar word by checking its inferred meaning in context or by consulting a dictionary.",
        ),
        (
            "grade-12",
            "The intricate epistemological frameworks underpinning contemporary discourse necessitate rigorous methodological scrutiny across heterogeneous academic disciplines.",
        ),
    ]
    print(f"AWL size: {len(awl_set())}, NGSL size: {len(ngsl_set())}")
    for label, txt in samples:
        s = score_vocabulary(txt)
        print(
            f"{label}: awl={s['pct_awl']:.2%} ngsl={s['pct_ngsl']:.2%} "
            f"off={s['pct_off_list']:.2%} ttr={s['type_token_ratio']:.2f} "
            f"len={s['mean_word_length']:.2f} n={int(s['n_content_tokens'])}"
        )
