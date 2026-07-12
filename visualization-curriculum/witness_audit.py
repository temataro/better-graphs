"""Deterministic accessibility and structural audits for Witness figures.

This module deliberately has no Matplotlib dependency.  It supplies the colour
math used by both figure construction and export receipts, plus small immutable
audit records that :mod:`witness` can compose with its figure-level checks.

Colour differences are CIE76 distances in CIE Lab under a D65 illuminant.  The
colour-vision-deficiency simulations use the severity-1.0 matrices published by
Machado, Oliveira, and Fernandes (2009), applied in linear RGB.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import Iterable, Literal, Mapping, Sequence

import numpy as np


Severity = Literal["error", "warning", "review"]
Color = str | Sequence[float] | np.ndarray
AlphaColor = str | Sequence[float] | np.ndarray

TEXT_CONTRAST_MIN = 4.5
ESSENTIAL_MARK_CONTRAST_MIN = 3.0
CVD_DELTA_E_TARGET = 12.0
CVD_DELTA_E_FAIL = 8.0
GRAYSCALE_DELTA_L_TARGET = 10.0

# The selected F2 x P2 light identity.  ``FAINT`` and ``GRID`` are support
# colours, not text or essential marks, so their intentionally quiet contrast is
# measured but is not held to the thresholds above.
SURFACE = "#FBF5E8"
INK = "#19231E"
MUTED = "#556258"
FAINT = "#7B857D"
GRID = "#DED8C8"
CATEGORICAL = ("#006B5E", "#A33A2B", "#67469B")


# Machado et al. (2009), anomalous trichromacy severity 1.0.  The values are
# intended for multiplication by a column vector in linear RGB.
CVD_MATRICES: Mapping[str, np.ndarray] = {
    "protanopia": np.array(
        [
            [0.152286, 1.052583, -0.204868],
            [0.114503, 0.786281, 0.099216],
            [-0.003882, -0.048116, 1.051998],
        ],
        dtype=float,
    ),
    "deuteranopia": np.array(
        [
            [0.367322, 0.860646, -0.227968],
            [0.280085, 0.672501, 0.047413],
            [-0.011820, 0.042940, 0.968881],
        ],
        dtype=float,
    ),
    "tritanopia": np.array(
        [
            [1.255528, -0.076749, -0.178779],
            [-0.078411, 0.930809, 0.147602],
            [0.004733, 0.691367, 0.303900],
        ],
        dtype=float,
    ),
}

RGB_TO_XYZ = np.array(
    [
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041],
    ],
    dtype=float,
)
D65_WHITE = np.array([0.95047, 1.0, 1.08883], dtype=float)


def _unit_rgb(value: Sequence[float] | np.ndarray, *, name: str) -> np.ndarray:
    """Return a finite float RGB array whose final dimension is three."""

    rgb = np.asarray(value, dtype=float)
    if rgb.ndim == 0 or rgb.shape[-1] != 3:
        raise ValueError(f"{name} must have a final dimension of three")
    if not np.all(np.isfinite(rgb)):
        raise ValueError(f"{name} must contain only finite values")
    if np.any((rgb < 0) | (rgb > 1)):
        raise ValueError(f"{name} values must lie between 0 and 1")
    return rgb


def hex_to_srgb(color: str) -> np.ndarray:
    """Convert ``#RRGGBB`` (or shorthand ``#RGB``) to unit-range sRGB."""

    if not isinstance(color, str):
        raise TypeError("hex colour must be a string")
    value = color.removeprefix("#")
    if len(value) == 3:
        value = "".join(character * 2 for character in value)
    if len(value) != 6:
        raise ValueError("hex colour must contain three or six hexadecimal digits")
    try:
        channels = [int(value[index : index + 2], 16) for index in (0, 2, 4)]
    except ValueError as error:
        raise ValueError("hex colour contains a non-hexadecimal digit") from error
    return np.asarray(channels, dtype=float) / 255.0


