# VISUALIZATION_GUIDE.md — choosing the chart, and building it as a publication

**A figure is a small publication, not a printout of arrays.** It has a headline, a standfirst,
a body, and a source line; it is edited for a specific reader with a specific attention budget;
and everything on it is either evidence or is cut. The library's job is to plot data. Your job —
or your agent's — is to *publish a finding*.

This is not aesthetic preference; it is measured. In controlled experiments (Ajani, Xiong,
Knaflic & Franconeri), *decluttered* charts scored no better than cluttered ones on recall —
but ***focused*** charts (decluttered **plus** one accented series **plus** a plain-language
annotation stating the conclusion) won decisively on recall, clarity, and trust. Tufte's
data-ink razor is the precondition, not the payoff. **Cleaning the chart is half the work;
the other half is telling the reader what they're looking at.**

So every figure answers three questions, in order:

1. **What am I saying?** — one sentence, written *before* any code. Chart choice follows from
   it via the checklist and lookup table below.
2. **Who is reading?** — the **register**: `glance`, `read`, or `study`. Sets the type scale,
   density, and annotation budget.
3. **How hard should I try?** — the **altitude**: themed default → composed chart → bespoke
   drawing. Effort is a budget; spend it where the audience and lifetime justify it.

This file decides **what** to draw and **who it's for, how hard to try, and what it should look
like**. `CLAUDE.md` governs the mechanics (OO API, `house_style.theme`, ticks, export) and holds
the non-negotiable *hard rules* — this guide cross-references them rather than restating them, so
they can't drift. The curriculum (`visualization-curriculum/better_graphs.qmd`) shows these picks
being made on real data.

The skill is asking **before** coding. Most bad charts are the *wrong chart drawn well*, not the
right chart drawn badly — so the chart-choice decision is where quality is won or lost.

---

## The ten rules (how to think)

1. **Know your audience.** An expert reading an appendix and a stranger glancing at a poster need different
   density. Decide who, and how long they'll look — that's the **register** (below).
2. **Lead with the message.** Know the one sentence the figure must land *before* you choose a chart. The
   title states that takeaway (not the axis names).
3. **Adapt to the medium.** Slide/poster → `house_style.theme("glance")`, one message, big marks.
   Report/README → `house_style.theme("read")`. Appendix/datasheet → `house_style.theme("study")`, more data,
   multi-panel.
4. **Caption everything.** Title = the message; the dek carries units, source, n, date. A figure should
   survive being copied out of its context (`house_style.page(kicker=, title=, dek=, source=)`).
5. **Distrust the defaults.** Summary stats hide shape — plot the data before trusting a mean (see the
   Datasaurus, M1). And distrust matplotlib's raw defaults (see M0).
6. **Use colour with intent.** Colour must *encode*, never decorate. Grey-for-context + **one accent**
   (`#6400FF`) is the *default* for a single-message chart — not a mandate; reach for the validated
   categorical or sequential palette when several series genuinely need telling apart (never rainbow). Colour
   is computed, not eyeballed — see **Colour**, below. (See `CLAUDE.md`.)
7. **Don't mislead.** Bars start at zero. No dual-y trickery. Consistent scales. Area/length must be
   proportional to value.
8. **Cut chartjunk.** Every drop of ink should carry data or aid reading. Remove gridlines, borders, and
   labels that don't.
9. **Message over beauty.** A plain chart that lands the point beats a gorgeous one that doesn't.
10. **Pick the right tool.** The rest of this file.

---

## Pre-flight checklist (answer in order, before any plotting code)

1. **Message.** Write the one-sentence takeaway first. The title is a shortening of it.
2. **Audience & medium — pick the register.** Slide/poster → `glance`; report/README → `read`;
   appendix/datasheet → `study`. Sets the density budget.
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

## The register — a contract with the reader

Pick the register by how the figure will be *consumed*, not by how proud you are of it.
`house_style.theme(register)` is the first plotting line; it makes the whole contract concrete.

| | **glance** | **read** | **study** |
|---|---|---|---|
| The reader | an executive, an audience | a colleague, a blog reader | an expert who needs the detail |
| Dwell time / distance | ~3 s, across a room | ~30 s, arm's length | minutes, leaning in |
| Lives in | slides, posters, summaries | reports, READMEs, posts | appendices, datasheets, notebooks |
| Messages | exactly one | one + supporting context | as many as the data honestly holds |
| Series shown | 1 accented (+ grey context) | ≤ 4, or small multiples | small multiples, mosaics welcome |
| Title (League Spartan) | 19 pt — the finding, verbatim | 15 pt takeaway + dek | 13 pt + dek carrying conditions |
| Ticks on the value axis | 3–4 | ~5 | ~6, denser grids allowed |
| Annotations | ≤ 1 (direct labels only) | ~3 interpretive callouts | budget for ~6; uncertainty shown |
| Legend | never — label directly | dissolve into dek or end-labels | allowed if a mosaic truly needs it |
| Uncertainty | omit (state in speech/deck) | band or note when material | **mandatory** where it exists |
| Never | novel chart forms; fine print | spaghetti; unexplained acronyms | bar-of-means for small n — show points |

