"""Witness — evidence-aware composition on native Matplotlib objects.

Witness treats a shared figure as an argument a reader can interrogate.  It is
deliberately not a data layer and not a chart grammar: callers keep explicit
NumPy transformations and ordinary ``Figure`` / ``Axes`` / ``Artist`` handles.
Witness adds a claim contract, semantic Artist roles, evidence-oriented layout,
structural audits, and accessible exports with a machine-readable receipt.

Minimal use::

    import witness

    claim = witness.Claim(
        statement="Annual passenger total reached 3.76× its 1949 level",
        measure="sum of twelve monthly counts",
        comparison="1960 divided by 1949",
        scope="calendar years 1949–1960",
        source="Box & Jenkins airline series",
        method="NumPy sum by year",
        uncertainty="Historical series; no inferential interval is claimed",
        caveat="The series does not establish why volume increased.",
        alt="A line rises from 1.52 million in 1949 to 5.71 million in 1960.",
    )
    witness.theme(purpose="explain", medium="html")
    fig, ax = witness.frame(claim)
    line = ax.plot(year, passengers)[0]
    witness.tag(line, role="observation", label="reported annual total")
    witness.finish(fig, ax)
    witness.save(fig, "annual_passengers")
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
import sys
import textwrap
from typing import Any, Literal

import matplotlib
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.collections import Collection, PolyCollection
from matplotlib.colors import to_rgba
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.image import AxesImage
from matplotlib.lines import Line2D
from matplotlib.text import Annotation, Text
from matplotlib.ticker import FixedFormatter, FixedLocator, FuncFormatter, MaxNLocator
from matplotlib.transforms import blended_transform_factory
import numpy as np

from witness_audit import (
    AuditFinding,
    AuditReport,
    CATEGORICAL,
    FAINT,
    GRID,
    INK,
    MUTED,
    SURFACE,
    PaletteReport,
    audit_chosen_light_palette,
    audit_required_fields,
    audit_used_colors,
    merge_reports,
)
from witness_export import FontFace, inspect_svg, make_accessible_svg, write_html


STYLE = Path(__file__).with_name("witness.mplstyle")
FONTS_DIR = Path(__file__).with_name("fonts") / "witness"
OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs"

# F2P2 — selected after a controlled typography × surface comparison.
EVERGREEN, BRICK, VIOLET = CATEGORICAL
EVIDENCE = EVERGREEN
COMPARATOR = VIOLET
EXCEPTION = BRICK
CONTEXT = "#A59D8F"
INTERVAL = "#C9DDD4"
MODEL = "#315E59"
DECISION = "#7A5B00"

DISPLAY_FAMILY = "IBM Plex Serif"
BODY_FAMILY = "IBM Plex Sans"
MONO_FAMILY = "IBM Plex Mono"
DISPLAY_STACK = [DISPLAY_FAMILY, "STIXGeneral", "DejaVu Serif"]
BODY_STACK = [BODY_FAMILY, "DejaVu Sans"]
MONO_STACK = [MONO_FAMILY, "DejaVu Sans Mono"]

DISPLAY = FontProperties(family=DISPLAY_FAMILY, weight=600)
BODY = FontProperties(family=BODY_FAMILY, weight=400)
BODY_SEMIBOLD = FontProperties(family=BODY_FAMILY, weight=600)
BODY_ITALIC = FontProperties(family=BODY_FAMILY, weight=400, style="italic")
MONO = FontProperties(family=MONO_FAMILY, weight=500)

Purpose = Literal["decide", "explain", "inspect"]
Medium = Literal["html", "slide", "print"]

ROLES = {
    "observation",
    "estimate",
    "model",
    "uncertainty",
    "comparator",
    "reference",
    "context",
    "exception",
    "decision",
}

_REDUNDANT_CHANNEL_PATTERN = re.compile(
    r"\b(marker|shape|circle|circular|diamond|square|triangle|line|stroke|solid|"
    r"dash|hatch|edge|outline|position|row|panel|label|text|value|leader|"
    r"endpoint|sample|size|length)\w*\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class Claim:
    """The semantic contract carried by a shared Witness figure."""

    statement: str
    measure: str
    comparison: str
    scope: str
    source: str
    method: str | None = None
    uncertainty: str | None = None
    caveat: str | None = None
    alt: str | None = None
    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ThemeState:
    purpose: Purpose
    medium: Medium
    figsize: tuple[float, float]
    plot_rect: tuple[float, float, float, float]
    title_size: float
    body_size: float
    tick_size: float
    footer_size: float
    linewidth: float
    marker_size: float
    nbins: int
    annotation_budget: int


@dataclass(frozen=True, slots=True)
class ExportBundle:
    """Paths and audit returned by :func:`save`."""

    paths: Mapping[str, Path]
    receipt: Path
    audit: AuditReport

    def __getitem__(self, format_name: str) -> Path:
        return self.paths[format_name]


_MEDIA = {
    "html": {
        "figsize": (8.4, 5.4),
        "plot_rect": (0.105, 0.205, 0.84, 0.505),
        "title_size": 16.0,
        "body_size": 9.5,
        "tick_size": 8.5,
        "footer_size": 7.5,
        "linewidth": 2.0,
        "marker_size": 28.0,
    },
    "slide": {
        "figsize": (13.333, 7.5),
        "plot_rect": (0.085, 0.165, 0.865, 0.54),
        "title_size": 24.0,
        "body_size": 13.0,
        "tick_size": 11.5,
        "footer_size": 9.0,
        "linewidth": 3.0,
        "marker_size": 52.0,
    },
    "print": {
        "figsize": (7.1, 4.8),
        "plot_rect": (0.115, 0.215, 0.835, 0.49),
        "title_size": 13.0,
        "body_size": 8.5,
        "tick_size": 7.5,
        "footer_size": 6.8,
        "linewidth": 1.5,
        "marker_size": 22.0,
    },
}

_PURPOSE = {
    "decide": {"nbins": 4, "annotations": 2},
    "explain": {"nbins": 5, "annotations": 4},
    "inspect": {"nbins": 6, "annotations": 8},
}

_current: ThemeState | None = None


def _register_fonts() -> None:
    """Register vendored IBM Plex TTF files idempotently."""

    if not FONTS_DIR.is_dir():
        return
    known = {entry.fname for entry in fm.fontManager.ttflist}
    for path in sorted(FONTS_DIR.glob("*.ttf")):
        if str(path) not in known:
            fm.fontManager.addfont(str(path))


_register_fonts()


def theme(purpose: Purpose = "explain", medium: Medium = "html") -> ThemeState:
    """Apply Witness and select independent purpose/medium contracts.

    Call this as the first plotting line.  Purpose controls which evidence the
    reader must be able to inspect; medium controls physical composition.
    """

    global _current
    if purpose not in _PURPOSE:
        raise ValueError(f"unknown purpose {purpose!r}; choose {', '.join(_PURPOSE)}")
    if medium not in _MEDIA:
        raise ValueError(f"unknown medium {medium!r}; choose {', '.join(_MEDIA)}")

    plt.style.use(str(STYLE))
    medium_values = _MEDIA[medium]
    purpose_values = _PURPOSE[purpose]
    _current = ThemeState(
        purpose=purpose,
        medium=medium,
        figsize=medium_values["figsize"],
        plot_rect=medium_values["plot_rect"],
        title_size=medium_values["title_size"],
        body_size=medium_values["body_size"],
        tick_size=medium_values["tick_size"],
        footer_size=medium_values["footer_size"],
        linewidth=medium_values["linewidth"],
        marker_size=medium_values["marker_size"],
        nbins=purpose_values["nbins"],
        annotation_budget=purpose_values["annotations"],
    )
    plt.rcParams.update(
        {
            "figure.figsize": _current.figsize,
            "font.size": _current.body_size,
            "xtick.labelsize": _current.tick_size,
            "ytick.labelsize": _current.tick_size,
            "lines.linewidth": _current.linewidth,
        }
    )
    return _current


def _root_figure(artist: Artist) -> Figure | None:
    """Return an Artist's root Figure without requiring Matplotlib 3.10."""

    candidate = artist.get_figure()
    seen: set[int] = set()
    while candidate is not None and id(candidate) not in seen:
        seen.add(id(candidate))
        if isinstance(candidate, Figure):
            return candidate
        parent = getattr(candidate, "figure", None)
        if parent is candidate:
            break
        candidate = parent
    return None