def srgb_to_hex(srgb: Sequence[float] | np.ndarray) -> str:
    """Convert one unit-range sRGB triplet to an uppercase ``#RRGGBB`` value."""

    rgb = _unit_rgb(srgb, name="sRGB")
    if rgb.shape != (3,):
        raise ValueError("srgb_to_hex accepts one RGB triplet")
    channels = np.rint(rgb * 255).astype(int)
    return "#" + "".join(f"{channel:02X}" for channel in channels)


def srgb_to_linear(srgb: Sequence[float] | np.ndarray) -> np.ndarray:
    """Decode one or more unit-range sRGB colours to linear RGB."""

    rgb = _unit_rgb(srgb, name="sRGB")
    return np.where(
        rgb <= 0.04045,
        rgb / 12.92,
        ((rgb + 0.055) / 1.055) ** 2.4,
    )


def linear_to_srgb(linear_rgb: Sequence[float] | np.ndarray) -> np.ndarray:
    """Encode one or more unit-range linear RGB colours as sRGB."""

    linear = _unit_rgb(linear_rgb, name="linear RGB")
    return np.where(
        linear <= 0.0031308,
        12.92 * linear,
        1.055 * linear ** (1 / 2.4) - 0.055,
    )


def linear_rgb_to_lab(linear_rgb: Sequence[float] | np.ndarray) -> np.ndarray:
    """Convert unit-range linear RGB to CIE Lab (D65, 2-degree observer)."""

    linear = _unit_rgb(linear_rgb, name="linear RGB")
    xyz = linear @ RGB_TO_XYZ.T
    ratio = xyz / D65_WHITE
    epsilon = (6 / 29) ** 3
    shaped = np.where(
        ratio > epsilon,
        np.cbrt(ratio),
        ratio / (3 * (6 / 29) ** 2) + 4 / 29,
    )
    lightness = 116 * shaped[..., 1] - 16
    green_red = 500 * (shaped[..., 0] - shaped[..., 1])
    blue_yellow = 200 * (shaped[..., 1] - shaped[..., 2])
    return np.stack((lightness, green_red, blue_yellow), axis=-1)


def srgb_to_lab(srgb: Sequence[float] | np.ndarray) -> np.ndarray:
    """Convert unit-range sRGB to CIE Lab."""

    return linear_rgb_to_lab(srgb_to_linear(srgb))


def hex_to_lab(color: str) -> np.ndarray:
    """Convert a hexadecimal sRGB colour to CIE Lab."""

    return srgb_to_lab(hex_to_srgb(color))


def _as_srgb(color: Color) -> np.ndarray:
    return hex_to_srgb(color) if isinstance(color, str) else _unit_rgb(color, name="sRGB")


def _as_srgba(color: AlphaColor, *, name: str) -> np.ndarray:
    """Return one RGB or RGBA colour as a unit-range RGBA triplet.

    Hex input accepts ``#RGB``, ``#RGBA``, ``#RRGGBB``, and ``#RRGGBBAA``.
    The alpha-last convention matches Matplotlib's public colour representation.
    """

    if isinstance(color, str):
        value = color.removeprefix("#")
        if len(value) in (3, 4):
            value = "".join(character * 2 for character in value)
        if len(value) not in (6, 8):
            raise ValueError(
                f"{name} must contain three, four, six, or eight hexadecimal digits"
            )
        try:
            channels = np.asarray(
                [int(value[index : index + 2], 16) for index in range(0, len(value), 2)],
                dtype=float,
            ) / 255.0
        except ValueError as error:
            raise ValueError(f"{name} contains a non-hexadecimal digit") from error
    else:
        channels = np.asarray(color, dtype=float)
        if channels.shape not in ((3,), (4,)):
            raise ValueError(f"{name} must be one RGB or RGBA colour")
        if not np.all(np.isfinite(channels)):
            raise ValueError(f"{name} must contain only finite values")
        if np.any((channels < 0) | (channels > 1)):
            raise ValueError(f"{name} values must lie between 0 and 1")

    if channels.shape == (3,):
        channels = np.append(channels, 1.0)
    return channels


