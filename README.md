# Better Graphs

**A course and reusable matplotlib toolkit for charts that help readers reason about evidence.**

Start with the reader's task, inspect the data, choose an honest encoding, and then compose a readable
figure. The house palette, typography and page anatomy are justified defaults, not universal laws.
Uncertainty, provenance and accessible reading matter more than making a chart look unlike Python.

📖 **Read it online (the live "blog"):** <https://temataro.github.io/better-graphs/>

---

Same synthetic teaching data, same library — different layout and emphasis. Here is an RF-style
report before and after composition. These are **not real device measurements** or proof that one
aesthetic improves every task:

<table>
<tr><td align="center"><b>Before</b> — plain matplotlib defaults</td></tr>
<tr><td><img src="assets/rf-before.png" width="100%"></td></tr>
<tr><td align="center"><b>After</b> — the house style</td></tr>
<tr><td><img src="assets/rf-after.png" width="100%"></td></tr>
</table>

### More before / afters

Raw default on the left, the full treatment on the right — every lesson in the
curriculum ends with one of these.

<table>
<tr>
  <td align="center"><b>Before</b> · a trend</td>
  <td align="center"><b>After</b></td>
</tr>
<tr>
  <td><img src="assets/line-before.png" width="100%"></td>
  <td><img src="assets/line-after.png" width="100%"></td>
</tr>
<tr>
  <td align="center"><b>Before</b> · a seasonality matrix</td>
  <td align="center"><b>After</b></td>
</tr>
<tr>
  <td><img src="assets/heatmap-before.png" width="100%"></td>
  <td><img src="assets/heatmap-after.png" width="100%"></td>
</tr>
<tr>
  <td align="center"><b>Before</b> · grouped bars for a change</td>
  <td align="center"><b>After</b> · the right chart</td>
</tr>
<tr>
  <td><img src="assets/chartchoice-before.png" width="100%"></td>
  <td><img src="assets/chartchoice-after.png" width="100%"></td>
</tr>
</table>

## What this is, in plain terms

A short **course** plus a **reusable style kit**. The rules live in plain files an AI
agent reads *before* it draws — so you (or your agent) get deliberate, presentation-ready
figures with explicit reasoning and repeatable checks. Three files do the real work:

- **[`CLAUDE.md`](CLAUDE.md)** — the operating manual: the workflow (brief → inspect evidence → choose encoding → compose → validate → export).
- **[`VISUALIZATION_GUIDE.md`](VISUALIZATION_GUIDE.md)** — *which* chart to use, *who* it's for
  (the `glance`/`read`/`study` register), and *how hard to try* (the altitude ladder): a
  checklist, a *(data shape × task) → chart* lookup, a catalog, and the page anatomy + colour
  system.
- **[`visualization-curriculum/house_style.py`](visualization-curriculum/house_style.py)** —
  the one-import lever: `theme()`, `page()`, `finish()`, `save()`, and the CVD-simulated
  palette. Helpers preserve consistent styling; they cannot validate data or claims.

The course (`visualization-curriculum/better_graphs.qmd`, modules M0–M7) is the worked-example
companion — each module states one principle, builds one thing, and folds one rule back into
those three files.

## Make your agent draw like this

Pick whichever fits — they stack:

**1. Drop-in skill (Claude Code).** Copy it in, and any "make me a chart" request loads the
rules automatically:

```bash
cp -r .claude/skills/house-charts ~/.claude/skills/
```

**2. Global instruction.** Paste this into `~/.claude/CLAUDE.md` (or your `AGENTS.md`) so *any*
agent consults the design system first — no clone needed:

```markdown
## Before making any chart or data visualization
Consult the Better Graphs design system first and follow its workflow + hard rules:
- Operating manual: https://raw.githubusercontent.com/temataro/better-graphs/main/CLAUDE.md
- Chart-choice framework: https://raw.githubusercontent.com/temataro/better-graphs/main/VISUALIZATION_GUIDE.md
- The lever module: https://raw.githubusercontent.com/temataro/better-graphs/main/visualization-curriculum/house_style.py
State reader/task/context, inspect evidence, then choose chart and register (glance/read/study).
A title may be a finding or a question. Keep material uncertainty in every register, identify synthetic
data, and provide redundant series identities and text alternatives. Use the OO API and verify actual
exports. House colours, direct labels and callouts are defaults, not mandatory persuasion.
```

**3. Project pointer.** One line in a repo's `CLAUDE.md`:

> For any figure, follow the Better Graphs house style
> (https://github.com/temataro/better-graphs) — chart choice first, then its workflow.

## Run it locally

The plotting stack is uv-managed; the datasets are gitignored but regenerate on demand:

```bash
uv sync --locked                                     # plotting + jupyter stack
uv run python data/build_datasets.py                 # download + synthesize data/*.npz
uv run quarto preview visualization-curriculum/better_graphs.qmd   # live-reload course
uv run python assets/readme_figures.py               # regenerate the before/afters above
```

## Review, tests and publication boundary

```bash
uv run python scripts/check_house_palette.py
uv run python -m unittest discover -s tests -v
uv run quarto render visualization-curriculum/better_graphs.qmd
uv run python scripts/validate_review.py
# If installed: actionlint .github/workflows/publish.yml
```

[The workflow](.github/workflows/publish.yml) builds and validates branch pushes and pull requests,
then uploads a downloadable `curriculum-review` artifact. **Reviews do not deploy.** Only a push to
`main` or a manual run selected on `main` can upload the Pages artifact and deploy with job-scoped
write permissions. Review builds have only `contents: read`. Human review and any later merge remain
the user's responsibility; this branch does not change main or trigger publishing.

For this proposal, open [reviews/gpt-6-astra/index.html](reviews/gpt-6-astra/index.html) locally after
downloading/cloning (GitHub's source view is not an HTML host). It is the actual self-contained render,
not the live site. [The review record](reviews/gpt-6-astra/REVIEW.md) lists changes, checks and limitations.

## Why I'm building this

I'll also be making this repo _with_ an agent. My planned outputs are to have a
drop in 'skill' (if those things will still be around in a year), a general
AGENTS.md (or CLAUDE.md) file on my workspace's home directory that will direct
any agent to seek further advice from a tome of Python graphing wisdom,
flowcharts and inspiration before lifting a single finger to make a graph.

But more importantly, I want to teach myself how to do these in a pinch or just
direct stupider agents by giving guidance. So the `visualization-curriculum/` repo will include
notebooks (rendered from Quarto markdown documents) going through designs and
'modules' as if this was an actual course on better graphic design through
Matplotlib.

The `.ipynb` files are only going to be an artifact of my journey and not the
actual things I'll be working on as I'll use quarto live rendering to make an
html page with chapter sections as the curriculum I go through live.

By default, I'll assume these graphs are going to be shown on either a nice,
high resolution display over mediums like {ppt,pdf,png,jpg,gif}s or on a poster
you're proud to show off. This will affect the way we structure information,
the density of data we're comfortable showing, how closeby a stranger needs to
be from our graphs before understanding what they're about and optimizing for
post-presentation questions about how the hell you got your graphs to not even
look like Python anymore.

## AI attribution

The repository's original attribution named **Claude Opus 4.8** as a pair author under human direction.
That historical claim is preserved, not independently verified by this revision. This review's
independent interpretation uses the configured model label **gpt-6-astra**. Editorial approval remains
with the human author; no approval, merge or publication is implied by the branch or generated HTML.
