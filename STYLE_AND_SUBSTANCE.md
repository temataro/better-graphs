# STYLE_AND_SUBSTANCE.md — the fable design system

*A reimagining of the Better Graphs house style. `VISUALIZATION_GUIDE.md` still decides **what**
to draw; this document decides **who it's for**, **how hard to try**, and **what it should look
like** — and `visualization-curriculum/fable.py` is the one-import lever that makes it so.
The worked examples live in `visualization-curriculum/style_and_substance.qmd`.*

---

## The thesis

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

So every fable figure answers three questions, in order:

1. **What am I saying?** — one sentence, written *before* any code. Chart choice follows from
   it via `VISUALIZATION_GUIDE.md` (data shape × task → chart).
2. **Who is reading?** — the **register**: `glance`, `read`, or `study`. Sets the type scale,
   density, and annotation budget.
3. **How hard should I try?** — the **altitude**: themed default → composed chart → bespoke
   drawing. Effort is a budget; spend it where the audience and lifetime justify it.

---

## The register — a contract with the reader

Pick the register by how the figure will be *consumed*, not by how proud you are of it.
`fable.theme(register)` is the first plotting line; it makes the whole contract concrete.

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
4. **It stays honest** (the gates below still apply at any altitude).

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

## The page — anatomy of a fable figure

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

`fable.page(kicker=…, title=…, dek=…, source=…, note=…)` builds all of it with inch-true
margins — which is why `fable.save()` **never uses `bbox_inches="tight"`**: the margins are
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
measures worst-pair ΔE, lightness band, chroma floor, and WCAG contrast against the surface.
This palette passes with min ΔE **26.6** (target ≥ 12) on paper and on white; the previous
house palette scored **6.9** under deuteranopia. That difference is invisible to a trichromat
squinting at swatches — which is exactly why **palettes are computed, not eyeballed**. Re-run
the check whenever a colour changes; simulate the rendered figure, not the swatches, when
lines are thin.

**Accent-and-grey vs. full palette.** Grey-context + violet is the default *for a
single-message chart* — the accent must be both darker and more saturated than the context.
When 3–6 co-equal series genuinely cross and must be traced, use the palette or facet;
forcing accent-and-grey there hides the story.

**Ramps.** Sequential = `fable.SEQUENTIAL` ("fable_seq": paper-lavender → violet → near-black,
Lab-arc-length equalised so equal steps mean equal perceived change) or viridis for scientific
neutrality. Diverging = `fable.DIVERGING` ("fable_div": rust ↔ warm neutral ↔ violet), always
centred on the meaningful zero via `diverging_norm()`. Never rainbow; never a hue at a
diverging midpoint.

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

## The workflow (the agent operating card)

1. Write the one-sentence finding. Choose the chart from `VISUALIZATION_GUIDE.md`; state
   *"`<chart>` because `<shape>` + `<task>`."*
2. Choose the **register** from the reader; state it. `fable.theme(register)`.
3. Choose the **altitude**; A2 requires passing the four-gate test aloud.
4. `fig, ax = fable.page(kicker=…, title=…, dek=…, source=…)` — the title states the finding;
   units go in the dek; series names colour-key into the dek (`dek_highlights`) instead of a
   legend box.
5. Draw with the OO API. Accent the message series; demote context to `CONTEXT`/`SMOKE`.
6. `fable.finish(ax)` (+ `units()`), then **spend the annotation budget**: `label_end()` for
   series, `mark()` for the interpretive callout, `spec_band()` for limits.
7. Check yourself: where do the eyes land first? It must be the accented element. Is every
   number honest at a glance (baselines, breaks, areas)? Would the figure survive being
   copied out of its document (title + dek + source intact)?
8. `fable.save(fig, stem)` — SVG + PDF + 2× PNG, margins preserved.

---

## Hard rules (the short list an agent must never break)

1. No rotated y-axis labels — units in the dek or `ylabel_above()`.
2. No centred titles; one left edge for the whole header stack.
3. No legend boxes on line charts — direct labels or dek colour-keying.
4. No naked "decluttered" figures — every shared figure carries its interpretive layer.
5. Bars start at zero, never broken; bar-of-means never hides raw points at small n.
6. Palette changes go through `check_palette.py`. No rainbow. No 7th series.
7. League Spartan never below 10 pt and never for tick labels or numeral columns
   (proportional figures jitter); Junction carries the working text.
8. Dual axes only for true unit pairs, zeros aligned, both axes colour-keyed — else split.
9. Bespoke (A2) requires the four-gate test, printed exact values for inexact encodings,
   and a how-to-read key for novel forms.
10. Export via `fable.save()`; never `bbox_inches="tight"` on a `page()` figure.

---

## Lineage

The system stands on: Tufte (data-ink, integrity) · Cleveland & McGill (encoding accuracy) ·
Bertin (visual variables) · The Economist/FT/NYT graphics desks (the anatomy, the discipline,
"the annotation layer is the most important thing we do" — Amanda Cox) · Doumont (label
geometry, meaningful ticks) · Lisa Charlotte Muth (colour craft) · Weissgerber (show the data)
· W. E. B. Du Bois (bespoke form, honestly repaid) · Rougier (matplotlib as a drawing
instrument) · Ajani/Xiong/Knaflic/Franconeri (why "focused" beats "decluttered").

The house style this reimagines (`CLAUDE.md`, `house_style.py`, minerva) remains on `main`;
fable is its second draft — same convictions, higher resolution.
