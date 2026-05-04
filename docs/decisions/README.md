# Architecture / Methodology Decision Records (ADRs)

ADRs in this repository follow the **MADR v3 (full)** convention. The blank template is at [`template.md`](template.md); copy it when starting a new ADR. The schema is enforced by structure, not just convention — keep the section ordering and frontmatter fields stable.

## Tooling

The repo is configured for [adr-tools](https://github.com/npryce/adr-tools). The `.adr-dir` file at the repo root points the CLI at this directory.

```bash
brew install adr-tools         # one-time, local install
adr new "Short title"          # creates the next-numbered ADR from the template
adr list                       # lists all ADRs
adr generate toc               # regenerates the index below
```

`adr-tools` is optional — you can also copy [`template.md`](template.md) by hand, increment the number, and fill it in.

## Index

- [ADR 0001 — Standards data source: Learning Commons Knowledge Graph](0001-data-source-learning-commons.md)

## When to write a new ADR

- Choosing a major dependency (data source, evaluator framework, model).
- Locking a methodology choice that downstream analyses will assume.
- Reversing a previous decision (write a new ADR with `Supersedes: NNNN` in frontmatter; add `Superseded-by: NNNN` to the original — the only edit allowed on an accepted ADR).

If a decision is reversible in five minutes by re-running a script, **do not** write an ADR — write a research-log entry instead.

## Etiquette

- **Sequential numbering** by acceptance order: `0001`, `0002`, `0003`, ...
- **Never edit accepted ADRs** except to add a `Superseded-by:` reference. To change a decision, write a new ADR.
- **One decision per file.** If you find yourself writing two decisions, split them.
- **Cross-link liberally.** ADRs should reference the research-log entries that produced them, the scope/methodology docs they affect, and any external standards they invoke.

## MADR section reference

The MADR-full template includes:

- **Frontmatter:** `status`, `date`, `decision-makers`, `consulted`, `informed`
- **Title** — short, representative of solved problem and found solution
- **Context and Problem Statement** — what forced the decision
- **Decision Drivers** — forces / concerns the decision must satisfy
- **Considered Options** — list of the alternatives surveyed
- **Decision Outcome** — chosen option + reason; sub-sections for **Consequences** (Good / Bad / Neutral bullets) and **Confirmation** (how compliance is verified)
- **Pros and Cons of the Options** — per-option Good/Neutral/Bad bullets
- **More Information** — pointers, deferred questions, validation plan

Optional sections (Confirmation, Pros and Cons, More Information) can be omitted when not load-bearing, but doing so reduces the ADR's evidentiary value — prefer to include unless deliberately trimming.
