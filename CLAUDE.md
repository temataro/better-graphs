# CLAUDE.md

This file provides guidance to any capable AI agents when working with code in this repository.

## What this project actually is

This is not a charts repo that happens to use agents — it is an **agent-instruction repo that happens to
produce charts**. The real deliverable is a reusable, self-contained instruction set so any future agent can
make professional, Tufte-grade matplotlib figures with zero re-explanation. The three durable artifacts are:

- **`CLAUDE.md`** (this file) — the agent operating rules: workflow + hard rules.
- **`VISUALIZATION_GUIDE.md`** — the full design framework: chart-choice (the 10 rules, a pre-flight checklist,
  a *(data shape × task) → chart* lookup, a chart catalog), the reader **register** (`glance`/`read`/`study`),
  the **altitude** ladder for how hard to try (A0 themed default → A1 composed → A2 bespoke, with the four-gate
  test), the editorial page anatomy, and the computed (CVD-validated) colour system.
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

The curriculum is **complete: M0–M7 are written**, each ending with a before/after on real data and a rule
distilled back into the three durable artifacts. The environment is set up and working. What exists:

- `pyproject.toml` + uv-managed `.venv/` + `uv.lock` — the plotting stack is installed; git is initialized
  on `main`.
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

A figure is a small publication, not a printout of arrays: a headline, a standfirst, a body, and a source
line, edited for a specific reader with a specific attention budget. Decluttering is the precondition, not the
payoff — a shipped figure also needs an accent series and a plain-language annotation stating the conclusion
(*focused* beats merely *decluttered*: Ajani, Xiong, Knaflic & Franconeri).

### Workflow (every time, in order)
1. Write the one-sentence finding, then answer the chart-choice checklist in `VISUALIZATION_GUIDE.md` and
   state it — *"`<chart>` because `<shape>` + `<task>`."*
2. Choose the **register** from the reader and say it — `glance` (a slide/poster, ~3 s), `read` (a report/
   README, ~30 s), or `study` (an appendix/datasheet, minutes). `house_style.theme(register)` is the first
   plotting line.
3. Choose the **altitude** — A0 themed default (your own eyes only) → A1 composed catalog chart (**the
   default for anything shared**) → A2 bespoke Artist drawing. A2 requires passing the four-gate test in
   `VISUALIZATION_GUIDE.md` aloud.
4. `fig, ax = house_style.page(kicker=…, title=…, dek=…, source=…)` — the title states the finding (a
   sentence with a verb, never the axis names); units go in the dek; series names colour-key into the dek
   (`dek_highlights=[{"color": c1}, ...]`) instead of a legend box.
5. Draw with the OO API only after `page()` (only `savefig` after that). Accent the message series in
   `house_style.ACCENT`/`SERIES`; demote context to `house_style.CONTEXT`/`SMOKE`.
6. `house_style.finish(ax)` (+ `units(ax, "y", kind)` for the unit-on-top-tick), then spend the annotation
   budget: `label_end()` for line-chart series (the legend, dissolved), `mark()` for the interpretive callout,
   `spec_band()` for limits, `stat()` for datasheet hero-number tiles.
7. Check yourself: where do the eyes land first? It must be the accented element. Would the figure survive
   being copied out of its document (title + dek + source intact)?
8. `house_style.save(fig, stem)` — SVG + PDF + 2× PNG. Never `bbox_inches="tight"` on a `page()` figure — the
   margins are deliberate and tight-cropping shaves them asymmetrically.

### Hard rules
- No rotated y-axis labels — units in the dek or `house_style.ylabel_above()`. No centred titles; one left
  edge for the whole header stack (kicker/title/dek).
- No legend boxes on line charts — `label_end()` direct labels or dek colour-keying.
- No naked "decluttered" figures — every shared figure carries its interpretive layer (`mark()`, at least
  one).
- Bars start at zero, never broken. Bar-of-means never hides raw points at small n — show the points beside
  the summary.
- No pie beyond ~5 slices. No dual-y-axis unless units truly differ — and then align the zeros and colour-key
  label + ticks + spine of *both* axes to their series; otherwise split into stacked shared-x panels (usually
  better even then).
- No rainbow/jet. Palette is computed, not eyeballed: categorical → `house_style.SERIES` (fixed order, violet
  leads, never cycled — a 7th series is a design failure); sequential → `house_style.SEQUENTIAL` or viridis;
  diverging → `house_style.diverging_norm()` (symmetric, centred) with `house_style.DIVERGING`. Any palette
  change runs `visualization-curriculum/check_palette.py` (CVD ΔE ≥ 12, contrast ≥ 3:1).
- Grey-for-context + one accent (`#6400FF`) is the *default* for a single-message chart — not a mandate.
  Use the validated categorical/sequential palette when several series genuinely need distinguishing (never
  rainbow); don't force everything to monochrome. Thousands separators + unit-aware tick formatters always.
- League Spartan is display-only (≥10 pt, never tick labels or numeral columns — proportional figures jitter);
  Junction carries the working text. Special glyphs (° → Ω) need `family=house_style.BODY_STACK` explicit.
- Colorbars sized to the axes: `fraction=0.046, pad=0.04`.
- Size the figure first (it's the master coordinate); compose multi-panel with `house_style.page(mosaic=…)`,
  sharing one colour encoding across panels. Many series → small multiples (one panel per group, shared axes),
  never spaghetti. Zoom with an inset (`inset_axes` + `indicate_inset_zoom`).
- One figure, one register — re-render for a different medium, never reuse.

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
