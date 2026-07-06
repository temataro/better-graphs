"""Render the README figures for the fable design system into assets/.

Run from the repo root:

    uv run python assets/fable_figures.py

Needs the built datasets (``uv run python data/build_datasets.py`` first). These
are the "next draft" heroes for the README: the same subjects as the original
before/afters (a trend; the RF DUT report), drawn as fable pages. The originals
(line-after.png, rf-after.png) become the honest *before* of this pair.
"""
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent  # repo/assets
sys.path.insert(0, str(HERE.parent / "visualization-curriculum"))
os.chdir(HERE)  # so ndata's DATA = ../data resolves to repo/data

import numpy as np

import fable
from ndata import load, group

DPI = 200


def _save(fig, stem):
    path = HERE / f"{stem}.png"
    fig.savefig(path, dpi=DPI)
    print(f"  wrote  {stem}.png")
    return path


def jet_age():
    flights = load("flights")
    year, passengers_per_year = group(
        flights["year"], flights["passengers"].astype(float), np.nansum
    )

    fable.theme("read")
    fig, ax = fable.page(
        kicker="Air travel · 1949–1960",
        title="The jet age took off before the jets did",
        dek="Passengers on international airlines, millions per year. The Boeing 707's\n"
            "1958 debut only steepened a climb already under way.",
        source="Source: Box & Jenkins airline series, via seaborn-data",
        note="better graphs · fable",
    )
    ax.plot(year, passengers_per_year / 1e3, color=fable.ACCENT, zorder=3)
    fable.gradient_fill(ax, year, passengers_per_year / 1e3, alpha_top=0.10)
    ax.set_ylim(0, 6)
    ax.margins(x=0.02)
    fable.finish(ax)
    fable.units(ax, "y", "count")
    passengers_1958_k = passengers_per_year[year == 1958][0] / 1e3
    fable.mark(ax, 1958, passengers_1958_k, "707 enters service",
               dx=-64, dy=26, color=fable.INK)
    return _save(fig, "fable-line")


def datasheet():
    dut = load("rf_dut_report")
    frequency_ghz = dut["freq_ghz"]
    power_amp = load("rf_pa_efficiency")
    drive_dbm = power_amp["pin_dbm"]
    pa_gain_db = power_amp["gain_db"]
    pae_pct = power_amp["pae_pct"]

    gain_spec_db = 18.0
    spec_cross_ghz = frequency_ghz[dut["gain_db"] < gain_spec_db][0]

    fable.theme("study")
    fig, panels = fable.page(
        size=(10.2, 8.6),
        mosaic="abcd\nGGRR\nNNPP\nNNEE",
        kicker="DUT-042 · wideband LNA · rev B silicon",
        title=f"Meets spec to {spec_cross_ghz:.1f} GHz — gain clips the 18 dB floor at the band edge",
        dek="Measured at 25 °C, Vdd 3.3 V, 50 Ω. Shaded regions fail spec; the dashed rules are the limits.",
        source="Source: synthesized DUT report + PA sweep (data/build_datasets.py)",
        note="sheet 1 of 1 · fable",
        height_ratios=[0.8, 2, 2, 2], hspace=0.5, wspace=0.42,
    )

    gain_db_meas = dut["gain_db"]
    noise_figure_db = dut["noise_figure_db"]
    return_loss_db = dut["return_loss_db"]
    small_signal_gain = pa_gain_db[:5].mean()
    p1db_index = int(np.argmin(np.abs(pa_gain_db - (small_signal_gain - 1))))

    fable.stat(panels["a"], f"{gain_db_meas.max():.1f} dB", "peak gain", "at 1.0 GHz")
    fable.stat(panels["b"], f"{noise_figure_db.min():.2f} dB", "best noise figure", "at 1.5 GHz")
    fable.stat(panels["c"], f"{drive_dbm[p1db_index]:.1f} dBm", "input P1dB", "PA sweep")
    fable.stat(panels["d"], f"{pae_pct.max():.0f}%", "peak PAE", "at full drive")

    gain_ax = panels["G"]
    gain_ax.plot(frequency_ghz, gain_db_meas, color=fable.ACCENT)
    gain_ax.set_ylim(15, 24)
    fable.panel_title(gain_ax, "Gain vs frequency")
    fable.finish(gain_ax)
    fable.spec_band(gain_ax, gain_spec_db, side="below", label="18 dB min")
    fable.units(gain_ax, "y", "db")
    fable.units(gain_ax, "x", "ghz")
    fable.mark(gain_ax, spec_cross_ghz, gain_spec_db,
               f"under spec beyond {spec_cross_ghz:.2f} GHz",
               dx=-88, dy=-26, color=fable.BAD, size=8)

    return_ax = panels["R"]
    return_ax.plot(frequency_ghz, return_loss_db, color=fable.NAVY)
    return_ax.set_ylim(-25, -8)
    fable.panel_title(return_ax, "Input return loss")
    fable.finish(return_ax)
    fable.spec_band(return_ax, -10, side="above", label="−10 dB max")
    fable.units(return_ax, "y", "db")
    fable.units(return_ax, "x", "ghz")

    noise_ax = panels["N"]
    noise_ax.plot(frequency_ghz, noise_figure_db, color=fable.EMERALD)
    noise_ax.set_ylim(1.0, 2.2)
    fable.panel_title(noise_ax, "Noise figure")
    fable.finish(noise_ax)
    fable.spec_band(noise_ax, 2.0, side="above", label="2.0 dB max")
    fable.units(noise_ax, "y", "db")
    fable.units(noise_ax, "x", "ghz")

    compression_ax = panels["P"]
    compression_ax.plot(drive_dbm, pa_gain_db, color=fable.ACCENT)
    compression_ax.scatter([drive_dbm[p1db_index]], [pa_gain_db[p1db_index]],
                           s=30, color=fable.INK, zorder=5)
    compression_ax.annotate("P1dB", (drive_dbm[p1db_index], pa_gain_db[p1db_index]),
                            xytext=(8, 4), textcoords="offset points",
                            family=fable.BODY_STACK, weight=700, size=8.5,
                            color=fable.INK)
    compression_ax.set_ylim(11, 16)
    fable.panel_title(compression_ax, "PA gain compression")
    fable.finish(compression_ax, nbins=4)
    fable.units(compression_ax, "y", "db")
    fable.units(compression_ax, "x", "dbm")

    efficiency_ax = panels["E"]
    efficiency_ax.sharex(compression_ax)
    efficiency_ax.plot(drive_dbm, pae_pct, color=fable.OCHRE)
    efficiency_ax.axvline(drive_dbm[p1db_index], lw=0.9, color=fable.FAINT, zorder=0)
    efficiency_ax.annotate("P1dB", (drive_dbm[p1db_index], 57), xytext=(4, 0),
                           textcoords="offset points", family=fable.BODY_STACK,
                           size=8, color=fable.MUTED)
    efficiency_ax.set_ylim(0, 60)
    fable.panel_title(efficiency_ax, "Power-added efficiency")
    fable.finish(efficiency_ax, nbins=4)
    fable.units(efficiency_ax, "y", "pct")
    fable.units(efficiency_ax, "x", "dbm")
    return _save(fig, "fable-datasheet")


if __name__ == "__main__":
    print("Rendering fable README figures ->", HERE)
    jet_age()
    datasheet()
    print("done.")
