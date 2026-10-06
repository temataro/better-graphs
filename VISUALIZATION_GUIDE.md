# Better Graphs — evidence before emphasis

**A chart is an interface to evidence, not a verdict dressed in a house style.** Its job is to
help a particular reader answer a particular question without concealing what the data cannot
say. Publication craft matters because it makes that work easier; beauty is neither evidence
nor an acceptance test.

Start with a question, inspect the data, then earn the headline. An exploratory chart may
have a question or descriptive title. A communication chart may state a finding, but its
strength must not exceed the analysis. Do not pick the story first and edit away the contrary
observations. A useful table, a plain chart, or an explicit “not enough evidence” can be the
right deliverable.

This guide governs decisions. [CLAUDE.md](CLAUDE.md) governs execution;
[the curriculum](visualization-curriculum/better_graphs.qmd) demonstrates them, and
[house_style.py](visualization-curriculum/house_style.py) supplies compatible defaults, not
proof of correctness. Existing M0–M7 examples remain useful demonstrations, not controlled
experiments establishing that one aesthetic always wins.

## 1. The decision brief — before drawing

Record these six answers in the working notes or figure caption:

1. **Reader and context.** Who uses this, what do they already know, what decision follows,
   on what screen/page, at what size and viewing distance? What is the cost of misreading?
2. **Task.** Compare levels, rank, detect change, inspect a distribution, estimate a relationship,
   assess a threshold, understand composition, or retrieve exact values? Pick a primary task.
3. **Evidence.** Name the source/version, observational unit, population, time coverage, units,
   denominator, sample size, missingness, exclusions and transformations. Is it measured,
   estimated, simulated, or an illustrative toy? Check joins and duplicate observations.
4. **Candidate forms.** State “`<chart>` because `<shape>` + `<task>`”; compare at least one
   plausible alternative. A table wins when lookup is the task; no chart wins when evidence is absent.
5. **Claim and limits.** Only after inspection, state the supported finding or open question.
   Name the uncertainty or competing interpretation that could change the decision.
6. **Delivery test.** Choose register, dimensions, required labels, alternative text/data access,
   and a concrete failure condition (e.g. “cannot distinguish the two intervals at slide size”).

**Example brief.** A colleague comparing life expectancy changes in selected countries needs
paired endpoints, not a ranking of country sizes. Use a dumbbell for 1952→2007; grouped bars
remain reasonable if the question is absolute levels against zero. Check coverage of both years,
keep country identities, and say “selected countries,” not “the world.” Differences are descriptive,
not evidence of a policy's causal effect.

### Worked decision: count or risk?

Invented samples with 18 failures in 200 trials before a change and 12 in 80 after it
have fewer failures but a higher observed rate: 9% versus 15%. For a reliability task,
show rates, denominators and justified intervals rather than celebrating a one-third fall
in counts. The curriculum executes this example with 95% Wilson intervals under an
independent-binomial assumption, direct labels and an accessible table. Intervals for the
two rates do not themselves test their difference, and neither chart establishes causation.
Repeated or clustered observations require a method that accounts for that dependence.

## 2. Non-negotiable integrity, revisable defaults

| Integrity requirement | House default and reason | When to depart / check |
|---|---|---|
| Encodings faithfully represent values | Common-position dots or zero-based bars for comparisons | Use area for spatial/overview tasks; scale area, not radius, to value and provide a key |
| Claims match evidence and scope | Finding title for an established result | Use a question/descriptive title in exploration or when estimates do not resolve the question |
| Readers can identify marks without colour alone | Direct labels and one accent for one focal comparison | Use markers, line patterns, panels or a keyed legend for co-equal series; retain legible context |
| Material limitations travel with the figure | Title, dek, plot and source/note | A compact caption can replace the header stack; never drop a caveat merely to fit the template |
| Essential evidence remains visible | Quiet grid, restrained spines, generous whitespace | Keep grids/borders when lookup or panel alignment needs them; “less ink” is not the objective |
| The output is readable in its destination | Warm paper, Junction body, League Spartan display | White paper, other fonts, centred headers or vertical unit labels are valid if they work better |

Defaults reduce repetitive decisions. An exception needs a task-based reason, not permission
from an aesthetic authority. A seventh series is a signal to reconsider layout, not a moral
failure; never silently reuse a colour for a different identity in the same figure.

