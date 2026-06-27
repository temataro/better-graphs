"""Numpy-native data helpers for the curriculum — no pandas in the plotting cells.

A dataset is just a **dict of numpy arrays** (its columns), loaded from the built
``.npz``::

    d = load("gapminder")              # {"year": int64[], "lifeExp": float64[], "country": <U[], ...}
    d["lifeExp"][d["year"] == 2007]    # plain numpy indexing — no hidden index alignment

The named keys are unavoidable (the data has named fields), but the *values* are raw
arrays and every operation below is explicit numpy. Aggregations are NaN-aware and use
``ddof=1`` so results match what pandas would have produced (drop-in parity).
"""
from pathlib import Path
import numpy as np

DATA = Path("../data")

# Month names in calendar order — a search list / index for the flights data.
MONTHS = np.array(["January", "February", "March", "April", "May", "June", "July",
                   "August", "September", "October", "November", "December"])


def load(name):
    """Return a built dataset as a dict of numpy arrays (from ``data/<name>.npz``).

    The data is gitignored (regenerable), so a fresh clone has none yet — fail with the
    exact build command instead of a bare error three frames deep.
    """
    path = DATA / f"{name}.npz"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found — the datasets are gitignored. Build them first:\n"
            f"    uv run python data/build_datasets.py")
    with np.load(path, allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def select(d, mask):
    """Row-subset every column of `d` by a boolean mask or index array.

    Columns whose first axis doesn't match the table's row count (e.g. a pre-pivoted
    ``matrix``) pass through unchanged.
    """
    rows = max(v.shape[0] for v in d.values() if v.ndim >= 1)
    return {k: (v[mask] if v.ndim >= 1 and v.shape[0] == rows else v) for k, v in d.items()}


def group(keys, values, func=np.nanmean, order=None):
    """Aggregate `values` within groups of `keys`.

    Returns ``(labels, aggregates)``. `order` fixes the label order (otherwise
    sorted-unique); `func` should be NaN-aware (default ``np.nanmean``) to match pandas.
    """
    labels = np.asarray(order) if order is not None else np.unique(keys)
    agg = np.array([func(values[keys == k]) for k in labels])
    return labels, agg


def pivot(row_keys, col_keys, values, rows=None, cols=None, fill=np.nan):
    """Reshape long ``(row_keys, col_keys, values)`` into a ``rows × cols`` matrix."""
    rows = np.unique(row_keys) if rows is None else np.asarray(rows)
    cols = np.unique(col_keys) if cols is None else np.asarray(cols)
    ri = {r: i for i, r in enumerate(rows)}
    ci = {c: j for j, c in enumerate(cols)}
    M = np.full((len(rows), len(cols)), fill, float)
    for rk, ck, v in zip(row_keys, col_keys, values):
        if rk in ri and ck in ci:
            M[ri[rk], ci[ck]] = v
    return rows, cols, M


def rolling_mean(y, window):
    """Centred moving average; the window-edge positions are NaN.

    Aligned to match ``pandas.Series.rolling(window, center=True).mean()``.
    """
    y = np.asarray(y, float)
    out = np.full(y.shape, np.nan)
    c = np.convolve(y, np.ones(window) / window, mode="valid")
    lo = window // 2          # pandas centres an even window at window//2
    out[lo:lo + len(c)] = c
    return out


def corr(x, y):
    """Pearson r between two arrays (``np.corrcoef``), matching pandas ``.corr()``."""
    return float(np.corrcoef(x, y)[0, 1])


def std(x):
    """Sample standard deviation (``ddof=1``), NaN-aware — matches pandas ``.std()``."""
    return float(np.nanstd(x, ddof=1))


def finite(*cols):
    """Boolean mask where all given numeric columns are non-NaN (≈ pandas ``dropna``)."""
    m = np.ones(len(cols[0]), bool)
    for c in cols:
        m &= np.isfinite(c)
    return m
