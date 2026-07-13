"""house_style — the Better Graphs lever: a figure is a small publication.

Three questions, asked in order, decide every figure:

1. **What am I saying?** — chart choice; answered by ``VISUALIZATION_GUIDE.md``.
2. **Who is reading?** — the *register*: ``glance`` (3 seconds, a slide or poster),
   ``read`` (30 seconds, a report or README), ``study`` (minutes, an appendix or
   datasheet). The register sets the type scale, density and annotation budget.
3. **How hard should I try?** — the *altitude*: A0 themed default (exploration),
   A1 composed catalog chart (the default for anything shared), A2 bespoke
   Artist drawing (only when the form itself carries the message and the
   audience pays for the craft). The test lives in ``VISUALIZATION_GUIDE.md``.

The visual identity: warm paper, warm ink, two typefaces (League Spartan for
display, Junction for working text), one violet accent leading a palette that
is *computed*, not eyeballed (``check_palette.py``), and an editorial page
anatomy — kicker, title, dek, plot, source line — built at figure level with
inch-true margins.

Minimal use::

    import house_style
    house_style.theme("read")
    fig, ax = house_style.page(
        kicker="Air travel · 1949–1960",
        title="The jet age took off before the jets did",
        dek="Passengers on international airlines, thousands per year.",
        source="Source: Box & Jenkins airline series",
    )
    ax.plot(year, passengers, color=house_style.ACCENT)
    house_style.finish(ax)
    house_style.save(fig, "jet_age")
"""
from __future__ import annotations

import textwrap
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
from matplotlib.textpath import TextPath
from matplotlib.ticker import FixedLocator, FixedFormatter, FuncFormatter, MaxNLocator

from check_palette import hex_to_lab  # palette math shared with the validator

STYLE = Path(__file__).with_name("minerva.mplstyle")
FONTS_DIR = Path(__file__).with_name("fonts")

# --------------------------------------------------------------------------- ink & paper
PAPER = "#FAF7F2"      # the page
INK = "#201D1A"        # primary text, hero numbers
MUTED = "#6B655D"      # secondary text: dek, axis labels, tick labels
FAINT = "#A39C91"      # tertiary text: source line, footnotes
HAIRLINE = "#E3DDD1"   # gridlines, rules
CONTEXT = "#B3AA9D"    # de-emphasised series (grey-for-context, warmed)
SMOKE = "#D8D2C6"      # faintest context (backgrounded small-multiple ghosts)

ACCENT = "#6400FF"     # the house violet — one series speaks
# Validated categorical order (check_palette.py: min pairwise dE 26.6 under
# protanopia/deuteranopia/tritanopia; contrast >= 3:1 on PAPER and on white).
# Assign in FIXED order; never cycle back for an 8th series — redesign instead.
SERIES = ["#6400FF", "#0FA077", "#C67D10", "#5C2340", "#142A6E", "#93330E"]
VIOLET, EMERALD, OCHRE, WINE, NAVY, RUST = SERIES

GOOD = EMERALD        # reserved status colours — never "series 7"
BAD = RUST

DISPLAY = "League Spartan"   # weights available: 400 / 600 / 700
BODY = "Junction"            # weights available: 300 / 500 / 700 (500 = regular)
# Glyph-level fallback (°, →, † …): pass the stack, not the bare family name.
DISPLAY_STACK = [DISPLAY, "DejaVu Sans"]
BODY_STACK = [BODY, "DejaVu Sans"]

_PT = 1 / 72          # inch per point


def _register_fonts() -> None:
    """Vendored League Spartan + Junction, registered idempotently on import."""
    if not FONTS_DIR.is_dir():
        return
    known = {f.fname for f in fm.fontManager.ttflist}
    for path in sorted(FONTS_DIR.glob("*.[ot]tf")):
        if str(path) not in known:
            fm.fontManager.addfont(str(path))


_register_fonts()

# The DejaVu fallback in the font stacks has no 500/600 faces, so findfont logs
# a WARNING per draw even though the primary face renders correctly. Keep
# notebook / quarto output clean; real failures still surface as ERROR.
import logging  # noqa: E402

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)


