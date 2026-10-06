# Review record — `gpt-6-astra` design-philosophy overhaul

**Branch:** `gpt-6-astra` · **Base:** `main` at `13787138af57` (unchanged by this branch).

## Authorship

The editorial overhaul — the revised design philosophy and its wording across
[`VISUALIZATION_GUIDE.md`](../../VISUALIZATION_GUIDE.md), [`CLAUDE.md`](../../CLAUDE.md),
[`README.md`](../../README.md), [`PLAN.md`](../../PLAN.md), the house-charts skill and the
curriculum prose — was authored by a platform-configured agent labelled `gpt-6-astra`.
That label is the configured name recorded in this repository's metadata; **it was not
independently verified, and nothing here establishes which model produced the text.**
The same caveat is carried inline in the curriculum front matter
(`editorial-review: "gpt-6-astra (configured model label; review branch)"`).

The initial workspace review record credited the Code Agent with implementation validation.
The final transfer and validation were performed directly by the coordinating assistant in
`~/code/github.com/temataro/better-graphs` on 2026-10-06: dataset regeneration, palette checks,
eight tests, all 33 Quarto cells, and HTML/link validation passed in that actual checkout.
The existing `visualization-curriculum/better_graphs.qmd` is the updated source used by Actions;
`visualization-curriculum/index.html` was regenerated there. The review copy is supplemental.

## What the overhaul changes

The revision keeps the M0–M7 curriculum, the before/after teaching convention and the public
`house_style` API, and changes the standard the figures are judged by: from "does this look
deliberate" to "what can the reader accurately infer, and what might they miss."

- **Design authority rewritten.** `VISUALIZATION_GUIDE.md` leads with an evidence-first decision
  brief (reader, task, provenance, denominator, n, missingness) before chart choice. Aesthetic
  absolutes become conditional rules with stated exceptions.
- **House defaults demoted from integrity laws.** Single accent, direct labels, a mandatory
  interpretive callout and a mandatory finding are now defaults, not requirements; legends,
  neutral/question titles and co-equal series are explicitly valid. Zero-baseline bars,
  honest missingness and stated uncertainty remain non-negotiable.
- **Uncertainty promoted into every register.** Two new curriculum cells
  (`uncertainty-every-register`, `uncertainty-accessible-table`) carry a paired-trial interval
  through `glance` and `study`, plus a text-table alternative to the figure.
- **`house_style.py`: documentation only.** The diff touches the module docstring, the `SERIES`
  comment and the `page`/`finish` docstrings. No function signature, default or palette value
  changed; the contract tests cover the full public surface.
- **Publication boundary tightened.** `.github/workflows/publish.yml` now builds and validates
  every branch and pull request with `contents: read` only, and confines Pages write
  permissions and deployment to `main`.

## Checks run

Executed in this repository on 2026-10-06 with the uv-managed project environment
(uv 0.11.13, Python 3.12.12, Quarto 1.9.38).

| Command | Result |
| --- | --- |
| `uv sync --locked` | 108 packages checked, lockfile honoured |
| `uv run python data/build_datasets.py` | 9 datasets written, **0 download failures** |
| `uv run python scripts/check_house_palette.py` | **PASS** on `#FAF7F2` and `#FFFFFF`; worst simulated pairwise ΔE = 26.6 |
| `uv run python -m unittest discover -s tests -v` | **8 tests, OK** |
| `uv run quarto render visualization-curriculum/better_graphs.qmd` | **33/33 cells executed**, no errors, `index.html` produced |
| `uv run python scripts/validate_review.py` | **PASS** — 28 embedded images all with alt text, 2372 anchors inspected, 24 local document links checked |

The eight tests assert the public helper surface across all three registers, mosaic layout and
SVG/PDF/PNG export with rcParam restoration, `diverging_norm` plus the six-colour palette on both
surfaces, that every `{python}` cell parses and every captioned figure has `fig-alt`, and the
workflow contract. The release condition is evaluated over all 16 ref/event combinations
(`main`, `gpt-6-astra`, a PR merge ref, a `main` tag × push, `workflow_dispatch`, `pull_request`,
`pull_request_target`) and deploys in exactly the two intended cases.

