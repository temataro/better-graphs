# Evidence by Design — the Witness system

*A third interpretation of Better Graphs. `VISUALIZATION_GUIDE.md` still decides
what chart answers the question. Witness governs what a shared figure must disclose,
how its evidence changes with purpose, and what leaves the plotting process with it.*

## The thesis

**A figure is an argument you can interrogate.**

A chart is not trustworthy because it is sparse, polished, or beautiful. It is
trustworthy when a reader can recover the path from observation to claim:

1. **Claim** — what does the figure say?
2. **Comparator** — compared with what: a baseline, another group, a model, a
   threshold, or an earlier state?
3. **Evidence** — which marks are observations, estimates, models, or context?
4. **Uncertainty** — what is measured, sampled, modelled, missing, or simply unknown?
5. **Boundary** — where does the claim stop holding; what is the exception or caveat?
6. **Provenance** — where did the data come from and what transformation produced
   the visible values?

These are not page decorations. They are the figure's epistemic structure. Witness
turns that structure into semantic Matplotlib Artists, an audit, and an export
receipt. The linter can check whether the structure is present; it can never certify
that the analysis is true.

## The separation Fable does not make

Purpose and medium are orthogonal.

The same analysis may be used to make a decision, explain a pattern, or permit close
inspection. Independently, it may live in HTML or on a slide. Combining those two
questions into a single "density" switch makes the design hard to reason about.

### Purpose — why the figure exists

| Purpose | Reader's job | Evidence foregrounded | Required restraint |
|---|---|---|---|
| `decide` | choose or act | threshold, margin, direction, material uncertainty | do not hide uncertainty that could reverse the decision |
| `explain` | understand why | claim, comparator, context, exception, plain-language warrant | do not turn interpretation into unsupported causality |
| `inspect` | verify or reuse | observations, estimand, interval semantics, n, method, missingness | do not replace distributions with summaries when the observations fit |

Purpose changes evidence emphasis, not truth standards. `decide` is not permission
to remove an inconvenient interval; `inspect` is not permission to dump every
variable into one axes.

### Medium — where the figure has to work

| Medium | Physical contract | Export contract |
|---|---|---|
| `html` | responsive reading width; selectable text; keyboard/reader context nearby | accessible SVG + self-contained HTML + receipt |
| `slide` | 16:9 or 4:3 at presentation distance; large type; one visual entry point | SVG/PDF + high-DPI PNG + speaker-safe caveat |
| `print` | column-width composition and grayscale first | vector PDF/SVG with reproducible dimensions |

One analysis may be re-composed as `purpose="inspect", medium="html"` and
`purpose="decide", medium="slide"`. It should not be resized from one into the
other.

## A thin semantic layer, not another plotting framework

Witness does not own data manipulation and does not replace `Axes.plot`,
`Axes.scatter`, `Axes.bar`, or any other Matplotlib method. NumPy remains the data
surface. Witness supplies a small semantic specification and returns native objects.

```python
import witness

claim = witness.Claim(
    statement="Measured Gentoo averaged 1.38 kg more than Adelie",
    measure="mean body-mass difference",
    comparison="Gentoo minus Adelie",
    scope="Palmer penguins with complete measurements",
    source="Palmer Station LTER",
    method="percentile bootstrap, 10,000 resamples",
    uncertainty="95% interval",
    caveat="Descriptive; unadjusted for sex and island.",
    alt="Body-mass distributions for three penguin species ...",
)

witness.theme(purpose="explain", medium="html")
fig, ax = witness.frame(claim)
points = ax.scatter(flipper_mm, body_mass_kg)
witness.tag(points, role="observation")
band = witness.interval(ax, x, low, high, kind="95% bootstrap interval")
witness.finish(fig, ax)
witness.save(fig, "penguin_mass", strict=True)
```

`tag()` returns the same Artist it receives. Helpers such as `interval()`,
`reference()`, `bracket()`, `margin_note()`, and `linked_detail()` return ordinary
Matplotlib Artists or Axes. Every semantic Artist receives a stable SVG group id.

## The evidence roles

The visual identity may change; these roles do not.

- **observation** — a recorded value; never silently styled as a model output.
- **estimate** — a statistic derived from observations.
- **model** — a fitted or simulated quantity, visually distinct from observations.
- **uncertainty** — an interval or distribution whose meaning is printed in words.
- **comparator** — the baseline, peer, prior state, or counterfactual that warrants
  the comparison.
- **reference** — a target, specification, or external threshold, including its
  source when it is not inherent to the data.
- **context** — relevant evidence that should remain available without winning the
  hierarchy.
- **exception** — evidence that limits, contradicts, or qualifies the main claim.
- **decision** — the action region or margin; never a substitute for the evidence.

Colour alone never distinguishes these roles. Stroke, marker, position, label, or
hatch supplies a redundant channel.

## The Matplotlib craft Witness should expose

The premise of this repository is that Matplotlib is a drawing instrument. Witness
therefore makes a few difficult, high-value compositions reusable:

