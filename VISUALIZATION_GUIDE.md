# VISUALIZATION_GUIDE.md — choosing the chart

The decision framework for this project. The loop is always the same:

> **Answer the checklist → read your *(data shape × task)* off the table → pick from the catalog →
> build it under the house rules in `CLAUDE.md`.**

This file decides **what** to draw. `CLAUDE.md` governs **how** to draw it (OO API, `apply_theme`, ticks,
colour, export) and holds the non-negotiable *hard rules* — this guide cross-references them rather than
restating them, so they can't drift. The curriculum (`visualization-curriculum/better_graphs.qmd`, **M1**)
shows these picks being made on real data.

The skill is asking **before** coding. Most bad charts are the *wrong chart drawn well*, not the right chart
drawn badly — so the chart-choice decision is where quality is won or lost.

---

## The ten rules (how to think)

1. **Know your audience.** An expert reading an appendix and a stranger glancing at a poster need different
   density. Decide who, and how long they'll look.
2. **Lead with the message.** Know the one sentence the figure must land *before* you choose a chart. The
   title states that takeaway (not the axis names).
3. **Adapt to the medium.** Slide/poster → `apply_theme("executive")`, one message, big marks. Report/appendix
   → `apply_theme("detailed")`, more data, multi-panel.
4. **Caption everything.** Title = the message; subtitle/caption = units, source, n, date. A figure should
   survive being copied out of its context.
5. **Distrust the defaults.** Summary stats hide shape — plot the data before trusting a mean (see the
   Datasaurus, M1). And distrust matplotlib's raw defaults (see M0).
6. **Use colour with intent.** Colour must *encode*, never decorate. Grey-for-context + **one accent**
   (`#6400FF`) is the *default* for a single-message chart — not a mandate; reach for a principled categorical
   or sequential palette when several series genuinely need telling apart (never rainbow). (See `CLAUDE.md`.)
7. **Don't mislead.** Bars start at zero. No dual-y trickery. Consistent scales. Area/length must be
   proportional to value.
8. **Cut chartjunk.** Every drop of ink should carry data or aid reading. Remove gridlines, borders, and
   labels that don't.
9. **Message over beauty.** A plain chart that lands the point beats a gorgeous one that doesn't.
10. **Pick the right tool.** The rest of this file.

---

## Pre-flight checklist (answer in order, before any plotting code)

1. **Message.** Write the one-sentence takeaway first. The title is a shortening of it.
2. **Audience & medium.** Slide/poster → `executive`; report/appendix → `detailed`. Sets the density budget.
3. **Data shape.**
   - **How many** variables shown at once? (1 / 2 / 3+)
   - **Type** of each: **quantitative** (continuous or discrete count) · **categorical** (nominal or ordinal)
     · **temporal** · **geographic**.
   - **Cardinality:** how many rows? how many categories/levels?
4. **Task — the verb.** What is the reader meant to *do*? Pick the one primary task:
   *comparison · ranking · distribution · relationship · part-to-whole · evolution (time) · deviation ·
   flow · spatial.*
5. **→ Chart.** Read *(shape × task)* off the table below and state it in one line —
   **"`<chart>` because `<shape>` + `<task>`."** That sentence is required by `CLAUDE.md` workflow step 1.

---

## Data shape × task → chart (the lookup)

Concrete enough to drive a pick: find your task, match the shape, take the default.

| Task | Typical data shape | Default pick | Also consider | Avoid |
|---|---|---|---|---|
| Compare across categories | 1 categorical + 1 quantitative | **horizontal bar, sorted** | dot / lollipop (many categories) | pie; 3-D bars; unsorted bars |
| Rank | 1 cat + 1 quant | **sorted bar or dot** | bump chart (rank over time) | pie; alphabetical order |
| Compare **two** time points (before→after) | 1 cat + 2 quant (t₀, t₁) | **dumbbell** or **slope** | arrow plot | grouped bars (hide the *change*) |
| Distribution of one variable | 1 quantitative | **histogram** or **ECDF** | KDE | one bar of the mean |
| Compare distributions across groups | 1 cat + 1 quant | **box / violin + jittered points** | faceted histograms; strip (small n) | bar-of-means ± error bar alone |
| Relationship between two numbers | 2 quantitative | **scatter** | hexbin / 2-D hist (large n); + trend line | dual-y line pair |
| …with a third variable | 2 quant + 1 cat/quant | **scatter, encode 3rd by colour or size** | small multiples by the category | piling on >2 extra encodings |
| Evolution over time | temporal + quantitative | **line** | area (single series, to zero); small multiples (many series) | "spaghetti" (many overlapping lines) |
| Part-to-whole | 1 cat + 1 quant (parts of a total) | **sorted bar of shares** or **stacked bar** | 100 % stacked (compare compositions); waterfall (build-up) | pie beyond ~5 slices; donut |
| Deviation from a baseline | 1 cat + 1 *signed* quant | **diverging bar**, centred at 0 | lollipop from the baseline | a sequential colormap for ± values |
| 2-D field / matrix | 2 cat (or a numeric grid) + 1 quant | **heatmap** (`pcolormesh`) | contour / `contourf` | rainbow/jet colormap |
| Flow / transfer | nodes + weighted edges | **sankey** (few nodes) | chord (sparingly) | sankey with dozens of tiny flows |
| Spatial | geographic + quantitative | **choropleth** (rates) / **symbol map** (counts) | hexbin map | choropleth of raw counts; bad projection |

---

## Chart catalog (when / when not / the anti-pattern)

