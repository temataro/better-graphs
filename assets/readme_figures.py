"""Render the README before/after showcase figures into assets/.

Run from the repo root:

    uv run python assets/readme_figures.py

Needs the built datasets (``data/*.npz``). Build them first if missing:

    uv run python data/build_datasets.py

Each showcase is a side-by-side *before | after* composite: every panel is
rendered on its own (the "before" line panel in genuine matplotlib defaults, so
the font/spine/colour change is honest), saved to a temp PNG, then laid out two
-up with a headline. The committed outputs are the ``showcase-*.png`` files.
"""
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent  # repo/assets
sys.path.insert(0, str(HERE.parent / "visualization-curriculum"))
os.chdir(HERE)  # so ndata's DATA = ../data resolves to repo/data

import numpy as np
import matplotlib.pyplot as plt

import house_style
from house_style import ACCENT, GREY
from ndata import load, group, pivot, MONTHS

PANEL_DPI = 200
COMPOSITE_DPI = 150


def _panel(fig, name):
    """Save one before/after panel to a temp PNG and return its path."""
    path = HERE / name
    fig.savefig(path, dpi=PANEL_DPI, bbox_inches="tight")
    plt.close(fig)
    return path


def _composite(panel_pngs, out_name, headline):
    """Lay two rendered panels side by side under a single headline."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.4))
    for ax, panel_png in zip(axes, panel_pngs):
        ax.imshow(plt.imread(panel_png))
        ax.axis("off")
    fig.suptitle(headline, x=0.01, ha="left", fontsize=15, weight="bold")
    fig.subplots_adjust(wspace=0.03, top=0.92)
    out_path = HERE / out_name
    fig.savefig(out_path, dpi=COMPOSITE_DPI, bbox_inches="tight")
    plt.close(fig)
    for panel_png in panel_pngs:
        panel_png.unlink()
    print(f"  wrote  {out_name}")
    return out_path


# ---------------------------------------------------------------- story 1: defaults vs house
def showcase_defaults():
    flights = load("flights")
    year, passengers_per_year = group(
        flights["year"], flights["passengers"].astype(float), np.nansum
    )

    with plt.style.context("default"):
        fig, ax = plt.subplots(figsize=(6.2, 4.4))
        ax.plot(year, passengers_per_year, marker="o")
        ax.set_title("Passengers")
        ax.set_xlabel("year")
        ax.set_ylabel("passengers")
        before = _panel(fig, "_tmp_defaults_before.png")

    house_style.apply_theme("executive")
    fig, ax = plt.subplots(figsize=(6.2, 4.4))
    ax.plot(year, passengers_per_year, color=ACCENT, lw=2.6)
    house_style.polish(ax, grid="y")
    house_style.thousands(ax, "y")
    ax.margins(x=0.10)
    ax.annotate(
        f"{passengers_per_year[-1]:,.0f}",
        (year[-1], passengers_per_year[-1]),
        xytext=(8, 0),
        textcoords="offset points",
        va="center",
        color=ACCENT,
        fontsize=11,
        weight="bold",
    )
    ax.set_title("Air travel ~doubled across the 1950s", loc="left", pad=10)
    after = _panel(fig, "_tmp_defaults_after.png")

    return _composite(
        [before, after], "showcase-defaults.png", "Same numbers — defaults vs. the house style"
    )


# ---------------------------------------------------------------- story 2: jet vs viridis
def _heatmap_panel(passenger_matrix, years, cmap, title, name):
    house_style.apply_theme("detailed")
    fig, ax = plt.subplots(figsize=(6.2, 4.4))
    heatmap = ax.imshow(passenger_matrix, aspect="auto", cmap=cmap)
    ax.set_yticks(range(12))
    ax.set_yticklabels([month[:3] for month in MONTHS], fontsize=7)
    ax.set_xticks(range(0, len(years), 2))
    ax.set_xticklabels(years[::2], fontsize=8)
    ax.set_title(title, loc="left")
    ax.grid(False)
    house_style.add_colorbar(fig, heatmap, ax)
    return _panel(fig, name)


def showcase_color():
    flights = load("flights")
    years = np.unique(flights["year"])
    _, _, passenger_matrix = pivot(
        flights["month"], flights["year"], flights["passengers"], rows=MONTHS, cols=years
    )
    jet_panel = _heatmap_panel(
        passenger_matrix, years, "jet", "jet — invents bands the data doesn't have", "_tmp_color_jet.png"
    )
    viridis_panel = _heatmap_panel(
        passenger_matrix, years, "viridis", "viridis — perceptually even", "_tmp_color_viridis.png"
    )
    return _composite(
        [jet_panel, viridis_panel], "showcase-color.png", "A rainbow ramp lies; a perceptual ramp doesn't"
    )


# ---------------------------------------------------------------- story 3: chart choice
def _life_expectancy(gapminder, country, year):
    is_row = (gapminder["country"] == country) & (gapminder["year"] == year)
    return float(gapminder["lifeExp"][is_row][0])


def showcase_chart_choice():
    gapminder = load("gapminder")
    countries = np.array(["Nigeria", "Bangladesh", "India", "Indonesia", "Brazil", "China"])
    life_exp_1952 = np.array([_life_expectancy(gapminder, c, 1952) for c in countries])
    life_exp_2007 = np.array([_life_expectancy(gapminder, c, 2007) for c in countries])

    order_by_2007 = np.argsort(life_exp_2007)
    countries = countries[order_by_2007]
    life_exp_1952 = life_exp_1952[order_by_2007]
    life_exp_2007 = life_exp_2007[order_by_2007]
    row = np.arange(len(countries))

    house_style.apply_theme("detailed")
    bar_height = 0.38
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    ax.barh(row - bar_height / 2, life_exp_1952, height=bar_height, color=GREY, label="1952")
    ax.barh(row + bar_height / 2, life_exp_2007, height=bar_height, color=ACCENT, label="2007")
    ax.set_yticks(row)
    ax.set_yticklabels(countries, fontsize=9)
    ax.set_xlabel("life expectancy (years)")
    ax.set_title("Grouped bars — you subtract to compare", loc="left")
    ax.legend(loc="lower right", fontsize=8)
    house_style.polish(ax, grid="x")
    grouped = _panel(fig, "_tmp_choice_grouped.png")

    house_style.apply_theme("detailed")
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    for row_y, start, end in zip(row, life_exp_1952, life_exp_2007):
        ax.plot([start, end], [row_y, row_y], color="#cfcfcf", lw=2.5, zorder=1)
    ax.scatter(life_exp_1952, row, color=GREY, s=45, zorder=2, label="1952")
    ax.scatter(life_exp_2007, row, color=ACCENT, s=60, zorder=3, label="2007")
    ax.set_yticks(row)
    ax.set_yticklabels(countries, fontsize=9)
    ax.set_xlabel("life expectancy (years)")
    ax.set_title("Dumbbell — the gain is the line", loc="left")
    ax.legend(loc="lower right", fontsize=8)
    house_style.polish(ax, grid="x")
    dumbbell = _panel(fig, "_tmp_choice_dumbbell.png")

    return _composite(
        [grouped, dumbbell], "showcase-chartchoice.png", "Same data — the right chart shows the change"
    )


if __name__ == "__main__":
    print("Rendering README showcase figures ->", HERE)
    showcase_defaults()
    showcase_color()
    showcase_chart_choice()
    print("done.")
