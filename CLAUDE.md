# CLAUDE.md — Working in this Repository

This file is loaded automatically by Claude Code at the start of every session in this repo. It captures the conventions, etiquette, and guardrails for working here. **Read it before doing anything beyond a single-line edit.**

When this format is reused for a new investigation, copy this file as-is and update only the topic-specific docs (`charter.md`, `scope.md`, `research-proposal.md`, ADRs). The conventions below stay constant across investigations.

---

## 1. This is a research repository, not a development repository

- The docs in `docs/` are the primary artifact. `src/` exists to support the research, not the other way around.
- A 30-line script that runs once is fine. A 300-line "framework" is overkill.
- The deliverable is a publishable finding (blog post, white paper, or both), not a piece of software.
- Optimize for findings that hold up under scrutiny, not for code that scales.
- "Don't add features beyond what the task requires" applies twice as strongly here — every abstraction has to earn its keep against a methodological need.

## 2. Document hierarchy and update etiquette

| Path | Role | When to edit |
|---|---|---|
| [`README.md`](README.md) | Top-level intro and navigation | Only when the central question, layout, or status materially changes |
| [`docs/charter.md`](docs/charter.md) | Canonical question map | Only when the scope of the investigation actually shifts; otherwise treat as load-bearing reference |
| [`docs/scope.md`](docs/scope.md) | Boundary spec — what's in, what's out, what's open | When a scope dimension is decided or a new open question surfaces |
| [`docs/methodology.md`](docs/methodology.md) | Operational pipeline (canonical) | When the actual run procedure changes |
| [`docs/research-proposal.md`](docs/research-proposal.md) | Heavy doc — full lit review, hypotheses, threats, reproducibility, timeline | Major revision lands a new version tag; minor edits are fine |
| [`docs/data-sources.md`](docs/data-sources.md) | Data source decisions | When access mode, license, or provenance changes |
| [`docs/attribution.md`](docs/attribution.md) | Living credit list | Every time a new dataset, evaluator, model, or rubric is incorporated |
| [`docs/decisions/0NNN-*.md`](docs/decisions/) | ADRs | New file per decision; never edit accepted ADRs (supersede instead) |
| [`docs/research-log/YYYY-MM-DD-*.md`](docs/research-log/) | Append-only running log | Any time direction, framing, or a sub-decision sharpens |

**Cross-reference rule.** When editing a doc that another doc depends on, update both. The Q-numbering, hypothesis numbering, evaluator tables, and Claude's role descriptions are deliberately repeated across files; keep them aligned. (See §3.)

## 3. Numbering conventions

These are the most-violated conventions when working at speed. Get them right.

### Research questions

- **Charter is the source of truth** for the question list.
- v0 anchor questions: `Q1`, `Q2`, `Q3` — the ones the publication answers.
- Deferred questions: `Q4`, `Q5`, ... — mechanism, beyond-reading-level, decoupling, loop-closure, etc.
- Other docs reference the charter's Q-numbering. **Do not introduce parallel numberings** (e.g., per-section question lists).
- Before pushing changes that touch Q-references, run:
  ```bash
  grep -rn -E '\bQ[0-9]\b' docs/ --include='*.md'
  ```
  Verify every reference matches the charter.

### Hypotheses

- Pre-registered in `research-proposal.md §4` and numbered `H1`, `H2`, `H3`, ...
- Each hypothesis maps explicitly to one or more research questions; that mapping is part of the hypothesis statement.
- Frozen at the pre-registration tag (see §10). New hypotheses discovered mid-study become **H1a, H2a, ...** as extensions, never renumber-and-overwrite.

### ADRs

- Sequential: `0001`, `0002`, `0003`, ... by acceptance order.
- Never edited once **Status: Accepted**. To reverse a decision, write a new ADR and add `Supersedes: 0NNN` to its frontmatter and `Superseded-by: 0NNN` to the original (the only edit allowed on an accepted ADR).
- An ADR is for decisions that are expensive to undo. If a decision is reversible in five minutes by re-running a script, write a research-log entry instead.

### Investigations within a series

- This repo is one investigation in a multi-part series.
- Refer to other investigations descriptively ("a follow-up on per-standard model uncertainty"), **never** by inherited cluster numbers from upstream documents. Cluster numbers are decoder-ring jargon for anyone who lacks the upstream doc.

## 4. Research log conventions