def composite_rgba(foreground: AlphaColor, surface: AlphaColor) -> np.ndarray:
    """Composite one RGB(A) foreground over one opaque surface in sRGB.

    The returned value is the effective opaque sRGB colour that readers see and
    therefore the colour against which WCAG contrast and palette separation must
    be computed.  The surface may be supplied as RGB or as RGBA with alpha 1.
    """

    foreground_rgba = _as_srgba(foreground, name="foreground")
    surface_rgba = _as_srgba(surface, name="surface")
    if not np.isclose(surface_rgba[3], 1.0, rtol=0, atol=1e-12):
        raise ValueError("colour-audit surface must be opaque")
    return (
        foreground_rgba[3] * foreground_rgba[:3]
        + (1 - foreground_rgba[3]) * surface_rgba[:3]
    )


def relative_luminance(color: Color) -> float:
    """Return WCAG relative luminance for one sRGB colour."""

    linear = srgb_to_linear(_as_srgb(color))
    if linear.shape != (3,):
        raise ValueError("relative_luminance accepts one RGB triplet")
    return float(linear @ np.array([0.2126, 0.7152, 0.0722]))


def contrast_ratio(foreground: Color, background: Color) -> float:
    """Return the WCAG contrast ratio between two opaque sRGB colours."""

    lighter, darker = sorted(
        (relative_luminance(foreground), relative_luminance(background)),
        reverse=True,
    )
    return (lighter + 0.05) / (darker + 0.05)


def simulate_cvd(color: Color, deficiency: str) -> np.ndarray:
    """Simulate complete protanopia, deuteranopia, or tritanopia in sRGB.

    The Machado matrix is applied in linear RGB.  Out-of-gamut simulated values
    are clipped before they are encoded back to sRGB.
    """

    if deficiency not in CVD_MATRICES:
        choices = ", ".join(CVD_MATRICES)
        raise ValueError(f"unknown CVD simulation {deficiency!r}; choose {choices}")
    linear = srgb_to_linear(_as_srgb(color))
    simulated = linear @ CVD_MATRICES[deficiency].T
    return linear_to_srgb(np.clip(simulated, 0, 1))


def delta_e(first_lab: Sequence[float], second_lab: Sequence[float]) -> float:
    """Return the CIE76 distance between two Lab triplets."""

    first = np.asarray(first_lab, dtype=float)
    second = np.asarray(second_lab, dtype=float)
    if first.shape != (3,) or second.shape != (3,):
        raise ValueError("delta_e accepts two Lab triplets")
    if not np.all(np.isfinite(first)) or not np.all(np.isfinite(second)):
        raise ValueError("Lab values must be finite")
    return float(np.linalg.norm(first - second))


def color_delta_e(
    first: Color,
    second: Color,
    *,
    deficiency: str | None = None,
) -> float:
    """Return CIE76 distance between two colours, optionally after CVD simulation."""

    first_srgb = _as_srgb(first)
    second_srgb = _as_srgb(second)
    if deficiency is not None:
        first_srgb = simulate_cvd(first_srgb, deficiency)
        second_srgb = simulate_cvd(second_srgb, deficiency)
    return delta_e(srgb_to_lab(first_srgb), srgb_to_lab(second_srgb))


def _color_values(colors: Mapping[str, Color] | Iterable[Color]) -> tuple[Color, ...]:
    return tuple(colors.values() if isinstance(colors, Mapping) else colors)


def minimum_pairwise_delta_e(
    colors: Mapping[str, Color] | Iterable[Color],
    *,
    deficiency: str | None = None,
) -> float:
    """Return the smallest CIE76 distance among at least two colours."""

    values = _color_values(colors)
    if len(values) < 2:
        raise ValueError("pairwise separation needs at least two colours")
    return min(
        color_delta_e(first, second, deficiency=deficiency)
        for first, second in combinations(values, 2)
    )