def _state(source: Figure | Axes | Artist | None = None) -> ThemeState:
    if source is not None:
        if isinstance(source, Figure):
            fig = source
        elif isinstance(source, Axes):
            fig = source.figure
        elif isinstance(source, Artist):
            fig = _root_figure(source)
        else:
            raise TypeError("theme state source must be a Figure, Axes, or Artist")
        state = getattr(fig, "_witness_theme", None)
        if state is not None:
            return state
    if _current is None:
        raise RuntimeError("call witness.theme(purpose=..., medium=...) before frame()")
    return _current


def _new_gid(fig: Figure, stem: str) -> str:
    fig._witness_gid_serial += 1
    return f"witness-{_slug(stem)}-{fig._witness_gid_serial:03d}"


def frame(
    claim: Claim,
    *,
    mosaic: Any | None = None,
    figsize: tuple[float, float] | None = None,
    gridspec_kw: Mapping[str, Any] | None = None,
) -> tuple[Figure, Axes | dict[str, Axes]]:
    """Create an evidence frame and return ordinary Matplotlib handles."""

    if not isinstance(claim, Claim):
        raise TypeError("frame() requires a witness.Claim")
    state = _state()
    fig = plt.figure(figsize=figsize or state.figsize, facecolor=SURFACE)
    left, bottom, width, height = state.plot_rect

    if mosaic is None:
        axes: Axes | dict[str, Axes] = fig.add_axes((left, bottom, width, height))
    else:
        default_gridspec = {
            "left": left,
            "right": left + width,
            "bottom": bottom,
            "top": bottom + height,
            "hspace": 0.30,
            "wspace": 0.24,
        }
        default_gridspec.update(dict(gridspec_kw or {}))
        axes = fig.subplot_mosaic(mosaic, gridspec_kw=default_gridspec)

    fig._witness_claim = claim
    fig._witness_theme = state
    fig._witness_registry = []
    fig._witness_notes = []
    fig._witness_gid_serial = 0
    fig._witness_finished_axes = set()
    fig._witness_finished = False

    _draw_argument_header(fig, claim, state)
    return fig, axes


def _draw_argument_header(fig: Figure, claim: Claim, state: ThemeState) -> None:
    width = 74 if state.medium == "slide" else 58
    title = textwrap.fill(claim.statement.strip(), width=width)
    ledger = f"{state.purpose.upper()}  /  {claim.measure.upper()}"
    warrant = f"COMPARATOR  {claim.comparison}   ·   SCOPE  {claim.scope}"

    fig.text(
        state.plot_rect[0],
        0.945,
        ledger,
        fontproperties=MONO,
        fontsize=state.footer_size,
        color=MUTED,
        va="top",
    )
    fig.text(
        state.plot_rect[0],
        0.895,
        title,
        fontproperties=DISPLAY,
        fontsize=state.title_size,
        color=INK,
        va="top",
        linespacing=0.94,
    )
    fig.text(
        state.plot_rect[0],
        0.785,
        textwrap.fill(warrant, width=112 if state.medium == "slide" else 90),
        fontproperties=BODY,
        fontsize=state.body_size - 0.5,
        color=MUTED,
        va="top",
    )
    header_rule = Line2D(
        [state.plot_rect[0], state.plot_rect[0] + state.plot_rect[2]],
        [state.plot_rect[1] + state.plot_rect[3] + 0.015] * 2,
        transform=fig.transFigure,
        color=GRID,
        lw=0.8,
    )
    header_rule.set_gid(_new_gid(fig, "structure-header-rule"))
    fig.add_artist(header_rule)

    fig.text(
        state.plot_rect[0],
        0.075 if state.medium != "slide" else 0.065,
        f"SOURCE  {claim.source}",
        fontproperties=BODY,
        fontsize=state.footer_size,
        color=MUTED,
        va="bottom",
    )
    method_parts = [part for part in (claim.method, claim.uncertainty) if part]
    if method_parts:
        fig.text(
            state.plot_rect[0],
            0.045 if state.medium != "slide" else 0.035,
            "METHOD  " + "  ·  ".join(method_parts),
            fontproperties=BODY,
            fontsize=state.footer_size,
            color=MUTED,
            va="bottom",
        )
    if claim.caveat:
        fig.text(
            state.plot_rect[0],
            0.115 if state.medium != "slide" else 0.105,
            textwrap.fill(
                "BOUNDARY  " + claim.caveat,
                width=116 if state.medium == "slide" else 92,
            ),
            fontproperties=BODY_ITALIC,
            fontsize=state.footer_size,
            color=MUTED,
            ha="left",
            va="bottom",
        )


def tag(
    artist: Artist,
    role: str,
    *,
    label: str | None = None,
    redundant: str | None = None,
) -> Artist:
    """Attach an evidence role and stable SVG id; return the same Artist."""

    if role not in ROLES:
        raise ValueError(f"unknown evidence role {role!r}; choose {', '.join(sorted(ROLES))}")
    if not isinstance(artist, Artist):
        raise TypeError("tag() requires a Matplotlib Artist")
    if redundant and not _REDUNDANT_CHANNEL_PATTERN.search(redundant):
        raise ValueError(
            "redundant must name a non-color channel such as marker, dash, "
            "hatch, position, outline, or direct label"
        )
    fig = _root_figure(artist)
    if fig is None or not hasattr(fig, "_witness_registry"):
        raise ValueError("the Artist must belong to a figure created by witness.frame()")

    registry: list[Artist] = fig._witness_registry
    existing_role = getattr(artist, "_witness_role", None)
    if artist in registry:
        if existing_role != role:
            raise ValueError(
                f"Artist is already tagged as {existing_role!r}; roles cannot be changed"
            )
        if label is not None:
            artist._witness_label = label
            if hasattr(artist, "set_label"):
                artist.set_label(label)
        if redundant is not None:
            artist._witness_redundant = redundant
        return artist

    artist.set_gid(_new_gid(fig, role))
    artist._witness_role = role
    artist._witness_label = label or artist.get_label()
    artist._witness_redundant = redundant
    if label and hasattr(artist, "set_label"):
        artist.set_label(label)
    registry.append(artist)
    return artist


