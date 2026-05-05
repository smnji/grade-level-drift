# Attribution

This work uses, builds on, or directly invokes the following. Any publication arising from this research carries the attributions listed below in its Methodology and Acknowledgments sections.

## Standards data

- **Learning Commons Knowledge Graph** — academic standards, learning components, learning progressions. Released under **CC BY 4.0**. https://learningcommons.org
- **CASE Network 2 (1EdTech)** — the standards-framework backbone underlying LC's standards data. Knowledge Graph received state standards and written permission under CC BY 4.0 from 1EdTech.
- **State Departments of Education** — the original publishers of the standards documents that flow through 1EdTech and LC.

## Measurement instruments (deterministic, open-source)

The v0 evaluation pipeline is fully deterministic. No LLM-as-judge is used. Every measurement is reproducible offline by anyone with Python.

### Readability formulas

- **`textstat`** — open-source Python implementation of classical readability formulas (Flesch-Kincaid Grade Level, SMOG, Coleman-Liau, Automated Readability Index, Gunning Fog, Dale-Chall, New Dale-Chall, Linsear Write, Spache). MIT-licensed. https://github.com/textstat/textstat
- **Flesch-Kincaid Grade Level** (Kincaid et al., 1975), **SMOG Index** (McLaughlin, 1969), **Coleman-Liau** (Coleman & Liau, 1975), **Automated Readability Index** (Smith & Senter, 1967), **Gunning Fog** (Gunning, 1952), **Dale-Chall** (Dale & Chall, revised 1995). Each formula is cited individually in the Methodology section of any publication.

### Vocabulary tier word lists

- **Coxhead's Academic Word List (AWL)** — 570 word families across 28 sub-lists; the standard reference for Tier-2 (Beck/McKeown) academic vocabulary. Free download from Victoria University of Wellington under fair-use terms for research. https://www.wgtn.ac.nz/lals/resources/academicwordlist. The 570 headwords are embedded verbatim at [`src/evaluators/wordlists/awl.txt`](../src/evaluators/wordlists/awl.txt) (SHA-256 `22bf86cd84fafec9a3b558be86ccd0fc4ea0b09f4acb9dcf0076af800e80d951`), fetched 2026-05-05 from the EAP Foundation mirror at https://www.eapfoundation.com/vocab/academic/awllists/.
- **New General Service List (NGSL)** — 2,800 most useful general English words. Browne, C., Culligan, B., & Phillips, J. (2013). https://www.newgeneralservicelist.com. The 2,799-headword EAP Foundation mirror (https://www.eapfoundation.com/vocab/general/ngsl/) is embedded verbatim at [`src/evaluators/wordlists/ngsl.txt`](../src/evaluators/wordlists/ngsl.txt) (SHA-256 `1befc69f89d4d55bc739e7a9c132b04bd3be15ce3b1f719b0f6071ba9bf3be8f`), fetched 2026-05-05. The mirror omits a small number of closed-class items (numerals, some modals); see [`src/evaluators/wordlists/README.md`](../src/evaluators/wordlists/README.md).
- **Dale-Chall list** — 3,000 words familiar to 4th-grade readers (bundled with `textstat`). Public-domain reference list.

### Syntactic complexity

- **spaCy** — industrial-strength dependency parser used to compute mean dependency depth, T-unit length, subordinate-clause ratio, passive ratio, and nominalization ratio per output. MIT-licensed. https://spacy.io
- **L2 Syntactic Complexity Analyzer (L2SCA)** — Lu (2010); the source of the T-unit-based syntactic complexity construct. We use spaCy's parser to compute L2SCA-style indices.

### Calibration corpus (optional CLEAR-trained predictor)

- **CommonLit Ease of Readability (CLEAR) Corpus** — 4,724 expert-rated passages with grade-level scores. Used to train an optional ridge-regression predictor that maps the deterministic feature set to expert-rated grade level. Open-licensed. https://github.com/scrosseye/CLEAR-Corpus

## Models used

To be filled in per published run, with model identifier, version, and access date:

- Instruction generators (multiple OpenAI frontier models per run, e.g. `gpt-5.5`, `gpt-5.4`, `gpt-4.1`).
- Standard-rewriter model (used to produce simplified-wording variants of each standard for the wording-condition arm; identity logged in run manifest).

## Canonical attribution line

The following sentence is included verbatim in any publication's Methodology section:

> Standards data are provided by Learning Commons under CC BY 4.0. Knowledge Graph received state standards and written permission under CC BY 4.0 from 1EdTech (CASE Network 2). The evaluation stack is fully deterministic and uses open-source instruments: `textstat` for classical readability formulas (Flesch-Kincaid, SMOG, Coleman-Liau, ARI, Gunning Fog, Dale-Chall), Coxhead's Academic Word List and the New General Service List for vocabulary-tier composition, and spaCy for dependency-based syntactic complexity. Optional CLEAR-corpus calibration is used to map the feature set to expert-rated grade level.

## License downstream

This repository's intended public-release posture (per [`LICENSE.md`](../LICENSE.md)) — MIT for code and CC BY 4.0 for data and prose — is chosen to match Learning Commons' own dual posture, so that derivatives can flow freely both upstream and downstream.
