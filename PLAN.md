 # Better Graphs — Build Plan

A principle-first path from "competent, but my defaults look like matplotlib" to "charts that read as
deliberate." The real output isn't the charts — it's a **reusable instruction set for coding agents**
(`VISUALIZATION_GUIDE.md`, `house_style.py`, `CLAUDE.md`) so future agents produce consistent, defensible
figures without re-explaining anything. Work through this in Claude Code module by module; each module
ends by distilling what you learned into those three durable artifacts.

## Sources & inspiration

- [matplotlib-journey.com](https://www.matplotlib-journey.com) — the paid course this plan is modeled against
- [data-to-viz.com](https://www.data-to-viz.com) — decision tree from data shape → the right chart
- [python-graph-gallery.com](https://www.python-graph-gallery.com) — hundreds of worked examples with code
- [matplotlib.org](https://matplotlib.org) — official docs, plus the [cheatsheets & handouts](https://matplotlib.org/cheatsheets/) that seed the "gems" section below
- DataCamp *Python for Data Science* cheat sheets (Matplotlib / Seaborn) — the uploaded reference
- [GeeksforGeeks: Mastering Tufte's principles](https://www.geeksforgeeks.org/data-visualization/mastering-tuftes-data-visualization-principles/) — the "when in doubt" reference: data-ink ratio, chartjunk, graphical/contextual integrity, and the distortions to avoid (non-zero baselines, inconsistent scales, over-slicing). Backs the integrity rules in **M1** and the data-ink discipline in **M5**.
- [Palette Finder](https://python-graph-gallery.com/color-palette-finder/) - An agent needs to be able to either point to this or study it to find good color palettes to work with or suggest.

## What you want → where it's handled

| Goal | Module |
|---|---|
| Make something professional-looking | whole path; capstone in **M7** |
| Questions to ask to pick the right chart | **M1** (decision framework) |
| A consistent theme / house style | **M6** (`house_style.py`) |
| Executive-summary vs. detailed vs. multi-dataset figures | **M7** (composition) |

---

## The core mental model (fixes ~80% of "ugly default" pain)

Most matplotlib pain is fighting the **pyplot state machine** — `plt.this`, `plt.that`, where "the current
axes" is invisible global state. The fix is to **hold object handles**:

```python
fig, ax = plt.subplots()   # fig = canvas, ax = one plotting region
ax.plot(x, y)              # operate on the object, not on hidden state
```

Everything is a hierarchy: **Figure → Axes → Artists** (every line, tick, label, spine, patch is an
`Artist` you can grab and `.set_*()`). On top sit four **coordinate systems** — data / axes-fraction /
figure-fraction / display — and **transforms**, which let you place anything anywhere (e.g. "10% in from the
left of the axes, regardless of data range"). Internalize this and the rest is vocabulary.

> **Agent rule:** always use the OO API. `fig, ax = plt.subplots()`; no `plt.*` plotting calls afterward
> (only `fig.savefig`).

---

## Curriculum (8 modules)

Each module: a principle, a thing you build, a rule you extract.

**M0 — Environment + mental model.** OO API; Figure/Axes/Artist hierarchy; coordinate systems & transforms.
*Build* `notebooks/00_mental_model.ipynb`: rebuild one ugly default via the OO API, labeling every Artist;
place one annotation in axes-fraction coords to feel transforms. *Extract:* the OO-API rule.

**M1 — Chart choice (the decision framework).** Match *data shape* → *encoding*: classify by **(# of
variables) × (types: numeric / categorical / temporal / geo) × (the question: comparison, ranking,
distribution, relationship, composition, evolution, flow, spatial)**. The skill is asking before coding.
Anchor on the cheatsheet's **ten rules**: know your audience; lead with the message; adapt the figure to the
medium; caption everything; distrust the defaults; use color with intent; don't mislead; cut chartjunk;
message over beauty; pick the right tool. *Build* `VISUALIZATION_GUIDE.md`: the question checklist + a chart
catalog (when to use, when not, the anti-pattern — e.g. no pie beyond ~5 slices; no dual-y-axis unless units
truly differ and both are labeled; prefer slope/dumbbell over grouped bars for two time points). *Extract:*
the question checklist (your "what to ask" deliverable).

**M2 — Layout & composition.** Figure size & DPI as the master coordinate; `subplots`, `GridSpec`,
`subplot_mosaic`; `constrained_layout`; aspect ratio; inset axes; twin/secondary axes; small multiples.
Whitespace and alignment are decisions, not leftovers. *Build* a `subplot_mosaic` multi-panel, a 3×3 small-
multiples grid, one inset zoom. *Extract:* sizing conventions (slide / print / web), mosaic-vs-gridspec
guidance, "always `constrained_layout=True`".

**M3 — Typography & text hierarchy.** Type is ~half of "professional." Title/subtitle/caption hierarchy;
font family/size/weight via rcParams; mathtext for units (`$\mathrm{dBm}$`); annotation as a first-class tool;
`highlight_text` to color the words in a title that name your series; direct labeling over legends where it
fits. *Build* a chart whose **title states the takeaway** (not the axis names), with colored series words and
1–2 annotated callouts on the data. *Extract:* text-hierarchy spec; "title = the message"; annotation patterns.

**M4 — Color, done right.** Perceptual uniformity (viridis family; why jet/rainbow mislead); sequential vs.
diverging vs. qualitative vs. cyclic; colorblind-safe palettes; **semantic color** (grey for context, one
accent for the story); normalization (`Normalize`, `LogNorm`, `TwoSlopeNorm`, `BoundaryNorm`); `pypalettes`
for curated sets. *Build* the same chart in three palette *types*; a grey-context + one-accent chart; a
diverging heatmap with a centered `TwoSlopeNorm`. *Extract:* palette-by-data-type rules; the "grey everything,
accent the point" default for exec charts.

**M5 — Polish (remove the "default matplotlib" tell).** Tufte's data-ink ratio. Spines off/customized;
**tick locators & formatters** (the biggest under-used lever — see gems); grid discipline; legend
customization or removal; consistent margins. *Build* take a default bar and line, apply an ordered polish
pass, capture it as a reusable `polish(ax)`. *Extract:* the polish checklist as ordered steps.

**M6 — House style (one theme, reused).** rcParams + a `.mplstyle` sheet + a thin `house_style.py` exposing
`apply_theme()` and a few builders — the lever agents call in one line. Context managers for one-offs.
*Build* a real `your_style.mplstyle` + `house_style.py` with `executive` and `detailed` modes. *Extract:*
"always `apply_theme()` first; `mode='executive'` for slides, `'detailed'` for appendices."

**M7 — Composition capstone (executive vs. detailed, multi-dataset).** One dataset → **two figures**: a
stripped **executive** one-liner (single message, one accented series, minimal axes) and a dense **detailed**
figure (multi-panel, multiple datasets layered, annotations, secondary axis). Then **export right**: vector
(SVG/PDF) for print/slides + PNG at 2× DPI for web, fonts embedded, `bbox_inches='tight'`. *Build* both
figures from one dataset, export all formats. *Extract:* the executive↔detailed decision + multi-dataset
layering patterns.

---

## Cheatsheet gems — the things even veterans forget

Curated from the uploaded sheets. Each is a small lever with outsized payoff; wire the starred ones into
`house_style.py` so you never have to remember them again.

**Ticks that look intentional ★** — the single biggest "looks pro" upgrade most people skip:
```python
from matplotlib.ticker import MultipleLocator, MaxNLocator, PercentFormatter, FuncFormatter
ax.xaxis.set_major_locator(MultipleLocator(5))                 # ticks every 5
ax.yaxis.set_major_locator(MaxNLocator(nbins=4))               # at most ~4 nice ticks
ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0))       # 0.25 → 25%
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))  # thousands separators
```

**Margins & aspect ★** — stop fiddling with `set_xlim`/`set_ylim`:
```python
ax.margins(x=0.0, y=0.1)     # add padding as a fraction of the data range
ax.set_aspect("equal")        # 1:1 data units — essential for maps & range geometry / antenna patterns
```

**Offset ("range frame") spines ★** — a clean Tufte touch:
```python
ax.spines["left"].set_position(("outward", 8))
ax.spines["bottom"].set_position(("outward", 8))
```

**Colorbar that actually fits its axes ★** — the magic numbers worth memorizing once:
```python
fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
```

**Colors *from* a colormap** — for discrete series or ordered categories:
```python
cmap = plt.get_cmap("Oranges")
colors = cmap(np.linspace(0.3, 0.9, n))        # n colors along the ramp
plt.get_cmap("viridis", 10)                     # 10 discrete bins
plt.get_cmap("viridis_r")                       # reversed: append _r
```

**Legend outside the plot** — the 1–10 `loc` grid + an anchor:
```python
ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), frameon=False)
```

**Text that survives a busy background** — outline it; align it deliberately:
```python
import matplotlib.patheffects as pe
ax.text(x, y, "Label", ha="center", va="bottom",
        path_effects=[pe.Stroke(linewidth=3, foreground="white"), pe.Normal()])
```

**Annotations with intent** — pick a connection + arrow style:
```python
ax.annotate("peak", xy=(x0, y0), xytext=(x0+1, y0+2),
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0.2"))
# connection styles: arc3 / angle3 / angle / arc ;  arrow styles: -> , -[ , |-| , fancy , simple , wedge
```

**Reference lines & bands** — for thresholds, tolerances, regions of interest:
```python
ax.axhline(y0, ls="--", lw=1); ax.axvspan(t0, t1, alpha=0.15)
ax.fill_between(x, y - err, y + err, alpha=0.2)   # error/uncertainty band, not error bars
```

**Vector / performance hygiene ★** — keep dense figures small and fast:
```python
ax.scatter(x, y, rasterized=True); fig.savefig("fig.pdf", dpi=600)  # raster the points, keep text vector
ax.plot(x, y, "o", ls="")     # faster than scatter() when all points share one color
im.set_data(new_array)        # in animation/loops, beats re-calling imshow()
```

**Plot types you forget exist** — `step`, `hexbin` (dense scatter), `contour/contourf/pcolormesh`, polar
projection (`subplot(..., projection="polar")`), `eventplot`, `barbs`/`quiver`/`streamplot` (fields).

**Margins gone, for real** — `fig.tight_layout()` (or `constrained_layout=True`); if a vector export still
has whitespace, `pdfcrop` (ships with TeX Live).

---

## Repo layout

```
matplotlib-craft/
├── PLAN.md                   # this file
├── pyproject.toml            # or requirements.txt
├── data/                     # sample datasets  (see "open question" below)
├── visualization-curriculum/ # 00_mental_model … 07_capstone
│   ├── utils.py              # apply_theme() + builders  ← agents call this
│   ├── better_graphs.qmd     # the visualization curriculum we'll build commit by commit to cover different scenarios as inspiration for future agents that aren't as creative as you, my current and smartest agent
│   ├── plot_conf.py          # plot or project specific parameters on top of mplstyles dictating size, render qualities, etc
│   ├── your_style.mplstyle   # base rcParams
│   └── charts.py             # reusable builders: bar, line, slope, dumbbell, dist, heatmap
├── outputs/                  # exported figures (png + svg/pdf)
├── VISUALIZATION_GUIDE.md    # decision framework (humans + agents)
└── CLAUDE.md                 # agent operating rules
```

**Stack:** `matplotlib`, `numpy`, `pandas`, plus `pypalettes` and
`highlight-text` (both `pip`). `quarto` and `jupyter` for the curriculum. A
plain `uv` `.venv` is fine — plotting needs no sandbox. A humanist sans (Inter,
Source Sans, or a condensed face like Roboto Condensed) noticeably lifts the
result; install once and point `font.family` at it. Find a nice palette of
fonts to use for different occasions (math, communication, to catch someone's
attention, etc).

**Our data:** Graphing is only as good as the data we're trying to represent
with it. As such, we'll have to come up with good scenarios to showcase
different chart objects, figure axes combinations and plots at their best by
synthesizing commonly used datasets. Let's make it interesting by first finding
a few good online datasets known for their visualization-ability, and a few on
RF measurements (S parameters, antenna patterns, efficiency curves, anything
over frequency, DUT test reports showing performance over freq. for multiple
parameters, etc)

End state: hand `CLAUDE.md` + `VISUALIZATION_GUIDE.md` + `house_style.py` to
any future agent for consistent charts with zero re-explanation.

---
