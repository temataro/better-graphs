# CLAUDE.md

This file provides guidance to any capable AI agents when working with code in this repository.

## What this project actually is

This is not a charts repo that happens to use agents — it is an **agent-instruction repo that happens to
produce charts**. The real deliverable is a reusable, self-contained instruction set so any future agent can
make professional, Tufte-grade matplotlib figures with zero re-explanation. The three durable artifacts are:

- **`CLAUDE.md`** (this file) — the agent operating rules: workflow + hard rules.
- **`VISUALIZATION_GUIDE.md`** — the chart-choice decision framework: the 10 rules, a pre-flight checklist, a
  *(data shape × task) → chart* lookup, and a chart catalog (when to use / when not / the anti-pattern).
- **`visualization-curriculum/house_style.py`** — the one-line lever agents call: `apply_theme()`, `despine()`,
  `polish()`, `thousands()`, `add_colorbar()`, `outlined_text()`, `takeaway_title(highlight=…)`,
  `diverging_norm()`, `save_all()`, the `CATEGORICAL`/`ACCENT`/`GREY` palette, and (eventually) chart builders.

Charts are byproducts; when you build one, the goal is to **extract the reusable rule** back into these three
files. `PLAN.md` is the full module-by-module roadmap (M0–M7); read it before substantive work — each module
states a principle, a thing to build, and a rule to extract. The `visualization-curriculum/` content is a
Quarto-rendered course (the eventual `.qmd` → HTML) meant as worked-example inspiration for *less capable*
future agents; `.ipynb` files are byproducts of that, not the working surface.

## Current state

The curriculum is **complete: M0–M7 are written**, each ending with a before/after on real data and a rule
distilled back into the three durable artifacts. The environment is set up and working. What exists:

- `pyproject.toml` + uv-managed `.venv/` + `uv.lock` — the plotting stack is installed; git is initialized
  on `main`.
- `visualization-curriculum/house_style.py` — the theme/helpers module. `apply_theme()` loads
  `minerva.mplstyle` and is verified working (it previously pointed at a nonexistent `your_style.mplstyle`).
- `visualization-curriculum/ndata.py` — numpy data layer (`load` → dict of arrays from `.npz`, plus
  `select`/`group`/`pivot`/`rolling_mean`/`corr`/`std`/`finite`). The curriculum uses this, not pandas.
- `visualization-curriculum/minerva.mplstyle` — base rcParams; the default font is **League Spartan**.
- `visualization-curriculum/fonts/` — vendored League Spartan + Junction (The League of Movable Type, OFL).
  `house_style` registers them on import, so figures need no system font install.
- `visualization-curriculum/better_graphs.qmd` — the curriculum source (Quarto → HTML); **M0–M7 written**.
  Its cells read `data/*.npz` via `ndata.load`, so build the datasets before rendering.
- `VISUALIZATION_GUIDE.md` — the chart-choice decision framework (written in M1; see above).
- `data/` — `build_datasets.py` (downloads + synthesizes the datasets) and `data/README.md` (provenance);
  these two are tracked. The data they produce (`data/raw/`, `data/*.csv`, `data/*.npz`) is gitignored and
  regenerated on demand: `uv run python data/build_datasets.py`.
- `PLAN.md`, `README.md`, `output.pdf` (a 9-page PDF reference, ~41 MB).

- `outputs/` — exported figures (`house_style.save_all` writes `<stem>.{svg,pdf,png}` here). Gitignored and
  regenerated on render, like `data/` — the export *code* is the deliverable, not the binaries.

Still planned but **not** present (per `PLAN.md`): the chart builders inside `house_style.py`
(`bar()`, `line()`, `slope()`, `dumbbell()`, `dist()`, `heatmap()`). Don't assume these exist.

## Charting rules (the operating manual)

### Workflow (every time, in order)
1. Answer the chart-choice checklist in `VISUALIZATION_GUIDE.md`. State the chart type and WHY in one line —
   *"`<chart>` because `<shape>` + `<task>`."*
