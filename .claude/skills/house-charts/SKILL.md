---
name: house-charts
description: >-
  Use when creating, reviewing or revising matplotlib charts. Apply Better Graphs'
  evidence-first decision brief, task-based chart choice, reader registers, uncertainty,
  accessible encodings and real-output checks. Preserve the reusable house-style API
  without treating its aesthetic defaults as integrity rules.
---

# House charts — evidence before emphasis

A chart helps a reader reason about evidence. Inspect the evidence before asserting a finding;
a question or descriptive title is valid. The house style is a starting point, not a correctness test.

## Before drawing

1. State reader, task, medium, dimensions and decision stakes.
2. Inspect provenance, units, observational unit, denominator, n, missingness, exclusions and transforms.
   Distinguish measured, estimated and synthetic data. State what cannot be inferred.
3. Say **“`<chart>` because `<shape>` + `<task>`”** and compare an alternative:

   | Task | Starting form | Check / alternative |
   |---|---|---|
   | Exact lookup | Table | Does graphical comparison actually help? |
   | Rank categories | Sorted dots/bars | Natural order may matter; magnitude bars start at zero |
   | Paired change | Dumbbell/slope | Grouped bars can serve comparison of levels |
   | Trend | Line | Real time spacing, missing-data gaps, smoothing disclosed |
   | Distribution | Points, histogram, ECDF | State n/bins; summary alone can hide shape |
   | Relationship | Scatter | Overplotting, confounding; no causal claim from association |
   | Composition | Shares/stacked bar | Whole/denominator known; a few labelled pie slices can work |
   | Matrix | Heatmap | Colour limits/units; table for exact values |

4. Choose `glance` (seconds), `read` (tens of seconds), or `study` (minutes) for density/size.
   These are heuristics. **Material uncertainty stays visible in every register.**
5. Choose effort: A0 provisional diagnostic, A1 composed default, A2 bespoke only with a standard-view
   comparison, specific task benefit, justified cost and decoding/integrity checks.

## Working pattern

```python
import house_style
house_style.theme("read")
fig, ax = house_style.page(
    kicker="Topic · period",
    title="A supported finding — or the question under study",
    dek="Population, measure, units and method.",
    source="Source: dataset/version; exclusions and synthetic status if relevant",
    note="Material limitation or interval definition, if applicable",
)
ax.plot(x, y, color=house_style.ACCENT, label="Identified series")
house_style.finish(ax)
# Add units(), label_end(), a legend or mark() only as the reading task requires.
house_style.save(fig, "stem")
```

Use the OO API; `page()` can create mosaics; `spec_band()` denotes a threshold, not uncertainty.
Preserve page margins at export; do not use `bbox_inches="tight"` on that layout. The exported
SVG uses text paths: provide accessible text separately, not an assumption that SVG is accessible.

## Integrity and readability checks

- Recompute summaries and validate units/denominators, filters, precision and time coverage.
- Magnitude bars start at zero; cropped dot/line scales can be valid when explicit. State log transforms.
- Define interval type, level, method and sampling unit; distinguish spread from estimator uncertainty.
  Show observations at small n when safe. Do not invent uncertainty or use overlap as a universal test.
- Prefer stacked shared-x panels over dual axes. Different units/zero alignment do not fix arbitrary
  scaling. If twins are justified, label both and warn that crossings/slopes are not comparable.
- Use categorical/sequential/diverging colour according to meaning. `SERIES`, `SEQUENTIAL`,
  `DIVERGING` and `diverging_norm()` are available; don't cycle into ambiguous identities.
  Run `check_palette.py` on changes; it is a swatch simulation, not accessibility certification.
- Keep essential text/marks legible. Use labels, patterns, markers or facets so identity survives loss of hue.
  Status colours need words/symbols. Provide alt text and a nearby caption/data route for HTML.
- One accent, quiet grids, direct labels, left headers, house fonts and horizontal unit labels are
  **defaults**. Co-equal series, legends, neutral titles and retained grids can better serve the task.
  Neither an accent nor `mark()` is mandatory. Do not cut caveats to fit an attention budget.
- Inspect exported output at intended size: no clipped labels, collisions, unreadable caveats or
  misleading emphasis. Verify local links. Report automation separately from human visual checks.

## Source of truth and reuse

Inside the repository read `CLAUDE.md`, `VISUALIZATION_GUIDE.md`,
`visualization-curriculum/house_style.py` and `visualization-curriculum/check_palette.py`.
Outside it, use the matching files at:

- https://raw.githubusercontent.com/temataro/better-graphs/main/CLAUDE.md
- https://raw.githubusercontent.com/temataro/better-graphs/main/VISUALIZATION_GUIDE.md
- https://raw.githubusercontent.com/temataro/better-graphs/main/visualization-curriculum/house_style.py

Those main URLs describe the released version, not an unmerged review branch. Use local branch files
when reviewing changes. If the helper is unavailable, reproduce evidence, scale and accessibility
checks first; matching warm paper/violet/fonts is optional. Extract conditional rules:
“For this task use X because Y; switch to Z when W; test by observing Q.”
Never merge, publish or deploy a review without explicit human approval.