def lightness(color: Color, *, deficiency: str | None = None) -> float:
    """Return CIE L*; this is the palette's grayscale/lightness coordinate."""

    srgb = _as_srgb(color)
    if srgb.shape != (3,):
        raise ValueError("lightness accepts one RGB triplet")
    if deficiency is not None:
        srgb = simulate_cvd(srgb, deficiency)
    return float(srgb_to_lab(srgb)[0])


def minimum_pairwise_lightness_difference(
    colors: Mapping[str, Color] | Iterable[Color],
) -> float:
    """Return the smallest absolute CIE L* difference among the colours."""

    values = _color_values(colors)
    if len(values) < 2:
        raise ValueError("pairwise separation needs at least two colours")
    levels = [lightness(color) for color in values]
    return min(abs(first - second) for first, second in combinations(levels, 2))


@dataclass(frozen=True)
class AuditFinding:
    """One deterministic error, warning, or human-review prompt."""

    code: str
    severity: Severity
    message: str
    subject: str | None = None
    details: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("audit finding code cannot be empty")
        if self.severity not in ("error", "warning", "review"):
            raise ValueError(f"unknown audit severity {self.severity!r}")
        if not self.message.strip():
            raise ValueError("audit finding message cannot be empty")

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serialisable representation for an export receipt."""

        result: dict[str, object] = {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
        }
        if self.subject is not None:
            result["subject"] = self.subject
        if self.details:
            result["details"] = dict(self.details)
        return result


class AuditError(RuntimeError):
    """Raised when strict export is asked to enforce a report with errors."""

    def __init__(self, report: "AuditReport") -> None:
        self.report = report
        codes = ", ".join(finding.code for finding in report.errors)
        super().__init__(f"audit failed with {len(report.errors)} error(s): {codes}")


@dataclass(frozen=True)
class AuditReport:
    """Composable collection of audit findings."""

    findings: tuple[AuditFinding, ...] = ()

    def __post_init__(self) -> None:
        findings = tuple(self.findings)
        if not all(isinstance(finding, AuditFinding) for finding in findings):
            raise TypeError("AuditReport findings must be AuditFinding instances")
        object.__setattr__(self, "findings", findings)

    @property
    def errors(self) -> tuple[AuditFinding, ...]:
        return tuple(finding for finding in self.findings if finding.severity == "error")

    @property
    def warnings(self) -> tuple[AuditFinding, ...]:
        return tuple(finding for finding in self.findings if finding.severity == "warning")

    @property
    def reviews(self) -> tuple[AuditFinding, ...]:
        return tuple(finding for finding in self.findings if finding.severity == "review")

    @property
    def passed(self) -> bool:
        """Whether the report has no deterministic errors."""

        return not self.errors

    @property
    def status(self) -> str:
        if self.errors:
            return "error"
        if self.warnings:
            return "warning"
        if self.reviews:
            return "review"
        return "pass"

    def add(self, finding: AuditFinding) -> "AuditReport":
        return AuditReport((*self.findings, finding))

    def extend(self, findings: Iterable[AuditFinding]) -> "AuditReport":
        return AuditReport((*self.findings, *tuple(findings)))

    def enforce(self) -> None:
        """Raise :class:`AuditError` when deterministic errors are present."""

        if self.errors:
            raise AuditError(self)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serialisable summary and finding list."""

        return {
            "status": self.status,
            "counts": {
                "error": len(self.errors),
                "warning": len(self.warnings),
                "review": len(self.reviews),
            },
            "findings": [finding.to_dict() for finding in self.findings],
        }


def merge_reports(*reports: AuditReport) -> AuditReport:
    """Combine reports without discarding their finding order."""

    return AuditReport(
        tuple(finding for report in reports for finding in report.findings)
    )


def audit_condition(
    condition: bool,
    *,
    code: str,
    severity: Severity,
    message: str,
    subject: str | None = None,
    details: Mapping[str, object] | None = None,
) -> AuditReport:
    """Create an empty report when a condition holds, otherwise one finding."""

    if condition:
        return AuditReport()
    return AuditReport(
        (
            AuditFinding(
                code=code,
                severity=severity,
                message=message,
                subject=subject,
                details={} if details is None else details,
            ),
        )
    )