# --------------------------------------------------------------------------- registers
@dataclass(frozen=True)
class Register:
    """One reading contract: how far away the reader is and how long they stay."""
    name: str
    figsize: tuple[float, float]
    kicker: float          # pt sizes for the page anatomy
    title: float
    dek: float
    footer: float
    tick: float
    label: float
    linewidth: float
    nbins: int             # value-axis tick budget
    annotations: int       # rough budget of callouts before the figure is "busy"


REGISTERS = {
    # 3 seconds, 3 metres: a slide, a poster hero, an exec summary.
    "glance": Register("glance", (9.0, 5.0), 9.5, 19.0, 11.0, 8.0, 10.5, 11.0, 3.0, 4, 1),
    # 30 seconds, arm's length: a report figure, a README, a blog post.
    "read": Register("read", (7.2, 4.5), 8.0, 15.0, 10.0, 7.5, 9.0, 9.5, 2.2, 5, 3),
    # minutes, an expert: an appendix, a datasheet, a lab notebook.
    "study": Register("study", (9.6, 6.0), 8.0, 13.0, 9.5, 7.0, 8.0, 8.5, 1.7, 6, 6),
}

_current: Register = REGISTERS["read"]


def theme(register: str = "read") -> Register:
    """Apply the house style sheet, then the register's overrides. Call first."""
    global _current
    _current = REGISTERS[register]
    plt.style.use(str(STYLE))
    plt.rcParams.update({
        "figure.figsize": _current.figsize,
        "xtick.labelsize": _current.tick,
        "ytick.labelsize": _current.tick,
        "axes.labelsize": _current.label,
        "lines.linewidth": _current.linewidth,
    })
    return _current


def register() -> Register:
    """The active register (set by ``theme``)."""
    return _current


# --------------------------------------------------------------------------- text measurement
def _text_width_in(s: str, size: float, family: str = BODY, weight=500) -> float:
    """Width of a single-line string in inches, measured from the real font."""
    prop = fm.FontProperties(family=family, weight=weight)
    return TextPath((0, 0), s, size=size, prop=prop).get_extents().width / 72


def _wrap(s: str, size: float, width_in: float, family: str = BODY, weight=500) -> list[str]:
    """Greedy wrap to a physical width; explicit newlines are respected."""
    lines: list[str] = []
    for paragraph in s.split("\n"):
        words, line = paragraph.split(), ""
        for word in words:
            trial = f"{line} {word}".strip()
            if line and _text_width_in(trial, size, family, weight) > width_in:
                lines.append(line)
                line = word
            else:
                line = trial
        lines.append(line)
    return lines


def _track(s: str) -> str:
    """Letterspace a kicker with thin spaces (matplotlib has no tracking)."""
    return " ".join(s.upper())


