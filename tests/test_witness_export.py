from __future__ import annotations

import base64
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET


CURRICULUM = Path(__file__).resolve().parents[1] / "visualization-curriculum"
sys.path.insert(0, str(CURRICULUM))

from witness_export import (  # noqa: E402
    FontFace,
    inspect_svg,
    make_accessible_svg,
    write_html,
)


SVG = """<?xml version="1.0" encoding="utf-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     width="320pt" height="180pt" viewBox="0 0 320 180">
  <metadata><source>unit test</source></metadata>
  <defs>
    <style type="text/css">* { stroke-linejoin: round; }</style>
    <path id="marker" d="M 0 0 L 1 1" />
  </defs>
  <g id="role-observation-1">
    <text x="12" y="24" style="font-family: 'IBM Plex Sans'">Measured 42 Ω</text>
    <use xlink:href="#marker" />
  </g>
</svg>
"""

SVG_NAMESPACE = "http://www.w3.org/2000/svg"
XLINK_NAMESPACE = "http://www.w3.org/1999/xlink"


class AccessibleSvgTests(unittest.TestCase):
    def test_metadata_fonts_namespaces_and_semantic_groups_survive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            svg_path = root / "figure.svg"
            font_path = root / "IBMPlexSans-Regular.woff2"
            font_bytes = b"wOF2\x00\x01selectable-test-font"
            svg_path.write_text(SVG, encoding="utf-8")
            font_path.write_bytes(font_bytes)

            result = make_accessible_svg(
                svg_path,
                "A measured difference",
                "One measured value is shown as selectable text.",
                [
                    FontFace(
                        font_path,
                        family="IBM Plex Sans",
                        style="normal",
                        weight=400,
                    )
                ],
            )

            self.assertEqual(result, svg_path)
            tree = ET.parse(svg_path)
            svg = tree.getroot()
            children = list(svg)
            self.assertEqual(children[0].tag, f"{{{SVG_NAMESPACE}}}title")
            self.assertEqual(children[1].tag, f"{{{SVG_NAMESPACE}}}desc")
            self.assertEqual(children[0].text, "A measured difference")
            self.assertEqual(svg.get("role"), "img")
            self.assertEqual(
                svg.get("aria-labelledby"),
                f"{children[0].get('id')} {children[1].get('id')}",
            )

            semantic_group = svg.find(
                f".//{{{SVG_NAMESPACE}}}g[@id='role-observation-1']"
            )
            self.assertIsNotNone(semantic_group)
            text = semantic_group.find(f"{{{SVG_NAMESPACE}}}text")
            self.assertEqual(text.text, "Measured 42 Ω")
            use = semantic_group.find(f"{{{SVG_NAMESPACE}}}use")
            self.assertEqual(use.get(f"{{{XLINK_NAMESPACE}}}href"), "#marker")

            font_style = svg.find(
                f".//{{{SVG_NAMESPACE}}}style[@id='witness-fonts']"
            )
            self.assertIn('@font-face { font-family: "IBM Plex Sans";', font_style.text)
            self.assertIn("font-style: normal; font-weight: 400", font_style.text)
            self.assertIn(
                base64.b64encode(font_bytes).decode("ascii"),
                font_style.text,
            )

            serialized = svg_path.read_text(encoding="utf-8")
            self.assertIn('xmlns="http://www.w3.org/2000/svg"', serialized)
            self.assertIn('xmlns:xlink="http://www.w3.org/1999/xlink"', serialized)
            self.assertIn("<text", serialized)

            inspection = inspect_svg(
                svg_path,
                expected_semantic_gids=("role-observation-1",),
                required_font_families=("IBM Plex Sans",),
            )
            self.assertTrue(inspection.passed)
            self.assertEqual(inspection.issues, ())
            self.assertEqual(
                inspection.details["embedded_font_families"],
                ["IBM Plex Sans"],
            )
            self.assertGreater(inspection.details["selectable_text_characters"], 0)
            self.assertEqual(inspection.as_dict()["issues"], [])

    def test_no_text_raises_without_modifying_source(self) -> None:
        path_only_svg = SVG.replace(
            "<text x=\"12\" y=\"24\" style=\"font-family: 'IBM Plex Sans'\">Measured 42 Ω</text>",
            '<path d="M 12 24 L 42 24" />',
        )
        with tempfile.TemporaryDirectory() as directory:
            svg_path = Path(directory) / "paths.svg"
            svg_path.write_text(path_only_svg, encoding="utf-8")
            original = svg_path.read_bytes()

            with self.assertRaisesRegex(ValueError, "svg.fonttype='none'"):
                make_accessible_svg(
                    svg_path,
                    "Paths only",
                    "This export should be rejected.",
                )

            self.assertEqual(svg_path.read_bytes(), original)

    def test_output_path_leaves_source_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.svg"
            destination = root / "nested" / "accessible.svg"
            source.write_text(SVG, encoding="utf-8")
            original = source.read_text(encoding="utf-8")

            result = make_accessible_svg(
                source,
                "Accessible copy",
                "The original SVG remains untouched.",
                output_path=destination,
            )

            self.assertEqual(result, destination)
            self.assertEqual(source.read_text(encoding="utf-8"), original)
            self.assertTrue(destination.exists())


