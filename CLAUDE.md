# CLAUDE.md

This file provides guidance to any capable AI agents when working with code in this repository.

## What this project actually is

This is not a charts repo that happens to use agents — it is an **agent-instruction repo that happens to
produce charts**. The real deliverable is a reusable, self-contained instruction set so any future agent can
make readable, evidence-led matplotlib figures with explicit context and checks. The three durable artifacts are:

- **`CLAUDE.md`** (this file) — the agent operating rules: workflow + hard rules.
- **`VISUALIZATION_GUIDE.md`** — the design authority: evidence-first decision brief, task-based
  chart choice, hierarchy, uncertainty, accessibility, registers, effort and release checks.
- **`visualization-curriculum/house_style.py`** — the one-line lever agents call: `theme(register)`,
  `page(kicker=, title=, dek=, source=)`, `finish()`, `units()`, `label_end()`, `mark()`, `spec_band()`,
  `stat()`, `panel_title()`, `diverging_norm()`, `save()`, the validated `SERIES`/`ACCENT` palette plus
  `SEQUENTIAL`/`DIVERGING` house colormaps, and (eventually) chart builders.

Charts are byproducts; when you build one, the goal is to **extract the reusable rule** back into these three
files. `PLAN.md` is the full module-by-module roadmap (M0–M7); read it before substantive work — each module
states a principle, a thing to build, and a rule to extract. The `visualization-curriculum/` content is a
Quarto-rendered course (the eventual `.qmd` → HTML) meant as worked-example inspiration for *less capable*
future agents; `.ipynb` files are byproducts of that, not the working surface.

## Current state

The curriculum is **complete: M0–M7 are written**, each ending with a before/after on public or explicitly synthetic teaching data and a rule
distilled back into the three durable artifacts. The environment is set up and working. What exists:

- `pyproject.toml` + uv-managed `.venv/` + `uv.lock` — the plotting stack is installed; the active branch is task-dependent; check it before changes.
- `visualization-curriculum/house_style.py` — the theme/helpers module: a figure is a small publication —
  registers (`glance`/`read`/`study`) set the type scale and density, `page()` builds the kicker/title/dek/
  source anatomy at inch-true margins, `finish()` polishes the axes. `theme()` loads `minerva.mplstyle`.
- `visualization-curriculum/ndata.py` — numpy data layer (`load` → dict of arrays from `.npz`, plus
  `select`/`group`/`pivot`/`rolling_mean`/`corr`/`std`/`finite`). The curriculum uses this, not pandas.
- `visualization-curriculum/minerva.mplstyle` — base rcParams: warm paper (`#FAF7F2`), warm ink, Junction as
  the working-text font. The default typefaces are **League Spartan** (display) + **Junction** (body).
- `visualization-curriculum/fonts/` — vendored League Spartan + Junction (The League of Movable Type, OFL).
  `house_style` registers them on import, so figures need no system font install.
- `visualization-curriculum/check_palette.py` — the palette validator: simulates protanopia/deuteranopia/
  tritanopia (Machado 2009), measures worst-pair ΔE, lightness band, chroma floor, and WCAG contrast against
  the paper/white surface. Any palette change must pass it — colour is computed, not eyeballed.
- `visualization-curriculum/better_graphs.qmd` — the curriculum source (Quarto → HTML); **M0–M7 written**.
  Its cells read `data/*.npz` via `ndata.load`, so build the datasets before rendering.
- `VISUALIZATION_GUIDE.md` — the full design framework (chart-choice, registers, altitude, anatomy, colour;
  see above).
- `data/` — `build_datasets.py` (downloads + synthesizes the datasets) and `data/README.md` (provenance);
  these two are tracked. The data they produce (`data/raw/`, `data/*.csv`, `data/*.npz`) is gitignored and
  regenerated on demand: `uv run python data/build_datasets.py`.
- `PLAN.md`, `README.md`, `output.pdf` (a 9-page PDF reference, ~41 MB).