# --------------------------------------------------------------------------- the page
def page(size=None, kicker=None, title=None, dek=None, source=None, note=None,
         mosaic=None, tab=True, margin_left=0.55, margin_right=0.30,
         margin_bottom=None, dek_highlights=None, hspace=0.55, wspace=0.35,
         height_ratios=None, width_ratios=None, gap_below_dek=0.16):
    """A figure with the editorial anatomy; margins are computed in inches.

    Returns ``(fig, ax)`` — or ``(fig, {label: ax})`` when ``mosaic`` is given
    (a ``subplot_mosaic`` string like ``"AB\\nCD"``).

    ``dek_highlights`` colour-keys ``<bracketed>`` words in the dek to series
    colours via highlight_text — the legend dissolves into the sentence, at
    body size, leaving the title to carry only the message.
    """
    reg = _current
    presets = {
        "single": reg.figsize, "wide": (9.8, 5.2), "slide": (10.0, 5.63),
        "square": (6.4, 6.4), "tall": (6.8, 7.8), "datasheet": (10.2, 7.8),
    }
    width, height = presets[size] if isinstance(size, str) else (size or reg.figsize)

    fig = plt.figure(figsize=(width, height), dpi=plt.rcParams["figure.dpi"])
    x0 = margin_left / width
    text_width_in = width - margin_left - margin_right

    # -- title block geometry: a downward cursor, inch-true --------------------
    texts = []      # deferred (x_frac, y_frac, s, style) — drawn after the axes exist
    y_in = height - 0.22
    if tab and (kicker or title):
        fig.add_artist(Rectangle((x0, (y_in - 0.02) / height), 0.30 / width, 0.045 / height,
                                 transform=fig.transFigure, facecolor=ACCENT, edgecolor="none"))
        y_in -= 0.14
    if kicker:
        texts.append((x0, y_in / height, _track(kicker),
                      dict(family=BODY_STACK, size=reg.kicker, weight=700, color=MUTED, va="top")))
        y_in -= reg.kicker * _PT + 0.09
    if title:
        for line in _wrap(title, reg.title, text_width_in, DISPLAY, 600):
            texts.append((x0, y_in / height, line,
                          dict(family=DISPLAY_STACK, size=reg.title, weight=600, color=INK, va="top")))
            y_in -= reg.title * _PT * 1.15
        y_in -= 0.06
    dek_lines = _wrap(dek, reg.dek, text_width_in, BODY, 500) if dek else []
    dek_y = y_in / height
    if dek and not dek_highlights:
        for line in dek_lines:
            texts.append((x0, y_in / height, line,
                          dict(family=BODY_STACK, size=reg.dek, color=MUTED, va="top")))
            y_in -= reg.dek * _PT * 1.38
    elif dek:
        y_in -= len(dek_lines) * reg.dek * _PT * 1.38
    top = (y_in - gap_below_dek) / height if (kicker or title or dek) else (height - 0.30) / height

    # -- footer ----------------------------------------------------------------
    if source:
        texts.append((x0, 0.13 / height, source,
                      dict(family=BODY_STACK, size=reg.footer, color=FAINT, va="bottom")))
    if note:
        texts.append((1 - margin_right / width, 0.13 / height, note,
                      dict(family=BODY_STACK, size=reg.footer, color=FAINT, va="bottom", ha="right")))
    if margin_bottom is None:
        # footer line + clearance for x tick labels (and an unhurried baseline)
        margin_bottom = (0.34 if (source or note) else 0.14) + reg.tick * _PT + 0.16
    bottom = margin_bottom / height

    gs_kw = dict(left=x0, right=1 - margin_right / width, top=top, bottom=bottom,
                 hspace=hspace, wspace=wspace)
    if height_ratios:
        gs_kw["height_ratios"] = height_ratios
    if width_ratios:
        gs_kw["width_ratios"] = width_ratios

    # axes first (so nothing downstream conjures a default axes), text second
    if mosaic:
        axes = fig.subplot_mosaic(mosaic, gridspec_kw=gs_kw)
        first_ax = next(iter(axes.values()))
    else:
        gs = fig.add_gridspec(1, 1, **{k: v for k, v in gs_kw.items()
                                       if k not in ("hspace", "wspace")})
        axes = fig.add_subplot(gs[0])
        first_ax = axes

    for x_frac, y_frac, s, style in texts:
        fig.text(x_frac, y_frac, s, **style)
    if dek and dek_highlights:
        from highlight_text import fig_text
        fig_text(x=x0, y=dek_y, s="\n".join(dek_lines), fig=fig, ax=first_ax,
                 highlight_textprops=dek_highlights, family=BODY_STACK,
                 fontsize=reg.dek, color=MUTED, va="top", ha="left",
                 annotationbbox_kw={"frameon": False})
    return fig, axes


