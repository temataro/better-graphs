#!/usr/bin/env python
"""Fetch and reformat the Better Graphs datasets into tidy CSV + .npz.

    uv run python data/build_datasets.py

Raw downloads land in data/raw/ (gitignored); cleaned, tidy outputs are written
next to this file in data/. Re-running is cheap: existing raw files are reused.
Every output is small enough to track in git. Provenance + licenses: data/README.md.
"""
from __future__ import annotations

import shutil
import subprocess
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent
RAW = DATA / "raw"
RAW.mkdir(parents=True, exist_ok=True)

SOURCES = {
    "penguins.csv":  "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/penguins.csv",
    "flights.csv":   "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/flights.csv",
    "anscombe.csv":  "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/anscombe.csv",
    "gapminder.csv": "https://raw.githubusercontent.com/vincentarelbundock/Rdatasets/master/csv/gapminder/gapminder.csv",
    "datasaurus.tsv":"https://raw.githubusercontent.com/jumpingrivers/datasauRus/master/inst/extdata/DatasaurusDozen-Long.tsv",
    "ring_slot.s2p": "https://raw.githubusercontent.com/scikit-rf/scikit-rf/master/skrf/data/ring%20slot.s2p",
}

MONTH_ORDER = ["January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]


def fetch(name: str) -> Path | None:
    dest = RAW / name
    if dest.exists():
        return dest
    url = SOURCES[name]
    # Prefer curl: it uses the system CA bundle, so it works on hosts where the
    # bundled Python's ssl can't locate root certs (e.g. NixOS without SSL_CERT_FILE).
    if shutil.which("curl"):
        try:
            subprocess.run(["curl", "-fsSL", url, "-o", str(dest)], check=True)
            print(f"  downloaded  {name}")
            return dest
        except subprocess.CalledProcessError as exc:
            print(f"  FAILED      {name}: curl exit {exc.returncode}")
            return None
    try:
        with urllib.request.urlopen(url, timeout=60) as r:   # portable fallback
            dest.write_bytes(r.read())
        print(f"  downloaded  {name}")
        return dest
    except Exception as exc:                      # noqa: BLE001 - report and skip
        print(f"  FAILED      {name}: {exc}")
        return None


def save(name: str, df: pd.DataFrame | None = None, **arrays) -> None:
    if df is not None:
        df.to_csv(DATA / f"{name}.csv", index=False)
        print(f"  wrote  {name}.csv   {df.shape[0]}x{df.shape[1]}")
    if arrays:
        np.savez(DATA / f"{name}.npz", **arrays)
        print(f"  wrote  {name}.npz   [{', '.join(arrays)}]")


# --- real datasets ----------------------------------------------------------

def build_penguins(path: Path) -> None:
    num = ["bill_length_mm", "bill_depth_mm", "flipper_length_mm", "body_mass_g"]
    df = pd.read_csv(path).dropna(subset=num).reset_index(drop=True)
    df["sex"] = df["sex"].fillna("unknown").str.lower()
    save("penguins", df,
         bill_length_mm=df.bill_length_mm.to_numpy(float),
         bill_depth_mm=df.bill_depth_mm.to_numpy(float),
         flipper_length_mm=df.flipper_length_mm.to_numpy(float),
         body_mass_g=df.body_mass_g.to_numpy(float),
         species=df.species.to_numpy("U16"),
         island=df.island.to_numpy("U16"),
         sex=df.sex.to_numpy("U8"))


def build_gapminder(path: Path) -> None:
    df = pd.read_csv(path)[["country", "continent", "year", "lifeExp", "pop", "gdpPercap"]]
    save("gapminder", df,
         year=df.year.to_numpy(int),
         lifeExp=df.lifeExp.to_numpy(float),
         pop=df["pop"].to_numpy(float),
         gdpPercap=df.gdpPercap.to_numpy(float),
         country=df.country.to_numpy("U40"),
         continent=df.continent.to_numpy("U16"))


def build_anscombe(path: Path) -> None:
    df = pd.read_csv(path)[["dataset", "x", "y"]]
    save("anscombe", df,
         dataset=df.dataset.to_numpy("U4"),
         x=df.x.to_numpy(float), y=df.y.to_numpy(float))


def build_datasaurus(path: Path) -> None:
    df = pd.read_csv(path, sep="\t")
    df.columns = [c.lower() for c in df.columns]
    df = df[["dataset", "x", "y"]]
    save("datasaurus", df,
         dataset=df.dataset.to_numpy("U12"),
         x=df.x.to_numpy(float), y=df.y.to_numpy(float))


def build_flights(path: Path) -> None:
    df = pd.read_csv(path)
    matrix = (df.pivot(index="month", columns="year", values="passengers")
                .reindex(MONTH_ORDER))                       # rows Jan..Dec
    save("flights", df,
         passengers=df.passengers.to_numpy(int),
         year=df.year.to_numpy(int),
         month=df.month.to_numpy("U12"),
         matrix=matrix.to_numpy(float),                      # 12 (month) x 12 (year)
         months=np.array(MONTH_ORDER, dtype="U12"),
         years=matrix.columns.to_numpy(int))


def build_ring_slot(path: Path) -> None:
    """Parse a 2-port Touchstone (.s2p), RI format, GHz. Column order S11 S21 S12 S22."""
    freqs, s = [], []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line[0] in "!#":                      # comments / option line
            continue
        v = [float(x) for x in line.split()]
        freqs.append(v[0])
        s.append([v[1] + 1j * v[2], v[3] + 1j * v[4],
                  v[5] + 1j * v[6], v[7] + 1j * v[8]])
    freq = np.asarray(freqs)
    s11, s21, s12, s22 = np.asarray(s).T
    db = lambda z: 20 * np.log10(np.abs(z))
    df = pd.DataFrame({"freq_ghz": freq,
                       "s11_db": db(s11), "s21_db": db(s21), "s22_db": db(s22),
                       "s11_deg": np.angle(s11, deg=True),
                       "s21_deg": np.angle(s21, deg=True)})
    save("rf_ring_slot", df, freq_ghz=freq, s11=s11, s21=s21, s12=s12, s22=s22)


# --- synthesized RF datasets (physically plausible, deterministic) ----------

def build_antenna_pattern() -> None:
    """8-element uniform linear array, half-wavelength spacing: normalized pattern."""
    n, d = 8, 0.5
    theta = np.linspace(-90, 90, 1801)
    psi = 2 * np.pi * d * np.sin(np.deg2rad(theta))
    with np.errstate(invalid="ignore", divide="ignore"):
        af = np.sin(n * psi / 2) / (n * np.sin(psi / 2))
    af[np.isnan(af)] = 1.0                                    # broadside limit
    gain = np.clip(20 * np.log10(np.abs(af) + 1e-9), -40, 0)
    df = pd.DataFrame({"angle_deg": theta, "gain_db": gain})
    save("rf_antenna_pattern", df, angle_deg=theta, gain_db=gain)


def build_pa_efficiency() -> None:
    """Power amplifier sweep: gain compression + drain efficiency / PAE vs drive."""
    pin = np.linspace(-15, 15, 121)                          # input power, dBm
    small_signal_gain = 15.0
    compression = 3.5 / (1 + np.exp(-(pin - 6) / 2.0))       # up to ~3.5 dB
    gain = small_signal_gain - compression
    pout = pin + gain
    drain_eff = 68.0 / (1 + np.exp(-(pout - 19) / 3.5))      # rises toward ~68%
    pae = drain_eff * (1 - 10 ** (-gain / 10))
    df = pd.DataFrame({"pin_dbm": pin, "pout_dbm": pout, "gain_db": gain,
                       "drain_eff_pct": drain_eff, "pae_pct": pae})
    save("rf_pa_efficiency", df, **{c: df[c].to_numpy() for c in df.columns})


def build_dut_report() -> None:
    """A device-under-test report: several parameters over frequency."""
    rng = np.random.default_rng(7)
    f = np.linspace(1.0, 6.0, 251)                           # GHz
    gain = 22 - 0.8 * (f - 1) + 0.3 * np.sin(2 * f) + rng.normal(0, 0.08, f.size)
    nf = 1.2 + 0.15 * (f - 1) + 0.10 * np.sin(3 * f) + rng.normal(0, 0.03, f.size)
    return_loss = -18 + 4 * np.sin(1.5 * f + 0.5) + rng.normal(0, 0.4, f.size)
    p1db = 18 - 0.4 * (f - 1) + rng.normal(0, 0.12, f.size)
    df = pd.DataFrame({"freq_ghz": f, "gain_db": gain, "noise_figure_db": nf,
                       "return_loss_db": return_loss, "output_p1db_dbm": p1db})
    save("rf_dut_report", df, **{c: df[c].to_numpy() for c in df.columns})


REAL = {
    "penguins.csv": build_penguins,
    "gapminder.csv": build_gapminder,
    "anscombe.csv": build_anscombe,
    "datasaurus.tsv": build_datasaurus,
    "flights.csv": build_flights,
    "ring_slot.s2p": build_ring_slot,
}
SYNTHETIC = [build_antenna_pattern, build_pa_efficiency, build_dut_report]


def main() -> int:
    print("Real datasets (download -> tidy):")
    failures = 0
    for name, builder in REAL.items():
        path = fetch(name)
        if path is None:
            failures += 1
            continue
        builder(path)
    print("Synthesized RF datasets:")
    for builder in SYNTHETIC:
        builder()
    print(f"Done ({failures} download failure(s)). Outputs in {DATA}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
