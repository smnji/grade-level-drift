---
status: accepted
date: 2026-05-04
decision-makers: principal investigator
consulted: []
informed: []
---

# ADR 0001 — Standards data source: Learning Commons Knowledge Graph

## Context and Problem Statement

The study requires K-12 academic standards text — full statement wording, codes (e.g., `3.NF.A.1`), grade levels, subject, and jurisdiction — as input to LLM instruction generation. Several open sources exist: Common Standards Project (CSP), CASE Network (1EdTech), OpenSALT, the Achievement Standards Network (ASN), and direct state Department of Education (DOE) publications. The companion project `standards-substrate` has already snapshotted CSP for a different research question (cross-state semantic drift); reusing that corpus here was an option.

Which data source — and which access mode within that source — gives v0 the best balance of speed-to-pilot, methodological coherence with the chosen evaluators, license cleanliness, and reproducibility on the publication path?

## Decision Drivers

* Pre-alignment with the chosen measurement instruments — Learning Commons' literacy evaluators are SAP-rubric-anchored, so pairing them with LC's own Knowledge Graph data avoids building (and validating) an alignment translation layer.
* Open license — work must be redistributable as part of the published artifact.
* API ergonomics for fast iteration during the pilot.
* Reproducibility option that does not depend on private-beta access at publication time.
* Methodological coherence with the broader research line (the parent question bank explicitly frames LC as "reference infrastructure").

## Considered Options

* **Learning Commons (LC) Knowledge Graph** — REST API during pilot and dev; public JSONL exports pinned for the publication freeze.
* **CSP corpus already snapshotted in `standards-substrate`** — bulk JSONL, ready locally.
* **Direct state DOE scrapes** — per-state PDF/HTML scrapers, authoritative original text.
* **Mixed: LC for structure + raw DOE for a fidelity slice** — full study runs on LC, with bootstrap-slice fidelity checks against raw DOE.

## Decision Outcome

**Chosen option: "Learning Commons (LC) Knowledge Graph",** because it satisfies all decision drivers simultaneously — pre-alignment with the evaluators eliminates an alignment layer, the CC BY 4.0 license enables open publication, the REST API supports fast pilot iteration, and the public JSONL exports give a non-gated reproduction path. Reuse of CSP would have saved fetch time but at the cost of building and validating a translation layer between CSP shape and what the LC evaluators expect.

### Consequences

* Good, because the v0 pipeline runs end-to-end on a single open data source with a single license to clear.
* Good, because the data and the measurement instrument come from the same stable upstream (LC), reducing version-drift risk between them.
* Good, because public JSONL exports allow third-party reproduction without LC platform access.
* Good, because LC's crosswalks across 15+ states for math give a richer comparison surface than CSP would.
* Bad, because the REST API is in private beta as of 2026-05; reproducibility during dev is gated by beta access. (Mitigated by snapshotting to public JSONL before the pre-registration freeze.)
* Bad, because the methodology is now coupled to LC's evaluator stack; a calibration issue in LC's evaluators would propagate to our findings. (Mitigated by a convergent-validity check against Flesch-Kincaid and Lexile on a sub-sample, planned in [`methodology.md`](../methodology.md).)
* Bad, because the provenance chain has two normalization layers (state DOE → 1EdTech CASE Network 2 → LC). (Disclosed in any publication's Methodology section.)

### Confirmation

* Pilot run succeeds in pulling standards via REST API and producing scored outputs end-to-end, with run manifest captured per [`methodology.md §5`](../methodology.md).
* Before the pre-registration freeze, the pilot run is reproduced against the public JSONL snapshot and outputs are verified to be identical (modulo provider drift in generation).
* Convergent-validity check against Flesch-Kincaid (and Lexile if API access is available) on a 50-standard subset shows correlation r > 0.6 with LC's Grade Level Appropriateness Evaluator.

## Pros and Cons of the Options

### Learning Commons (LC) Knowledge Graph

Multi-state, multi-subject K-12 standards anchored on CASE Network 2. REST API + MCP + public JSONL exports. CC BY 4.0.

* Good, because it is pre-aligned with the LC literacy evaluators we use for scoring.
* Good, because the license (CC BY 4.0) is fully redistributable.
* Good, because public JSONL exports give a non-gated reproduction path.
* Good, because crosswalks across 15+ states for math support richer comparisons.
* Neutral, because the REST API is in private beta (2026-05) — fast for us, gated for replicators until the JSONL freeze.
* Bad, because methodology becomes coupled to LC's evaluator-stack version drift.

### CSP corpus already snapshotted in `standards-substrate`

Already fetched; ready locally.

* Good, because zero fetch time.
* Good, because the corpus is already reproducible from a committed snapshot.
* Bad, because CSP standards are not aligned to LC's evaluators; we would need to build and validate a translation layer.
* Bad, because the CSP snapshot contains all subjects across all vintages — much larger than this study needs; filtering work duplicates effort.

### Direct state DOE scrapes

Authoritative original text from each state's official publication.

* Good, because state DOE publications are the canonical authority — no normalization layers.
* Bad, because ~50 different scrapers and significant PDF-parsing effort.
* Bad, because the v0 contribution is measurement, not source-fidelity verification — that work is in `standards-substrate`'s scope, not here.

### Mixed: LC + raw DOE for a fidelity slice

* Good, because methodological rigor — LC's text is verified at scale on a slice.
* Bad, because doubling the data layer in v0 expands scope; the fidelity check is more useful in v1 once a baseline drift signal exists.

## More Information

* [`docs/data-sources.md`](../data-sources.md) — full option map and operating procedures.
* [`docs/attribution.md`](../attribution.md) — attribution requirements.
* [`docs/research-log/2026-05-04-repo-initialized.md`](../research-log/2026-05-04-repo-initialized.md) — the session that produced this ADR.

To revisit this decision: write a new ADR with `Supersedes: 0001` in its frontmatter, and add `Superseded-by: NNNN` to this file's frontmatter (the only edit allowed on an accepted ADR).