# --------------------------------------------------------------------------- polish
def finish(ax, grid="y", nbins=None, zero=False, on_grid=None, bound_spine=True):
    """The ordered polish pass for one axes.

    Value-axis tick budget (``MaxNLocator``), hairline grid on that axis only,
    no y tick marks, bottom rule as the single axis line, ending at the last
    tick (``bound_spine``). In the editorial registers (glance/read) the y tick
    labels sit *on* their gridline (``on_grid=True``, the Economist/FT move);
    the study register keeps them classically centred. ``grid=None`` clears the
    grid; ``grid="xy"`` (study) allows both. ``zero=True`` pins the value axis
    to include 0.

    Polish is a *precondition*, not the finish line: a shipped figure still
    needs its accent series and one interpretive annotation (focused beats
    merely decluttered — Ajani et al.).
    """
    nbins = nbins or _current.nbins
    ax.grid(False)
    if grid in ("y", "xy", "x"):
        for axis_name in grid:
            getattr(ax, f"{axis_name}axis").set_major_locator(MaxNLocator(nbins=nbins))
        ax.grid(axis="both" if grid == "xy" else grid, visible=True)
        ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    if zero:
        lo, hi = ax.get_ylim()
        ax.set_ylim(min(lo, 0), max(hi, 0))
    if on_grid is None:
        on_grid = _current.name in ("glance", "read") and grid == "y"
    if on_grid:
        ax.tick_params(axis="y", pad=2)
        for label in ax.get_yticklabels():
            label.set_va("bottom")
            # the label punches through its own gridline, not the reverse
            label.set_path_effects([pe.withStroke(linewidth=2.5, foreground=PAPER)])
    if bound_spine and ax.spines["bottom"].get_visible():
        # The baseline spans the data (clipped to the view), stretched to any
        # tick that would otherwise float beyond its end.
        data_x0, data_x1 = ax.dataLim.x0, ax.dataLim.x1
        if np.isfinite(data_x0) and np.isfinite(data_x1) and data_x1 > data_x0:
            lo, hi = ax.get_xlim()
            ticks = [t for t in ax.xaxis.get_ticklocs() if lo <= t <= hi]
            x0 = min([max(lo, data_x0)] + ticks)
            x1 = max([min(hi, data_x1)] + ticks)
            ax.spines["bottom"].set_bounds(x0, x1)
    return ax


def ylabel_above(ax, text, dy=0.02):
    """A horizontal y-axis label above the axis (Doumont / Observable Plot) —
    the replacement for the rotated ylabel in the study register."""
    ax.text(0, 1 + dy, text, transform=ax.transAxes, family=BODY_STACK, weight=500,
            size=_current.label, color=MUTED, va="bottom", ha="left")
    return ax


def _minus(s: str) -> str:
    """Typeset negatives with a true minus (U+2212), matching matplotlib's own ticks."""
    return s.replace("-", "−")


_UNITS = {
    "count": lambda v: _minus(f"{v:,.10g}"),
    "si": lambda v: _minus(_fmt_si(v)),
    "pct": lambda v: _minus(f"{v:g}%"),
    "db": lambda v: _minus(f"{v:g} dB"),
    "dbm": lambda v: _minus(f"{v:g} dBm"),
    "ghz": lambda v: _minus(f"{v:g} GHz"),
    "mm": lambda v: _minus(f"{v:g} mm"),
    "years": lambda v: _minus(f"{v:.0f}"),
    "usd": lambda v: _minus(f"${_fmt_si(v)}"),
}


def _fmt_si(v: float) -> str:
    for cut, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "k")):
        if abs(v) >= cut:
            x = v / cut
            return f"{x:,.1f}{suffix}".replace(".0" + suffix, suffix)
    return f"{v:g}"


def units(ax, axis="y", kind="count", top_only=True):
    """Unit-aware tick labels; by default the unit is spelt out on the top
    tick only ("20 dB" up top, bare numbers below — the FT convention).

    Call *after* ``finish()`` and after limits are final: with ``top_only``
    the current tick positions are frozen (FixedLocator) so the labelled tick
    can't silently move.
    """
    fmt = _UNITS[kind]
    ax_obj = ax.yaxis if axis == "y" else ax.xaxis
    if not top_only:
        ax_obj.set_major_formatter(FuncFormatter(lambda v, _: fmt(v)))
        return ax
    lo, hi = (ax.get_ylim() if axis == "y" else ax.get_xlim())
    ticks = [t for t in ax_obj.get_ticklocs() if lo <= t <= hi]
    bare = _UNITS["count"] if kind in ("count", "si", "usd") else (lambda v: _minus(f"{v:g}"))
    labels = [fmt(t) if i == len(ticks) - 1 else bare(t) for i, t in enumerate(ticks)]
    ax_obj.set_major_locator(FixedLocator(ticks))
    ax_obj.set_major_formatter(FixedFormatter(labels))
    return ax


