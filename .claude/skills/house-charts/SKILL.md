---
name: house-charts
description: >-
  Use whenever creating, reviewing, or revising a matplotlib chart, figure, or data
  visualization. Applies the "Better Graphs" house style — a figure is a small publication,
  with an editorial page anatomy (kicker/title/dek/source), three audience registers
  (glance/read/study), an altitude ladder that says when to go bespoke with raw Artists, and
  a computed (CVD-validated) palette on warm paper — and forces a deliberate chart-CHOICE
  decision before any plot is drawn. Trigger on requests like "plot this", "make a chart/
  graph/figure", "visualize", "improve this plot", or any matplotlib work.
---

# House charts — a figure is a small publication

Not a printout of arrays: a headline, a standfirst, a body, and a source line, edited for a
specific reader with a specific attention budget. Decluttering is the precondition, not the
payoff — a shipped figure also needs an accent series and a plain-language annotation stating
the conclusion (*focused* beats merely *decluttered*: Ajani, Xiong, Knaflic & Franconeri).

## Before drawing anything — answer three questions, in order

1. **What am I saying?** One sentence with a verb, written before any code. If
   `VISUALIZATION_GUIDE.md` from the Better Graphs repo is available, answer its chart-choice
   checklist; otherwise apply these defaults, and state the pick: **"`<chart>` because
   `<data shape>` + `<task>`."**

   | You want the reader to see…        | Use                          | Not                         |
   |------------------------------------|------------------------------|-----------------------------|
   | a ranking across categories        | horizontal bars, sorted      | vertical bars, pie          |
   | change between two states          | dumbbell / slope             | grouped bars                |
   | a trend over time                  | line (direct-labelled)       | many-series spaghetti       |
   | a part-to-whole (≤5 parts)         | stacked bar / bar            | pie with many slices        |
   | a relationship                     | scatter                      | dual-axis tricks             |
   | a matrix / seasonality             | heatmap (sequential ramp)    | 3-D, rainbow                |

2. **Who is reading?** Pick the **register** and say it — `house_style.theme(register)` is
   the first plotting line:
   - `glance` — 3 s, a slide/poster: one message, one accent, direct labels, ≤4 ticks.
   - `read` — 30 s, a report/README: full anatomy, ≤4 series, ~3 interpretive callouts.
   - `study` — minutes, an appendix/datasheet: mosaics, uncertainty shown, exact values.

3. **How hard should I try?** The **altitude**: A0 themed default (own eyes only) →
   A1 composed catalog chart (**default for anything shared**) → A2 bespoke Artists. A2
   requires all four gates: the message survives a standard form; the standard form buries
   it or the form itself carries meaning; audience × lifetime pays for the craft; it stays
   honest (position/length for the core quantity, zero-based lengths, printed exact values
   for inexact encodings, a how-to-read key for novel forms — and never bespoke at glance).

## The workflow

```python
import house_style
house_style.theme("read")                        # the register, first plotting line
fig, ax = house_style.page(
    kicker="Topic · period",                      # tracked caps, above the title
    title="A finding with a verb",                # League Spartan; never the axis names
    dek="What/units/method. <Series> names colour-key into this sentence.",
    dek_highlights=[{"color": house_style.ACCENT, "weight": 700}],   # legend, dissolved
    source="Source: …",                           # non-negotiable
)
ax.plot(x, y, color=house_style.ACCENT)           # OO API only after this point
house_style.finish(ax)                            # polish: grid, tick budget, bounded spine
house_style.units(ax, "y", "db")                  # unit on the top tick only
house_style.mark(ax, x0, y0, "what it MEANS")     # the interpretive layer — mandatory
house_style.save(fig, "stem")                     # svg+pdf+png; never bbox_inches='tight'
```

`label_end()` replaces line-chart legends; `spec_band()` draws limits; `stat()` makes
datasheet hero-number tiles; `panel_title()` titles mosaic panels.

## Hard rules

- No rotated y-axis labels — units in the dek or `house_style.ylabel_above()`. No centred
  titles; one left edge for the whole header stack (kicker/title/dek).
- No legend boxes on line charts — `label_end()` direct labels or dek colour-keying.
- No naked "decluttered" figures — every shared figure carries its interpretive layer
  (`mark()`, at least one).
- Bars start at zero, never broken. Bar-of-means never hides raw points at small n — show
  the points beside the summary.
- No pie beyond ~5 slices. No dual-y-axis unless units truly differ — and then align the
  zeros and colour-key label + ticks + spine of *both* axes to their series; otherwise split
  into stacked shared-x panels (usually better even then).
- No rainbow/jet. Palette is computed, not eyeballed: categorical → `house_style.SERIES`
  (fixed order, violet leads, never cycled — a 7th series is a design failure); sequential →
  `house_style.SEQUENTIAL` or viridis; diverging → `house_style.diverging_norm()` (symmetric,
  centred) with `house_style.DIVERGING`. Context series take `house_style.CONTEXT`/`SMOKE`
  grey; `GOOD`/`BAD` (emerald/rust) are reserved status colours, never a "series 7". Any
  palette change runs `check_palette.py` (CVD ΔE ≥ 12, contrast ≥ 3:1).
- League Spartan is display-only (≥10 pt, never tick labels); Junction carries working text.
  For special glyphs (° → Ω), pass `family=house_style.BODY_STACK` explicitly.
- One figure, one register — re-render for a different medium, never reuse.
- Export via `house_style.save()`; never `bbox_inches="tight"` on a `page()` figure — the
  margins are deliberate and tight-cropping shaves them asymmetrically.

## The reusable artifacts (read these; they are the source of truth)

If working inside the Better Graphs repo, these are local; otherwise fetch the raw versions:

- **`CLAUDE.md`** — the full operating manual (workflow + hard rules).
- **`VISUALIZATION_GUIDE.md`** — the design framework: chart-choice (10 rules, a pre-flight
  checklist, a *(data shape × task) → chart* lookup, a catalog), the reader register, the
  altitude ladder, the page anatomy, and the computed colour system.
- **`visualization-curriculum/house_style.py`** — the one-import lever: `theme()`, `page()`,
  `finish()`, `units()`, `label_end()`, `mark()`, `spec_band()`, `stat()`, `panel_title()`,
  `diverging_norm()`, `save()`, and the `SERIES`/`ACCENT` palette plus `SEQUENTIAL`/
  `DIVERGING` house colormaps.
- **`visualization-curriculum/check_palette.py`** — the palette validator (CVD + contrast).

Raw URLs (replace if the repo moves):
`https://raw.githubusercontent.com/temataro/better-work-graphs/main/CLAUDE.md`,
`https://raw.githubusercontent.com/temataro/better-work-graphs/main/VISUALIZATION_GUIDE.md`,
`https://raw.githubusercontent.com/temataro/better-work-graphs/main/visualization-curriculum/house_style.py`.

When `house_style.py` is not importable, replicate its decisions by hand: warm paper
`#FAF7F2`, warm ink `#201D1A`, muted text `#6B655D`, hairline grid `#E3DDD1`, violet accent
`#6400FF`, League-Spartan-ish display + humanist body, y labels sitting on their gridlines,
bottom rule ending at the data, a kicker/title/dek/source stack sharing one left edge.