## 3. Task × data shape → a starting chart

| Task / shape | Start with | Alternative and concrete check |
|---|---|---|
| Exact lookup / a few values | Table, with units in headers | Dot plot for patterns; can the reader recover needed precision? |
| Compare or rank / categories + number | Sorted horizontal dots or bars | Preserve natural/ordinal order when meaningful; bars start at zero |
| Paired change / category + two values | Dumbbell or slope | Grouped bars for levels; show unmatched observations rather than silently dropping them |
| Trend / time + number | Line, with real time spacing | Points for sparse observations; do not connect across unknown intervals as if measured |
| Distribution / numeric observations | Histogram or ECDF | State bins; KDE bandwidth changes shape; do not confuse a density with counts |
| Group distributions / category + observations | Points + box/interval | At small n show observations; label n and distinguish spread from uncertainty of an estimate |
| Relationship / two numbers | Scatter | Hexbin for dense data; disclose transforms, overplotting and fitted-model assumptions |
| Composition / parts of a known whole | Shares or stacked bar | A few labelled pie slices are usable for rough part-to-whole judgments, not precise ranking |
| Deviation / number relative to reference | Dot or diverging bar | State reference; only use diverging colour when that centre has substantive meaning |
| Matrix / two dimensions + magnitude | Heatmap | Label colourbar units and limits; supply values/table if exact lookup matters |
| Geography / place + measure | Rate choropleth or sized symbols for counts | A ranked bar may answer better; state denominator, projection and unobserved areas |
| Flows / nodes + quantities | Sankey with conservation accounting | Table/network for detail; reconcile inflow, outflow and omitted small flows |

### Chart-specific checks

- **Lines:** order x, expose gaps, identify smoothing windows and retain raw observations where smoothing
  affects the conclusion. Direct labels are useful only when they do not collide or obscure endpoints.
- **Bars and lollipop stems:** length represents distance from a declared baseline; use zero for values.
  A floating interval is not a zero-based magnitude bar. Use dots for a tightly cropped comparison.
- **Dots and lines:** a nonzero axis is legitimate. Make the range explicit; test whether the apparent
  effect survives a wider range. Do not suggest that a small absolute difference is a large proportional one.
- **Small multiples:** common scales support magnitude comparison. Free scales support shape inspection;
  mark that choice prominently and do not invite cross-panel height comparisons.
- **Maps:** area is not population. Rates with unstable small denominators may need uncertainty or suppression.
- **Dual y axes:** different units do not make arbitrary scaling safe, and aligned zeros do not make slopes
  comparable. Prefer stacked shared-x panels. If a domain convention requires twins, label both scales,
  distinguish marks redundantly, and explicitly forbid inference from crossings or relative slopes.
- **Log axes:** explain multiplicative spacing, handle zeros/negatives explicitly, and label ticks in data units.

### Domain charts — RF / measurements over frequency

Keep specialist forms when the reader knows the convention:

- Magnitude vs frequency: dB for amplitude ratios is `20·log10|S|`; power ratios use `10·log10`.
  State reference, GHz units, test conditions, and the band of interest.
- Polar radiation patterns: declare the dB floor (e.g. −40 dB), orientation and normalization;
  annotate main lobe and sidelobes without implying values below the floor are zero.
- Smith charts: complex reflection coefficient warrants the domain projection; use a tested library
  such as `scikit-rf`, not improvised geometry.
- PA gain/efficiency: shared drive power does not imply shared response units. The curriculum retains
  a labelled twin-axis example as a convention to audit, not proof that two coloured axes are honest.
- `rf_ring_slot` contains measured scikit-rf S-parameters. The antenna, PA and DUT teaching
  datasets are **synthetic**; do not describe those as measurements of a production device.

## 4. Hierarchy is a reading order, not a mandatory accent

Design three levels: **orientation** (what population/measure?), **evidence** (what comparison?),
**qualification** (how certain, under what conditions?). The main visual comparison should be findable
before the reader decodes every footnote. Important qualifications must not be demoted below legibility.

A supported title can lead, followed by units/method in the dek, marks/axes, and source/limitations.
Use `page()` when this self-contained anatomy helps; compact lesson panels can use a shared caption.
Annotation should resolve an ambiguity, explain a mechanism with evidence, or locate an event. Do not
add `mark()` just to satisfy a quota, repeat the title, or turn correlation into causation.

