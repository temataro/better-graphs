"""Tests for Witness colour math and composable audit records."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

import numpy as np


CURRICULUM = Path(__file__).resolve().parents[1] / "visualization-curriculum"
sys.path.insert(0, str(CURRICULUM))

import witness_audit as audit  # noqa: E402


class ColorConversionTests(unittest.TestCase):
    def test_hex_srgb_and_linear_round_trip(self) -> None:
        srgb = audit.hex_to_srgb("#A33A2B")

        self.assertEqual(audit.srgb_to_hex(srgb), "#A33A2B")
        np.testing.assert_allclose(
            audit.linear_to_srgb(audit.srgb_to_linear(srgb)),
            srgb,
            atol=1e-12,
        )

    def test_hex_shorthand_and_invalid_inputs(self) -> None:
        np.testing.assert_allclose(
            audit.hex_to_srgb("#abc"),
            np.array([0xAA, 0xBB, 0xCC]) / 255,
        )
        with self.assertRaises(ValueError):
            audit.hex_to_srgb("#12GG00")
        with self.assertRaises(ValueError):
            audit.srgb_to_linear([1.1, 0.2, 0.3])

    def test_lab_reference_endpoints(self) -> None:
        np.testing.assert_allclose(audit.hex_to_lab("#000000"), [0, 0, 0], atol=1e-9)
        np.testing.assert_allclose(
            audit.hex_to_lab("#FFFFFF"),
            [100, 0, 0],
            atol=2e-5,
        )

    def test_wcag_black_white_contrast_is_twenty_one(self) -> None:
        self.assertAlmostEqual(audit.contrast_ratio("#000000", "#FFFFFF"), 21.0)
        self.assertAlmostEqual(audit.contrast_ratio("#FFFFFF", "#000000"), 21.0)

    def test_machado_simulations_are_bounded_and_distinct(self) -> None:
        original = audit.hex_to_srgb("#A33A2B")
        simulations = {
            deficiency: audit.simulate_cvd(original, deficiency)
            for deficiency in audit.CVD_MATRICES
        }

        for simulated in simulations.values():
            self.assertEqual(simulated.shape, (3,))
            self.assertTrue(np.all((simulated >= 0) & (simulated <= 1)))
        self.assertFalse(
            np.allclose(simulations["protanopia"], simulations["tritanopia"])
        )
        with self.assertRaises(ValueError):
            audit.simulate_cvd(original, "achromatopsia")


class AlphaCompositingTests(unittest.TestCase):
    def test_rgba_is_composited_over_the_opaque_surface(self) -> None:
        np.testing.assert_allclose(
            audit.composite_rgba((0, 0, 0, 0.5), "#FFFFFF"),
            [0.5, 0.5, 0.5],
        )
        np.testing.assert_allclose(
            audit.composite_rgba("#00000080", "#FFFFFF"),
            np.full(3, 127 / 255),
        )

    def test_compositing_rejects_translucent_surfaces(self) -> None:
        with self.assertRaisesRegex(ValueError, "surface must be opaque"):
            audit.composite_rgba("#0008", "#FFFFFF80")
        with self.assertRaisesRegex(ValueError, "one RGB or RGBA"):
            audit.composite_rgba((0, 0, 0, 0.5, 1), "#FFFFFF")


class PaletteAuditTests(unittest.TestCase):
    def test_chosen_light_palette_passes_hard_thresholds(self) -> None:
        report = audit.audit_chosen_light_palette()

        self.assertTrue(report.passed)
        self.assertGreaterEqual(report.minimum_text_contrast, 4.5)
        self.assertGreaterEqual(report.minimum_mark_contrast, 3.0)
        self.assertGreaterEqual(report.minimum_cvd_delta_e, 12.0)
        self.assertAlmostEqual(report.minimum_cvd_delta_e, 21.6982074667, places=7)
        self.assertEqual(report.audit.status, "warning")
        self.assertEqual(
            [finding.code for finding in report.audit.warnings],
            ["palette.grayscale_separation"],
        )

    def test_chosen_palette_reports_support_colours_without_enforcing_them(self) -> None:
        report = audit.audit_chosen_light_palette()

        self.assertEqual(set(report.support_contrast), {"faint", "grid"})
        self.assertLess(report.support_contrast["grid"], 3.0)
        self.assertEqual(report.surface, audit.SURFACE)
        json.dumps(report.to_dict())

    def test_bad_text_and_marks_are_errors(self) -> None:
        report = audit.audit_palette(
            "#FFFFFF",
            text_colors={"quiet_text": "#AAAAAA"},
            mark_colors={"one": "#BBBBBB", "two": "#CCCCCC"},
        )

        self.assertFalse(report.passed)
        self.assertIn("palette.text_contrast", [item.code for item in report.audit.errors])
        self.assertIn("palette.mark_contrast", [item.code for item in report.audit.errors])
        self.assertIn("palette.cvd_separation", [item.code for item in report.audit.errors])
        with self.assertRaises(audit.AuditError):
            report.enforce()

    def test_cvd_target_warns_above_failure_floor(self) -> None:
        # Raising the target above this strong palette proves the warning tier
        # independently of the hard failure floor.
        report = audit.audit_palette(
            audit.SURFACE,
            mark_colors=audit.CATEGORICAL,
            cvd_delta_e_target=30,
            cvd_delta_e_fail=8,
            grayscale_delta_l_target=0,
        )

        self.assertTrue(report.passed)
        self.assertTrue(
            any(item.code == "palette.cvd_separation" for item in report.audit.warnings)
        )

    def test_pairwise_metrics_accept_named_palettes(self) -> None:
        colors = {"green": audit.CATEGORICAL[0], "brick": audit.CATEGORICAL[1]}

        self.assertGreater(audit.minimum_pairwise_delta_e(colors), 70)
        self.assertLess(audit.minimum_pairwise_lightness_difference(colors), 1)

    def test_used_colors_audits_named_effective_rgba_values(self) -> None:
        report = audit.audit_used_colors(
            "#FFFFFF",
            text_colors={"caption": (0, 0, 0, 0.5)},
            mark_colors={"threshold": "#00000040"},
        )

        self.assertAlmostEqual(
            report.text_contrast["caption"],
            audit.contrast_ratio((0.5, 0.5, 0.5), "#FFFFFF"),
        )
        self.assertAlmostEqual(
            report.mark_contrast["threshold"],
            audit.contrast_ratio(np.full(3, 191 / 255), "#FFFFFF"),
        )
        self.assertEqual(
            [(finding.code, finding.subject) for finding in report.audit.errors],
            [
                ("palette.text_contrast", "caption"),
                ("palette.mark_contrast", "threshold"),
            ],
        )

    def test_categorical_colors_are_essential_marks_and_are_pairwise_audited(self) -> None:
        colors = {
            "estimate": audit.CATEGORICAL[0],
            "comparison": audit.CATEGORICAL[1],
            "exception": audit.CATEGORICAL[2],
        }
        report = audit.audit_used_colors(
            audit.SURFACE,
            categorical_colors=colors,
            redundant_channels={name: True for name in colors},
        )

        self.assertEqual(set(report.mark_contrast), set(colors))
        self.assertEqual(
            set(report.cvd_min_delta_e),
            {"typical", "protanopia", "deuteranopia", "tritanopia"},
        )
        self.assertFalse(
            any(
                finding.code == "palette.grayscale_separation"
                for finding in report.audit.findings
            )
        )

    def test_grayscale_warns_only_for_pairs_lacking_full_redundancy(self) -> None:
        colors = {
            "estimate": audit.CATEGORICAL[0],
            "comparison": audit.CATEGORICAL[1],
            "exception": audit.CATEGORICAL[2],
        }
        report = audit.audit_used_colors(
            audit.SURFACE,
            categorical_colors=colors,
            redundant_channels={
                "estimate": True,
                "comparison": True,
                "exception": False,
            },
        )

        grayscale = next(
            finding
            for finding in report.audit.warnings
            if finding.code == "palette.grayscale_separation"
        )
        confusing_pairs = grayscale.details["confusing_pairs"]
        self.assertEqual(len(confusing_pairs), 2)
        self.assertTrue(
            all("exception" in pair["colors"] for pair in confusing_pairs)
        )

    def test_cvd_findings_name_the_confusing_pair(self) -> None:
        report = audit.audit_used_colors(
            "#FFFFFF",
            categorical_colors={"first": "#111111", "second": "#111111"},
            redundant_channels={"first": True, "second": True},
        )

        cvd_findings = [
            finding
            for finding in report.audit.errors
            if finding.code == "palette.cvd_separation"
        ]
        self.assertEqual(len(cvd_findings), 4)
        self.assertTrue(
            all(finding.details["pair"] == ["first", "second"] for finding in cvd_findings)
        )
        self.assertFalse(
            any(
                finding.code == "palette.grayscale_separation"
                for finding in report.audit.findings
            )
        )

    def test_redundancy_declarations_are_validated(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown categorical"):
            audit.audit_used_colors(
                "#FFFFFF",
                categorical_colors={"known": "#000000"},
                redundant_channels={"unknown": True},
            )
        with self.assertRaisesRegex(TypeError, "must be boolean"):
            audit.audit_used_colors(
                "#FFFFFF",
                categorical_colors={"known": "#000000"},
                redundant_channels={"known": "label"},  # type: ignore[dict-item]
            )


class StructuralAuditTests(unittest.TestCase):
    def test_required_fields_blank_values_are_errors(self) -> None:
        report = audit.audit_required_fields(
            {"claim": "A measured claim", "comparison": "  ", "source": None},
            ("claim", "comparison", "source", "alt"),
            subject="figure",
        )

        self.assertFalse(report.passed)
        self.assertEqual(
            [finding.code for finding in report.errors],
            [
                "figure.missing_comparison",
                "figure.missing_source",
                "figure.missing_alt",
            ],
        )

    def test_reports_compose_and_serialize(self) -> None:
        warning = audit.audit_condition(
            False,
            code="figure.untagged_artist",
            severity="warning",
            message="A visible artist has no evidence role.",
            subject="Line2D",
        )
        review = audit.audit_condition(
            False,
            code="claim.causality",
            severity="review",
            message="Does the design warrant causal language?",
        )
        report = audit.merge_reports(audit.AuditReport(), warning, review)

        self.assertTrue(report.passed)
        self.assertEqual(report.status, "warning")
        self.assertEqual(len(report.warnings), 1)
        self.assertEqual(len(report.reviews), 1)
        json.dumps(report.to_dict())
        report.enforce()


if __name__ == "__main__":
    unittest.main()