- `outputs/` — exported figures (`house_style.save()` writes `<stem>.{svg,pdf,png}` here). Gitignored and
  regenerated on render, like `data/` — the export *code* is the deliverable, not the binaries.

Still planned but **not** present (per `PLAN.md`): the chart builders inside `house_style.py`
(`bar()`, `line()`, `slope()`, `dumbbell()`, `dist()`, `heatmap()`). Don't assume these exist.

## Charting rules (the operating manual)

A chart is an interface to evidence. A publication-like header is a useful delivery pattern,
not a substitute for analysis. `VISUALIZATION_GUIDE.md` is the decision authority; if an older
roadmap or example states an aesthetic absolute, use the guide's conditional rule instead.

### Workflow (every time, in order)
1. **Brief the reader/task/context.** State the decision, medium, dimensions and cost of error.
2. **Inspect evidence before writing a finding.** Record provenance, observational unit, units,
   denominator, n, missingness, exclusions and transformations. Identify simulated data. A question
   or descriptive title is appropriate until a finding is supported.
3. **Choose the chart and an alternative.** State "`<chart>` because `<shape>` + `<task>`."
   Prefer a table for lookup; check baselines, aggregation and what the encoding hides.
4. **Choose register and effort.** `theme("glance"|"read"|"study")` sets typography/density,
   not an exemption from uncertainty. A0 diagnostic, A1 composed, A2 bespoke; justify A2 with the
   guide's four checks. An explicitly provisional A0 can be shared as such.
5. **Compose evidence and qualification.** Use `page(kicker=, title=, dek=, source=, note=)`
   when a self-contained header helps. Use the OO API. Supported claim or question in the title;
   units, population, time, method and material caveat must be discoverable. Accent only a justified
   focal comparison; co-equal groups deserve equal treatment.
6. **Add reading aids as needed.** `finish()`, `units()`, `label_end()`, `mark()`, `spec_band()`,
   `stat()` and `panel_title()` are tools, not quotas. A legend can outperform colliding direct labels.
   A spec band is not an uncertainty interval. Do not add an unsupported interpretive callout.
7. **Validate the real output.** Recompute summaries, check scales and limits, inspect at delivery
   size, check redundant identity/contrast and provide alt text plus a caption/data route. Report
   which checks were automated and which were visual; do not claim accessibility certification.
8. **Export and extract a reusable conditional rule.** `house_style.save(fig, stem)` exports
   SVG/PDF/PNG. Preserve `page()` margins (do not tight-crop that layout). Re-render when reuse fails
   destination-size checks. Record the task, choice, reason, exception and observable acceptance test.

### Integrity requirements vs. house defaults
- Bars encode magnitude by length: start at zero; do not break the scale. Cropped dot/line axes are
  permitted when clearly labelled and proportionate to the task. State log transforms and references.
- Show raw points alongside summaries at small n when disclosure is safe. Define uncertainty type,
  level/method and sampling unit; material uncertainty belongs in **every** register. Never invent it.
- Show missingness honestly, retain denominator changes and distinguish association from causation.
- Prefer shared-x panels over dual y axes. Different units and aligned zeros do not fix arbitrary
  scale comparisons. If a domain convention warrants twins, label both scales, distinguish marks
  without colour alone, and warn against interpreting crossings or relative slopes.
- Use categorical/sequential/diverging colour for the appropriate semantics. Do not cycle a palette
  into ambiguous identities or use rainbow/jet for ordered magnitude. Palette changes run
  `check_palette.py`; swatch checks alone do not establish chart accessibility.
- Single accent, left-aligned title, horizontal unit labels, six categorical colours, direct labels,
  quiet grid and the house fonts are **defaults**, not integrity laws. Keep/revise them based on task,
  fit and readability. No compulsory `mark()`, no compulsory finding, no automatic ban on legends.
- League Spartan is the display default, Junction the body default. Special glyphs may need
  `family=house_style.BODY_STACK`. Check actual glyphs and text contrast in exported output.
- Set size before composition. Shared scales support magnitude comparison; if using free scales
  for shape, label that explicitly. Keep colour identities consistent across panels.