def interval(
    ax: Axes,
    x: Sequence[float],
    low: Sequence[float],
    high: Sequence[float],
    *,
    kind: str,
    label: str | None = None,
    color: str = EVIDENCE,
    alpha: float = 0.20,
    hatch: str | None = None,
    edge: bool = True,
    **kwargs,
) -> PolyCollection:
    """Draw a named uncertainty band and return its native PolyCollection."""

    if not kind or not kind.strip():
        raise ValueError("interval() requires explicit semantics, e.g. kind='95% CI'")
    state = _state(ax)
    band = ax.fill_between(
        x,
        low,
        high,
        facecolor=to_rgba(color, alpha),
        edgecolor=color if edge else "none",
        linewidth=max(0.65, state.linewidth * 0.32) if edge else 0,
        hatch=hatch,
        zorder=1,
        **kwargs,
    )
    band._witness_interval_kind = kind.strip()
    tag(
        band,
        "uncertainty",
        label=label or kind.strip(),
        redundant="edge" if edge else ("hatch" if hatch else None),
    )
    return band


def reference(
    ax: Axes,
    value: float,
    *,
    axis: Literal["x", "y"] = "y",
    label: str,
    source: str | None = None,
    color: str = COMPARATOR,
    linestyle: tuple[int, tuple[int, ...]] | str = (0, (5, 3)),
) -> Line2D:
    """Draw and directly label a reference rule in mixed coordinates."""

    if not label.strip():
        raise ValueError("reference() requires a human-readable label")
    state = _state(ax)
    rule_width = max(1.2, state.linewidth * 0.60)
    if axis == "y":
        line = ax.axhline(value, color=color, lw=rule_width, ls=linestyle, zorder=1)
        transform = blended_transform_factory(ax.transAxes, ax.transData)
        text = ax.text(
            1.0,
            value,
            label,
            transform=transform,
            ha="right",
            va="bottom",
            color=color,
            fontproperties=BODY_SEMIBOLD,
            fontsize=state.tick_size,
            bbox={"facecolor": SURFACE, "edgecolor": "none", "pad": 1.5},
        )
    elif axis == "x":
        line = ax.axvline(value, color=color, lw=rule_width, ls=linestyle, zorder=1)
        transform = blended_transform_factory(ax.transData, ax.transAxes)
        text = ax.text(
            value,
            1.0,
            label,
            transform=transform,
            ha="left",
            va="top",
            rotation=90,
            color=color,
            fontproperties=BODY_SEMIBOLD,
            fontsize=state.tick_size,
            bbox={"facecolor": SURFACE, "edgecolor": "none", "pad": 1.5},
        )
    else:
        raise ValueError("axis must be 'x' or 'y'")
    line._witness_reference_source = source
    tag(line, "reference", label=label, redundant="dash + direct label")
    text.set_gid(f"{line.get_gid()}-label")
    return line


def bracket(
    ax: Axes,
    start: float,
    end: float,
    level: float,
    text: str,
    *,
    color: str = COMPARATOR,
    text_offset: float = 6,
) -> Artist:
    """Add a comparison bracket with data endpoints and point-offset text."""

    state = _state(ax)
    annotation = ax.annotate(
        "",
        xy=(start, level),
        xytext=(end, level),
        arrowprops={
            "arrowstyle": "|-|",
            "color": color,
            "lw": max(1.2, state.linewidth * 0.60),
        },
        annotation_clip=False,
    )
    tag(annotation, "comparator", label=text, redundant="position + label")
    label = ax.annotate(
        text,
        xy=((start + end) / 2, level),
        xytext=(0, text_offset),
        textcoords="offset points",
        ha="center",
        va="bottom",
        color=color,
        fontproperties=BODY_SEMIBOLD,
        fontsize=state.tick_size,
        annotation_clip=False,
    )
    label.set_gid(f"{annotation.get_gid()}-label")
    return annotation


def margin_note(
    ax: Axes,
    x: float,
    y: float,
    text: str,
    *,
    role: str = "exception",
    color: str | None = None,
    side: Literal["right", "left"] = "right",
) -> Artist:
    """Place a renderer-resolved note in the outer evidence gutter."""

    note_color = color or (EXCEPTION if role == "exception" else INK)
    x_axes = 1.025 if side == "right" else -0.025
    horizontal = "left" if side == "right" else "right"
    mixed = blended_transform_factory(ax.transAxes, ax.transData)
    note = ax.annotate(
        text,
        xy=(x, y),
        xycoords=ax.transData,
        xytext=(x_axes, y),
        textcoords=mixed,
        ha=horizontal,
        va="center",
        color=note_color,
        fontproperties=BODY,
        fontsize=_state(ax).tick_size,
        arrowprops={
            "arrowstyle": "-",
            "color": note_color,
            "lw": max(0.8, _state(ax).linewidth * 0.30),
            "shrinkA": 4,
            "shrinkB": 4,
        },
        annotation_clip=False,
        path_effects=[pe.withStroke(linewidth=2.4, foreground=SURFACE)],
        zorder=7,
    )
    note._witness_note_y = float(y)
    note._witness_note_side = side
    tag(note, role, label=text, redundant="leader + text")
    ax.figure._witness_notes.append(note)
    return note


def linked_detail(
    ax: Axes,
    *,
    bounds: tuple[float, float, float, float],
    xlim: tuple[float, float],
    ylim: tuple[float, float],
    label: str | None = None,
) -> Axes:
    """Create a linked inset lens; return the native inset Axes."""

    inset = ax.inset_axes(bounds)
    inset.set_xlim(*xlim)
    inset.set_ylim(*ylim)
    inset.set_facecolor(SURFACE)
    state = _state(ax)
    inset.tick_params(labelsize=max(state.tick_size - 1.5, 6), length=0)
    for side in ("top", "right"):
        inset.spines[side].set_visible(False)
    indicator = ax.indicate_inset_zoom(
        inset,
        edgecolor=COMPARATOR,
        alpha=0.75,
    )
    if hasattr(indicator, "rectangle"):
        indicator.set_gid(_new_gid(ax.figure, "linked-detail-indicator"))
        rectangle = indicator.rectangle
        connectors = indicator.connectors or ()
    else:  # Matplotlib 3.8–3.9 returned ``(rectangle, connectors)``.
        rectangle, connectors = indicator
    rectangle.set_gid(_new_gid(ax.figure, "linked-detail-region"))
    for connector in connectors:
        connector.set_gid(_new_gid(ax.figure, "linked-detail-connector"))
    inset._witness_role = "linked-detail"
    if label:
        inset.set_title(
            label,
            loc="left",
            fontproperties=BODY_SEMIBOLD,
            fontsize=state.tick_size,
            color=INK,
        )
    return inset