def _missing(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    try:
        return len(value) == 0  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False


def audit_required_fields(
    values: Mapping[str, object],
    required: Iterable[str],
    *,
    subject: str = "figure",
    severity: Severity = "error",
) -> AuditReport:
    """Audit required semantic fields, treating blank strings as absent."""

    findings = []
    for field_name in required:
        if field_name not in values or _missing(values[field_name]):
            readable_name = field_name.replace("_", " ")
            findings.append(
                AuditFinding(
                    code=f"{subject}.missing_{field_name}",
                    severity=severity,
                    message=f"{subject.capitalize()} requires {readable_name}.",
                    subject=subject,
                    details={"field": field_name},
                )
            )
    return AuditReport(tuple(findings))


@dataclass(frozen=True)
class PaletteReport:
    """Computed accessibility receipt for one palette on one surface."""

    surface: str
    text_contrast: Mapping[str, float]
    mark_contrast: Mapping[str, float]
    support_contrast: Mapping[str, float]
    cvd_min_delta_e: Mapping[str, float]
    grayscale_min_delta_l: float | None
    text_contrast_min: float
    mark_contrast_min: float
    cvd_delta_e_target: float
    cvd_delta_e_fail: float
    grayscale_delta_l_target: float
    findings: tuple[AuditFinding, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "findings", tuple(self.findings))

    @property
    def audit(self) -> AuditReport:
        return AuditReport(self.findings)

    @property
    def passed(self) -> bool:
        return self.audit.passed

    @property
    def minimum_text_contrast(self) -> float | None:
        return min(self.text_contrast.values(), default=None)

    @property
    def minimum_mark_contrast(self) -> float | None:
        return min(self.mark_contrast.values(), default=None)

    @property
    def minimum_cvd_delta_e(self) -> float | None:
        cvd_values = [
            separation
            for vision, separation in self.cvd_min_delta_e.items()
            if vision != "typical"
        ]
        return min(cvd_values, default=None)

    def enforce(self) -> None:
        self.audit.enforce()

    def to_dict(self) -> dict[str, object]:
        """Return all metrics, thresholds, and findings for a receipt."""

        return {
            "surface": self.surface,
            "text_contrast": dict(self.text_contrast),
            "mark_contrast": dict(self.mark_contrast),
            "support_contrast": dict(self.support_contrast),
            "cvd_min_delta_e": dict(self.cvd_min_delta_e),
            "grayscale_min_delta_l": self.grayscale_min_delta_l,
            "thresholds": {
                "text_contrast_min": self.text_contrast_min,
                "essential_mark_contrast_min": self.mark_contrast_min,
                "cvd_delta_e_target": self.cvd_delta_e_target,
                "cvd_delta_e_fail": self.cvd_delta_e_fail,
                "grayscale_delta_l_target": self.grayscale_delta_l_target,
            },
            "audit": self.audit.to_dict(),
        }


def _named_colors(
    colors: Mapping[str, Color] | Iterable[Color] | None,
    *,
    prefix: str,
) -> dict[str, Color]:
    if colors is None:
        return {}
    if isinstance(colors, Mapping):
        return dict(colors)
    return {f"{prefix}_{index}": color for index, color in enumerate(colors, start=1)}


def _minimum_named_pair(
    colors: Mapping[str, Color],
    *,
    deficiency: str | None = None,
) -> tuple[str, str, float]:
    """Return the names and distance of the least-separated colour pair."""

    if len(colors) < 2:
        raise ValueError("pairwise separation needs at least two colours")
    pairs = (
        (
            first_name,
            second_name,
            color_delta_e(first, second, deficiency=deficiency),
        )
        for (first_name, first), (second_name, second) in combinations(
            colors.items(),
            2,
        )
    )
    return min(pairs, key=lambda pair: pair[2])


def _validated_redundancy(
    redundant_channels: Mapping[str, bool] | None,
    names: Iterable[str],
) -> dict[str, bool]:
    """Validate redundancy declarations against categorical colour names."""

    redundancy = {} if redundant_channels is None else dict(redundant_channels)
    known_names = set(names)
    unknown_names = set(redundancy) - known_names
    if unknown_names:
        unknown = ", ".join(sorted(unknown_names))
        raise ValueError(f"redundancy declared for unknown categorical colour(s): {unknown}")
    for name, value in redundancy.items():
        if not isinstance(value, (bool, np.bool_)):
            raise TypeError(f"redundancy for {name!r} must be boolean")
    return {name: bool(redundancy.get(name, False)) for name in known_names}


def audit_palette(
    surface: Color,
    *,
    text_colors: Mapping[str, Color] | Iterable[Color] = (),
    mark_colors: Mapping[str, Color] | Iterable[Color] = (),
    categorical_colors: Mapping[str, Color] | Iterable[Color] | None = None,
    redundant_channels: Mapping[str, bool] | None = None,
    support_colors: Mapping[str, Color] | Iterable[Color] = (),
    text_contrast_min: float = TEXT_CONTRAST_MIN,
    mark_contrast_min: float = ESSENTIAL_MARK_CONTRAST_MIN,
    cvd_delta_e_target: float = CVD_DELTA_E_TARGET,
    cvd_delta_e_fail: float = CVD_DELTA_E_FAIL,
    grayscale_delta_l_target: float = GRAYSCALE_DELTA_L_TARGET,
) -> PaletteReport:
    """Audit text, essential marks, CVD separation, and grayscale separation.

    Text and essential marks below their WCAG-derived minima are errors.  A CVD
    pairwise distance below ``cvd_delta_e_fail`` is an error; a distance between
    that floor and the preferred target is a warning.  Weak grayscale separation
    warns only for confusing pairs where one or both colours lack a declared
    redundant marker, stroke, label, or positional channel.  If
    ``categorical_colors`` is omitted, ``mark_colors`` retains its historical role
    as both the contrast and categorical set.  ``support_colors`` are reported but
    never promoted to text or essential-mark requirements.
    """

    thresholds = (
        text_contrast_min,
        mark_contrast_min,
        cvd_delta_e_target,
        cvd_delta_e_fail,
        grayscale_delta_l_target,
    )
    if not all(np.isfinite(threshold) and threshold >= 0 for threshold in thresholds):
        raise ValueError("palette thresholds must be finite and non-negative")
    if cvd_delta_e_fail > cvd_delta_e_target:
        raise ValueError("CVD failure floor cannot exceed the preferred target")

    surface_srgb = _as_srgb(surface)
    if surface_srgb.shape != (3,):
        raise ValueError("palette surface must be one RGB triplet")
    surface_hex = srgb_to_hex(surface_srgb)
    named_text = _named_colors(text_colors, prefix="text")
    named_marks = _named_colors(mark_colors, prefix="mark")
    named_categorical = (
        named_marks
        if categorical_colors is None
        else _named_colors(categorical_colors, prefix="category")
    )
    redundancy = _validated_redundancy(
        redundant_channels,
        named_categorical,
    )
    named_support = _named_colors(support_colors, prefix="support")

    text_contrast = {
        name: contrast_ratio(color, surface_srgb) for name, color in named_text.items()
    }
    mark_contrast = {
        name: contrast_ratio(color, surface_srgb) for name, color in named_marks.items()
    }
    support_contrast = {
        name: contrast_ratio(color, surface_srgb)
        for name, color in named_support.items()
    }

    findings: list[AuditFinding] = []
    for name, ratio in text_contrast.items():
        if ratio < text_contrast_min:
            findings.append(
                AuditFinding(
                    code="palette.text_contrast",
                    severity="error",
                    message=(
                        f"Text colour {name!r} has {ratio:.2f}:1 contrast; "
                        f"it requires at least {text_contrast_min:.2f}:1."
                    ),
                    subject=name,
                    details={"ratio": ratio, "minimum": text_contrast_min},
                )
            )
    for name, ratio in mark_contrast.items():
        if ratio < mark_contrast_min:
            findings.append(
                AuditFinding(
                    code="palette.mark_contrast",
                    severity="error",
                    message=(
                        f"Essential mark {name!r} has {ratio:.2f}:1 contrast; "
                        f"it requires at least {mark_contrast_min:.2f}:1."
                    ),
                    subject=name,
                    details={"ratio": ratio, "minimum": mark_contrast_min},
                )
            )

    cvd_min_delta_e: dict[str, float] = {}
    grayscale_min_delta_l: float | None = None
    if len(named_categorical) >= 2:
        for vision in ("typical", *CVD_MATRICES):
            deficiency = None if vision == "typical" else vision
            first_name, second_name, separation = _minimum_named_pair(
                named_categorical,
                deficiency=deficiency,
            )
            cvd_min_delta_e[vision] = separation
            if separation < cvd_delta_e_fail:
                findings.append(
                    AuditFinding(
                        code="palette.cvd_separation",
                        severity="error",
                        message=(
                            f"{vision.capitalize()} minimum series separation is "
                            f"Delta E {separation:.1f}; the failure floor is "
                            f"{cvd_delta_e_fail:.1f}."
                        ),
                        subject=vision,
                        details={
                            "delta_e": separation,
                            "pair": [first_name, second_name],
                            "failure_floor": cvd_delta_e_fail,
                            "target": cvd_delta_e_target,
                        },
                    )
                )
            elif separation < cvd_delta_e_target:
                findings.append(
                    AuditFinding(
                        code="palette.cvd_separation",
                        severity="warning",
                        message=(
                            f"{vision.capitalize()} minimum series separation is "
                            f"Delta E {separation:.1f}; prefer at least "
                            f"{cvd_delta_e_target:.1f}."
                        ),
                        subject=vision,
                        details={
                            "delta_e": separation,
                            "pair": [first_name, second_name],
                            "failure_floor": cvd_delta_e_fail,
                            "target": cvd_delta_e_target,
                        },
                    )
                )
        grayscale_pairs = []
        for (first_name, first), (second_name, second) in combinations(
            named_categorical.items(),
            2,
        ):
            separation = abs(lightness(first) - lightness(second))
            grayscale_pairs.append((first_name, second_name, separation))
        grayscale_min_delta_l = min(pair[2] for pair in grayscale_pairs)
        confusing_pairs = [
            {
                "colors": [first_name, second_name],
                "delta_l": separation,
                "redundant": {
                    first_name: redundancy[first_name],
                    second_name: redundancy[second_name],
                },
            }
            for first_name, second_name, separation in grayscale_pairs
            if separation < grayscale_delta_l_target
            and not (redundancy[first_name] and redundancy[second_name])
        ]
        if confusing_pairs:
            findings.append(
                AuditFinding(
                    code="palette.grayscale_separation",
                    severity="warning",
                    message=(
                        f"{len(confusing_pairs)} essential colour pair(s) converge "
                        "in grayscale without redundant channels on both series; "
                        "add a marker, stroke, label, or positional channel."
                    ),
                    subject="grayscale",
                    details={
                        "delta_l": grayscale_min_delta_l,
                        "target": grayscale_delta_l_target,
                        "confusing_pairs": confusing_pairs,
                    },
                )
            )

    return PaletteReport(
        surface=surface_hex,
        text_contrast=text_contrast,
        mark_contrast=mark_contrast,
        support_contrast=support_contrast,
        cvd_min_delta_e=cvd_min_delta_e,
        grayscale_min_delta_l=grayscale_min_delta_l,
        text_contrast_min=text_contrast_min,
        mark_contrast_min=mark_contrast_min,
        cvd_delta_e_target=cvd_delta_e_target,
        cvd_delta_e_fail=cvd_delta_e_fail,
        grayscale_delta_l_target=grayscale_delta_l_target,
        findings=tuple(findings),
    )


def audit_used_colors(
    surface: AlphaColor,
    *,
    text_colors: Mapping[str, AlphaColor] | None = None,
    mark_colors: Mapping[str, AlphaColor] | None = None,
    categorical_colors: Mapping[str, AlphaColor] | None = None,
    redundant_channels: Mapping[str, bool] | None = None,
    support_colors: Mapping[str, AlphaColor] | None = None,
    text_contrast_min: float = TEXT_CONTRAST_MIN,
    mark_contrast_min: float = ESSENTIAL_MARK_CONTRAST_MIN,
    cvd_delta_e_target: float = CVD_DELTA_E_TARGET,
    cvd_delta_e_fail: float = CVD_DELTA_E_FAIL,
    grayscale_delta_l_target: float = GRAYSCALE_DELTA_L_TARGET,
) -> PaletteReport:
    """Audit named colours exactly as rendered over an opaque surface.

    RGB colours are treated as opaque; RGBA colours are composited over
    ``surface`` before any metric is calculated.  ``categorical_colors`` are
    automatically treated as essential marks for contrast and are the only set
    tested pairwise for CVD and grayscale separation.  Names make every metric
    and finding traceable to the figure Artist that supplied the colour.
    """

    surface_rgb = composite_rgba((0, 0, 0, 0), surface)

    def effective(
        colors: Mapping[str, AlphaColor] | None,
    ) -> dict[str, np.ndarray]:
        return {
            name: composite_rgba(color, surface_rgb)
            for name, color in (() if colors is None else colors.items())
        }

    effective_text = effective(text_colors)
    effective_marks = effective(mark_colors)
    effective_categorical = effective(categorical_colors)
    effective_support = effective(support_colors)

    for name, color in effective_categorical.items():
        if name in effective_marks and not np.allclose(
            effective_marks[name],
            color,
            rtol=0,
            atol=1e-12,
        ):
            raise ValueError(
                f"essential mark and categorical colour {name!r} disagree"
            )
        effective_marks[name] = color

    return audit_palette(
        surface_rgb,
        text_colors=effective_text,
        mark_colors=effective_marks,
        categorical_colors=effective_categorical,
        redundant_channels=redundant_channels,
        support_colors=effective_support,
        text_contrast_min=text_contrast_min,
        mark_contrast_min=mark_contrast_min,
        cvd_delta_e_target=cvd_delta_e_target,
        cvd_delta_e_fail=cvd_delta_e_fail,
        grayscale_delta_l_target=grayscale_delta_l_target,
    )


def audit_chosen_light_palette() -> PaletteReport:
    """Return the deterministic receipt for the selected F2 x P2 identity."""

    return audit_palette(
        SURFACE,
        text_colors={"ink": INK, "muted": MUTED},
        mark_colors={
            "categorical_1": CATEGORICAL[0],
            "categorical_2": CATEGORICAL[1],
            "categorical_3": CATEGORICAL[2],
        },
        support_colors={"faint": FAINT, "grid": GRID},
    )


__all__ = [
    "AlphaColor",
    "AuditError",
    "AuditFinding",
    "AuditReport",
    "CATEGORICAL",
    "CVD_DELTA_E_FAIL",
    "CVD_DELTA_E_TARGET",
    "CVD_MATRICES",
    "ESSENTIAL_MARK_CONTRAST_MIN",
    "FAINT",
    "GRAYSCALE_DELTA_L_TARGET",
    "GRID",
    "INK",
    "MUTED",
    "PaletteReport",
    "SURFACE",
    "TEXT_CONTRAST_MIN",
    "audit_chosen_light_palette",
    "audit_condition",
    "audit_palette",
    "audit_required_fields",
    "audit_used_colors",
    "color_delta_e",
    "composite_rgba",
    "contrast_ratio",
    "delta_e",
    "hex_to_lab",
    "hex_to_srgb",
    "lightness",
    "linear_rgb_to_lab",
    "linear_to_srgb",
    "merge_reports",
    "minimum_pairwise_delta_e",
    "minimum_pairwise_lightness_difference",
    "relative_luminance",
    "simulate_cvd",
    "srgb_to_hex",
    "srgb_to_lab",
    "srgb_to_linear",
]
