"""Render the README before/after figures into assets/.

Run from the repo root:

    uv run python assets/readme_figures.py

Needs the built datasets (``data/*.npz``). Build them first if missing:

    uv run python data/build_datasets.py

Every example is a true *before vs. after*: the **before** is plain matplotlib with
zero style choices (rendered under ``plt.style.context("default")``, so the boxed
spines, primary blue, DejaVu font, and bare titles are honest), and the **after** is
the full house style. Each panel is saved once at high DPI as its own ``*-before.png``
/ ``*-after.png`` — no re-compositing, so they stay crisp on a retina display. The
README lays the pairs out side by side.
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

DPI = 200


def _save(fig, stem):
    path = HERE / f"{stem}.png"
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote  {stem}.png")
    return path


# ============================================================ hero: the 4-panel RF DUT report
def rf_before():
    dut_report = load("rf_dut_report")
    frequency_ghz = dut_report["freq_ghz"]
    power_amp = load("rf_pa_efficiency")
    input_drive_dbm = power_amp["pin_dbm"]

    with plt.style.context("default"):
        fig, axes = plt.subplots(2, 2, figsize=(11, 6.6))
        axes[0, 0].plot(frequency_ghz, dut_report["gain_db"])
        axes[0, 0].set_title("gain_db")
        axes[0, 0].set_xlabel("freq_ghz")
        axes[0, 1].plot(frequency_ghz, dut_report["noise_figure_db"])
        axes[0, 1].set_title("noise_figure_db")
        axes[0, 1].set_xlabel("freq_ghz")
        axes[1, 0].plot(frequency_ghz, dut_report["return_loss_db"])
        axes[1, 0].set_title("return_loss_db")
        axes[1, 0].set_xlabel("freq_ghz")
        compression = axes[1, 1]
        compression.plot(input_drive_dbm, power_amp["gain_db"])
        twin = compression.twinx()
        twin.plot(input_drive_dbm, power_amp["pae_pct"])  # same default blue — indistinguishable
        compression.set_title("gain_db & pae_pct vs pin_dbm")
        compression.set_xlabel("pin_dbm")
        fig.suptitle("rf_dut_report")
        fig.tight_layout()
        return _save(fig, "rf-before")


def rf_after():
    house_style.apply_theme("detailed")
    dut_report = load("rf_dut_report")
    frequency_ghz = dut_report["freq_ghz"]
    power_amp = load("rf_pa_efficiency")
    input_drive_dbm = power_amp["pin_dbm"]
    pa_gain_db = power_amp["gain_db"]
    pae_pct = power_amp["pae_pct"]

    GAIN_COLOR = ACCENT
    PAE_COLOR = house_style.CATEGORICAL[1]  # teal — the second series' key

    fig, panels = plt.subplot_mosaic("AB\nCD", figsize=(11, 6.6), constrained_layout=True)

    gain_ax = panels["A"]
    gain_ax.plot(frequency_ghz, dut_report["gain_db"], color=GAIN_COLOR, lw=2)
    gain_ax.set_title("Gain", loc="left", fontsize=11)
    gain_ax.set_ylabel("Gain (dB)")
    house_style.despine(gain_ax)

    noise_figure_ax = panels["B"]
    noise_figure_ax.plot(frequency_ghz, dut_report["noise_figure_db"], color=GREY, lw=2)
    noise_figure_ax.set_title("Noise figure", loc="left", fontsize=11)
    noise_figure_ax.set_ylabel("NF (dB)")
    house_style.despine(noise_figure_ax)

    return_loss_ax = panels["C"]
    return_loss_ax.plot(frequency_ghz, dut_report["return_loss_db"], color=GREY, lw=2)
    return_loss_ax.axhline(-10, ls="--", lw=1, color=ACCENT)
    return_loss_ax.annotate(
        "-10 dB match limit",
        xy=(frequency_ghz[-1], -10),
        xytext=(0, 4),
        textcoords="offset points",
        ha="right",
        fontsize=8,
        color=ACCENT,
    )
    return_loss_ax.set_title("Return loss", loc="left", fontsize=11)
    return_loss_ax.set_xlabel("Frequency (GHz)")
    return_loss_ax.set_ylabel(r"$S_{11}$ (dB)")
    house_style.despine(return_loss_ax)

    compression_ax = panels["D"]
    compression_ax.plot(input_drive_dbm, pa_gain_db, color=GAIN_COLOR, lw=2)
    compression_ax.set_title("PA compression & efficiency", loc="left", fontsize=11)
    compression_ax.set_xlabel("Input drive (dBm)")
    compression_ax.set_ylabel("Gain (dB)", color=GAIN_COLOR)
    compression_ax.tick_params(axis="y", colors=GAIN_COLOR)
    compression_ax.spines["left"].set_color(GAIN_COLOR)
    compression_ax.spines["top"].set_visible(False)

    pae_ax = compression_ax.twinx()
    pae_ax.plot(input_drive_dbm, pae_pct, color=PAE_COLOR, lw=2)
    pae_ax.set_ylabel("PAE (%)", color=PAE_COLOR)
    pae_ax.tick_params(axis="y", colors=PAE_COLOR)
    pae_ax.spines["right"].set_color(PAE_COLOR)
    pae_ax.spines["top"].set_visible(False)

    small_signal_gain_db = pa_gain_db[:5].mean()
    p1db_index = int(np.argmin(np.abs(pa_gain_db - (small_signal_gain_db - 1.0))))
    compression_ax.scatter(
        [input_drive_dbm[p1db_index]], [pa_gain_db[p1db_index]], color=GAIN_COLOR, zorder=5
    )
    compression_ax.annotate(
        "P1dB",
        xy=(input_drive_dbm[p1db_index], pa_gain_db[p1db_index]),
        xytext=(6, -2),
        textcoords="offset points",
        fontsize=8,
        color=GAIN_COLOR,
    )

    fig.suptitle(
        "DUT report — four measurements, one consistent sheet",
        x=0.01,
        ha="left",
        fontsize=14,
        weight="medium",
    )
    return _save(fig, "rf-after")


# ============================================================ a trend over time
def line_pair():
    flights = load("flights")
    year, passengers_per_year = group(
        flights["year"], flights["passengers"].astype(float), np.nansum
    )

    with plt.style.context("default"):
        fig, ax = plt.subplots(figsize=(6.6, 4.6))
        ax.plot(year, passengers_per_year, marker="o")
        ax.set_title("passengers")
        ax.set_xlabel("year")
        ax.set_ylabel("passengers")
        _save(fig, "line-before")

    house_style.apply_theme("executive")
    fig, ax = plt.subplots(figsize=(6.6, 4.6))
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
    _save(fig, "line-after")


# ============================================================ a matrix / seasonality
def heatmap_pair():
    flights = load("flights")
    years = np.unique(flights["year"])
    _, _, passenger_matrix = pivot(
        flights["month"], flights["year"], flights["passengers"], rows=MONTHS, cols=years
    )

    with plt.style.context("default"):
        fig, ax = plt.subplots(figsize=(6.8, 4.8))
        heatmap = ax.imshow(passenger_matrix, aspect="auto")
        ax.set_title("passengers")
        ax.set_xlabel("year index")
        ax.set_ylabel("month index")
        fig.colorbar(heatmap)
        fig.tight_layout()
        _save(fig, "heatmap-before")

    house_style.apply_theme("detailed")
    fig, ax = plt.subplots(figsize=(6.8, 4.8))
    heatmap = ax.imshow(passenger_matrix, aspect="auto", cmap="viridis")
    ax.set_yticks(range(12))
    ax.set_yticklabels([month[:3] for month in MONTHS], fontsize=8)
    ax.set_xticks(range(0, len(years), 2))
    ax.set_xticklabels(years[::2], fontsize=8)
    ax.set_xlabel("year")
    ax.grid(False)
    colorbar = house_style.add_colorbar(fig, heatmap, ax)
    colorbar.set_label("passengers / month")
    ax.set_title("Air travel peaks every summer — and the peaks keep growing", loc="left", pad=10)
    _save(fig, "heatmap-after")


# ============================================================ the right chart for a change
def _life_expectancy(gapminder, country, year):
    is_row = (gapminder["country"] == country) & (gapminder["year"] == year)
    return float(gapminder["lifeExp"][is_row][0])


def chart_choice_pair():
    gapminder = load("gapminder")
    countries = np.array(["Nigeria", "Bangladesh", "India", "Indonesia", "Brazil", "China"])
    life_exp_1952 = np.array([_life_expectancy(gapminder, c, 1952) for c in countries])
    life_exp_2007 = np.array([_life_expectancy(gapminder, c, 2007) for c in countries])

    with plt.style.context("default"):
        column = np.arange(len(countries))
        bar_width = 0.4
        fig, ax = plt.subplots(figsize=(6.8, 4.8))
        ax.bar(column - bar_width / 2, life_exp_1952, width=bar_width, label="1952")
        ax.bar(column + bar_width / 2, life_exp_2007, width=bar_width, label="2007")
        ax.set_xticks(column)
        ax.set_xticklabels(countries, rotation=30, ha="right")
        ax.set_ylabel("lifeExp")
        ax.set_title("lifeExp by country")
        ax.legend()
        fig.tight_layout()
        _save(fig, "chartchoice-before")

    order_by_2007 = np.argsort(life_exp_2007)
    countries = countries[order_by_2007]
    life_exp_1952 = life_exp_1952[order_by_2007]
    life_exp_2007 = life_exp_2007[order_by_2007]
    row = np.arange(len(countries))

    house_style.apply_theme("detailed")
    fig, ax = plt.subplots(figsize=(6.8, 4.8))
    for row_y, start, end in zip(row, life_exp_1952, life_exp_2007):
        ax.plot([start, end], [row_y, row_y], color="#cfcfcf", lw=2.5, zorder=1)
    ax.scatter(life_exp_1952, row, color=GREY, s=55, zorder=2, label="1952")
    ax.scatter(life_exp_2007, row, color=ACCENT, s=70, zorder=3, label="2007")
    ax.set_yticks(row)
    ax.set_yticklabels(countries, fontsize=10)
    ax.set_xlabel("life expectancy (years)")
    ax.legend(loc="lower right", fontsize=9)
    house_style.polish(ax, grid="x")
    ax.set_title(r"Life expectancy, 1952 $\rightarrow$ 2007 — the line is the gain", loc="left", pad=10)
    _save(fig, "chartchoice-after")


if __name__ == "__main__":
    print("Rendering README before/after figures ->", HERE)
    rf_before()
    rf_after()
    line_pair()
    heatmap_pair()
    chart_choice_pair()
    print("done.")