def panel_title(ax: Axes, title: str, detail: str | None = None) -> Axes:
    """Add a quiet panel title; the figure claim remains dominant."""

    ax.set_title(
        title,
        loc="left",
        fontproperties=BODY_SEMIBOLD,
        fontsize=_state(ax).body_size,
        color=INK,
        pad=7,
    )
    if detail:
        ax.text(
            1,
            1.02,
            detail,
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            fontproperties=MONO,
            fontsize=_state(ax).footer_size,
            color=MUTED,
        )
    return ax


def label_end(
    ax: Axes,
    line: Line2D,
    label: str,
    *,
    pad_points: float = 7,
    color: str | None = None,
) -> Artist:
    """Direct-label a line at its last finite value."""

    x = np.asarray(line.get_xdata())
    y = np.asarray(line.get_ydata(), dtype=float)
    finite = np.isfinite(y)
    if not finite.any():
        raise ValueError("cannot label a line with no finite y values")
    annotation = ax.annotate(
        label,
        xy=(x[finite][-1], y[finite][-1]),
        xytext=(pad_points, 0),
        textcoords="offset points",
        ha="left",
        va="center",
        fontproperties=BODY_SEMIBOLD,
        fontsize=_state(ax).tick_size,
        color=color or line.get_color(),
        annotation_clip=False,
    )
    annotation.set_gid(f"{line.get_gid() or 'witness-line'}-end-label")
    return annotation


def finish(
    fig: Figure,
    axes: Axes | Mapping[str, Axes] | Iterable[Axes],
    *,
    grid: Literal["x", "y"] | None = "y",
    margins: Mapping[str, float] | None = None,
) -> Axes | Mapping[str, Axes] | Iterable[Axes]:
    """Run the ordered evidence-polish pass and resolve gutter collisions."""

    if not isinstance(fig, Figure) or not hasattr(fig, "_witness_theme"):
        raise ValueError("finish() requires a figure created by witness.frame()")
    if grid not in ("x", "y", None):
        raise ValueError("grid must be 'x', 'y', or None")
    normalized = _axes_list(axes)
    if not normalized:
        raise ValueError("finish() requires at least one Axes")
    foreign = [ax for ax in normalized if not isinstance(ax, Axes) or ax.figure is not fig]
    if foreign:
        raise ValueError("every Axes passed to finish() must belong to fig")

    state = _state(fig)
    for ax in normalized:
        ax.grid(False)
        if grid in ("x", "y"):
            axis = getattr(ax, f"{grid}axis")
            axis.set_major_locator(MaxNLocator(nbins=state.nbins))
            ax.grid(axis=grid, color=GRID, lw=0.7)
        ax.set_axisbelow(True)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_visible(True)
        ax.spines["bottom"].set_color(GRID)
        ax.tick_params(axis="both", length=0, colors=MUTED, labelsize=state.tick_size)
        if margins:
            ax.margins(**dict(margins))
        _ensure_zero_rule(ax, value_axis=grid)

    fig.canvas.draw()
    _resolve_notes(fig)
    _trim_bottom_spines(normalized)
    fig._witness_finished_axes.update(normalized)
    fig._witness_finished = all(
        ax in fig._witness_finished_axes
        for ax in fig.axes
    )
    return axes


def _axes_list(axes: Axes | Mapping[str, Axes] | Iterable[Axes]) -> list[Axes]:
    if isinstance(axes, Axes):
        return [axes]
    if isinstance(axes, Mapping):
        return list(axes.values())
    return list(axes)


def _resolve_notes(fig: Figure) -> None:
    notes: list[Artist] = getattr(fig, "_witness_notes", [])
    state = _state(fig)
    for ax in {note.axes for note in notes if note.axes is not None}:
        on_axis = [note for note in notes if note.axes is ax]
        for side in ("left", "right"):
            group = [note for note in on_axis if note._witness_note_side == side]
            if len(group) < 2:
                continue
            group.sort(key=lambda note: ax.transData.transform((0, note._witness_note_y))[1])
            minimum_gap = state.tick_size * fig.dpi / 72 * 1.45
            positions = [ax.transData.transform((0, note._witness_note_y))[1] for note in group]
            for index in range(1, len(positions)):
                positions[index] = max(positions[index], positions[index - 1] + minimum_gap)
            for note, y_pixels in zip(group, positions):
                y_data = ax.transData.inverted().transform((0, y_pixels))[1]
                x_axes = 1.025 if side == "right" else -0.025
                note.set_position((x_axes, y_data))


def _trim_bottom_spines(axes: Iterable[Axes]) -> None:
    for ax in axes:
        ticks = [tick for tick in ax.get_xticks() if ax.get_xlim()[0] <= tick <= ax.get_xlim()[1]]
        if len(ticks) >= 2:
            ax.spines["bottom"].set_bounds(ticks[0], ticks[-1])


def _ensure_zero_rule(
    ax: Axes,
    *,
    value_axis: Literal["x", "y"] | None,
) -> None:
    """Draw zero on the quantitative axis, unless the caller already did.

    The grid direction is Witness's value-axis declaration.  This matters for
    horizontal bars: a categorical row numbered zero is not a quantitative
    zero and must not receive a horizontal rule.
    """

    if value_axis == "y":
        low, high = ax.get_ylim()
        has_zero = any(_line_is_zero(line, "y") for line in ax.lines)
        if low < 0 < high and not has_zero:
            zero = ax.axhline(0, color=MUTED, lw=1.15, zorder=0)
            zero.set_gid(_new_gid(ax.figure, "structure-zero"))
    elif value_axis == "x":
        low, high = ax.get_xlim()
        has_zero = any(_line_is_zero(line, "x") for line in ax.lines)
        if low < 0 < high and not has_zero:
            zero = ax.axvline(0, color=MUTED, lw=1.15, zorder=0)
            zero.set_gid(_new_gid(ax.figure, "structure-zero"))


def _line_is_zero(line: Line2D, axis: Literal["x", "y"]) -> bool:
    try:
        values = np.asarray(
            line.get_xdata() if axis == "x" else line.get_ydata(),
            dtype=float,
        )
    except (TypeError, ValueError):
        return False
    return bool(values.size and np.allclose(values, 0))


def units(
    ax: Axes,
    *,
    axis: Literal["x", "y"] = "y",
    kind: str = "count",
    top_only: bool = True,
) -> Axes:
    """Apply unit-aware ticks; optionally spell the unit on the final tick."""

    if axis not in ("x", "y"):
        raise ValueError("axis must be 'x' or 'y'")
    if kind not in _UNIT_FORMATTERS:
        raise ValueError(f"unknown unit kind {kind!r}; choose {', '.join(_UNIT_FORMATTERS)}")
    axis_object = ax.yaxis if axis == "y" else ax.xaxis
    metadata = getattr(ax, "_witness_units", {})
    metadata[axis] = {"kind": kind, "top_only": bool(top_only)}
    ax._witness_units = metadata
    formatter = _UNIT_FORMATTERS[kind]
    if not top_only:
        axis_object.set_major_formatter(FuncFormatter(lambda value, _: formatter(value)))
        return ax

    limits = ax.get_ylim() if axis == "y" else ax.get_xlim()
    lower, upper = sorted(limits)
    ticks = [tick for tick in axis_object.get_ticklocs() if lower <= tick <= upper]
    if not ticks:
        return ax
    if axis == "y":
        display_positions = [ax.transData.transform((0, tick))[1] for tick in ticks]
    else:
        display_positions = [ax.transData.transform((tick, 0))[0] for tick in ticks]
    end_index = int(np.argmax(display_positions))
    labels = [
        formatter(tick) if index == end_index else _bare_number(tick)
        for index, tick in enumerate(ticks)
    ]
    axis_object.set_major_locator(FixedLocator(ticks))
    axis_object.set_major_formatter(FixedFormatter(labels))
    return ax


