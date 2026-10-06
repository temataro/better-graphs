"""Contract tests: public API, executable source, and main-only release policy."""
import ast
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "visualization-curriculum"))
sys.path.insert(0, str(ROOT / "scripts"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml  # Installed by the locked Jupyter toolchain.
import house_style as hs
from validate_review import RenderParser

RELEASE = "github.ref == 'refs/heads/main' && (github.event_name == 'push' || github.event_name == 'workflow_dispatch')"


class ChartContract(unittest.TestCase):
    def tearDown(self):
        plt.close("all")

    def test_public_helpers_and_registers(self):
        for name in ("theme", "page", "finish", "units", "label_end", "mark", "spec_band",
                     "stat", "panel_title", "diverging_norm", "save", "ylabel_above"):
            self.assertTrue(callable(getattr(hs, name)), name)
        for register in ("glance", "read", "study"):
            hs.theme(register)
            fig, ax = hs.page(title="A question under study", source="Synthetic smoke test")
            line, = ax.plot([0, 1, 2], [1, 2, 3], label="Series")
            hs.finish(ax)
            hs.units(ax, "y", "count")
            hs.label_end(ax, [(line, "Series")])
            hs.mark(ax, 1, 2, "Illustration")
            hs.spec_band(ax, 2.5)
            hs.ylabel_above(ax, "Count")
            fig.canvas.draw()
            self.assertGreater(len(fig.axes), 0)

    def test_mosaic_and_exports(self):
        hs.theme("study")
        fig, axes = hs.page(mosaic="AB", title="Synthetic export check")
        axes["A"].plot([0, 1], [0, 1])
        hs.panel_title(axes["A"], "A")
        hs.stat(axes["B"], "24", "Synthetic pairs")
        before = dict(plt.rcParams)
        with tempfile.TemporaryDirectory() as directory:
            hs.save(fig, "contract", outdir=directory)
            for extension in ("svg", "pdf", "png"):
                self.assertGreater((Path(directory) / f"contract.{extension}").stat().st_size, 1000)
        self.assertEqual(dict(plt.rcParams), before)

    def test_diverging_norm_and_palette(self):
        norm = hs.diverging_norm(np.array([-2., 0., 5.]))
        np.testing.assert_allclose(norm([-5, 0, 5]), [0, 0.5, 1])
        self.assertEqual(len(set(hs.SERIES)), 6)
        from check_palette import check
        for surface in (hs.PAPER, "#FFFFFF"):
            self.assertTrue(check(hs.SERIES, bg=surface)["ok"])

    def test_all_curriculum_cells_compile_and_figures_have_alt(self):
        text = (ROOT / "visualization-curriculum/better_graphs.qmd").read_text()
        cells = re.findall(r"```\{python\}\n(.*?)```", text, re.S)
        self.assertGreaterEqual(len(cells), 25)
        for index, cell in enumerate(cells):
            ast.parse(cell, filename=f"qmd-cell-{index}")
            if "#| fig-cap:" in cell:
                self.assertIn("#| fig-alt:", cell)
        self.assertIn("assert interval_low < 0 < interval_high", text)


class WorkflowContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = yaml.load((ROOT / ".github/workflows/publish.yml").read_text(), Loader=yaml.BaseLoader)

    def test_review_triggers_and_least_privilege(self):
        workflow = self.workflow
        self.assertEqual(set(workflow["on"]), {"push", "pull_request", "workflow_dispatch"})
        self.assertEqual(workflow["on"]["push"]["branches"], ["**"])
        self.assertEqual(workflow["permissions"], {"contents": "read"})
        self.assertNotIn("permissions", workflow["jobs"]["build"])
        self.assertEqual(workflow["jobs"]["deploy"]["permissions"],
                         {"pages": "write", "id-token": "write"})
        checkout = workflow["jobs"]["build"]["steps"][0]
        self.assertEqual(checkout["with"]["persist-credentials"], "false")

    def test_release_expression_event_matrix(self):
        workflow = self.workflow
        self.assertEqual(workflow["jobs"]["deploy"]["if"], RELEASE)
        pages = [step for step in workflow["jobs"]["build"]["steps"]
                 if step.get("uses", "").startswith("actions/upload-pages-artifact")]
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]["if"], RELEASE)
        # Evaluate this narrowly specified expression for all event/ref combinations.
        for ref in ("refs/heads/main", "refs/heads/gpt-6-astra", "refs/pull/1/merge", "refs/tags/main"):
            for event in ("push", "workflow_dispatch", "pull_request", "pull_request_target"):
                expression = RELEASE.replace("github.ref", repr(ref)).replace("github.event_name", repr(event))
                expression = expression.replace("&&", "and").replace("||", "or")
                actual = eval(expression, {"__builtins__": {}}, {})
                self.assertEqual(actual, ref == "refs/heads/main" and event in ("push", "workflow_dispatch"))

    def test_validation_precedes_artifacts(self):
        steps = self.workflow["jobs"]["build"]["steps"]
        validate = next(i for i, s in enumerate(steps) if "scripts/validate_review.py" in s.get("run", ""))
        for index, step in enumerate(steps):
            if "upload-" in step.get("uses", ""):
                self.assertGreater(index, validate)
        self.assertEqual(self.workflow["jobs"]["deploy"]["needs"], "build")


class HtmlContract(unittest.TestCase):
    def test_parser_tracks_alt_resources_and_fragments(self):
        parser = RenderParser()
        parser.feed('<h1 id="x">X</h1><a href="#x">Link</a><img alt="Evidence" src="data:image/png;base64,AA">')
        self.assertEqual(parser.ids, {"x"})
        self.assertEqual(parser.anchors, ["#x"])
        self.assertEqual(parser.images[0]["alt"], "Evidence")
        self.assertEqual(parser.resources, ["data:image/png;base64,AA"])


if __name__ == "__main__":
    unittest.main()