Use an accent when attention has a justified target. With co-equal groups, give each equal visual
status. Grey is still data: check its contrast and whether de-emphasis hides an exception. A legend
is a valid lookup device; use it when direct labels would overlap or reading identities together helps.

**Checks:** at intended size, can a new reader identify the measure, compare the intended marks,
and find the limitation? In greyscale, can they still identify series? With the title covered, do
marks support the claim? With the chart removed, does the alternative text retain the key evidence?

## 5. Registers — budgets for attention, not for truth

`house_style.theme(register)` selects typography and density. The times below are planning heuristics,
not measured reader capabilities or promises of comprehension.

| | `glance` | `read` | `study` |
|---|---|---|---|
| Typical context | Slide / distant display | Report / article | Appendix / analysis |
| Planning attention | Seconds | Tens of seconds | Minutes |
| Starting composition | One comparison, large labels | Main comparison + supporting context | Panels, detail and lookup |
| Starting tick budget | 3–4 | ~5 | ~6, adapt to task |
| Identity | Direct labels if they fit | Direct labels or legend | Shared legend or panel keys |
| Uncertainty | Show if it could change interpretation | Show and define interval | Show method, assumptions, n and sensitivity |
| Acceptance test | Readable at viewing distance | Readable at final column width | Detail recoverable without ambiguous encodings |

Never hide material uncertainty in speech alone: figures travel without presenters. A concise interval,
range, or “difference unresolved” title may be more valuable than a hero number. If there is no room,
simplify the task, split the chart, or point to a companion view while keeping the limitation visible.
Re-render when the destination changes enough to break readability; verified reuse is not forbidden.

## 6. Uncertainty, missingness and honest claims

Separate **variation in observations**, **uncertainty about a parameter**, **prediction uncertainty**,
and **measurement/model limitations**. They are not interchangeable error bars. Identify the interval
(CI, credible interval, SD, IQR, min–max), level, method, n and sampling unit. Repeated observations are
not independent samples. A bootstrap over rows cannot repair selection bias or dependence.

For estimates, plot points with intervals on a common scale. For distributions, show the distribution;
small n often merits the raw points. Avoid using error-bar overlap as a universal significance test.
For a difference, estimate the difference and its uncertainty directly when the design permits it.

- Record missing counts and denominator changes; do not recode missing as zero or interpolate silently.
- Label synthetic data and simulations on the figure, including seed/method in the accompanying text.
- State aggregation, weighting and filters. Check whether subgroup patterns reverse the aggregate.
- Distinguish percentage-point from percent change, rate from count, nominal from inflation-adjusted values.
- Match precision to measurement and uncertainty. No spurious decimal places; no “proves” from association.
- A threshold/spec band is a decision reference, not a confidence interval. State who set it and its scope.
- If uncertainty is unavailable, say so. Do not manufacture intervals to make an example look scientific.

## 7. Colour and accessibility — test the actual encoding

The unchanged house identity is warm paper `#FAF7F2`, ink `#201D1A`, violet accent `#6400FF`.
`SERIES` supplies six categorical colours; `CONTEXT`/`SMOKE` support secondary structure;
`GOOD`/`BAD` are optional status colours, always paired with words or symbols.
Use sequential colour for ordered magnitude; use `DIVERGING` and `diverging_norm()` for deviations
from a meaningful centre. The helper uses symmetric limits, which is a useful default, not evidence
that the underlying distribution is symmetric. Do not use rainbow/jet for ordered magnitude.

Run `uv run python scripts/check_house_palette.py` after palette changes. It simulates
three colour-vision deficiencies and tests swatch separation/contrast under its stated model.
Passing is **not accessibility certification**: thin lines, small type, overlap, projection, print
and colour vision beyond the simulated cases still matter. Check the rendered marks, not just hex codes.

For essential text, target WCAG contrast of 4.5:1 (3:1 for large text); for essential graphical objects,
3:1 against adjacent colours is a useful baseline. These thresholds do not guarantee comprehension.
Use shape, line style, position, labels or faceting as redundant identifiers. Do not communicate pass/fail
only in red/green. Keep context readable if the reader must compare it.