def _minus(text: str) -> str:
    return text.replace("-", "−")


def _bare_number(value: float) -> str:
    return _minus(f"{value:,.3g}")


def _format_si(value: float) -> str:
    for threshold, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "k")):
        if abs(value) >= threshold:
            scaled = value / threshold
            return _minus(f"{scaled:,.1f}{suffix}".replace(f".0{suffix}", suffix))
    return _bare_number(value)


_UNIT_FORMATTERS = {
    "count": lambda value: _minus(f"{value:,.0f}"),
    "si": _format_si,
    "percent": lambda value: _minus(f"{value:g}%"),
    "fraction_percent": lambda value: _minus(f"{value * 100:g}%"),
    "db": lambda value: _minus(f"{value:g} dB"),
    "dbm": lambda value: _minus(f"{value:g} dBm"),
    "ghz": lambda value: _minus(f"{value:g} GHz"),
    "kg": lambda value: _minus(f"{value:g} kg"),
    "years": lambda value: _minus(f"{value:.0f}"),
    "usd": lambda value: "$" + _format_si(value),
}


def _figure_palette_report(fig: Figure) -> PaletteReport:
    """Audit the colors actually used by semantic Artists and visible text."""

    surface = fig.get_facecolor()
    text_colors: dict[str, tuple[float, float, float, float]] = {}
    seen_text: set[int] = set()
    text_artists: list[Artist] = list(fig.texts)
    for ax in fig.axes:
        text_artists.extend(
            [
                *ax.texts,
                ax.title,
                ax.xaxis.label,
                ax.yaxis.label,
                *ax.get_xticklabels(),
                *ax.get_yticklabels(),
            ]
        )
    for index, artist in enumerate(text_artists):
        if id(artist) in seen_text or not artist.get_visible() or not artist.get_text():
            continue
        seen_text.add(id(artist))
        text_colors[f"text-{index:03d}"] = to_rgba(
            artist.get_color(),
            artist.get_alpha(),
        )

    mark_groups: dict[
        tuple[float, float, float, float],
        dict[str, Any],
    ] = {}
    artist_color_keys_by_role: dict[
        str,
        list[set[tuple[float, float, float, float]]],
    ] = {}
    support_colors: dict[str, tuple[float, float, float, float]] = {}
    registry: list[Artist] = getattr(fig, "_witness_registry", [])
    for artist in registry:
        role = artist._witness_role
        colors = _primary_artist_colors(artist)
        if not colors:
            continue
        if role == "context" or _is_support_region(artist):
            for color_index, color in enumerate(colors):
                support_colors[f"{artist.get_gid()}-{color_index}"] = color
            continue
        artist_keys: set[tuple[float, float, float, float]] = set()
        for color in colors:
            key = tuple(round(float(channel), 8) for channel in color)
            artist_keys.add(key)
            group = mark_groups.setdefault(
                key,
                {
                    "name": artist.get_gid() or type(artist).__name__,
                    "color": color,
                    "redundant": True,
                },
            )
            group["redundant"] = bool(group["redundant"]) and bool(
                getattr(artist, "_witness_redundant", None)
            )
        artist_color_keys_by_role.setdefault(role, []).append(artist_keys)

    mark_colors = {
        group["name"]: group["color"]
        for group in mark_groups.values()
    }
    redundant = {
        group["name"]: bool(group["redundant"])
        for group in mark_groups.values()
    }
    categorical_keys = {
        key
        for artist_keys in artist_color_keys_by_role.values()
        if len(artist_keys) > 1
        for key in set().union(*artist_keys)
        if len(set().union(*artist_keys)) > 1
    }
    categorical_colors = {
        mark_groups[key]["name"]: mark_groups[key]["color"]
        for key in categorical_keys
    }
    categorical_redundant = {
        name: redundant[name]
        for name in categorical_colors
    }
    return audit_used_colors(
        surface,
        text_colors=text_colors,
        mark_colors=mark_colors,
        categorical_colors=categorical_colors,
        redundant_channels=categorical_redundant,
        support_colors=support_colors,
    )


def _primary_artist_colors(
    artist: Artist,
) -> list[tuple[float, float, float, float]]:
    """Return visible primary RGBA values without treating grid/support as data."""

    if isinstance(artist, Annotation) and artist.arrow_patch is not None:
        return [to_rgba(artist.arrow_patch.get_edgecolor(), artist.get_alpha())]

    if isinstance(artist, Line2D):
        color = artist.get_color()
        if color in (None, "none", "None"):
            return []
        return [to_rgba(color, artist.get_alpha())]

    if isinstance(artist, AxesImage):
        rendered = np.asarray(artist.to_rgba(artist.get_array(), bytes=False))
        colors = rendered.reshape(-1, 4)
        if colors.shape[0] > 256:
            sample = np.linspace(0, colors.shape[0] - 1, 256, dtype=int)
            colors = colors[sample]
        return _unique_rgba(colors)

    if isinstance(artist, Collection):
        if isinstance(artist, PolyCollection) and artist._witness_role == "uncertainty":
            candidates = artist.get_edgecolors()
        else:
            candidates = artist.get_facecolors()
            if not len(candidates):
                candidates = artist.get_edgecolors()
        return _unique_rgba(candidates)

    if hasattr(artist, "get_facecolor"):
        face = artist.get_facecolor()
        try:
            rgba = to_rgba(face)
        except (TypeError, ValueError):
            return []
        alpha = artist.get_alpha()
        if alpha is not None:
            rgba = (*rgba[:3], float(alpha))
        return [rgba] if rgba[3] > 0 else []

    if hasattr(artist, "get_color"):
        try:
            return [to_rgba(artist.get_color(), artist.get_alpha())]
        except (TypeError, ValueError):
            return []
    return []


def _unique_rgba(values: Any) -> list[tuple[float, float, float, float]]:
    unique: dict[tuple[float, float, float, float], None] = {}
    for value in np.asarray(values).reshape(-1, 4):
        rgba = tuple(float(channel) for channel in value)
        if rgba[3] > 0:
            unique[rgba] = None
    return list(unique)


def _is_support_region(artist: Artist) -> bool:
    """Treat low-hierarchy hatched decision backgrounds as support, not marks."""

    if getattr(artist, "_witness_role", None) != "decision":
        return False
    linewidth = getattr(artist, "get_linewidth", lambda: 1.0)()
    hatch = getattr(artist, "get_hatch", lambda: None)()
    return bool(hatch and float(linewidth) == 0)


