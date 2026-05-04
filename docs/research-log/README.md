# Research Log

Append-only, dated. Captures the running narrative — reasoning, dead ends, framing arguments, and intermediate findings — that doesn't fit a single ADR or scope document. Designed to be machine-queryable via YAML front matter.

## Format

One entry per file. Filename: `YYYY-MM-DD-short-slug.md`. Each file begins with YAML front matter, followed by a markdown body.

## Front matter schema

```yaml
---
date: 2026-05-04           # required, ISO 8601
severity: major            # required, enum: minor | moderate | major
area: infrastructure       # required, enum: see vocabulary below
tags: [repo, scaffold]     # optional, kebab-case keywords
decisions: [adr-0001]      # optional, ADRs this entry produced or affected
title: Short title         # required, used in indexes and queries
---
```

## Controlled vocabulary

### severity

- `minor` — clarification or small learning; no change to direction
- `moderate` — sharpens or refines a sub-decision
- `major` — changes project direction or invalidates prior work

### area

Extend as needed; record additions here.

- `data-source` — corpus acquisition and provenance
- `scope` — subject/grade/state/model/output boundaries
- `methodology` — pipeline design, sampling, statistical choices
- `framing` — research questions, paper narrative, audience
- `infrastructure` — repo, tooling, code architecture
- `analysis` — findings, results, intermediate measurements
- `evaluators` — anything specific to evaluator behavior or calibration
- `other` — anything else

## Querying

```python
# entries in a date range with given severity / area
from pathlib import Path
import yaml

for path in sorted(Path("docs/research-log").glob("20*.md")):
    text = path.read_text()
    front = text.split("---\n", 2)[1]
    meta = yaml.safe_load(front)
    if (meta["severity"] == "major"
        and meta["area"] == "methodology"
        and "2026-05-01" <= str(meta["date"]) <= "2026-12-31"):
        print(path.name, "—", meta["title"])
```
