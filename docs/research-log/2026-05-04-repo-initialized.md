---
date: 2026-05-04
severity: major
area: infrastructure
tags: [repo, scaffold, learning-commons, reading-level]
decisions: [adr-0001]
title: Repo initialized; data source decided; scaffolding in place
---

Initialized the `grade-level-drift` repository as the first investigation in a multi-part research line on LLMs and K-12 academic standards. The reading-level question is publishing-order #1 in a private upstream research-questions document.

## Decisions made today

- **Data source:** Learning Commons Knowledge Graph, REST API for pilot, JSONL freeze for publication. ADR-0001.
- **Subjects:** ELA + Math.
- **Grades:** Full K-12, reported by band.
- **Models (v0):** Claude pinned for pilot; second model added before publication for cross-model claims (Q2).
- **Output type:** Short student-facing explanation, 100–250 words, no worked examples.
- **Evaluators:** All five LC literacy evaluators on every output (Grade Level Appropriateness as primary outcome; the rest as orthogonal channels).
- **License posture:** private during research; intended public-release license MIT (code) + CC BY 4.0 (data and prose), matching LC's own.

## Repo layout

```
grade-level-drift/
├── .env / .env.example / .gitignore / LICENSE.md / README.md / requirements.txt
├── docs/
│   ├── charter.md, scope.md, methodology.md, data-sources.md, attribution.md
│   ├── research-proposal.md            (full: lit review, hypotheses, methodology, threats, reproducibility, timeline)
│   ├── decisions/0001-data-source-learning-commons.md
│   └── research-log/   (this file is the opening entry)
├── src/
│   ├── __init__.py
│   └── lc_client.py    (thin LC REST wrapper — skeleton)
├── data/
└── notebooks/
```

## API probe

Confirmed the LC REST API key works against `GET /standards-frameworks` — 200 OK, 100 frameworks returned (paginated; +70 more available). Frameworks span ELA, Math, Science, and Social Studies across many states. Multi-State Mathematics (Common Core) framework UUID: `c6496676-d7cb-11e8-824f-0242ac160002`.

## Open items entering the pilot

1. Confirm the 3–5 candidate states for the bootstrap slice. Candidate set: California, Texas, Florida, Massachusetts, Virginia.
2. Decide output length: fixed 100–250 across grades, or band-tiered.
3. Pick the second model for cross-model claims (GPT-4-class, Gemini, or both).
4. Decide whether jurisdiction is a stratification variable or an unmodeled covariate in v0.

## Notes

- The format established in this scaffold (charter / scope / methodology / data-sources / attribution / ADRs / research-log / research-proposal) is intended to be reused for future investigations in this series. Generic structure with topic-specific content per repo.
- The companion project `standards-substrate` (whitepaper-corpus work) provided the documentation conventions adopted here. No data is shared between repos in v0.
- The research proposal is the heaviest doc — full literature review, pre-registered hypotheses (H1-H5), methodology, threats to validity, reproducibility plan, ethics, and timeline. Lit review surfaced 28 sources across four themes (text-complexity metrics, LLM-as-judge validity, LLM register/complexity drift, LLMs as educational content generators).