def audit(fig: Figure) -> AuditReport:
    """Audit deterministic structure and emit explicit human-review prompts."""

    claim: Claim | None = getattr(fig, "_witness_claim", None)
    if claim is None:
        return AuditReport(
            (
                AuditFinding(
                    code="figure.missing_claim",
                    severity="error",
                    message="Figure was not created by witness.frame().",
                ),
            )
        )

    required = audit_required_fields(
        claim.to_dict(),
        (
            "statement",
            "measure",
            "comparison",
            "scope",
            "source",
            "method",
            "uncertainty",
            "caveat",
            "alt",
        ),
        subject="figure",
    )
    surface_findings: list[AuditFinding] = []
    figure_surface = np.asarray(fig.get_facecolor(), dtype=float)
    if figure_surface.shape != (4,) or figure_surface[3] < 1:
        surface_findings.append(
            AuditFinding(
                code="figure.translucent_surface",
                severity="error",
                message="Strict color auditing requires an opaque figure surface.",
            )
        )
    for index, ax in enumerate(fig.axes):
        if not np.allclose(ax.get_facecolor(), fig.get_facecolor()):
            surface_findings.append(
                AuditFinding(
                    code="figure.unchecked_axes_surface",
                    severity="error",
                    message=(
                        "Axes and figure surfaces differ; Witness cannot certify "
                        "one-surface contrast for this composition."
                    ),
                    subject=f"axes-{index}",
                )
            )
    try:
        used_palette = _figure_palette_report(fig)
    except (TypeError, ValueError) as error:
        used_palette = audit_chosen_light_palette()
        surface_findings.append(
            AuditFinding(
                code="figure.palette_audit_unavailable",
                severity="error",
                message=f"Actual used-color audit failed: {error}",
            )
        )
    fig._witness_used_palette = used_palette
    findings = (
        list(required.findings)
        + surface_findings
        + list(used_palette.audit.findings)
    )

    if not getattr(fig, "_witness_finished", False):
        findings.append(
            AuditFinding(
                code="figure.not_finished",
                severity="error",
                message="Call witness.finish(fig, axes) before exporting.",
            )
        )

    registry: list[Artist] = getattr(fig, "_witness_registry", [])
    if not registry:
        findings.append(
            AuditFinding(
                code="figure.no_semantic_artists",
                severity="error",
                message="Tag at least one evidence Artist before export.",
            )
        )

    uncertainty_artists = [artist for artist in registry if artist._witness_role == "uncertainty"]
    for artist in uncertainty_artists:
        if not getattr(artist, "_witness_interval_kind", "").strip():
            findings.append(
                AuditFinding(
                    code="figure.unnamed_uncertainty",
                    severity="error",
                    message="Every uncertainty Artist must state its interval semantics.",
                    subject=artist.get_gid(),
                )
            )

    for artist in registry:
        if artist._witness_role != "reference":
            continue
        source = getattr(artist, "_witness_reference_source", None)
        if not source or not source.strip():
            findings.append(
                AuditFinding(
                    code="figure.reference_missing_source",
                    severity="error",
                    message="Every external reference or threshold must name its source.",
                    subject=artist.get_gid(),
                )
            )

    fig.canvas.draw()
    renderer = fig._get_renderer()
    publication_text = [
        text_artist
        for text_artist in fig.texts
        if text_artist.get_visible() and text_artist.get_text().strip()
    ]
    publication_boxes = [
        text_artist.get_window_extent(renderer=renderer)
        for text_artist in publication_text
    ]
    clipped_publication = [
        text_artist.get_text()[:48]
        for text_artist, box in zip(publication_text, publication_boxes)
        if box.x0 < fig.bbox.x0
        or box.y0 < fig.bbox.y0
        or box.x1 > fig.bbox.x1
        or box.y1 > fig.bbox.y1
    ]
    if clipped_publication:
        findings.append(
            AuditFinding(
                code="figure.publication_text_clipped",
                severity="warning",
                message="Figure-level claim/provenance text extends outside the canvas.",
                details={"text": clipped_publication},
            )
        )
    overlap_pairs = [
        [publication_text[first].get_text()[:32], publication_text[second].get_text()[:32]]
        for first in range(len(publication_boxes))
        for second in range(first + 1, len(publication_boxes))
        if publication_boxes[first].overlaps(publication_boxes[second])
    ]
    if overlap_pairs:
        findings.append(
            AuditFinding(
                code="figure.publication_text_overlap",
                severity="warning",
                message="Figure-level claim/provenance text overlaps after rendering.",
                details={"pairs": overlap_pairs},
            )
        )
    if claim.uncertainty and not uncertainty_artists and "no inferential" not in claim.uncertainty.lower():
        findings.append(
            AuditFinding(
                code="figure.uncertainty_not_drawn",
                severity="warning",
                message="The claim declares uncertainty, but no uncertainty Artist is tagged.",
            )
        )

    tagged_ids = {id(artist) for artist in registry}
    for ax in fig.axes:
        visible_marks = (*ax.lines, *ax.collections, *ax.patches, *ax.images)
        for artist in visible_marks:
            gid = artist.get_gid() or ""
            if (
                id(artist) in tagged_ids
                or gid.startswith("witness-structure")
                or gid.startswith("witness-linked-detail")
            ):
                continue
            if not artist.get_visible():
                continue
            findings.append(
                AuditFinding(
                    code="figure.untagged_artist",
                    severity="warning",
                    message="A visible data Artist has no Witness evidence role.",
                    subject=type(artist).__name__,
                )
            )

        for container in ax.containers:
            orientation = getattr(container, "orientation", None)
            value_limits = (
                ax.get_ylim() if orientation == "vertical" else ax.get_xlim()
            )
            zero_visible = min(value_limits) <= 0 <= max(value_limits)
            if orientation in ("vertical", "horizontal") and not zero_visible:
                findings.append(
                    AuditFinding(
                        code="figure.bar_zero_hidden",
                        severity="error",
                        message="A bar length encoding must display its zero baseline.",
                        subject=orientation,
                    )
                )
            for patch in container:
                if orientation == "vertical" and abs(float(patch.get_y())) > 1e-12:
                    findings.append(
                        AuditFinding(
                            code="figure.bar_baseline",
                            severity="error",
                            message="Vertical bar lengths must start at zero.",
                            subject=patch.get_gid(),
                        )
                    )
                if orientation == "horizontal" and abs(float(patch.get_x())) > 1e-12:
                    findings.append(
                        AuditFinding(
                            code="figure.bar_baseline",
                            severity="error",
                            message="Horizontal bar lengths must start at zero.",
                            subject=patch.get_gid(),
                        )
                    )

    roles = {artist._witness_role for artist in registry}
    purpose: Purpose = fig._witness_theme.purpose
    if purpose == "decide" and roles.isdisjoint({"decision", "reference", "comparator"}):
        findings.append(
            AuditFinding(
                code="purpose.decide_missing_decision_evidence",
                severity="error",
                message=(
                    "A decide figure must tag a decision region, reference, or comparator."
                ),
            )
        )
    elif purpose == "inspect" and roles.isdisjoint({"observation", "estimate", "model"}):
        findings.append(
            AuditFinding(
                code="purpose.inspect_missing_primary_evidence",
                severity="error",
                message="An inspect figure must expose observations, estimates, or model output.",
            )
        )
    elif purpose == "explain" and roles.isdisjoint(
        {"estimate", "comparator", "reference", "exception"}
    ):
        findings.append(
            AuditFinding(
                code="purpose.explain_implicit_warrant",
                severity="warning",
                message=(
                    "The explanation has no tagged estimate, comparator, reference, "
                    "or exception; make its warrant recoverable."
                ),
            )
        )

    state: ThemeState = fig._witness_theme
    annotation_count = sum(isinstance(artist, Annotation) for artist in registry)
    if annotation_count > state.annotation_budget:
        findings.append(
            AuditFinding(
                code="purpose.annotation_budget",
                severity="warning",
                message=(
                    f"{annotation_count} semantic callouts exceed the {purpose} "
                    f"budget of {state.annotation_budget}."
                ),
                details={
                    "count": annotation_count,
                    "budget": state.annotation_budget,
                },
            )
        )

    minimum_type = {"html": 6.5, "slide": 9.0, "print": 6.0}[state.medium]
    undersized_text = [
        text_artist
        for text_artist in fig.findobj(match=Text)
        if text_artist.get_visible()
        and text_artist.get_text().strip()
        and text_artist.get_fontsize() < minimum_type
    ]
    if undersized_text:
        findings.append(
            AuditFinding(
                code="medium.text_too_small",
                severity="warning",
                message=(
                    f"{len(undersized_text)} visible text item(s) are below the "
                    f"{minimum_type:g} pt {state.medium} floor."
                ),
                details={"minimum_points": minimum_type},
            )
        )

    for artist in registry:
        if artist._witness_role not in {"estimate", "exception", "decision"}:
            continue
        get_sizes = getattr(artist, "get_sizes", None)
        if get_sizes is None:
            continue
        sizes = np.asarray(get_sizes(), dtype=float)
        if sizes.size and np.nanmin(sizes) < state.marker_size:
            findings.append(
                AuditFinding(
                    code="medium.marker_too_small",
                    severity="warning",
                    message=(
                        f"A focal marker is smaller than the {state.marker_size:g} "
                        f"pt² {state.medium} floor."
                    ),
                    subject=artist.get_gid(),
                    details={
                        "minimum_area_points_squared": state.marker_size,
                        "actual_area_points_squared": float(np.nanmin(sizes)),
                    },
                )
            )
    colored_groups: dict[str, list[Artist]] = {}
    for artist in registry:
        colored_groups.setdefault(artist._witness_role, []).append(artist)
    for role, artists in colored_groups.items():
        if len(artists) > 1 and all(not getattr(artist, "_witness_redundant", None) for artist in artists):
            findings.append(
                AuditFinding(
                    code="figure.color_only_role",
                    severity="warning",
                    message=f"Multiple {role} Artists do not declare a redundant channel.",
                    subject=role,
                )
            )

    if _contains_causal_language(claim.statement):
        findings.append(
            AuditFinding(
                code="claim.causal_warrant",
                severity="review",
                message="Does the design and analysis warrant the causal verb in the claim?",
            )
        )
    findings.extend(
        [
            AuditFinding(
                code="claim.comparator_review",
                severity="review",
                message="Is the comparator meaningful rather than merely convenient?",
            ),
            AuditFinding(
                code="claim.scope_review",
                severity="review",
                message="Does the scope support the title's generalization?",
            ),
        ]
    )
    return AuditReport(tuple(findings))


