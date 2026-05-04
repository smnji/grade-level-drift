# notebooks/

## Naming convention

Notebooks follow `NN.NN-AB-short-description.ipynb`:

- **First `NN`** — phase. Two digits, leading zero.
  - `00` — exploratory (one-off, not part of a run)
  - `01` — pilot (small-scale runs to debug the pipeline)
  - `02` — full study (the pre-registered run)
  - `03` — analysis (notebooks tied to a specific `run_id`)
  - `04` — writeup (figures, tables, exposition for the publication)
- **Second `NN`** — sequence within phase. Increments per notebook.
- **`AB`** — author initials.
- **`short-description`** — kebab-case description of what the notebook does.

Examples:

- `00.01-sn-explore-lc-frameworks.ipynb`
- `01.02-sn-pilot-claude-grade-3.ipynb`
- `03.01-sn-analysis-pilot-001-drift.ipynb`
- `04.02-sn-figures-band-cut.ipynb`

## Etiquette

- **One concern per notebook.** Don't pile.
- **Logic that runs more than twice migrates to `src/`.** Notebooks call into `src/`, not the other way around.
- **Notebooks tied to a specific run reference the `run_id` in the description.** That makes the lineage discoverable from a `find` or a `grep`.
- **Re-running should be deterministic** if the upstream `run_id`'s artifacts haven't changed. Pin random seeds and cell ordering.
- **Don't commit cell outputs** if they're large or non-deterministic. Use `nbstripout` or clear before commit if necessary.

## Don't do

- Don't keep a "scratch.ipynb" in the repo. If the work matters, name and date it.
- Don't write production logic in a notebook because it's faster — refactor to `src/` as soon as it's clear the code matters.
- Don't reference paths relative to the notebook's location; reference repo-relative or use `pathlib.Path(__file__).parent` patterns from `src/`.