- an annotation gutter laid out in display coordinates, so labels collide less;
- comparison brackets using data coordinates for endpoints and point offsets for
  caps and text;
- evidence rails that align estimates, intervals, and thresholds without a second
  quantitative axis;
- linked details and lenses built with inset Axes and `ConnectionPatch`;
- interval ribbons with explicit edges and optional hatching for grayscale;
- direct labels separated in display space after the renderer measures them;
- stable semantic `gid` values for accessible SVG groups.

The plotted quantity still uses the most accurate available encoding. Bespoke
composition clarifies the argument around it; it does not turn imprecise geometry
into spectacle.

## Every export leaves a receipt

`witness.save()` will write the requested visual formats and a machine-readable
`*.receipt.json`. For HTML it will also write a self-contained figure wrapper.

The receipt records:

- claim, comparison, scope, source, method, caveat, and alt description;
- purpose and medium;
- semantic Artist roles and their labels;
- axes limits, scales, units, and tick counts;
- the selected design palette and the alpha-composited colours actually used;
- data fingerprints supplied by the caller (never hidden data manipulation);
- Python / NumPy / Matplotlib versions, font and visual-artifact hashes;
- audit findings, strictness, and any explicit override reason.

Accessible SVG keeps text as text. Export adds `<title>`, `<desc>`, `role="img"`,
ARIA references, and semantic group ids. A second, post-export inspection resolves
the ARIA references, checks every expected `gid`, rejects duplicate IDs, validates
the embedded WOFF2 payloads, and rejects remote font/CSS dependencies. The HTML
wrapper adds a visible caption, an adjacent text summary, and a no-JavaScript
method/provenance disclosure.

## What the audit can and cannot do

### Deterministic errors

- a shared figure omits any part of its claim / measure / comparator / scope /
  source / method / uncertainty / boundary / alt-text contract;
- an uncertainty Artist has no interval semantics;
- an external reference has no source;
- a length encoding starts away from zero or hides zero outside the visible scale;
- a `decide` or `inspect` figure omits its purpose-specific evidence role;
- SVG text was converted to paths;
- actual rendered text or graphical marks fail severe contrast thresholds after
  alpha compositing on the figure surface;
- the exported SVG fails any semantic, accessibility, font, or self-containment gate.

### Warnings

- colour appears to be the only distinguishing channel;
- visible data Artists have no semantic role;
- declared material uncertainty is absent;
- focal type or markers are too small for the selected medium;
- the purpose's annotation budget is exceeded;
- figure-level claim or provenance copy clips or collides after renderer measurement.

### Human-review prompts

- does the design warrant causal language?
- is the comparator meaningful rather than merely convenient?
- is the uncertainty method appropriate to the estimand?
- does the scope support the generalization in the title?
- was a material exception demoted as "context"?
- are denominators, sample size, missingness, and exclusions explicit enough?
- do shared panels use comparable limits where the reader will compare them?

`strict=True` blocks deterministic errors before and after SVG generation,
records warnings, and leaves these questions visibly unresolved. An exceptional
`strict=False` export with errors requires a non-empty `override_reason`, which is
written to the receipt. Structure can be linted. Truth still requires a person.

## Hard rules

1. State the chart type and why before plotting; chart choice remains governed by
   `VISUALIZATION_GUIDE.md`.
2. A shared figure carries a claim, comparator, scope, and provenance.
3. Observations, estimates, models, and uncertainty are not visually
   interchangeable.
4. An interval says what interval it is. "Error bars" is not a definition.
5. Causal verbs require a causal design; styling cannot upgrade evidence.
6. Small-n summaries show the observations. Missingness and exclusions are stated.
7. Bars and other length encodings start at zero. Signed quantities show zero.
8. Colour is redundant for essential distinctions; palettes pass CVD, contrast,
   and grayscale checks on the actual surface.
9. HTML/SVG exports keep selectable text and carry an equivalent text description.
10. Witness helpers return native Matplotlib objects. Data transformations stay
    explicit NumPy unless another structure has a concrete, documented benefit.
11. An audit receipt accompanies every final export. It is evidence about the
    rendering process, not a certificate of analytical truth.

## Visual identity — F2P2

The semantic role system was fixed before its colours and typography. Four font
systems and three surfaces were compared on identical evidence in a controlled
4 × 3 calibration board; the selected direction is **F2P2**:

- IBM Plex Serif SemiBold for claims;
- IBM Plex Sans for working text and scientific symbols;
- IBM Plex Mono for aligned numeral receipts;
- parchment `#FBF5E8`, ink `#19231E`, and an evergreen / brick / violet
  categorical set (`#006B5E`, `#A33A2B`, `#67469B`).

The first calibration SVG exposed an important failure: selectable SVG text that
merely names a local font is not portable. A viewer without that font silently
substitutes another face, making every candidate look the same. Witness therefore
ships IBM's official TTF and WOFF2 builds, keeps text selectable, embeds WOFF2 in
SVG/HTML, and audits the output for both text nodes and embedded font rules.
