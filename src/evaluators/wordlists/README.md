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

This file is the published 570-headword set, fetched 2026-05-05 from the
EAP Foundation mirror (https://www.eapfoundation.com/vocab/academic/awllists/)
and embedded verbatim so the evaluator stack does not depend on a network
call at scoring time. Headwords are British-English variants where the AWL
specifies them (e.g., `analyse`, not `analyze`); the evaluator lemmatizes
inputs before lookup, and the spaCy lemmatizer maps American variants onto
the same lemma so coverage is symmetric.

SHA-256: `22bf86cd84fafec9a3b558be86ccd0fc4ea0b09f4acb9dcf0076af800e80d951`

## `ngsl.txt` — New General Service List (NGSL)

Browne, C., Culligan, B., & Phillips, J. (2013). The New General Service
List. The list is published at https://www.newgeneralservicelist.com under a
permissive-attribution license.

This file is the NGSL headword set as published on the EAP Foundation
mirror (2,799 entries, fetched 2026-05-05 from
https://www.eapfoundation.com/vocab/general/ngsl/), embedded verbatim.
Inflected forms are not enumerated here — derivational members are matched
via spaCy lemmatization at scoring time.

**Caveat — closed-class omissions.** The EAP Foundation listing excludes
numerals (`two`, `three`, ..., `hundred`, `thousand`) and a small number of
modal verbs (`can`, `must`, ...). The published NGSL of Browne et al. does
include these. The wordlist `pct_*` features are therefore a slightly
conservative covariate (more text counts as "off-list" than under the strict
NGSL), but the bias is uniform across all generations being compared. The
headline outcome (Δ = ensemble_grade − target_grade) does not depend on
these features — they are reported as convergent-validity covariates only.

SHA-256: `1befc69f89d4d55bc739e7a9c132b04bd3be15ce3b1f719b0f6071ba9bf3be8f`