Three corollaries worth internalizing:

- **One figure, one register.** Reusing a slide figure in an appendix (or vice versa) fails both
  readers. Re-render with a different `theme()` — that's why it's one line.
- **The register caps novelty.** A `glance` reader gets familiar forms only; an unfamiliar
  form needs a motivated reader (`read`+, with a how-to-read key — see the altitude test).
- **Type hierarchy comes from weight and ink, not size explosions.** The scale is compressed
  (the Economist's whole print ladder spans 6.5–9.5 pt); hierarchy is carried by League Spartan
  600 vs Junction 500 vs muted/faint ink. Posters are not big charts — they are re-set at
  physical size (~15 pt of title per metre of viewing distance).

---

## The altitude — how hard to try

Three altitudes of craft. The mistake isn't flying low — it's flying at the wrong altitude
for the audience, in either direction.

- **A0 · themed default.** `theme()` + a plain `ax.plot`/`ax.bar`. For *your own eyes*:
  exploration, debugging, internal one-offs. The theme keeps even these presentable, but an
  A0 figure is not a deliverable.
- **A1 · composed.** The catalog chart (guide-chosen), on a `page()` with kicker/title/dek/source,
  polished by `finish()`, accented, annotated, exported by `save()`. **The default for anything
  another human will see.** Most figures should live and die at A1.
- **A2 · bespoke.** Raw Artists: custom geometry, hand-built scales, illustration-grade
  composition. Justified rarely — and gloriously.

**The altitude test.** A figure earns A2 only if **all four** gates pass:

1. **The message survives a standard form.** You can state the finding in one sentence and an
   A1 chart *could* show it. (If no standard chart can, your analysis isn't done — fix that first.)
2. **The standard form actively buries it** — the key structure is not the dominant visual
   signal (e.g. cyclical data forced onto a linear axis), **or** the form itself carries meaning
   (a cycle drawn as a cycle, a flow drawn as a flow).
3. **The audience × lifetime pays for it.** A README hero, a poster centerpiece, a flagship
   report figure — many eyes or a long shelf life. A weekly status plot never qualifies.
4. **It stays honest** (the encoding-honesty rules below still apply at any altitude).

**Honesty gates for bespoke work:**

- **Spend the good encodings on the message.** Cleveland & McGill's accuracy ordering —
  position on a common scale > position on non-aligned scales > length > direction/angle >
  area > shading/saturation. The quantity the reader must compare precisely gets position or
  length; area and hue are for context and gestalt.
- **The debt rule.** An inexact encoding (spiral, coxcomb, pictogram, area) must *print the
  exact values on the figure*. Du Bois annotated dollar amounts on every spiral bar; that's why
  his bespoke forms are data graphics and not decoration. Inexact encoding without printed
  values is decoration.
- **Radii grow as √value** (a coxcomb with radius ∝ value turns a 4:1 ratio into a perceived
  16:1 lie). Pictograms repeat at one size — more symbols, never bigger ones.
- **Topical, singular embellishment only.** One motif *about the subject* helps memorability
  (Bateman); unrelated ornament hurts recall. Never two motifs.
- **Novel forms ship with a how-to-read key**: one exemplar mark, inset, with 2–3 labelled
  arrows naming each encoding. And never at `glance`.

---

## The page — anatomy of a figure

Every shared figure is a stack of typographic blocks with **one shared left edge**:

```
▮ tab                 a 0.30 in violet rectangle — the brand device; never moves
KICKER                Junction 700, tracked caps, muted — topic · period
Title                 League Spartan 600, ink — states the finding, never the axes
Dek                   Junction 500, muted — what/units/how measured; series names
                      colour-keyed into the sentence (the legend, dissolved)
[ the plot ]          y labels sit ON their gridlines; the only axis line is the
                      bottom rule, and it ends where the data ends
Source: …      note   Junction 500, faint — source left, footnotes/mark right
```

`house_style.page(kicker=…, title=…, dek=…, source=…, note=…)` builds all of it with inch-true
margins — which is why `house_style.save()` **never uses `bbox_inches="tight"`**: the margins are
deliberate, and tight-cropping shaves them asymmetrically.

Rules the anatomy enforces:

- **Units live in the dek, not on a rotated y-label.** The rotated ylabel is the single
  loudest "default matplotlib" tell. In `study`, where an axis label genuinely helps, use
  `ylabel_above()` — horizontal, above the axis (Doumont's convention). On the axis itself the
  top tick may spell the unit once (`units(ax, "y", "db")` → "20 dB" up top, bare numbers below).
- **A title is a sentence with a verb**, sized by register, never centred. If the title
  repeats an axis label, it isn't a title yet.
- **The source line is not optional.** A figure that leaves the room must carry its
  provenance: `Source: …` bottom-left, footnote symbols (* † ‡ §) right-aligned on the same
  baseline. Notes define method and scope; they never repeat the takeaway.
- **A figure without an interpretive annotation is unfinished** (`read`/`study`). `finish()`
  is a precondition; `mark()` — the callout that *interprets* ("707 enters service", not
  "y = 4,060") — is the payoff.

---

## Colour — computed, not eyeballed

Warm paper (`#FAF7F2`), warm ink (`#201D1A`), and a strict role system. Colour *encodes*;
ink demotes. Text is never set in a series colour except direct labels of that series.

**The ink ramp** (roles, not decoration): `INK` titles/hero numbers → `MUTED` dek/axis/tick
text → `FAINT` source lines → `HAIRLINE` gridlines → `CONTEXT`/`SMOKE` de-emphasised series.
Two levels of grey text maximum on any one figure — more turns to mud.

**The series palette** — violet leads, five follow, in fixed order:

| | violet | emerald | ochre | wine | navy | rust |
|---|---|---|---|---|---|---|
| | `#6400FF` | `#0FA077` | `#C67D10` | `#5C2340` | `#142A6E` | `#93330E` |

This order is **assigned, never cycled**: series 1 is always violet, a 7th series is a design
failure (fold into "Other", facet, or rethink). `GOOD`/`BAD` status colours are reserved
(emerald/rust) and never double as "series 7".

The palette is a *claim* — "distinguishable, by everyone, on this background" — and the claim
is checkable: `check_palette.py` simulates protanopia/deuteranopia/tritanopia (Machado 2009),
measures worst-pair ΔE, lightness band, chroma floor, and WCAG contrast against the paper/white
surface. This palette passes with min ΔE **26.6** (target ≥ 12) on paper and on white — computed,
not eyeballed. Re-run the check whenever a colour changes; simulate the rendered figure, not the
swatches, when lines are thin.

**Accent-and-grey vs. full palette.** Grey-context + violet is the default *for a
single-message chart* — the accent must be both darker and more saturated than the context.
When 3–6 co-equal series genuinely cross and must be traced, use the palette or facet;
forcing accent-and-grey there hides the story.

**Ramps.** Sequential = `house_style.SEQUENTIAL` (paper-lavender → violet → near-black,
Lab-arc-length equalised so equal steps mean equal perceived change) or viridis for scientific
neutrality. Diverging = `house_style.DIVERGING` (rust ↔ warm neutral ↔ violet), always centred
on the meaningful zero via `diverging_norm()`. Never rainbow; never a hue at a diverging
midpoint.

---

## Encoding honesty (any register, any altitude)

- **Length starts at zero** — bars, areas, lollipop stems. Never break a bar scale. Position
  (lines, dots) may crop, but a cropped line axis that could mislead gets a declared break or
  a zero note.
- **Bolden the zero line** when data spans it.
- **Dual axes**: only for genuinely different units (the PA gain/PAE case). Align the zeros,
  never break either scale, colour-key label + ticks + spine of *both* axes to their series —
  or split into stacked panels sharing x (usually better).
- **Bar width > gap** (≈ 0.75 on unit spacing). **Scatter**: dots ~50 % alpha for trend
  reading, opaque for highlighted points; rasterize beyond ~10⁴ points.
- **Small multiples share everything** — identical scales, one colour encoding, one header
  block, per-panel micro-titles (`panel_title`).
- **Show raw data with the summary** for small n — strip the points beside the box; a
  bar-of-means is a `study`-register bug (Weissgerber).

---

## Lineage

This framework stands on: Tufte (data-ink, integrity) · Cleveland & McGill (encoding accuracy) ·
Bertin (visual variables) · The Economist/FT/NYT graphics desks (the anatomy, the discipline,
"the annotation layer is the most important thing we do" — Amanda Cox) · Doumont (label
geometry, meaningful ticks) · Lisa Charlotte Muth (colour craft) · Weissgerber (show the data)
· W. E. B. Du Bois (bespoke form, honestly repaid) · Rougier (matplotlib as a drawing
instrument) · Ajani/Xiong/Knaflic/Franconeri (why "focused" beats "decluttered").

---

## See also

- **`CLAUDE.md`** — how to draw (OO API, theme, ticks, export) and the hard rules.
- **`visualization-curriculum/better_graphs.qmd` (M1)** — these picks demonstrated right-vs-wrong on real data.
- **`PLAN.md`** — the full curriculum roadmap and sources.