2. `from house_style import apply_theme; apply_theme(mode=...)` as the first plotting line.
   - mode='executive' → slides / one-message charts;  mode='detailed' → appendices / multi-panel.
3. OO API: `fig, ax = plt.subplots(constrained_layout=True)`. No `plt.*` plotting calls after (only savefig).
4. TITLE states the takeaway, not the axis names. Colour-key the series words into it:
   `takeaway_title(ax, msg, highlight=[{"color": c1}, ...])` (wraps highlight_text) — a coloured word in the
   sentence beats a legend box.
5. Polish: `house_style.polish(ax, grid="y"|"x")` runs the ordered pass — offset/trim spines, `MaxNLocator`
   on the value axis, grid behind the data, margins. Then unit-aware formatters + direct labels.
6. Export with `house_style.save_all(fig, stem)`: vector (SVG+PDF) for print/slides AND PNG at 2× dpi for web,
   all `bbox_inches='tight'`. Dense scatter/large N → rasterized=True with a high savefig dpi.

### Hard rules
- No pie beyond ~5 slices. No dual-y-axis unless units truly differ (label + color both axes).
- No rainbow/jet. Match palette *type* to data: categorical → `house_style.CATEGORICAL` (accent-led);
  sequential → viridis; diverging → `house_style.diverging_norm()` (symmetric, centred TwoSlopeNorm).
- Grey-for-context + one accent (`#6400FF`) is the *default* for a single-message chart — not a mandate.
  Use a principled categorical/sequential palette when several series genuinely need distinguishing (never
  rainbow); don't force everything to monochrome. Thousands separators + unit-aware tick formatters always.
- Colorbars sized to the axes: fraction=0.046, pad=0.04.
- Size the figure first (it's the master coordinate); compose multi-panel with `subplot_mosaic` +
  `constrained_layout`, sharing one colour encoding across panels. Many series → small multiples (one panel
  per group, shared axes), never spaghetti. Zoom with an inset (`inset_axes` + `indicate_inset_zoom`).

### Libraries / stack
matplotlib (OO API), numpy, pypalettes (palettes), highlight-text (titles). **Curriculum data is numpy, not
pandas** (see below); pandas is used only by `data/build_datasets.py` (one-time ETL).

### Data & curriculum conventions
- **Data is numpy, via `visualization-curriculum/ndata.py`.** `load(name)` returns a *dict of numpy arrays*
  (a dataset's columns, read from the built `.npz`); helpers `select`, `group`, `pivot`, `rolling_mean`,
  `corr`, `std`, `finite` cover the few table ops (NaN-aware, pandas-parity). Plotting cells do plain numpy —
  `gapminder["lifeExp"][gapminder["year"] == 2007]`, never a DataFrame. Keep new data work in this style.
- **Every curriculum module ends with a before/after figure on real data** (raw/wrong → house/right) that
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

The env is uv-managed and git is initialized on `main`. There is no test/lint/CI yet.

- **Sync / install deps:** `uv sync` — installs the plotting stack plus the `dev` group (jupyter + ipykernel,
  needed to render Quarto). Add a dep with `uv add <pkg>`.
- **Run in the env:** `uv run python ...` (e.g. `uv run python -c "import house_style"` from the
  `visualization-curriculum/` dir).
- **Build datasets:** `uv run python data/build_datasets.py` (downloads via `curl` + synthesizes RF data).
  **Run this before rendering** — the curriculum's cells read `data/*.npz` (via `ndata`), which are gitignored.
- **Render the curriculum:** `uv run quarto render visualization-curriculum/better_graphs.qmd`, or
  `uv run quarto preview visualization-curriculum/better_graphs.qmd` for live reload. Quarto uses the jupyter
  engine, so run it through `uv run` to pick up the venv kernel. Code cells `import house_style`, which
  resolves because each cell's working directory is the `.qmd`'s own folder.

When you add tests/lint/CI, record the commands here.
