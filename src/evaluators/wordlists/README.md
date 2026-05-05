# Word lists

These plain-text word lists are loaded once at evaluator import time and used
for the `pct_awl` / `pct_ngsl` / `pct_off_list` features in
`src/evaluators/vocabulary.py`. One headword per line, lowercase. Provenance
matters — these lists are part of the deterministic scoring contract.

## `awl.txt` — Coxhead Academic Word List (AWL), 570 headwords

Coxhead, A. (2000). A new academic word list. *TESOL Quarterly, 34*(2),
213-238. The 570 headwords cover sublists 1-10 (each headword represents a
word family — derivational members are matched via spaCy lemmatization rather
than enumerated here).

Canonical source:
https://www.wgtn.ac.nz/lals/resources/academicwordlist

This file is the published 570-headword set, embedded verbatim so the
evaluator stack does not depend on a network call at scoring time.

## `ngsl.txt` — New General Service List (NGSL)

Browne, C., Culligan, B., & Phillips, J. (2013). The New General Service
List. The list is published at https://www.newgeneralservicelist.com under a
permissive-attribution license.

This file is a representative seed of the most-frequent NGSL headwords
(approximately the top 2,800). For full reproducibility of the published v0
results, replace this file with the canonical 2,800-headword release from
the publisher and record the SHA-256 in the run manifest.
