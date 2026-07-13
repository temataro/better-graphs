"""Palette checks you run, not eyeball.

A palette is a claim — "these colours are distinguishable, by everyone, on this
background" — and the claim is computable. This module checks it:

- **CVD separation.** Simulate protanopia / deuteranopia / tritanopia (Machado
  et al. 2009, severity 1.0) and measure the minimum pairwise CIE76 ΔE within
  each simulated palette. Target ≥ 12; 8–12 is a floor that is only acceptable
  with a secondary encoding (direct labels, markers, dash patterns).
- **Lightness band.** Series colours should sit in a common L* band (spread
  ≤ ~40) so no series visually shouts or vanishes.
- **Chroma floor.** Greys masquerading as series colours (C*ab < 15) get flagged
  — context grey is a *role*, not a palette member.
- **Background contrast.** Every colour needs WCAG contrast ≥ 3:1 against the
  chart surface to survive thin lines and small markers.

Usage::

    uv run python visualization-curriculum/check_palette.py "#6400FF,#1AA7A0,#E8833A" --bg "#FAF7F2"

or from code::

    from check_palette import check
    report = check(["#6400FF", "#1AA7A0"], bg="#FAF7F2")   # dict; report["ok"] is the verdict
"""
from __future__ import annotations

import numpy as np

# Machado, Oliveira & Fernandes (2009), severity 1.0 — applied in *linear* RGB.
CVD_MATRICES = {
    "protanopia": np.array([
        [0.152286, 1.052583, -0.204868],
        [0.114503, 0.786281, 0.099216],
        [-0.003882, -0.048116, 1.051998],
    ]),
    "deuteranopia": np.array([
        [0.367322, 0.860646, -0.227968],
        [0.280085, 0.672501, 0.047413],
        [-0.011820, 0.042940, 0.968881],
    ]),
    "tritanopia": np.array([
        [1.255528, -0.076749, -0.178779],
        [-0.078411, 0.930809, 0.147602],
        [0.004733, 0.691367, 0.303900],
    ]),
}

# sRGB (D65) → XYZ
RGB_TO_XYZ = np.array([
    [0.4124564, 0.3575761, 0.1804375],
    [0.2126729, 0.7151522, 0.0721750],
    [0.0193339, 0.1191920, 0.9503041],
])
D65 = np.array([0.95047, 1.00000, 1.08883])


def hex_to_srgb(color: str) -> np.ndarray:
    color = color.strip().lstrip("#")
    return np.array([int(color[i:i + 2], 16) for i in (0, 2, 4)]) / 255.0


def srgb_to_linear(srgb: np.ndarray) -> np.ndarray:
    return np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)


def linear_to_lab(linear_rgb: np.ndarray) -> np.ndarray:
    xyz = RGB_TO_XYZ @ np.clip(linear_rgb, 0, 1)
    t = xyz / D65
    f = np.where(t > (6 / 29) ** 3, np.cbrt(t), t / (3 * (6 / 29) ** 2) + 4 / 29)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])


def hex_to_lab(color: str, cvd: str | None = None) -> np.ndarray:
    linear = srgb_to_linear(hex_to_srgb(color))
    if cvd:
        linear = CVD_MATRICES[cvd] @ linear
    return linear_to_lab(linear)


def delta_e(lab_a: np.ndarray, lab_b: np.ndarray) -> float:
    """CIE76 — coarse but monotone enough for a pass/fail gate."""
    return float(np.linalg.norm(lab_a - lab_b))


def relative_luminance(color: str) -> float:
    return float(np.array([0.2126, 0.7152, 0.0722]) @ srgb_to_linear(hex_to_srgb(color)))


def contrast_ratio(fg: str, bg: str) -> float:
    lums = sorted([relative_luminance(fg), relative_luminance(bg)], reverse=True)
    return (lums[0] + 0.05) / (lums[1] + 0.05)


def min_pairwise_delta_e(colors: list[str], cvd: str | None = None) -> tuple[float, tuple[str, str]]:
    labs = [hex_to_lab(c, cvd) for c in colors]
    worst, worst_pair = np.inf, (colors[0], colors[0])
    for i in range(len(colors)):
        for j in range(i + 1, len(colors)):
            d = delta_e(labs[i], labs[j])
            if d < worst:
                worst, worst_pair = d, (colors[i], colors[j])
    return worst, worst_pair


def check(colors: list[str], bg: str = "#FFFFFF",
          de_target: float = 12.0, de_floor: float = 8.0,
          contrast_min: float = 3.0, lightness_spread_max: float = 40.0,
          chroma_floor: float = 15.0) -> dict:
    """Run every check; returns a dict report with an overall boolean ``ok``."""
    labs = [hex_to_lab(c) for c in colors]
    lightness = [lab[0] for lab in labs]
    chroma = [float(np.hypot(lab[1], lab[2])) for lab in labs]

    separation = {}
    for cvd in (None, *CVD_MATRICES):
        worst, pair = min_pairwise_delta_e(colors, cvd)
        separation[cvd or "normal"] = {
            "min_delta_e": round(worst, 1), "worst_pair": pair,
            "verdict": "PASS" if worst >= de_target else ("FLOOR" if worst >= de_floor else "FAIL"),
        }
    contrast = {c: {"ratio": round(contrast_ratio(c, bg), 2),
                    "verdict": "PASS" if contrast_ratio(c, bg) >= contrast_min else "WARN"}
                for c in colors}
    spread = max(lightness) - min(lightness)
    low_chroma = [c for c, ch in zip(colors, chroma) if ch < chroma_floor]

    ok = (all(v["verdict"] != "FAIL" for v in separation.values())
          and all(v["verdict"] == "PASS" for v in contrast.values())
          and spread <= lightness_spread_max and not low_chroma)
    return {
        "ok": ok,
        "separation": separation,
        "contrast_vs_bg": contrast,
        "lightness": {"values": [round(l, 1) for l in lightness], "spread": round(spread, 1),
                      "verdict": "PASS" if spread <= lightness_spread_max else "WARN"},
        "chroma": {"values": [round(c, 1) for c in chroma], "below_floor": low_chroma},
    }


def main() -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("colors", help="comma-separated hex colours, e.g. '#6400FF,#1AA7A0'")
    parser.add_argument("--bg", default="#FFFFFF", help="chart surface colour (default white)")
    args = parser.parse_args()

    report = check([c for c in args.colors.split(",") if c.strip()], bg=args.bg)
    print(json.dumps(report, indent=2))
    print(f"\noverall: {'OK' if report['ok'] else 'NOT OK — fix before shipping'}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
