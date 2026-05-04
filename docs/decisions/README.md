# Architecture / Methodology Decision Records

ADRs (architecture decision records) capture a single significant decision, the context for it, the options considered, and the consequences. One file per decision, numbered in the order made. Older ADRs are not edited; if a decision is reversed, a new ADR supersedes it (with `Supersedes:` and `Superseded-by:` cross-references).

## Format

```markdown
# ADR NNNN — Short title

**Status:** Proposed | Accepted | Superseded by ADR-NNNN
**Date:** YYYY-MM-DD

## Context

What forced the decision. Constraints, prior options, what we knew and didn't.

## Decision

The choice, stated plainly.

## Rationale

Why this choice, vs the alternatives. Pressure-testing.

## Consequences

What we accept by choosing this. Known limitations, downstream implications, open questions.

## See also

Links to related research-log entries, scope/methodology docs, or external references.
```

## Index

- [ADR 0001 — Standards data source: Learning Commons Knowledge Graph](0001-data-source-learning-commons.md)

## When to write a new ADR

- Choosing a major dependency (data source, evaluator framework, model).
- Locking a methodology choice that downstream analyses will assume.
- Reversing a previous decision.

If a decision is reversible in five minutes by re-running a script, it does not warrant an ADR. ADRs are for choices that would be expensive to undo.