### Libraries / stack
matplotlib (OO API), numpy, pypalettes (palettes), highlight-text (titles). **Curriculum data is numpy, not
pandas** (see below); pandas is used only by `data/build_datasets.py` (one-time ETL).

### Data & curriculum conventions
- **Data is numpy, via `visualization-curriculum/ndata.py`.** `load(name)` returns a *dict of numpy arrays*
  (a dataset's columns, read from the built `.npz`); helpers `select`, `group`, `pivot`, `rolling_mean`,
  `corr`, `std`, `finite` cover the few table ops (NaN-aware, pandas-parity). Plotting cells do plain numpy —
  `gapminder["lifeExp"][gapminder["year"] == 2007]`, never a DataFrame. Keep new data work in this style.
- **Every curriculum module ends with a before/after figure on documented data** (default → task-adapted) that
  distils the module's principle. Preserve this convention when adding modules.
- **Snippet code style — names that read like the chart, black-*style* readability (not black output).**
  Variables (including intermediates) name *what they hold*, not their type: `median_life_exp`, not `vals`;
  `order_by_2007`, not `o`; `gain_ax`/`pae_ax`, not `ax1`/`ax2`. Dataset bindings spell the dataset out
  (`gapminder`, `penguins`, `flights`), never `gap`/`peng`/`fl`. Formatting follows black's *conventions* — no
  semicolons or compound statements, one statement per line, trailing commas on multiline calls — but the cells
  are deliberately **denser than strict black**: many-kwarg matplotlib calls are grouped a few args per
  continuation line, where `black` would explode each to its own line (a 7-kwarg `ax.text` → 9 lines). That
  density is intentional for worked examples, so **don't run `black` over the cells** — it would bloat them and
  isn't wired up (these are `.qmd` cells, no `[tool.black]`). Treat "how would black format this?" as a
  *tiebreaker* when a wrap is genuinely ambiguous, not a post-processor. (Extracted from a full-curriculum
  refactor; honour it in every new cell.)

## Environment & commands

The env is uv-managed. Work on the requested review branch; do not merge or publish without human
approval. `.github/workflows/publish.yml` builds branch/PR reviews with read-only permissions;
only a main push or main manual run can deploy. Never trigger that deployment during review.

- **Sync / install deps:** `uv sync --locked` — installs the plotting stack plus the `dev` group (jupyter + ipykernel,
  needed to render Quarto). Add a dep with `uv add <pkg>`.
- **Run in the env:** `uv run python ...` (e.g. `uv run python -c "import house_style"` from the
  `visualization-curriculum/` dir).
- **Build datasets:** `uv run python data/build_datasets.py` (downloads via `curl` + synthesizes RF data).
  **Run this before rendering** — the curriculum's cells read `data/*.npz` (via `ndata`), which are gitignored.
- **Render the curriculum:** `uv run quarto render visualization-curriculum/better_graphs.qmd`, or
  `uv run quarto preview visualization-curriculum/better_graphs.qmd` for live reload. Quarto uses the jupyter
  engine, so run it through `uv run` to pick up the venv kernel. Code cells `import house_style`, which
  resolves because each cell's working directory is the `.qmd`'s own folder.

### Review and validation commands

```bash
uv sync --locked
uv run python data/build_datasets.py
uv run python scripts/check_house_palette.py
uv run python -m unittest discover -s tests -v
uv run quarto render visualization-curriculum/better_graphs.qmd
uv run python scripts/validate_review.py
```

The validator checks local Markdown paths, embedded HTML images/alt text/internal anchors, and
self-contained resources; it does not claim a live external-link or screen-reader audit. Workflow
conditions are covered by tests; use `actionlint` as the separate GitHub Actions syntax check.
For this review, copy the rendered file to `reviews/gpt-6-astra/index.html` after validation. That
single explicit HTML location is unignored; do not stage other build outputs, `observations/`,
`skills/` or unrelated files. Commit only explicit paths, then push the review branch, never main.
The committed preview is a downloadable local artifact, not a deployed preview site.