Independent spot-check of the new statistics: the Wilson intervals in the M0 rate cell
(18/200 → 5.77–13.78%; 12/80 → 8.79–24.41%) were confirmed to machine precision against the roots
of the defining quadratic. Interval overlap alone is not a formal test of the difference between two proportions;
the teaching example should not be read as one.

### Fixes made during validation

Both were missing review artifacts rather than defects in the overhaul:

1. Added this record at `reviews/gpt-6-astra/REVIEW.md` — `README.md` and the validator's
   document list both referenced it.
2. Regenerated the curriculum and copied the real render to
   [`reviews/gpt-6-astra/index.html`](index.html); the directory was previously empty.

## Publication boundary

Branch and pull-request runs build, test and validate, then upload a downloadable
`curriculum-review` artifact. They do not deploy. Only a push to `main`, or a manual run
selected on `main`, passes the release condition that gates both the Pages artifact upload and
the `deploy` job — which holds the only `pages: write` / `id-token: write` grant. Review builds
run with `contents: read` and `persist-credentials: false`. No deployment was triggered during
this review, and `main` was not modified.

## Limitations

- **Authorship is a configured label, not a verified model identity.** See above.
- **`reviews/gpt-6-astra/index.html` is a downloadable local artifact, not a hosted preview.**
  GitHub's source view will not render it; download or clone, then open it in a browser.
- **The validator is an offline structural check.** It confirms embedded resources, non-empty
  alt text, internal anchors and local paths. It does **not** fetch external URLs, and it is not
  a visual or assistive-technology audit — human review of contrast, glyph rendering at delivery
  size and screen-reader behaviour remains outstanding. No accessibility certification is claimed.
- **`check_palette.py` validates the palette, not the charts.** Passing swatch separation does not
  establish that any particular figure is legible.
- **`actionlint` was not run** — it is not installed in this environment. The workflow was parsed
  as YAML and its trigger, permission and gating structure is covered by the contract tests, but
  that is not a substitute for Actions syntax linting.
- **The RF datasets and the two uncertainty cells are synthetic**, and labelled as such in the
  curriculum. Specification bands are teaching thresholds, not confidence intervals.
- **Scope.** The editorial interpretation was reviewed for internal consistency and factual
  accuracy, not rewritten. Chart builders (`bar()`, `line()`, `slope()`, `dumbbell()`, `dist()`,
  `heatmap()`) remain unimplemented, as `PLAN.md` states.


## M8 extension — substantive new workshop (2026-10-06)

Implemented in the original `~/code/github.com/temataro/better-graphs` checkout, not only a workspace preview.
The source `visualization-curriculum/better_graphs.qmd` now contains **M8 — Tables inside figures:
the evidence ledger**: six new rendered compositions and three accessible-table cells.

- A deliberate before example and three audience-specific views of the historical paired sleep data.
- A Berkeley admissions figure with shared-row rates and admitted/N columns; no causal fairness claim.
- A synthetic three-trial comparison with an explicit A-minus-B contrast, not an unjustified pooled effect.
- Reusable `evidence_tables.py`: source arrays, interval calculations, shared-row layouts and exports.
- Four new tests for numeric transcriptions, pairing, seeded bootstrap reproducibility, text bounds,
  missing glyphs and row alignment; existing eight tests retained.

Validation: **12 tests passed; all 42 Quarto cells executed; 34 embedded figures with alt text,
2699 HTML anchors and 24 local document links passed structural validation.** Quarto reported
`Output created: index.html`; the shell wrapper then timed out. The finished output was independently
checked, copied to the review render and validated. Generated trailing whitespace was normalized.
Two example PNGs were also inspected through the image reader for legibility. This is not a full
browser or screen-reader audit. R source numeric arrays and documentation, Matplotlib documentation
and Cochrane chapter 10 were checked online; primary-source links are embedded in M8.

The bootstrap example is deliberately synthetic and centered to fixed illustrative effects. Nominal
intervals do not establish multiplicity control or a coverage guarantee. No publication or merge occurs.
