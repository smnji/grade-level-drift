# ADR 0001 — Standards data source: Learning Commons Knowledge Graph

**Status:** Accepted
**Date:** 2026-05-04

## Context

The study requires K-12 academic standards text — full statement wording, codes (e.g. `3.NF.A.1`), grade levels, subject, and jurisdiction — as input to LLM instruction generation. Several open sources exist: Common Standards Project (CSP), CASE Network (1EdTech), OpenSALT, the Achievement Standards Network (ASN), and direct state DOE publications.

The companion project `standards-substrate` already snapshotted CSP for a different research question (cross-state semantic drift). Reusing that corpus here was an option.

## Decision

**Use Learning Commons (LC) Knowledge Graph as the primary standards data source.** Use the **REST API** during the pilot and dev phase; pin to **public JSONL exports** for the published artifact freeze.

## Rationale

- **Pre-aligned to the evaluators.** LC's evaluators were built against the same CASE Network 2 standards backbone that LC's Knowledge Graph exposes. Using LC for both data and measurement removes an alignment layer that we would otherwise have to build and validate.
- **Open license.** Knowledge Graph data is CC BY 4.0 — fully redistributable with attribution.
- **API ergonomics.** A single REST surface returns standards, frameworks, learning components, progressions, and crosswalks. CSP's surface is shallower and would have required a normalization pass to reach the same shape.
- **Reproducibility option.** LC publishes the data as public JSONL, so a published version of this study can run end-to-end with no auth, even though the live API is in private beta.
- **Methodological coherence.** The research-questions document (parent series) explicitly frames LC as "reference infrastructure." Building on it is on-mission.

## Alternatives considered

- **CSP (the standards-substrate corpus).** Already snapshotted, but lacks alignment to the LC evaluators and would require a translation layer to map CSP standards to whatever the evaluators expect. Reuse would save fetch time but cost more in alignment effort.
- **Direct state DOE scrapes.** Authoritative but ~50 different scrapers and significant PDF-parsing cost. Out of scope for a measurement-focused first study.
- **Mixed (LC + state DOE for fidelity check).** Worth doing in v1; deferred to keep v0 narrow.

## Consequences

- **Beta gating during pilot.** The REST API is private beta. Reproducibility during dev is gated by beta access. Mitigated by snapshotting to public JSONL before publication.
- **Methodology coupling.** The decision pairs us tightly with LC's data and evaluator stack. If LC's evaluators are revealed to have a calibration issue, our findings inherit it. Mitigation: a convergent-validity check against Flesch-Kincaid (and Lexile if API access is available) on a sub-sample.
- **Provenance chain.** state DOE → 1EdTech CASE Network 2 → LC. Disclosed in any publication.
- **Subject coverage.** LC Knowledge Graph is deepest for math; ELA is good but smaller; other subjects are uneven. Confines v0 to ELA + Math (already locked in `scope.md`).

## See also

- [`docs/data-sources.md`](../data-sources.md) — option map and operating procedures.
- [`docs/attribution.md`](../attribution.md) — attribution requirements.
- [`docs/research-log/2026-05-04-repo-initialized.md`](../research-log/2026-05-04-repo-initialized.md) — the session that produced this ADR.
