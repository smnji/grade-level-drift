"""Syntactic-complexity features from the spaCy dependency parse.

Returned features (flat dict, NaN if input has no parsable sentences):

- `mean_dep_depth` — mean depth of token-to-root dependency path
- `mean_t_unit_length` — mean token length of T-units (Lu's L2SCA construct).
  A T-unit is one main clause plus any subordinate clauses or non-clausal
  structures attached to it. Operationally we approximate one T-unit per
  ROOT verb in a sentence and assign the sentence's tokens to its T-units
  proportionally; for short student-explanation outputs (1-2 sentences with
  one root each) this approximation collapses to "tokens per main clause".
- `subord_clause_ratio` — subordinate clauses per main clause. Subordinate
  clauses are tokens with dep ∈ {advcl, ccomp, xcomp, csubj, acl, relcl}.
- `passive_ratio` — passive constructions per finite verb. A passive
  construction is detected by an `auxpass` or `nsubjpass` dependency.
- `nominalization_ratio` — nominalized verbs per noun. Heuristic: a NOUN
  whose lemma ends in {-tion, -ment, -ance, -ence, -ity, -ness, -sion}.
- `n_sentences`, `n_tokens` — counts surfaced for downstream weighting.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Iterable

NOMINALIZATION_SUFFIXES = ("tion", "ment", "ance", "ence", "ity", "ness", "sion")
SUBORDINATE_DEPS = frozenset({"advcl", "ccomp", "xcomp", "csubj", "csubjpass", "acl", "relcl"})


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


def _depth_to_root(token) -> int:
    d = 0
    cur = token
    # spaCy: a root token's head is itself (compare by index, not identity —
    # `token.head` returns a fresh Token wrapper each call).
    while cur.head.i != cur.i:
        d += 1
        cur = cur.head
        if d > 200:  # pathological safeguard
            break
    return d


def _nan_result() -> dict[str, float]:
    return {
        "mean_dep_depth": float("nan"),
        "mean_t_unit_length": float("nan"),
        "subord_clause_ratio": float("nan"),
        "passive_ratio": float("nan"),
        "nominalization_ratio": float("nan"),
        "n_sentences": 0.0,
        "n_tokens": 0.0,
    }


def score_syntax(text: str) -> dict[str, float]:
    if not text or not text.strip():
        return _nan_result()
    nlp = _spacy_nlp()
    doc = nlp(text)

    sents = [s for s in doc.sents if any(not t.is_space and not t.is_punct for t in s)]
    if not sents:
        return _nan_result()

    n_tokens = sum(1 for t in doc if not t.is_space and not t.is_punct)
    if n_tokens == 0:
        return _nan_result()

    # mean_dep_depth across content tokens (alpha)
    depths = [_depth_to_root(t) for t in doc if t.is_alpha]
    mean_dep_depth = (sum(depths) / len(depths)) if depths else float("nan")

    # main vs subordinate clauses
    main_clauses = 0
    subord_clauses = 0
    finite_verbs = 0
    passive_marks = 0
    nouns = 0
    nominalizations = 0
    for tok in doc:
        if tok.is_space or tok.is_punct:
            continue
        # main clause: ROOT verb of a sentence (one per sent)
        if tok.dep_ == "ROOT" and tok.pos_ in {"VERB", "AUX"}:
            main_clauses += 1
        if tok.dep_ in SUBORDINATE_DEPS:
            subord_clauses += 1
        # finite verbs: VERB or AUX with TENSE=Pres/Past or VerbForm=Fin
        if tok.pos_ in {"VERB", "AUX"}:
            morph = tok.morph
            if "Fin" in morph.get("VerbForm") or "Pres" in morph.get(
                "Tense"
            ) or "Past" in morph.get("Tense"):
                finite_verbs += 1
        if tok.dep_ in {"auxpass", "nsubjpass", "csubjpass"}:
            passive_marks += 1
        if tok.pos_ == "NOUN":
            nouns += 1
            lemma = (tok.lemma_ or tok.text).lower()
            if any(lemma.endswith(suf) for suf in NOMINALIZATION_SUFFIXES) and len(lemma) >= 6:
                nominalizations += 1

    # mean_t_unit_length: tokens / main clauses (one T-unit per main clause)
    if main_clauses == 0:
        # fall back: one T-unit per sentence
        main_clauses_eff = len(sents)
    else:
        main_clauses_eff = main_clauses
    mean_t_unit_length = n_tokens / main_clauses_eff

    subord_ratio = subord_clauses / main_clauses_eff
    passive_ratio = (passive_marks / finite_verbs) if finite_verbs else 0.0
    nominalization_ratio = (nominalizations / nouns) if nouns else 0.0

    return {
        "mean_dep_depth": float(mean_dep_depth),
        "mean_t_unit_length": float(mean_t_unit_length),
        "subord_clause_ratio": float(subord_ratio),
        "passive_ratio": float(passive_ratio),
        "nominalization_ratio": float(nominalization_ratio),
        "n_sentences": float(len(sents)),
        "n_tokens": float(n_tokens),
    }


def score_syntax_batch(texts: Iterable[str]) -> list[dict[str, float]]:
    return [score_syntax(t) for t in texts]


if __name__ == "__main__":
    samples = [
        ("kindergarten", "We can count to one hundred. We count one, two, three, four, five."),
        (
            "grade-7",
            "Verify the meaning of an unfamiliar word by checking its inferred meaning in context or by consulting a dictionary.",
        ),
        (
            "grade-12",
            "Investigations of intricate epistemological frameworks, which are necessitated by contemporary discourse, demand that rigorous methodological scrutiny be applied across heterogeneous academic disciplines.",
        ),
    ]
    for label, txt in samples:
        s = score_syntax(txt)
        print(
            f"{label}: depth={s['mean_dep_depth']:.2f} tu_len={s['mean_t_unit_length']:.2f} "
            f"subord={s['subord_clause_ratio']:.2f} passive={s['passive_ratio']:.2f} "
            f"nom={s['nominalization_ratio']:.2f} n_sent={int(s['n_sentences'])}"
        )