Per chart: the nuance the table can't hold. House notes point at `CLAUDE.md`.

**Bar (sorted).** The default for comparing categories. *Use:* lengths are read precisely; horizontal handles
long labels. *Avoid:* unsorted (sort by value unless the category has a natural order); a non-zero baseline
(length encodes value → **must start at 0**). *House:* direct-label or keep ≤ ~12 bars.

**Dot / lollipop.** Bar's lighter cousin for many categories or when zero isn't meaningful. *Use:* rankings,
dense category lists. *Avoid:* when the audience expects the familiar bar and precision matters.

**Dumbbell / slope.** Two values per category (before→after, two years). *Use:* the *change* is the message —
the connecting line *is* the data. *Avoid:* >2 time points (use a line). *Anti-pattern:* grouped bars for two
time points — they bury the change the reader came for. (Demonstrated in M1.)

**Line.** Evolution of a quantity over a continuum (usually time). *Use:* ordered x, trend matters. *Avoid:*
categorical x (use bars); >~5 series overlapping → **small multiples** or grey-all-but-one. *Anti-pattern:*
"spaghetti."

**Area.** A single series' magnitude over time, filled to zero. *Use:* one series, cumulative feel. *Avoid:*
stacking many (middle bands become unreadable) — facet instead.

**Histogram / ECDF.** The shape of one distribution. *Use:* histogram for intuition; ECDF for reading
quantiles and comparing distributions without bin choices. *Avoid:* hiding a distribution behind a single
mean. *House:* state bin width/count.

**Box / violin (+ points).** Compare distributions across groups. *Use:* several groups, want spread + median.
*Avoid:* small n behind a violin (show the points — strip/swarm); a bar-of-means that hides spread.

**Scatter.** Relationship between two quantities. *Use:* correlation, clusters, outliers; encode a third
variable by colour/size; rasterize when dense (`CLAUDE.md`). *Avoid:* overplotting (→ hexbin/2-D hist /
alpha). *Anti-pattern:* forcing two unrelated series onto a dual-y line chart instead of a scatter or two
panels.

**Heatmap (`pcolormesh`).** A value over a 2-D grid (category×category, or x×y field). *Use:* matrices,
seasonality (month×year), correlation matrices. *Avoid:* rainbow/jet — sequential **viridis**, or a centred
diverging norm for signed data (`CLAUDE.md`). *House:* colorbar `fraction=0.046, pad=0.04`.

**Diverging bar.** Deviations around a meaningful zero (vs target, vs average). *Use:* signed values, centred
axis. *Avoid:* a sequential palette (use a centred `TwoSlopeNorm`-style two-hue split).

**Stacked bar.** Composition within each of a few categories. *Use:* ≤ ~5 parts, totals also matter; 100 %
stacked to compare *compositions*. *Avoid:* many thin segments (unreadable) — facet or bar-of-shares.

**Pie / donut.** *Rarely.* Only ≤ ~5 slices that obviously sum to a whole, when precise comparison doesn't
matter. *Otherwise use a sorted bar.* (Hard rule, `CLAUDE.md`; demonstrated in M1.)

**Sankey / chord.** Flows between nodes. *Use:* a few nodes, conserved quantity. *Avoid:* many tiny flows —
becomes a hairball.

**Choropleth / symbol map.** Spatial quantities. *Use:* choropleth for **rates**, symbol/bubble for counts.
*Avoid:* choropleth of raw counts (big areas dominate); careless projections.

### Domain charts — RF / measurements over frequency

The project's RF datasets (`data/rf_*`) call for a few specialist forms:

- **Magnitude vs frequency, in dB.** S-parameters, gain, return loss: y in dB (`20·log10|S|`), x in
  GHz with unit-aware ticks. Highlight the band of interest with `axvspan`.
- **Polar radiation pattern.** Antenna gain vs angle → `projection="polar"`, radial axis in dB with a floor
  (e.g. −40 dB); annotate the main-lobe and first sidelobe.
- **Smith chart.** Complex reflection coefficient — a domain-specific projection; reach for `scikit-rf`
  rather than hand-rolling.
- **Twin-axis (a legitimate dual-y).** Gain compression **and** efficiency vs drive power: the two genuinely
  different units (dB, %) are the textbook case where dual-y is allowed — **label and colour both axes**
  (`CLAUDE.md`), and mark P1dB / peak-PAE directly.

---

## Hard anti-patterns (chart-choice errors)

The execution hard rules live in `CLAUDE.md`; these are the *choice* errors that precede them:

- **Pie beyond ~5 slices**, or any pie used for ranking/precise comparison → sorted bar.
- **Grouped bars for two time points** → dumbbell or slope.
- **Dual-y axes** unless the units truly differ — and then label + colour both (the RF gain/efficiency case
  is the rare yes).
- **Bars not starting at zero** — length must be proportional to value (lines/scatter may crop).
- **Rainbow/jet** colormaps → sequential viridis; diverging → centred.
- **Spaghetti** line charts → small multiples or highlight-one / grey-the-rest.
- **Raw counts in a choropleth** → normalize to rates or use a symbol map.
- **Over-slicing** (too many categories/segments) → group the tail into "Other", or switch chart.
- **3-D** for inherently 2-D data.

---

## See also

- **`CLAUDE.md`** — how to draw (OO API, theme, ticks, export) and the hard rules.
- **`visualization-curriculum/better_graphs.qmd` (M1)** — these picks demonstrated right-vs-wrong on real data.
- **`PLAN.md`** — the full curriculum roadmap and sources.
