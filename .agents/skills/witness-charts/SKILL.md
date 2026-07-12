---
name: witness-charts
description: >-
  Create, review, or revise evidence-aware Matplotlib figures with the Witness
  system. Use for quantitative charts intended for accessible HTML/SVG, slides,
  scientific inspection, decision support, or any request that needs explicit
  claims, comparators, uncertainty semantics, provenance, structural audits, and
  machine-readable export receipts while keeping NumPy transformations and native
  Matplotlib Figure/Axes/Artist handles.
---

# Witness charts — make the evidence interrogable

Witness treats a shared figure as an argument, not a styled array dump. Keep data
work explicit in NumPy and plotting native to Matplotlib; add a claim contract,
semantic Artist roles, an audit, and accessible exports.

## Before plotting

Answer these in order:

1. Write one supported claim with a verb.
2. Name the comparator: baseline, group, prior state, model, or threshold.
3. State scope and provenance.
4. State what uncertainty means—or say why no inferential interval is claimed.
5. Name the boundary, exception, or caveat.
6. Choose the chart from `VISUALIZATION_GUIDE.md` and state:
   **"`<chart>` because `<data shape>` + `<reader task>`."**
7. Choose purpose and medium independently:
   - `decide`: foreground threshold, margin, direction, and decision-changing uncertainty.
   - `explain`: foreground claim, warrant, context, and exception.
   - `inspect`: foreground observations, estimand, interval semantics, n, method, and missingness.
   - `html`: selectable, described, responsive SVG/HTML.
   - `slide`: physically re-typeset for distance; never resize an HTML figure.

## Workflow

```python
import witness

claim = witness.Claim(
    statement="A supported finding with a verb",
    measure="the visible estimand and unit",
    comparison="what is compared with what",
    scope="population, period, exclusions, and n",
    source="data provenance",
    method="explicit NumPy transformation or statistical method",
    uncertainty="what the interval/distribution represents",
    caveat="where the claim stops",
    alt="Equivalent plain-language description of the evidence and finding.",
)

witness.theme(purpose="explain", medium="html")  # first plotting line
fig, ax = witness.frame(claim)

line = ax.plot(x, y, color=witness.EVIDENCE)[0]
witness.tag(line, role="observation", label="reported values", redundant="line + label")

band = witness.interval(ax, x, low, high, kind="95% bootstrap interval")
witness.reference(ax, target, axis="y", label="target", source="specification source")
witness.finish(fig, ax)
witness.save(fig, "finding", strict=True)
```

`tag()` returns the same Artist. Helpers return native Artists or Axes. Continue
using `ax.plot`, `ax.scatter`, `ax.bar`, `subplot_mosaic`, transforms, and inset
Axes directly.

## Evidence roles

- `observation`: recorded values.
- `estimate`: statistics derived from observations.
- `model`: fitted or simulated quantities; never present them as observations.
- `uncertainty`: named intervals or distributions.
- `comparator`: the baseline or peer that warrants the claim.
- `reference`: external target/specification; name its source.
- `context`: relevant but subordinate evidence.
- `exception`: evidence limiting or contradicting the claim.
- `decision`: action region or margin; never a replacement for evidence.

Use `witness.tag(artist, role=..., redundant=...)`. Colour alone is not a
redundant channel: add marker shape, stroke, hatch, position, or direct text.

## Uncertainty discipline

- Compute intervals explicitly in NumPy; Witness does not hide analysis.
- Pass a specific `kind` to `witness.interval()`: “95% percentile-bootstrap
  interval,” not “error.”
- Distinguish observation, model uncertainty, sampling uncertainty, measurement
  error, and missing uncertainty.
- If uncertainty is unavailable, say so in `Claim.uncertainty`; do not imply
  precision with a clean line.
- Show raw observations with small-n summaries.
- Use descriptive/noncausal wording unless the design warrants causality.

## Composition levers

- `reference()` — labelled baseline/specification in mixed coordinates.
- `bracket()` — data-anchored comparison with point-offset label.
- `margin_note()` — renderer-resolved annotation gutter.
- `linked_detail()` — inset lens retaining overview and context.
- `label_end()` — direct line label.
- `panel_title()` — quiet titles inside a mosaic.
- `units()` — unit-aware ticks.
- `fingerprint()` — stable digest for explicit NumPy arrays in the receipt.

## Export and audit

Call `witness.finish()` and `witness.save(..., strict=True)` for every shared
figure. Strict export blocks missing claim fields, missing alt text/source,
unnamed uncertainty, nonzero bar baselines, absent semantic Artists, and
path-only SVG text. Warnings and human-review prompts remain in the receipt.

Witness writes accessible SVG with embedded IBM Plex WOFF2, self-contained HTML,
PDF, PNG, and `*.receipt.json`. SVG must retain `<text>`, `<title>`, `<desc>`,
ARIA linkage, and semantic `gid` groups.

## Hard rules

1. Use the Matplotlib OO API; no pyplot plotting after figure creation.
2. Keep transformations explicit in NumPy unless another structure gives a
   concrete, documented benefit.
3. Never style an estimate/model as an observation.
4. Never leave interval semantics implicit.
5. Bars and other length encodings start at zero; signed data show zero.
6. Essential distinctions use redundant encodings; palettes pass CVD, contrast,
   and grayscale checks.
7. Meaningful small text uses `witness.MUTED`, not the low-contrast support grey.
8. Recompose for `slide` versus `html`; do not stretch one export.
9. A linter checks structure, not analytical truth. Resolve the receipt's human
   review prompts yourself.

## Sources of truth

- `../../../EVIDENCE_BY_DESIGN.md` — full design system and epistemic rules.
- `../../../VISUALIZATION_GUIDE.md` — chart choice.
- `../../../visualization-curriculum/witness.py` — public API and F2P2 tokens.
- `../../../visualization-curriculum/witness_audit.py` — executable gates.
- `../../../visualization-curriculum/evidence_by_design.qmd` — worked examples.