# --------------------------------------------------------------------------- direct labels
def label_end(ax, lines_and_labels, pad_pt=7, size=None, weight=700, min_gap_pt=None):
    """Direct labels at the right edge, one per series — the legend, dissolved.

    ``lines_and_labels``: iterable of ``(Line2D, str)`` (or ``(x, y, str, color)``
    tuples). Labels sit just outside the axes (reserve ``margin_right``!) at the
    final data value, nudged apart in display space when they would collide.
    """
    reg = _current
    size = size or reg.tick
    min_gap = (min_gap_pt or size * 1.25) * _PT * ax.figure.dpi  # px
    entries = []
    for item in lines_and_labels:
        if len(item) == 2:
            line, text = item
            x, y = line.get_xdata(), line.get_ydata()
            ok = np.isfinite(np.asarray(y, float))
            xe, ye = np.asarray(x)[ok][-1], np.asarray(y, float)[ok][-1]
            color = line.get_color()
        else:
            xe, ye, text, color = item
        entries.append([xe, ye, text, color])

    # collision pass, top-down in display space; the nudge becomes a point offset
    entries.sort(key=lambda e: -ax.transData.transform((0, e[1]))[1])
    prev = None
    for xe, ye, text, color in entries:
        y_px = ax.transData.transform((0, ye))[1]
        if prev is not None and prev - y_px < min_gap:
            y_px = prev - min_gap
        prev = y_px
        dy_pt = (y_px - ax.transData.transform((0, ye))[1]) / ax.figure.dpi * 72
        ax.annotate(text, xy=(xe, ye), xytext=(pad_pt, dy_pt),
                    textcoords="offset points", va="center", ha="left",
                    family=BODY_STACK, weight=weight, size=size, color=color,
                    annotation_clip=False)
    return ax


def mark(ax, x, y, text, dx=10, dy=10, color=INK, size=None, dot=True, ha=None):
    """One annotated point: a dot, a short leader, a haloed label."""
    size = size or _current.tick
    if dot:
        ax.scatter([x], [y], s=26, color=color, zorder=5, clip_on=False)
    ha = ha or ("left" if dx >= 0 else "right")
    ax.annotate(text, xy=(x, y), xytext=(dx, dy), textcoords="offset points",
                family=BODY_STACK, size=size, color=color, ha=ha, va="center",
                path_effects=[pe.withStroke(linewidth=2.8, foreground=PAPER)],
                arrowprops=dict(arrowstyle="-", color=FAINT, lw=0.8,
                                connectionstyle="arc3,rad=0.18",
                                shrinkA=4, shrinkB=4) if (abs(dx) + abs(dy)) > 22 else None,
                zorder=6)
    return ax


def spec_band(ax, limit, side="above", label=None, color=BAD, axis="y"):
    """A spec limit: dashed line + a whisper of shade over the failing side."""
    span = ax.axhspan if axis == "y" else ax.axvspan
    line = ax.axhline if axis == "y" else ax.axvline
    lo, hi = (ax.get_ylim() if axis == "y" else ax.get_xlim())
    fail = (limit, max(hi, limit)) if side == "above" else (min(lo, limit), limit)
    span(*fail, color=color, alpha=0.055, zorder=0, lw=0)
    line(limit, ls=(0, (5, 3)), lw=1.0, color=color, alpha=0.8, zorder=1)
    if label:
        x = ax.get_xlim()[1] if axis == "y" else limit
        y = limit if axis == "y" else ax.get_ylim()[1]
        va = "bottom" if side == "above" else "top"
        offset = 3 if side == "above" else -3
        ax.annotate(label, xy=(x, y), xytext=(0, offset), textcoords="offset points",
                    ha="right", va=va, family=BODY_STACK, size=_current.footer + 0.5,
                    color=color, annotation_clip=False)
    return ax


def stat(ax, value, label, sublabel=None, color=INK):
    """A hero number in a dead axes — the datasheet stat tile."""
    ax.set_axis_off()
    ax.text(0, 0.62, value, family=DISPLAY_STACK, size=_current.title + 3, weight=600,
            color=color, transform=ax.transAxes, va="baseline")
    ax.text(0, 0.30, label, family=BODY_STACK, size=_current.dek - 0.5, color=MUTED,
            transform=ax.transAxes, va="baseline")
    if sublabel:
        ax.text(0, 0.06, sublabel, family=BODY_STACK, size=_current.footer,
                color=FAINT, transform=ax.transAxes, va="baseline")
    return ax


