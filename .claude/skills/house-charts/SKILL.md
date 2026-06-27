---
name: house-charts
description: >-
  Use whenever creating, reviewing, or revising a matplotlib chart, figure, or data
  visualization. Applies the "Better Graphs" house style — Tufte-grade figures with a
  takeaway title, an accent-led palette over grey context, trimmed/offset spines, and
  unit-aware ticks — and forces a deliberate chart-CHOICE decision before any plot is
  drawn. Trigger on requests like "plot this", "make a chart/graph/figure", "visualize",
  "improve this plot", or any matplotlib work.
---

# House charts — make figures that read as deliberate

The goal is charts that don't look like matplotlib: no boxed-in spines, no primary blue,
no title that just repeats the y-axis label. Taste, written as rules.

## Before drawing anything — choose the chart

State the chart type and WHY in one line: **"`<chart>` because `<data shape>` + `<task>`."**
If `VISUALIZATION_GUIDE.md` from the Better Graphs repo is available, answer its chart-choice
checklist first; otherwise apply these defaults:

| You want the reader to see…        | Use                          | Not                         |
|------------------------------------|------------------------------|-----------------------------|
| a ranking across categories        | horizontal bars, sorted      | vertical bars, pie          |
| change between two states          | dumbbell / slope             | grouped bars                |
| a trend over time                  | line (direct-labelled)       | many-series spaghetti       |
| a part-to-whole (≤5 parts)         | stacked bar / bar            | pie with many slices        |
| a relationship                     | scatter                      | dual-axis tricks            |
| a matrix / seasonality             | heatmap (sequential ramp)    | 3-D, rainbow                |

## The workflow (every figure, in order)

1. **Choose** the chart (above) and say why.
2. **Theme:** `from house_style import apply_theme; apply_theme(mode=...)` as the first plotting
   line. `mode="executive"` for slides/one-message; `mode="detailed"` for appendices/multi-panel.
3. **OO API only:** `fig, ax = plt.subplots(constrained_layout=True)`. No `plt.*` plotting after
   (savefig is fine).
4. **Title states the takeaway, not the axes.** Colour-key the series words into the sentence:
   `takeaway_title(ax, msg, highlight=[{"color": c1}, ...])` — a coloured word beats a legend box.
5. **Polish (data-ink):** `house_style.polish(ax, grid="y"|"x")` — trims/offsets spines, sets a
   sane tick locator, puts a single light grid behind the value axis. Add unit-aware tick
   formatters (`thousands()`), direct end-labels instead of legends where possible.
6. **Export:** `house_style.save_all(fig, "stem")` — writes SVG + PDF (selectable/embedded fonts)
   + PNG@200dpi for web, at savefig time only.

## Hard rules

- **Palette matches data type.** Categorical → `house_style.CATEGORICAL` (accent `#6400FF` leads,
  grey carries context). Sequential → `viridis`. Diverging → `house_style.diverging_norm()`
  (symmetric, centred). **Never jet/rainbow.** Grey-for-context + one accent is the default for a
  single-message chart, not a mandate — use a real categorical palette when several series
  genuinely differ; never spaghetti (use small multiples).
- No pie beyond ~5 slices. No dual-y-axis unless units truly differ — then colour-key each axis's
  label + ticks + spine to its series.
- Always: thousands separators + unit-aware tick formatters. Colorbars sized `fraction=0.046,
  pad=0.04`. Size the figure first; compose multi-panel with `subplot_mosaic` +
  `constrained_layout`, sharing one colour encoding.

## The reusable artifacts (read these; they are the source of truth)

If working inside the Better Graphs repo, these are local; otherwise fetch the raw versions:

- **`CLAUDE.md`** — the full operating manual (workflow + hard rules).
- **`VISUALIZATION_GUIDE.md`** — the chart-choice framework: 10 rules, a pre-flight checklist, a
  *(data shape × task) → chart* lookup, and a catalog (when to use / when not / the anti-pattern).
- **`visualization-curriculum/house_style.py`** — the one-import lever: `apply_theme()`, `polish()`,
  `despine()`, `thousands()`, `add_colorbar()`, `takeaway_title()`, `diverging_norm()`,
  `outlined_text()`, `save_all()`, and the `CATEGORICAL`/`ACCENT`/`GREY` palette.

Raw URLs (replace if the repo moves):
`https://raw.githubusercontent.com/temataro/better-work-graphs/main/CLAUDE.md`,
`https://raw.githubusercontent.com/temataro/better-work-graphs/main/VISUALIZATION_GUIDE.md`,
`https://raw.githubusercontent.com/temataro/better-work-graphs/main/visualization-curriculum/house_style.py`.

When `house_style.py` is not importable, replicate its decisions by hand: League-Spartan-ish sans,
text `#222`, accent `#6400FF`, grey `#9e9e9e`, top/right spines off and kept spines offset 8pt, one
light `#ddd` y-grid behind the data, a takeaway title, and unit-aware ticks.