class SvgInspectionTests(unittest.TestCase):
    def test_reports_accessibility_semantics_ids_fonts_and_external_resources(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root_directory = Path(directory)
            svg_path = root_directory / "broken.svg"
            font_path = root_directory / "IBMPlexSans-Regular.woff2"
            svg_path.write_text(SVG, encoding="utf-8")
            font_path.write_bytes(b"wOF2\x00\x01selectable-test-font")
            make_accessible_svg(
                svg_path,
                "A measured difference",
                "One measured value is shown as selectable text.",
                [FontFace(font_path, family="IBM Plex Sans", weight=400)],
            )

            tree = ET.parse(svg_path)
            svg = tree.getroot()
            svg.set("role", "presentation")
            svg.set("aria-labelledby", "missing-label")
            ET.SubElement(
                svg,
                f"{{{SVG_NAMESPACE}}}g",
                {"id": "marker"},
            )
            external_style = ET.SubElement(svg, f"{{{SVG_NAMESPACE}}}style")
            external_style.text = """
                @import url("https://example.test/chart.css");
                @font-face {
                    font-family: "Remote Face";
                    src: local("Remote Face"), url("../fonts/remote.woff2");
                }
            """
            for parent in svg.iter():
                for child in list(parent):
                    if child.tag == f"{{{SVG_NAMESPACE}}}text":
                        parent.remove(child)
            tree.write(svg_path, encoding="utf-8", xml_declaration=True)

            inspection = inspect_svg(
                svg_path,
                expected_semantic_gids=(
                    "role-observation-1",
                    "role-boundary-1",
                ),
                required_font_families=(
                    "IBM Plex Sans",
                    "IBM Plex Serif",
                ),
            )

            self.assertFalse(inspection.passed)
            self.assertEqual(
                set(inspection.issues),
                {
                    "wrong-root-role",
                    "duplicate-document-id",
                    "unresolved-aria-reference",
                    "aria-label-mismatch",
                    "no-selectable-text",
                    "missing-semantic-gid",
                    "missing-embedded-font-family",
                    "external-css-or-font-resource",
                },
            )
            self.assertEqual(inspection.details["duplicate_ids"], {"marker": 2})
            self.assertEqual(
                inspection.details["missing_semantic_gids"],
                ["role-boundary-1"],
            )
            self.assertEqual(
                inspection.details["missing_font_families"],
                ["IBM Plex Serif"],
            )
            resource_kinds = {
                resource["kind"]
                for resource in inspection.details["external_resources"]
            }
            self.assertEqual(
                resource_kinds,
                {"css-import", "css-url", "local-font"},
            )

    def test_rejects_an_invalid_embedded_woff2_payload(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            svg_path = root / "invalid-font.svg"
            font_path = root / "IBMPlexSans-Regular.woff2"
            font_bytes = b"wOF2\x00\x01selectable-test-font"
            svg_path.write_text(SVG, encoding="utf-8")
            font_path.write_bytes(font_bytes)
            make_accessible_svg(
                svg_path,
                "A measured difference",
                "One measured value is shown as selectable text.",
                [FontFace(font_path, family="IBM Plex Sans", weight=400)],
            )
            encoded_font = base64.b64encode(font_bytes).decode("ascii")
            document = svg_path.read_text(encoding="utf-8")
            svg_path.write_text(
                document.replace(encoded_font, "not-valid-base64!"),
                encoding="utf-8",
            )

            inspection = inspect_svg(
                svg_path,
                required_font_families=("IBM Plex Sans",),
            )

            self.assertFalse(inspection.passed)
            self.assertIn("invalid-embedded-font-data", inspection.issues)
            self.assertIn("missing-embedded-font-family", inspection.issues)
            self.assertEqual(
                inspection.details["invalid_embedded_font_data"][0]["family"],
                "IBM Plex Sans",
            )

    def test_malformed_xml_is_a_structured_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            svg_path = Path(directory) / "malformed.svg"
            svg_path.write_text("<svg><broken></svg>", encoding="utf-8")

            inspection = inspect_svg(svg_path)

            self.assertFalse(inspection.passed)
            self.assertEqual(inspection.issues, ("invalid-svg",))
            self.assertIn("parse_error", inspection.details)


class HtmlExportTests(unittest.TestCase):
    def test_inline_svg_caption_summary_and_receipt_are_self_contained(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            svg_path = root / "figure.svg"
            html_path = root / "site" / "figure.html"
            svg_path.write_text(SVG, encoding="utf-8")
            make_accessible_svg(
                svg_path,
                "A measured difference",
                "One measured value is shown as selectable text.",
            )

            result = write_html(
                svg_path,
                html_path,
                caption="Measured value & interval",
                summary="The observation is 42 Ω; <not an HTML tag>.",
                receipt={
                    "method": "direct observation",
                    "n": 1,
                    "caveat": "<illustrative>",
                },
            )

            self.assertEqual(result, html_path)
            document = html_path.read_text(encoding="utf-8")
            self.assertIn("<!doctype html>", document)
            self.assertIn("<figure id=\"witness-figure\"", document)
            self.assertIn("<svg", document)
            self.assertNotIn("&lt;svg", document)
            self.assertIn("<text", document)
            self.assertIn(
                "<figcaption id=\"witness-figure-caption\">Measured value &amp; interval</figcaption>",
                document,
            )
            self.assertIn(
                "The observation is 42 Ω; &lt;not an HTML tag&gt;.",
                document,
            )
            self.assertIn("<details class=\"witness-receipt\">", document)
            self.assertIn('&quot;caveat&quot;: &quot;&lt;illustrative&gt;&quot;', document)
            self.assertNotIn("<script", document)
            self.assertNotIn("https://", document)


if __name__ == "__main__":
    unittest.main()