For HTML, supply informative image alt text and a nearby caption or table describing values, scope,
and limits. A raster figure or SVG with text converted to paths is not inherently screen-reader-readable.
Link the data/method when available; protect private observations. Check keyboard access to interactive
controls and reading order. Test at final size and zoom; do not claim a screen-reader audit from an
HTML parser alone.

## 8. Effort — spend it on the reader's risk

- **A0: diagnostic.** Fast plots/tables to inspect shape, missingness and assumptions. May be shared as
  explicitly provisional analysis; never pass a diagnostic off as reviewed evidence.
- **A1: composed.** A familiar form with necessary context, legible hierarchy and checked export.
  This is the default deliverable. It need not have every component of the house header.
- **A2: bespoke.** Custom Artists/layout when a standard form hides important structure or a domain
  convention materially helps. More decoration does not mean more analytical work.

Before A2: (1) compare against a standard view/table, (2) identify the specific task benefit,
(3) justify development and maintenance cost against audience and stakes, (4) validate decoding and
integrity. Provide a how-to-read key and exact values/table when the encoding cannot support needed
precision. Area scales with value; radius scales with its square root. Familiarity and testing matter
more than an absolute ban on novelty in slides.

## 9. Release checklist — concrete failure tests

- [ ] Recompute plotted summaries from the stated inputs; check units, joins, denominators and exclusions.
- [ ] Match title strength and population/time scope to the evidence, including inconvenient observations.
- [ ] Verify baselines, scale transforms, missing-data gaps, colour limits and cross-panel comparability.
- [ ] Define intervals and thresholds; show any limitation that could change the decision in every register.
- [ ] Inspect exported output at delivery size: no clipped labels, collisions, tiny caveats or hidden series.
- [ ] Identify series without hue alone; check text/mark contrast and greyscale/CVD views where applicable.
- [ ] Provide alt text plus caption/data route; test local links and separate structural checks from human audits.
- [ ] Re-run code from a clean environment and record actual commands, versions and failures.
- [ ] Keep source, provenance and synthetic labels attached; log justified departures from defaults.

**Reusable rule format:** “For `<task/context>`, start with `<choice>` because `<benefit>`;
use `<alternative>` when `<failure condition>`; verify with `<observable check>`.” Extract that,
not “this chart looks better,” after each example.

## Lineage and evidence limits

Tufte motivates integrity and economy; Cleveland & McGill inform judgments of elementary encodings;
Bertin informs visual variables; Weissgerber and colleagues motivate showing distributions rather than
only summaries. Editorial graphics and Du Bois demonstrate purposeful composition, not universal recipes.
Research on decluttering/focus (Ajani, Xiong, Knaflic & Franconeri) motivates testing emphasis; it does not
establish that every chart needs a highlight and callout, or that greater reported trust means greater truth.

Useful source routes: [graphical perception](https://doi.org/10.1080/01621459.1984.10478080),
[beyond bar and line graphs](https://doi.org/10.1371/journal.pbio.1002128),
[WCAG contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html),
[non-text contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html).
These support parts of the framework; the register budgets, palette and page anatomy are local design
choices to validate in context, not scientific laws. [PLAN.md](PLAN.md) retains the original course roadmap.

## M8 — Integrated evidence tables

When readers need both comparative shape and exact lookup, reserve three shared-row lanes inside
one figure: identity, marks, and numerical account. A table inside a figure need not overlap its data.
Use the new M8 workshop in `visualization-curriculum/better_graphs.qmd` and `evidence_tables.py`:

- **Glance:** one contrast, denominator and interval; keep material uncertainty.
- **Read:** context rows plus a separately identified contrast, each with its own interval.
- **Study:** raw pairs or trial context alongside estimates; preserve independent-unit counts.
- Align numeric columns and precision; give units in headers; distinguish zero, missing and not-applicable.
- Generate marks, numeric cells and an accessible text table from the same records.
- Compare effects with a contrast, not with the presence/absence of significance in separate studies.
- Keep aggregates, subgroups, raw observations and contrasts in visibly different blocks.
- Never pool incompatible endpoints or treat shared-control contrasts as independent merely to complete a table.

The M8 historical examples cite R's sleep and Berkeley datasets; the multi-trial example is synthetic.
This is a composition pattern, not a statistical model or a claim of a new chart invention.
