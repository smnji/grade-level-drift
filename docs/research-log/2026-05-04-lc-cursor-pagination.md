---
date: 2026-05-04
severity: moderate
area: infrastructure
tags: [lc-api, pagination, bug, snapshot]
title: LC API uses cursor pagination — fixed; true universe ~10× what page-based stub returned
---

While probing the Learning Commons `/academic-standards` endpoint to count standards in the Multi-State Common Core frameworks, both ELA and Math returned exactly 100 records — a count too clean to be true. CCSS has hundreds of standards per subject by any public reference.

## Diagnosis

`src/lc_client.py` was checking `payload["pagination"]["hasNextPage"]` for the loop condition, but the LC API actually returns:

```json
"pagination": {"limit": 100, "nextCursor": "<base64>", "hasMore": true}
```

— cursor-based pagination, not page-based. `hasNextPage` is always missing, so the loop exited after the first 100 records every time. The endpoint also takes `cursor=<token>` as a query param, not `page=<n>`.

## Fix

Rewrote `standards_in_framework()` to thread `nextCursor` forward and stop on `hasMore == False`. Single commit, kept the public signature. Verified against both CC frameworks.

## What the true universe looks like

| Subject | All items | `normalizedStatementType == "Standard"` | `Standard Grouping` |
|---|---|---|---|
| ELA  | 1463 | 1100 | 362 |
| Math |  836 |  597 | 226 |

The "Standard Grouping" bucket is organizational (Strands, Domains, Clusters, Conceptual Categories, Grade-Level headers) — these don't admit a "100-250 word student-facing explanation" the way a leaf standard does. So the working population for sampling is the 1100 ELA + 597 Math `Standard` records.

## Implications

- The pilot sample (n=100 per subject) is now a real sample (~9% ELA, ~17% Math), not the entire universe.
- The methodology doc previously specified `statementType == "Standard"` (393 in Math) as the frame; using `normalizedStatementType` is broader and includes the `Component` and `Content Standard` rows that are also leaf learning expectations. Updated `methodology.md §1` to reflect the broader cut.
- Future LC endpoints likely use the same cursor pattern. Anyone adding a new `*_in_framework`-style method should follow it.

## Why this is a research-log entry, not an ADR

The fix is a code change with no methodological lock-in. The methodological choice (which `normalizedStatementType` defines the sampling frame) is captured in the companion sampling-plan log entry and reflected in `methodology.md`.