- One entry per file. Filename: `YYYY-MM-DD-short-slug.md`.
- Append-only. Once an entry is written, it is not edited (with one narrow exception: a same-day entry can be updated with end-of-session results, since the day isn't over).
- Every entry begins with YAML frontmatter:

  ```yaml
  ---
  date: 2026-05-04
  severity: major          # minor | moderate | major
  area: methodology        # see vocabulary below
  tags: [kebab, case]
  decisions: [adr-0001]    # optional
  title: Short title
  ---
  ```

- **severity:**
  - `minor` — clarification or small learning; no change to direction
  - `moderate` — sharpens or refines a sub-decision
  - `major` — changes project direction or invalidates prior work
- **area:** `data-source`, `scope`, `methodology`, `framing`, `infrastructure`, `analysis`, `evaluators`, `other`. Add new areas as needed and document them in `research-log/README.md`.
- When in doubt, write an entry. Future-you and future-Claude can query the log; silent decisions evaporate.

## 5. Cookbook — when to add to where

| Trigger | Action |
|---|---|
| Decided something significant (data source, methodology choice, model selection) | New ADR with full Context / Decision / Rationale / Consequences |
| Made a discovery that changes direction | Research-log entry, `severity: major` |
| Sharpened a sub-decision (e.g., chose 3-of-5 candidate states) | Research-log entry, `severity: moderate`, plus scope.md edit |
| Learned something but no decision yet | Research-log entry, `severity: minor` |
| Updated a scope decision | Edit `scope.md` + research-log entry that links the change |
| Updated methodology | Edit `methodology.md` + research-log entry |
| Updated charter or hypotheses | Edit those docs + research-log entry, `severity: major`; verify all Q/H references still match |
| Encountered a dead end | Research-log entry — dead ends are the most undervalued log entries; they save future-you from repeating the failure |
| Found a literature source that shifts the framing | Update research-proposal §5 + research-log entry |

## 6. Hypotheses, assumptions, and open questions

These three live in different places on purpose.

| Kind | Where it lives | When to surface |
|---|---|---|
| **Hypotheses** | `research-proposal.md §4` | Pre-registered before pilot; frozen at the freeze tag |
| **Open scope questions** | `scope.md` "Decisions still open" | Before the pilot run; resolved into ADRs |
| **Threats to validity / assumptions** | `research-proposal.md §8` | Updated whenever a new threat is discovered, with the discovery date |

If a question doesn't fit any of these three, it probably belongs in a research-log entry as an open thread.

## 7. Secrets and API keys

- `.env` is **gitignored from the very first commit**. Never commit it; never echo its contents.
- `.env.example` documents the required environment variables with empty values.
- API keys and tokens are **never** written to a file other than `.env`, **never** logged, **never** echoed in command output, and **never** repeated back in chat.
- If a key leaks anywhere — into a transcript, a log file, a public diff — tell the user immediately and recommend rotation. Do not pretend it didn't happen.
- If you change which env vars the code reads (e.g., adding `LC_API_BASE`), update `.env.example` in the same commit. Don't leave the example lying about what's required.

## 8. Data and artifacts

- `data/raw/` is **gitignored** — contents are regenerable from APIs or public exports. Don't commit bulk data.
- `data/processed/` is committable — sample frames, run manifests, aggregated results.
- Every analysis run produces a `data/processed/{run_id}_manifest.json` with: model IDs and versions, prompt-template SHA, evaluator versions and backends, random seed, dataset snapshot date, generation timestamps, environment (Python version, key dependencies).
- Generated artifacts are write-once. Re-running produces a new `run_id`; never overwrite a previous run's outputs in place.

## 9. Reproducibility standards

A run is reproducible if a reader can regenerate the headline result without privileged access. To support that:

- Pin model IDs and versions; record them in the run manifest.
- Pin random seeds; record them.
- Hash the prompt template at run time; record the hash.
- Record evaluator versions and judge-model backends.
- Store all raw outputs and per-output scores before aggregation.
- Disclose every external dependency the reader needs (which API keys, which packages, which approximate cost).
- If a dependency is gated (private beta, paid), say so explicitly and provide an alternate access path on the published reproduction route.

## 10. Pre-registration

Before the full study run begins, freeze the following in a tagged commit (`pre-reg-v1`):

- Sample frame and seed
- Prompt template (file and SHA)
- Model IDs and decoding parameters
- Evaluator versions and backend model IDs
- Primary analyses (with specific test statistics and α levels)
- Hypotheses with predicted directions and magnitudes

Pilot runs may happen *before* the freeze and may inform what gets frozen. The full study runs *after*. Anything not in the pre-registration is exploratory and labeled as such in the writeup.

## 11. Threats to validity

- Maintained in `research-proposal.md §8`. Each threat is a labeled item (`T1`, `T2`, ...).
- Each threat is paired with a planned mitigation (or a frank acknowledgement when no mitigation is available).
- New threats discovered during pilot or analysis are added with the discovery date; they are not retroactively folded into the original list.
- A threat that turns out not to apply is annotated as resolved, never silently deleted.

## 12. What Claude should and shouldn't do in this repo

### Always

- **Cross-check numbering.** Before committing edits to any of charter / scope / methodology / research-proposal, grep for Q-numbering and hypothesis-numbering consistency.
- **Update both sides of a cross-reference.** If you edit a section other docs depend on, update those docs too in the same commit.
- **Verify `.env` isn't being staged.** Run `git diff --cached --name-only | grep -E '\.env$'` before any commit. Output should be empty.
- **Write a research-log entry for any non-trivial decision.** "Non-trivial" = anything you'd describe as "I decided X because Y."
- **Match charter Q-numbering and hypothesis H-numbering.** Don't introduce parallel local numberings.
- **Read `methodology.md` before changing the pipeline.** It is the source of truth for "how the run works."
- **Treat `.env.example` and `lc_client.py`-style modules as code-doc cross-references.** If `.env.example` says a var is required, the code should read it.

### Sometimes

- Generate a PDF from a doc when the user wants a shareable artifact (`pandoc input.md -o output.pdf --pdf-engine=weasyprint`).
- Convert intermediate findings into research-log entries proactively when a finding is about to be lost to context.
- Update this file when conventions evolve.

### Never

- **Never commit `.env`** or any file containing real keys.
- **Never edit accepted ADRs.** Supersede instead.
- **Never introduce parallel numbering schemes.** Q1 in charter must be Q1 everywhere.
- **Never invent results.** If a number is not yet computed, say so. Placeholders go in clearly-marked TODO blocks, not as confident claims.
- **Never add code or features beyond what a methodology decision requires.** This is the single most common drift mode in research repos.
- **Never write narrative-of-conversation in commits** ("then I tried X, then Y suggested Z..."). Commits describe state changes; narrative belongs in the research log.

## 13. Commit etiquette

- **Subject:** descriptive, under ~72 chars. State *what changed*. Examples: "Coherence pass: align Q-numbering, refresh status markers", "Initialize grade-level-drift repo".
- **Body:** focuses on **why**, not what — the diff shows what. State the constraint or motivation that forced the change.
- Match the style of recent commits in `git log`. If the repo's style is descriptive headers + body paragraphs, don't suddenly switch to one-line conventional-commits style.
- Always include the trailer when committing on the user's behalf:
  ```
  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
  ```
- Stage files explicitly (`git add path/to/file`), not `git add -A` or `git add .`. Bulk-staging is how `.env` and `.DS_Store` end up in commits.

## 14. Open-source posture

- This repo is **private during research**. Intended public-release license is **MIT for code + CC BY 4.0 for data and prose** (see `LICENSE.md`).
- Write everything as if it could go public tomorrow:
  - No internal jargon (cluster numbers, project codenames, person-specific shorthand).
  - No reliance on undocumented context. Cross-link any concept that isn't defined inline.
  - Attribution complete and current — every dataset, evaluator, rubric, and model credited.
  - No PII, no proprietary data, no API keys.
- The "private now, open later" path means we should never have a "scrub before publishing" task. The repo should be opt-in-public at any moment.

## 15. Working with the user

- This is a research project, not a build. Bias toward outputs that hold up to peer review, not features that ship.
- The user is using this format as a template across investigations. Keep the structure clean and reusable; don't bake in topic-specific assumptions in places that should be generic (this file, research-log conventions, ADR template).
- When conventions need to evolve, evolve them **here**, in this file, and in `research-log/`. Don't drift silently.
- When the user asks "is this coherent?" — actually audit. Read the docs, grep for stale references, check cross-doc consistency. Don't answer from memory of what you wrote.

## 16. When starting a new investigation in this format

If using this repo as a template for a new investigation:

1. Copy the whole repo structure (including this `CLAUDE.md`) to a new location.
2. Update topic-specific docs:
   - `README.md` — central question, why-this-matters, status
   - `docs/charter.md` — central question and sub-question map
   - `docs/scope.md` — dimensions and decisions for the new investigation
   - `docs/methodology.md` — pipeline for the new study
   - `docs/research-proposal.md` — full proposal (lit review, hypotheses, etc.)
   - `docs/decisions/0001-*.md` — first ADR (often the data-source decision)
   - `docs/research-log/YYYY-MM-DD-repo-initialized.md` — opening entry
3. Leave conventions docs alone:
   - This `CLAUDE.md`
   - `docs/decisions/README.md`
   - `docs/research-log/README.md`
4. Re-initialize git, set up `.env` and `.env.example`, push to a new private repo.
5. Open the first research-log entry; record the data-source decision as ADR-0001.

The conventions in this file should not need to change between investigations. If they do — that's a signal to update *here*, then carry the update back to other repos in the series.
