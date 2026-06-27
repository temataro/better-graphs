# Datasets

Working data for the curriculum. Two formats per dataset:

- **`<name>.csv`** — tidy (one row per observation), for `pandas.read_csv`.
- **`<name>.npz`** — the same data as named NumPy arrays, for `np.load("<name>.npz")["col"]`
  (complex S-parameters and the flights matrix are preserved as real arrays here).

## (Re)building

```sh
uv run python data/build_datasets.py
```

Real datasets are downloaded to `data/raw/` and reshaped; the synthesized RF sets are generated
deterministically. **The data is not committed** — `data/raw/`, `data/*.csv`, and `data/*.npz` are all
gitignored. This script (plus this manifest) is the tracked source of truth; regenerate the data rather
than committing it. Re-running reuses any raw files already present.

## What's here

| File | Rows | What it is | Good for | Source · license |
|---|---|---|---|---|
| `penguins` | 342 | Palmer penguins: species × bill/flipper/mass | distribution, scatter, categorical small-multiples | [seaborn-data] · CC0 |
| `gapminder` | 1704 | country-year life expectancy, GDP/cap, population (1952–2007) | evolution over time, bubble, ranking, slope | [Rdatasets/gapminder] · CC-BY 4.0 (Gapminder) |
| `anscombe` | 44 | Anscombe's quartet — 4 sets, near-identical summary stats | "why you must plot it"; relationship | [seaborn-data] · public domain |
| `datasaurus` | 1846 | Datasaurus Dozen — 13 sets, identical stats, wild shapes | distribution, the visualize-first argument | [datasauRus] · Matejka & Fitzmaurice 2017 (MIT pkg) |
| `flights` | 144 | monthly airline passengers 1949–1960 (+ 12×12 `matrix`) | heatmap, seasonality, line | [seaborn-data] · public domain |
| `rf_ring_slot` | 201 | **measured** 2-port S-parameters, 75–110 GHz (complex) | S-params over freq (dB), Smith chart, group delay | [scikit-rf] · BSD-3 |
| `rf_antenna_pattern` | 1801 | synthesized 8-element ULA pattern, normalized gain vs angle | polar plot, dB radial axis, sidelobe annotation | synthesized · CC0 |
| `rf_pa_efficiency` | 121 | synthesized PA sweep: gain compression, drain eff, PAE vs drive | twin-axis, P1dB / peak-PAE callouts | synthesized · CC0 |
| `rf_dut_report` | 251 | synthesized DUT: gain / NF / return-loss / P1dB over 1–6 GHz | multi-panel detailed figure, small multiples | synthesized · CC0 |

[seaborn-data]: https://github.com/mwaskom/seaborn-data
[Rdatasets/gapminder]: https://github.com/vincentarelbundock/Rdatasets/blob/master/csv/gapminder/gapminder.csv
[datasauRus]: https://github.com/jumpingrivers/datasauRus
[scikit-rf]: https://github.com/scikit-rf/scikit-rf/tree/master/skrf/data

## Adding a candidate

Drop a `fetch` URL into `SOURCES` and a `build_*` function in `build_datasets.py` that ends with
`save(name, df, **arrays)`. Keep raw acquisition in the script (not manual steps) so the set stays
reproducible. Candidates not yet pulled in: Our World in Data CO₂/energy (rich time series, but large —
subset it), NYC taxi (spatial), Vega datasets (`vega_datasets`).
