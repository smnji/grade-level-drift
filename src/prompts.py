"""Frozen prompt templates for v0.

Each template's text is hashed at import time; the SHA is recorded in the
run manifest so that any change to wording invalidates downstream artifacts
in a discoverable way.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


# ---- generator templates (S/M/L by input token size) ---------------------

GENERATOR_S_TEMPLATE = """\
Standard ({grade}): {description}

Explain this to a grade {grade} student in 100-250 words.
"""

GENERATOR_M_TEMPLATE = """\
You are a teacher writing a short student-facing explanation of a K-12 academic standard.

Standard: {statement_code} (grade {grade})
Description: {description}

Write 100-250 words explaining what this standard means and what the student is expected to learn. Write at a reading level appropriate for grade {grade}. Do not include worked examples, problem sets, or follow-up questions.
"""

GENERATOR_L_TEMPLATE = """\
You are a teacher writing a short student-facing explanation of a K-12 academic standard.

Example —
Standard: K.CC.A.1 (grade K)
Description: Count to 100 by ones and by tens.
Explanation: We are learning to count up to 100. We can count one at a time: 1, 2, 3, 4, 5, all the way up to 100. We can also count by tens, jumping ten numbers at a time: 10, 20, 30, 40, 50, 60, 70, 80, 90, 100. Counting helps us know how many things there are.

Now write the same kind of explanation for this standard:

Standard: {statement_code} (grade {grade})
Description: {description}

Write 100-250 words. Write at a reading level appropriate for grade {grade}. Do not include worked examples or follow-up questions.
"""

# ---- rewriter (simplified-wording arm) -----------------------------------

REWRITER_TEMPLATE = """\
Rewrite the following K-12 academic standard so a 4th-grade reader can understand it. Preserve the learning expectation exactly — do not change what the student is asked to know or do. Simplify only the language: shorter sentences, more familiar vocabulary, no jargon. Keep the result to 1-3 sentences.

Standard: {description}
"""


@dataclass(frozen=True)
class PromptSpec:
    name: str
    template: str
    sha: str

    def render(self, **kwargs: object) -> str:
        return self.template.format(**kwargs)


GENERATOR_PROMPTS: dict[str, PromptSpec] = {
    "S": PromptSpec("S", GENERATOR_S_TEMPLATE, _sha(GENERATOR_S_TEMPLATE)),
    "M": PromptSpec("M", GENERATOR_M_TEMPLATE, _sha(GENERATOR_M_TEMPLATE)),
    "L": PromptSpec("L", GENERATOR_L_TEMPLATE, _sha(GENERATOR_L_TEMPLATE)),
}

REWRITER_PROMPT = PromptSpec("rewriter_v1", REWRITER_TEMPLATE, _sha(REWRITER_TEMPLATE))


def render_grade(grade_level: list[str] | str | None) -> str:
    """Render a standard's gradeLevel field into a target string for prompts.

    - Single grade ["3"] → "3"
    - Pair ["9","10"] → "9-10"
    - Span ["9","10","11","12"] → "9-12"
    - Empty / cross-grade → "K-12"
    """
    if not grade_level:
        return "K-12"
    if isinstance(grade_level, str):
        return grade_level
    if len(grade_level) == 1:
        return grade_level[0]
    nums: list[str] = []
    for g in grade_level:
        nums.append("0" if g == "K" else g)
    try:
        ints = sorted(int(n) for n in nums)
    except ValueError:
        return ",".join(grade_level)
    if ints == list(range(min(ints), max(ints) + 1)):
        lo = "K" if ints[0] == 0 else str(ints[0])
        hi = str(ints[-1])
        return f"{lo}-{hi}"
    return ",".join(grade_level)


if __name__ == "__main__":
    for name, spec in GENERATOR_PROMPTS.items():
        print(f"{name}: sha={spec.sha} chars={len(spec.template)}")
    print(f"rewriter: sha={REWRITER_PROMPT.sha} chars={len(REWRITER_PROMPT.template)}")
