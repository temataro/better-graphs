---
name: fable-charts
description: >-
  Use whenever creating, reviewing, or revising a matplotlib chart, figure, or data
  visualization with the "fable" design system (Better Graphs, second draft). Treats a
  figure as a small publication: an editorial page anatomy (kicker / title / dek / source),
  three audience registers (glance / read / study), an altitude ladder that says when to go
  bespoke with raw Artists, and a computed (CVD-validated) palette on warm paper. Trigger on
  requests like "plot this", "make a chart/figure", "visualize", "improve this plot", or any
  matplotlib work where the fable system is preferred over the original house style.
---

# fable charts — a figure is a small publication

Three questions, in order, before any code:

1. **What am I saying?** One sentence with a verb. Chart choice follows via
   `VISUALIZATION_GUIDE.md` (data shape × task → chart): state *"`<chart>` because
   `<shape>` + `<task>`."*
2. **Who is reading?** Pick the **register** and say it:
   - `glance` — 3 s, a slide/poster: one message, one accent, direct labels, ≤4 ticks.
   - `read` — 30 s, a report/README: full anatomy, ≤4 series, ~3 interpretive callouts.
   - `study` — minutes, an appendix/datasheet: mosaics, uncertainty shown, exact values.
3. **How hard should I try?** The **altitude**: A0 themed default (own eyes only) →
   A1 composed catalog chart (**default for anything shared**) → A2 bespoke Artists.
   A2 requires all four gates: message survives a standard form; the standard form buries
   it or the form itself carries meaning; audience × lifetime pays for the craft; it stays
   honest (position/length for the core quantity, zero-based lengths, printed exact values
   for inexact encodings, a how-to-read key for novel forms — and never bespoke at glance).

## The workflow

```python
import fable
fable.theme("read")                        # the register, first plotting line
fig, ax = fable.page(
    kicker="Topic · period",               # tracked caps, above the title
    title="A finding with a verb",         # League Spartan; never the axis names
    dek="What/units/method. <Series> names colour-key into this sentence.",
    dek_highlights=[{"color": fable.ACCENT, "weight": 700}],   # legend, dissolved
    source="Source: …",                    # non-negotiable
)
ax.plot(x, y, color=fable.ACCENT)          # OO API only after this point
fable.finish(ax)                           # polish: grid, tick budget, bounded spine
fable.units(ax, "y", "db")                 # unit on the top tick only
fable.mark(ax, x0, y0, "what it MEANS")    # the interpretive layer — mandatory
fable.save(fig, "stem")                    # svg+pdf+png; never bbox_inches='tight'
```

Decluttering is a precondition, not the payoff: a shipped figure needs its accent series
and one plain-language annotation stating the conclusion (focused beats decluttered —
Ajani et al.). `label_end()` replaces line-chart legends; `spec_band()` draws limits;
`stat()` makes datasheet hero-number tiles; `panel_title()` titles mosaic panels.

## Hard rules

- Units in the dek or `ylabel_above()` — never a rotated y-label. One left edge for the
  whole header stack; titles never centred.
- Palette: violet `#6400FF` leads; then emerald `#0FA077`, ochre `#C67D10`, wine `#5C2340`,
  navy `#142A6E`, rust `#93330E` — **fixed order, never cycled; no 7th series**. Context
  series take `fable.CONTEXT`/`SMOKE` grey. `GOOD`/`BAD` (emerald/rust) are reserved status
  colours. Any palette change runs `check_palette.py` (CVD ΔE ≥ 12, contrast ≥ 3:1).
- Sequential ramp `fable.SEQUENTIAL` (or viridis); diverging `fable.DIVERGING` centred on
  the meaningful zero via `fable.diverging_norm()`. Never rainbow.
- Bars start at zero, never broken; show raw points beside small-n summaries.
- Dual axes only for true different-unit pairs — else **split into stacked shared-x
  panels** (usually better even then).
- League Spartan is display-only (≥10 pt, never tick labels); Junction carries working
  text. For special glyphs (° → Ω), pass `family=fable.BODY_STACK` explicitly.
- One figure, one register — re-render for a different medium, never reuse.

## The artifacts (source of truth, in-repo)

- **`STYLE_AND_SUBSTANCE.md`** — the full system: registers table, altitude test, anatomy
  spec, colour rules, workflow, hard rules.
- **`visualization-curriculum/fable.py`** — the one-import lever (everything above).
- **`visualization-curriculum/check_palette.py`** — the palette validator (CVD + contrast).
- **`visualization-curriculum/style_and_substance.qmd`** — worked examples: anatomy,
  registers, colour receipts, the altitude ladder, bespoke antenna drawing, the DUT
  datasheet capstone.
- `VISUALIZATION_GUIDE.md` — chart choice (unchanged from the original system).

When `fable.py` is not importable, replicate by hand: warm paper `#FAF7F2`, warm ink
`#201D1A`, muted text `#6B655D`, hairline grid `#E3DDD1`, violet accent, League-Spartan-ish
display + humanist body, y labels on gridlines, bottom rule ending at the data, kicker /
title / dek / source stack with one left edge.
