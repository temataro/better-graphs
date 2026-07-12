"""Integration tests for the Witness semantic Matplotlib layer."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
from types import SimpleNamespace
import xml.etree.ElementTree as ET
import warnings

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import numpy as np


CURRICULUM = Path(__file__).resolve().parents[1] / "visualization-curriculum"
sys.path.insert(0, str(CURRICULUM))

import witness  # noqa: E402
from witness_audit import AuditError  # noqa: E402


SVG = "http://www.w3.org/2000/svg"


def complete_claim(**overrides) -> witness.Claim:
    values = {
        "statement": "Measured response rose above its baseline",
        "measure": "response",
        "comparison": "final value versus first",
        "scope": "five deterministic test points",
        "source": "test fixture",
        "method": "identity transform",
        "uncertainty": "No inferential interval is claimed",
        "caveat": "Illustrative only.",
        "alt": "A green line rises from one to three across five points.",
    }
    values.update(overrides)
    return witness.Claim(**values)


class WitnessCoreTests(unittest.TestCase):
    def tearDown(self) -> None:
        plt.close("all")

    def test_frame_and_tag_keep_native_matplotlib_handles(self) -> None:
        witness.theme("explain", "html")
        fig, ax = witness.frame(complete_claim())
        line = ax.plot([0, 1], [1, 2], color=witness.EVIDENCE)[0]
        tagged = witness.tag(
            line,
            "observation",
            label="reported response",
            redundant="line + endpoints",
        )

        self.assertIsInstance(fig, Figure)
        self.assertIsInstance(ax, Axes)
        self.assertIsInstance(tagged, Line2D)
        self.assertIs(tagged, line)
        self.assertRegex(tagged.get_gid(), r"^witness-observation-\d{3}$")
        self.assertEqual(tagged._witness_role, "observation")

        witness.finish(fig, ax)
        report = witness.audit(fig)
        self.assertTrue(report.passed)
        self.assertFalse(report.errors)

    def test_tag_is_idempotent_and_rejects_role_changes(self) -> None:
        witness.theme("explain", "html")
        fig, ax = witness.frame(complete_claim())
        line = ax.plot([0, 1], [1, 2])[0]

        first = witness.tag(line, "observation", redundant="line + endpoints")
        original_gid = first.get_gid()
        second = witness.tag(line, "observation", label="renamed evidence")

        self.assertIs(first, second)
        self.assertEqual(second.get_gid(), original_gid)
        self.assertEqual(len(fig._witness_registry), 1)
        with self.assertRaises(ValueError):
            witness.tag(line, "model")
        with self.assertRaises(ValueError):
            witness.tag(ax.scatter([0], [0]), "observation", redundant="color")
        with self.assertRaises(ValueError):
            witness.tag(ax.scatter([1], [1]), "observation", redundant="banana")

    def test_theme_requires_known_orthogonal_purpose_and_medium(self) -> None:
        with self.assertRaises(ValueError):
            witness.theme("glance", "html")
        with self.assertRaises(ValueError):
            witness.theme("explain", "poster")

    def test_existing_figure_keeps_its_theme_after_global_theme_changes(self) -> None:
        html_state = witness.theme("explain", "html")
        fig, ax = witness.frame(complete_claim())
        line = ax.plot([0, 1], [1, 2])[0]
        witness.tag(line, "observation", redundant="line + endpoints")

        witness.theme("decide", "slide")
        witness.reference(ax, 1, label="baseline", source="first point")
        witness.finish(fig, ax)

        self.assertEqual(fig._witness_theme, html_state)
        self.assertTrue(
            all(label.get_size() == html_state.tick_size for label in ax.get_xticklabels())
        )

    def test_interval_requires_and_records_semantics(self) -> None:
        witness.theme("inspect", "html")
        fig, ax = witness.frame(
            complete_claim(uncertainty="95% percentile-bootstrap interval")
        )
        x = np.arange(4)
        line = ax.plot(x, [1.0, 1.5, 1.8, 2.0], color=witness.EVIDENCE)[0]
        witness.tag(line, "estimate", redundant="solid line")

        with self.assertRaises(ValueError):
            witness.interval(ax, x, [0.8] * 4, [2.2] * 4, kind="  ")

        band = witness.interval(
            ax,
            x,
            [0.8, 1.2, 1.5, 1.7],
            [1.2, 1.8, 2.1, 2.3],
            kind="95% percentile-bootstrap interval",
        )
        witness.finish(fig, ax)

        self.assertEqual(band._witness_role, "uncertainty")
        self.assertEqual(
            band._witness_interval_kind,
            "95% percentile-bootstrap interval",
        )
        self.assertTrue(witness.audit(fig).passed)

    def test_strict_audit_rejects_missing_contract_fields(self) -> None:
        witness.theme("explain", "html")
        fig, ax = witness.frame(complete_claim(comparison="", source="", alt=None))
        line = ax.plot([0, 1], [1, 2])[0]
        witness.tag(line, "observation", redundant="line")
        witness.finish(fig, ax)

        report = witness.audit(fig)
        codes = {finding.code for finding in report.errors}
        self.assertEqual(
            codes,
            {
                "figure.missing_comparison",
                "figure.missing_source",
                "figure.missing_alt",
            },
        )
        with self.assertRaises(AuditError):
            report.enforce()

    def test_nonzero_bar_baseline_is_a_deterministic_error(self) -> None:
        witness.theme("decide", "slide")
        fig, ax = witness.frame(complete_claim())
        bars = ax.bar(["A", "B"], [2, 3], bottom=1, color=witness.CATEGORICAL[:2])
        for index, bar in enumerate(bars):
            witness.tag(
                bar,
                "observation",
                label=f"bar {index}",
                redundant="position + category label",
            )
        witness.finish(fig, ax)

        report = witness.audit(fig)
        self.assertIn("figure.bar_baseline", [finding.code for finding in report.errors])

    def test_hidden_bar_zero_is_a_deterministic_error(self) -> None:
        witness.theme("explain", "html")
        fig, ax = witness.frame(complete_claim())
        bars = ax.bar(["A", "B"], [100, 101])
        for index, bar in enumerate(bars):
            witness.tag(
                bar,
                "observation",
                label=f"bar {index}",
                redundant="category position + value label",
            )
        ax.set_ylim(99, 102)
        witness.finish(fig, ax)

        self.assertIn(
            "figure.bar_zero_hidden",
            [finding.code for finding in witness.audit(fig).errors],
        )

    def test_actual_low_contrast_semantic_mark_is_rejected(self) -> None:
        witness.theme("explain", "html")
        fig, ax = witness.frame(complete_claim())
        invisible_line = ax.plot([0, 1], [1, 2], color=witness.SURFACE)[0]
        witness.tag(
            invisible_line,
            "observation",
            redundant="line + endpoint labels",
        )
        witness.finish(fig, ax)

        report = witness.audit(fig)
        self.assertIn(
            "palette.mark_contrast",
            [finding.code for finding in report.errors],
        )

    def test_zero_rule_follows_the_declared_value_axis(self) -> None:
        witness.theme("decide", "html")
        fig, ax = witness.frame(complete_claim())
        bars = ax.barh([0, 1], [-0.4, 1.2], color=witness.CATEGORICAL[:2])
        for index, bar in enumerate(bars):
            witness.tag(
                bar,
                "decision",
                label=f"margin {index}",
                redundant="signed length + row label",
            )
        ax.set_xlim(-1, 2)
        ax.set_ylim(-0.6, 1.6)

        witness.finish(fig, ax, grid="x")

        zero_rules = [
            line for line in ax.lines
            if (line.get_gid() or "").startswith("witness-structure-zero-")
        ]
        self.assertEqual(len(zero_rules), 1)
        self.assertTrue(np.allclose(zero_rules[0].get_xdata(), 0))
        self.assertFalse(np.allclose(zero_rules[0].get_ydata(), 0))

    def test_finish_rejects_empty_and_foreign_axes(self) -> None:
        witness.theme("explain", "html")
        fig, ax = witness.frame(complete_claim())
        other_fig, other_ax = plt.subplots()

        with self.assertRaises(ValueError):
            witness.finish(fig, [])
        with self.assertRaises(ValueError):
            witness.finish(fig, other_ax)
        plt.close(other_fig)

    def test_linked_detail_uses_current_matplotlib_api_without_deprecation(self) -> None:
        witness.theme("inspect", "html")
        fig, ax = witness.frame(complete_claim())
        line = ax.plot([0, 1, 2], [0, 1, 0])[0]
        witness.tag(line, "observation", redundant="line + samples")

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            inset = witness.linked_detail(
                ax,
                bounds=(0.55, 0.5, 0.35, 0.35),
                xlim=(0.5, 1.5),
                ylim=(0.5, 1.1),
            )

        self.assertIsInstance(inset, Axes)
        self.assertFalse(any(issubclass(item.category, DeprecationWarning) for item in caught))

    def test_linked_detail_accepts_matplotlib_38_tuple_return(self) -> None:
        witness.theme("inspect", "html")
        fig, ax = witness.frame(complete_claim())
        rectangle = Rectangle((0, 0), 1, 1)
        connectors = tuple(Line2D([], []) for _ in range(4))

        with mock.patch.object(
            ax,
            "indicate_inset_zoom",
            return_value=(rectangle, connectors),
        ):
            inset = witness.linked_detail(
                ax,
                bounds=(0.55, 0.5, 0.35, 0.35),
                xlim=(0, 1),
                ylim=(0, 1),
            )

        self.assertIsInstance(inset, Axes)
        gids = [rectangle.get_gid(), *(connector.get_gid() for connector in connectors)]
        self.assertTrue(all(gid and gid.startswith("witness-linked-detail") for gid in gids))
        self.assertEqual(len(gids), len(set(gids)))

    def test_structure_gids_are_unique_across_signed_panels(self) -> None:
        witness.theme("inspect", "html")
        fig, axes = witness.frame(complete_claim(), mosaic=[["a", "b"]])
        for ax in axes.values():
            line = ax.plot([-1, 1], [-1, 1])[0]
            witness.tag(line, "observation", redundant="line + signed position")
        witness.finish(fig, axes)

        zero_gids = [
            line.get_gid()
            for ax in axes.values()
            for line in ax.lines
            if (line.get_gid() or "").startswith("witness-structure-zero-")
        ]
        self.assertEqual(len(zero_gids), 2)
        self.assertEqual(len(zero_gids), len(set(zero_gids)))

    def test_units_validate_axis_and_handle_inversion(self) -> None:
        witness.theme("inspect", "html")
        fig, ax = witness.frame(complete_claim())
        line = ax.plot([0, 1], [0, 1000])[0]
        witness.tag(line, "observation", redundant="line + endpoints")
        ax.set_ylim(1000, 0)
        witness.finish(fig, ax)

        witness.units(ax, axis="y", kind="kg")
        labels = [label.get_text() for label in ax.get_yticklabels()]
        self.assertTrue(labels)
        self.assertEqual(sum(label.endswith("kg") for label in labels), 1)
        self.assertIn("0 kg", labels)
        with self.assertRaises(ValueError):
            witness.units(ax, axis="z", kind="si")

    def test_numpy_fingerprint_is_stable_and_shape_sensitive(self) -> None:
        values = np.arange(6, dtype=np.int64)

        self.assertEqual(witness.fingerprint(values), witness.fingerprint(values.copy()))
        self.assertNotEqual(
            witness.fingerprint(values),
            witness.fingerprint(values.reshape(2, 3)),
        )
        self.assertNotEqual(
            witness.fingerprint(values, values),
            witness.fingerprint(np.concatenate([values, values])),
        )
        with self.assertRaises(TypeError):
            witness.fingerprint(np.array(["unstable"], dtype=object))


class WitnessExportIntegrationTests(unittest.TestCase):
    def tearDown(self) -> None:
        plt.close("all")

    def test_export_embeds_distinct_plex_faces_and_receipt(self) -> None:
        witness.theme("explain", "html")
        fig, ax = witness.frame(complete_claim())
        x = np.arange(5)
        y = np.array([1.0, 1.4, 1.9, 2.5, 3.0])
        line = ax.plot(x, y, color=witness.EVIDENCE, marker="o")[0]
        witness.tag(
            line,
            "observation",
            label="reported response",
            redundant="line + markers",
        )
        witness.reference(
            ax,
            1.0,
            axis="y",
            label="baseline",
            source="first observation",
        )
        witness.finish(fig, ax)

        with tempfile.TemporaryDirectory() as directory:
            bundle = witness.save(
                fig,
                "integration",
                outdir=directory,
                strict=True,
                data_fingerprints={"series": witness.fingerprint(x, y)},
            )

            self.assertEqual(set(bundle.paths), {"svg", "html", "pdf", "png"})
            self.assertTrue(all(path.exists() for path in bundle.paths.values()))
            self.assertTrue(bundle.receipt.exists())

            svg_path = bundle.paths["svg"]
            tree = ET.parse(svg_path)
            root = tree.getroot()
            self.assertEqual(root.get("role"), "img")
            self.assertTrue(root.get("aria-labelledby"))
            self.assertTrue(root.findall(f".//{{{SVG}}}text"))
            self.assertIsNotNone(
                root.find(f".//{{{SVG}}}g[@id='{line.get_gid()}']")
            )

            font_style = root.find(f".//{{{SVG}}}style[@id='witness-fonts']")
            self.assertIsNotNone(font_style)
            self.assertIn('font-family: "IBM Plex Serif"', font_style.text)
            self.assertIn('font-family: "IBM Plex Sans"', font_style.text)
            self.assertIn('font-family: "IBM Plex Mono"', font_style.text)

            svg_text = svg_path.read_text(encoding="utf-8")
            self.assertIn("font-family: 'IBM Plex Serif'", svg_text)
            self.assertIn("font-family: 'IBM Plex Sans'", svg_text)
            self.assertIn("font-family: 'IBM Plex Mono'", svg_text)

            receipt = json.loads(bundle.receipt.read_text(encoding="utf-8"))
            self.assertEqual(receipt["system"], "Witness")
            self.assertEqual(receipt["purpose"], "explain")
            self.assertEqual(receipt["medium"], "html")
            self.assertEqual(receipt["role_counts"]["observation"], 1)
            self.assertEqual(receipt["audit"]["counts"]["error"], 0)
            self.assertTrue(receipt["data_fingerprints"]["series"].startswith("sha256:"))
            self.assertTrue(receipt["svg_accessibility"]["passed"])
            self.assertEqual(
                receipt["svg_accessibility"]["embedded_font_families"],
                ["IBM Plex Serif", "IBM Plex Sans", "IBM Plex Mono"],
            )

            html = bundle.paths["html"].read_text(encoding="utf-8")
            self.assertIn("<figure", html)
            self.assertIn("<figcaption", html)
            self.assertIn("<details class=\"witness-receipt\">", html)
            self.assertNotIn("<script", html)

    def test_strict_export_enforces_postprocessed_svg_inspection(self) -> None:
        witness.theme("explain", "html")
        fig, ax = witness.frame(complete_claim())
        line = ax.plot([0, 1], [1, 2], color=witness.EVIDENCE)[0]
        witness.tag(line, "observation", redundant="line + endpoints")
        witness.reference(ax, 1, label="baseline", source="first point")
        witness.finish(fig, ax)

        failed = SimpleNamespace(
            passed=False,
            issues=("missing-semantic-gid",),
            details={"missing_semantic_gids": [line.get_gid()]},
        )
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(witness, "inspect_svg", return_value=failed):
                with self.assertRaises(AuditError):
                    witness.save(
                        fig,
                        "broken-svg",
                        outdir=directory,
                        formats=("svg",),
                        strict=True,
                    )

    def test_non_strict_errors_require_and_record_an_override_reason(self) -> None:
        witness.theme("explain", "html")
        fig, ax = witness.frame(complete_claim(source=""))
        line = ax.plot([0, 1], [1, 2], color=witness.EVIDENCE)[0]
        witness.tag(line, "observation", redundant="line + endpoints")
        witness.finish(fig, ax)

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                witness.save(
                    fig,
                    "override",
                    outdir=directory,
                    formats=("png",),
                    strict=False,
                )
            bundle = witness.save(
                fig,
                "override",
                outdir=directory,
                formats=("png",),
                strict=False,
                override_reason="Source metadata is pending archival recovery.",
            )
            receipt = json.loads(bundle.receipt.read_text(encoding="utf-8"))
            self.assertFalse(receipt["export_policy"]["strict"])
            self.assertEqual(
                receipt["export_policy"]["override_reason"],
                "Source metadata is pending archival recovery.",
            )


if __name__ == "__main__":
    unittest.main()