def panel_title(ax, text, pad=6):
    """A quiet per-panel title for mosaics (the page title does the talking)."""
    ax.set_title(text, loc="left", family=BODY_STACK, weight=700,
                 size=_current.label + 0.5, color=INK, pad=pad)
    return ax


# --------------------------------------------------------------------------- colour ramps
def _lab_arclength_equalize(cmap, n=256):
    """Re-parameterise a colormap so equal steps mean equal Lab distance."""
    samples = cmap(np.linspace(0, 1, n))[:, :3]
    hexes = ["#{:02X}{:02X}{:02X}".format(*(np.round(c * 255).astype(int))) for c in samples]
    labs = np.array([hex_to_lab(h) for h in hexes])
    arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(labs, axis=0), axis=1))])
    arc /= arc[-1]
    even = np.interp(np.linspace(0, 1, n), arc, np.linspace(0, 1, n))
    return LinearSegmentedColormap.from_list(cmap.name, cmap(even), N=n)


def _build_cmaps():
    # One hue, honestly spaced: lavender-white to near-black violet. The start
    # is cool so it separates from the warm paper by hue, and L* falls
    # monotonically 93 -> 12 (verified in Lab; equalised below).
    seq = LinearSegmentedColormap.from_list(
        "house_seq",
        ["#EFEAF6", "#D3BEEF", "#A87DE8", "#7A3AE0", "#5303C8", "#2E0060"])
    div = LinearSegmentedColormap.from_list(
        "house_div",
        ["#93330E", "#C58A64", "#EEE5D9", "#A98BDB", "#6400FF"])
    seq = _lab_arclength_equalize(seq)
    div = _lab_arclength_equalize(div)
    for cmap in (seq, div, seq.reversed("house_seq_r"), div.reversed("house_div_r")):
        try:
            plt.colormaps.register(cmap, force=True)
        except Exception:
            pass
    return seq, div


SEQUENTIAL, DIVERGING = _build_cmaps()


def diverging_norm(values, center=0.0):
    """Symmetric TwoSlopeNorm — equal colour reach on both sides of centre."""
    from matplotlib.colors import TwoSlopeNorm
    span = max(abs(np.nanmin(values) - center), abs(np.nanmax(values) - center))
    return TwoSlopeNorm(vmin=center - span, vcenter=center, vmax=center + span)


# --------------------------------------------------------------------------- artisan layer
def gradient_fill(ax, x, y, color=ACCENT, alpha_top=0.18, to=0.0):
    """A fading fill under a line — an RGBA ramp clipped to the fill path."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    rgb = tuple(int(color.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
    ramp = np.ones((220, 1, 4))
    ramp[..., :3] = rgb
    ramp[..., 3] = np.linspace(alpha_top, 0.0, 220).reshape(-1, 1)
    img = ax.imshow(ramp, extent=(np.nanmin(x), np.nanmax(x), to, np.nanmax(y)),
                    aspect="auto", origin="upper", interpolation="bicubic", zorder=1)
    fill = ax.fill_between(x, y, to, color="none", zorder=1)
    img.set_clip_path(fill.get_paths()[0], transform=ax.transData)
    fill.remove()
    return img


def halo(artist_text, lw=2.8, color=PAPER):
    """Make any text survive a busy background (paper-coloured stroke)."""
    artist_text.set_path_effects([pe.withStroke(linewidth=lw, foreground=color)])
    return artist_text


# --------------------------------------------------------------------------- export
def save(fig, stem, outdir="../outputs", dpi=200, formats=("svg", "pdf", "png")):
    """Vector + web export. No ``bbox_inches='tight'``: the page's margins are
    deliberate, and tight-cropping would shave them off asymmetrically."""
    out_dir = Path(outdir)
    out_dir.mkdir(parents=True, exist_ok=True)
    export_rc = {"pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "path"}
    written = []
    with plt.rc_context(export_rc):
        for ext in formats:
            path = out_dir / f"{stem}.{ext}"
            fig.savefig(path, dpi=dpi)
            written.append(path)
    return written