def _contains_causal_language(statement: str) -> bool:
    pattern = r"\b(cause[ds]?|drives?|led to|results? in|because of|produces?)\b"
    return re.search(pattern, statement.lower()) is not None


def save(
    fig: Figure,
    stem: str,
    *,
    outdir: str | Path | None = None,
    formats: Sequence[str] = ("svg", "html", "pdf", "png"),
    dpi: int = 200,
    strict: bool = True,
    override_reason: str | None = None,
    data_fingerprints: Mapping[str, str] | None = None,
) -> ExportBundle:
    """Export accessible visual formats and a JSON evidence receipt."""

    if not stem or Path(stem).name != stem:
        raise ValueError("stem must be a non-empty filename stem without directories")
    if not formats:
        raise ValueError("formats must request at least one visual export")
    supported = {"svg", "html", "pdf", "png"}
    unknown = set(formats) - supported
    if unknown:
        raise ValueError(f"unsupported format(s): {', '.join(sorted(unknown))}")

    report = audit(fig)
    if strict:
        report.enforce()
    elif report.errors and not (override_reason and override_reason.strip()):
        raise ValueError(
            "override_reason is required when strict=False exports audit errors"
        )

    out_dir = Path(outdir) if outdir is not None else OUTPUTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    claim: Claim = fig._witness_claim
    receipt_path = out_dir / f"{stem}.receipt.json"

    written: dict[str, Path] = {}
    svg_accessibility: dict[str, Any] | None = None
    needs_svg = "svg" in formats or "html" in formats
    if needs_svg:
        svg_path = out_dir / f"{stem}.svg"
        with plt.rc_context({"svg.fonttype": "none"}):
            fig.savefig(
                svg_path,
                format="svg",
                metadata={
                    "Title": claim.statement,
                    "Description": claim.alt or claim.statement,
                    "Creator": "Witness / Matplotlib",
                },
            )
        make_accessible_svg(
            svg_path,
            title=claim.statement,
            description=claim.alt or claim.statement,
            fonts=_embedded_fonts(),
            require_text=True,
        )
        written["svg"] = svg_path
        expected_gids = [
            artist.get_gid()
            for artist in fig._witness_registry
            if artist.get_gid()
        ]
        inspection = inspect_svg(
            svg_path,
            expected_semantic_gids=expected_gids,
            required_font_families=(DISPLAY_FAMILY, BODY_FAMILY, MONO_FAMILY),
        )
        svg_accessibility = _svg_receipt(inspection, expected_gids)
        if not inspection.passed:
            report = merge_reports(
                report,
                AuditReport(
                    tuple(
                        AuditFinding(
                            code=f"export.svg_{issue.replace('-', '_')}",
                            severity="error",
                            message=f"Accessible SVG inspection failed: {issue}.",
                            subject=svg_path.name,
                            details=inspection.details,
                        )
                        for issue in inspection.issues
                    )
                ),
            )
            if strict:
                report.enforce()

    if "pdf" in formats:
        pdf_path = out_dir / f"{stem}.pdf"
        with plt.rc_context({"pdf.fonttype": 42, "ps.fonttype": 42}):
            fig.savefig(
                pdf_path,
                format="pdf",
                metadata={"Title": claim.statement, "Subject": claim.alt or claim.statement},
            )
        written["pdf"] = pdf_path

    if "png" in formats:
        png_path = out_dir / f"{stem}.png"
        fig.savefig(
            png_path,
            format="png",
            dpi=dpi,
            metadata={"Title": claim.statement, "Description": claim.alt or claim.statement},
        )
        written["png"] = png_path

    if "html" in formats:
        html_path = out_dir / f"{stem}.html"
        written["html"] = html_path

    if not strict and report.errors and not (override_reason and override_reason.strip()):
        raise ValueError(
            "override_reason is required when strict=False exports audit errors"
        )

    receipt = _receipt(
        fig,
        report,
        data_fingerprints or {},
        strict=strict,
        override_reason=override_reason,
    )
    if svg_accessibility is not None:
        receipt["svg_accessibility"] = svg_accessibility
    receipt["exports"] = {
        format_name: path.name for format_name, path in sorted(written.items())
    }
    receipt["artifact_hashes"] = {
        format_name: _file_digest(path)
        for format_name, path in sorted(written.items())
        if format_name != "html" and path.exists()
    }
    receipt["font_hashes"] = {
        Path(face.path).name: _file_digest(Path(face.path))
        for face in _embedded_fonts()
    }
    receipt_path.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    if "html" in formats:
        write_html(
            written["svg"],
            written["html"],
            caption=claim.statement,
            summary=claim.alt or claim.statement,
            receipt=receipt,
            figure_id=f"witness-{_slug(stem)}",
        )

    return ExportBundle(paths=written, receipt=receipt_path, audit=report)


