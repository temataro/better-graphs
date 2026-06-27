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
  `thousands()`, `add_colorbar()`, `outlined_text()`, `takeaway_title()`, and (eventually) chart builders.

Charts are byproducts; when you build one, the goal is to **extract the reusable rule** back into these three
files. `PLAN.md` is the full module-by-module roadmap (M0–M7); read it before substantive work — each module
states a principle, a thing to build, and a rule to extract. The `visualization-curriculum/` content is a
Quarto-rendered course (the eventual `.qmd` → HTML) meant as worked-example inspiration for *less capable*
future agents; `.ipynb` files are byproducts of that, not the working surface.

## Current state (most of `PLAN.md`'s layout does not exist yet)

This repo is at **M1 stage** (M0 and M1 of the curriculum are written) with the environment set up and
working. What exists:

- `pyproject.toml` + uv-managed `.venv/` + `uv.lock` — the plotting stack is installed; git is initialized
  on `main`.
- `visualization-curriculum/house_style.py` — the theme/helpers module. `apply_theme()` loads
  `minerva.mplstyle` and is verified working (it previously pointed at a nonexistent `your_style.mplstyle`).
- `visualization-curriculum/minerva.mplstyle` — base rcParams; the default font is **League Spartan**.
- `visualization-curriculum/fonts/` — vendored League Spartan + Junction (The League of Movable Type, OFL).
  `house_style` registers them on import, so figures need no system font install.
- `visualization-curriculum/better_graphs.qmd` — the curriculum source (Quarto → HTML); **M0–M1 written**.
  Its M1 cells read `data/*.csv`, so build the datasets before rendering.
- `VISUALIZATION_GUIDE.md` — the chart-choice decision framework (written in M1; see above).
- `data/` — `build_datasets.py` (downloads + synthesizes the datasets) and `data/README.md` (provenance);
  these two are tracked. The data they produce (`data/raw/`, `data/*.csv`, `data/*.npz`) is gitignored and
  regenerated on demand: `uv run python data/build_datasets.py`.
- `PLAN.md`, `README.md`, `output.pdf` (a 9-page PDF reference, ~41 MB).

Still planned but **not** present (per `PLAN.md`): `outputs/` and the chart builders inside `house_style.py`
(`bar()`, `line()`, `slope()`, `dumbbell()`, `dist()`, `heatmap()`). Don't assume these exist.

## Charting rules (the operating manual)

### Workflow (every time, in order)
1. Answer the chart-choice checklist in `VISUALIZATION_GUIDE.md`. State the chart type and WHY in one line —
   *"`<chart>` because `<shape>` + `<task>`."*
2. `from house_style import apply_theme; apply_theme(mode=...)` as the first plotting line.
   - mode='executive' → slides / one-message charts;  mode='detailed' → appendices / multi-panel.
3. OO API: `fig, ax = plt.subplots(constrained_layout=True)`. No `plt.*` plotting calls after (only savefig).
4. TITLE states the takeaway, not the axis names. Use highlight_text to key series by color.
5. Polish: offset/trim spines; set tick locators + unit-aware formatters; grid discipline; direct labels.
6. Export: vector (SVG or PDF) for print/slides AND PNG at dpi=200 for web; bbox_inches='tight'.
   Dense scatter/large N → rasterized=True with a high savefig dpi.

### Hard rules
- No pie beyond ~5 slices. No dual-y-axis unless units truly differ (label + color both axes).
- No rainbow/jet. Sequential → viridis family; diverging → centered TwoSlopeNorm.
- Grey-for-context + one accent (`#6400FF`) is the *default* for a single-message chart — not a mandate.
  Use a principled categorical/sequential palette when several series genuinely need distinguishing (never
  rainbow); don't force everything to monochrome. Thousands separators + unit-aware tick formatters always.
- Colorbars sized to the axes: fraction=0.046, pad=0.04.
- Size the figure first (it's the master coordinate); compose multi-panel with `subplot_mosaic` +
  `constrained_layout`, sharing one colour encoding across panels. Many series → small multiples (one panel
  per group, shared axes), never spaghetti. Zoom with an inset (`inset_axes` + `indicate_inset_zoom`).

### Libraries / stack
matplotlib (OO API), numpy, pandas, pypalettes (palettes), highlight-text (titles).

## Environment & commands

The env is uv-managed and git is initialized on `main`. There is no test/lint/CI yet.

- **Sync / install deps:** `uv sync` — installs the plotting stack plus the `dev` group (jupyter + ipykernel,
  needed to render Quarto). Add a dep with `uv add <pkg>`.
- **Run in the env:** `uv run python ...` (e.g. `uv run python -c "import house_style"` from the
  `visualization-curriculum/` dir).
- **Build datasets:** `uv run python data/build_datasets.py` (downloads via `curl` + synthesizes RF data).
  **Run this before rendering** — the curriculum's M1 cells read `data/*.csv`, which are gitignored.
- **Render the curriculum:** `uv run quarto render visualization-curriculum/better_graphs.qmd`, or
  `uv run quarto preview visualization-curriculum/better_graphs.qmd` for live reload. Quarto uses the jupyter
  engine, so run it through `uv run` to pick up the venv kernel. Code cells `import house_style`, which
  resolves because each cell's working directory is the `.qmd`'s own folder.

When you add tests/lint/CI, record the commands here.