def _svg_receipt(inspection: Any, expected_gids: Sequence[str]) -> dict[str, Any]:
    details = inspection.details
    embedded = set(details.get("embedded_font_families", ()))
    missing = set(details.get("missing_semantic_gids", ()))
    return {
        "passed": inspection.passed,
        "issues": list(inspection.issues),
        "role": details.get("role"),
        "aria_labelledby": " ".join(details.get("aria_labelledby", ())),
        "selectable_text_nodes": details.get("selectable_text_nodes", 0),
        "semantic_groups": [gid for gid in expected_gids if gid not in missing],
        "embedded_font_families": [
            family
            for family in (DISPLAY_FAMILY, BODY_FAMILY, MONO_FAMILY)
            if family in embedded
        ],
        "external_resources": details.get("external_resources", []),
        "details": details,
    }


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"


def _embedded_fonts() -> tuple[FontFace, ...]:
    return (
        FontFace(FONTS_DIR / "IBMPlexSerif-SemiBold.woff2", DISPLAY_FAMILY, weight=600),
        FontFace(FONTS_DIR / "IBMPlexSans-Regular.woff2", BODY_FAMILY, weight=400),
        FontFace(FONTS_DIR / "IBMPlexSans-SemiBold.woff2", BODY_FAMILY, weight=600),
        FontFace(FONTS_DIR / "IBMPlexSans-Italic.woff2", BODY_FAMILY, style="italic", weight=400),
        FontFace(FONTS_DIR / "IBMPlexMono-Medium.woff2", MONO_FAMILY, weight=500),
    )


def _receipt(
    fig: Figure,
    report: AuditReport,
    data_fingerprints: Mapping[str, str],
    *,
    strict: bool,
    override_reason: str | None,
) -> dict[str, Any]:
    claim: Claim = fig._witness_claim
    state: ThemeState = fig._witness_theme
    registry: list[Artist] = fig._witness_registry
    used_palette = getattr(fig, "_witness_used_palette", None)
    if used_palette is None:
        used_palette = _figure_palette_report(fig)
    axes_receipt = []
    for index, ax in enumerate(fig.axes):
        axes_receipt.append(
            {
                "index": index,
                "xlim": [float(value) for value in ax.get_xlim()],
                "ylim": [float(value) for value in ax.get_ylim()],
                "xscale": ax.get_xscale(),
                "yscale": ax.get_yscale(),
                "xlabel": ax.get_xlabel(),
                "ylabel": ax.get_ylabel(),
                "units": dict(getattr(ax, "_witness_units", {})),
                "xticks": len(ax.get_xticks()),
                "yticks": len(ax.get_yticks()),
            }
        )
    artists = []
    for artist in registry:
        artists.append(
            {
                "gid": artist.get_gid(),
                "type": type(artist).__name__,
                "role": artist._witness_role,
                "label": artist._witness_label,
                "redundant_channel": artist._witness_redundant,
                "interval_kind": getattr(artist, "_witness_interval_kind", None),
                "reference_source": getattr(artist, "_witness_reference_source", None),
            }
        )
    return {
        "system": "Witness",
        "claim": claim.to_dict(),
        "purpose": state.purpose,
        "medium": state.medium,
        "figure_inches": [float(value) for value in fig.get_size_inches()],
        "palette": used_palette.to_dict(),
        "design_palette": audit_chosen_light_palette().to_dict(),
        "role_counts": dict(Counter(artist._witness_role for artist in registry)),
        "artists": artists,
        "axes": axes_receipt,
        "data_fingerprints": dict(data_fingerprints),
        "export_policy": {
            "strict": bool(strict),
            "override_reason": override_reason,
        },
        "runtime": {
            "python": sys.version.split()[0],
            "numpy": np.__version__,
            "matplotlib": matplotlib.__version__,
        },
        "audit": report.to_dict(),
    }


def fingerprint(*arrays: np.ndarray) -> str:
    """Return a stable, versioned SHA-256 digest for explicit NumPy arrays.

    Object arrays are rejected because their raw bytes contain process-specific
    pointers.  Numeric/string arrays are normalized to little-endian storage and
    every metadata/payload boundary is length-delimited.
    """

    digest = hashlib.sha256()
    digest.update(b"witness-fingerprint-v1\0")
    digest.update(len(arrays).to_bytes(8, "big"))
    for position, array in enumerate(arrays):
        values = np.asarray(array)
        if values.dtype.hasobject:
            raise TypeError(
                f"array {position} has object dtype; convert it to an explicit "
                "numeric or fixed-width string dtype before fingerprinting"
            )
        normalized_dtype = values.dtype.newbyteorder("<")
        normalized = np.ascontiguousarray(values.astype(normalized_dtype, copy=False))
        metadata = json.dumps(
            {
                "dtype": normalized.dtype.str,
                "shape": list(normalized.shape),
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        payload = normalized.tobytes(order="C")
        digest.update(len(metadata).to_bytes(8, "big"))
        digest.update(metadata)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return f"sha256:{digest.hexdigest()}"


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "figure"


__all__ = [
    "BODY",
    "BODY_ITALIC",
    "BODY_SEMIBOLD",
    "BRICK",
    "CATEGORICAL",
    "Claim",
    "COMPARATOR",
    "CONTEXT",
    "DECISION",
    "DISPLAY",
    "EVIDENCE",
    "EVERGREEN",
    "EXCEPTION",
    "ExportBundle",
    "FAINT",
    "GRID",
    "INK",
    "INTERVAL",
    "MODEL",
    "MONO",
    "MUTED",
    "SURFACE",
    "VIOLET",
    "audit",
    "bracket",
    "fingerprint",
    "finish",
    "frame",
    "interval",
    "label_end",
    "linked_detail",
    "margin_note",
    "panel_title",
    "reference",
    "save",
    "tag",
    "theme",
    "units",
]
