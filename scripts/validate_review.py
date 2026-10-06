"""Offline structural checks; not a visual, external availability or accessibility audit."""
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = (
    "README.md", "CLAUDE.md", "PLAN.md", "VISUALIZATION_GUIDE.md",
    ".claude/skills/house-charts/SKILL.md", "reviews/gpt-6-astra/REVIEW.md",
    "visualization-curriculum/better_graphs.qmd",
)


class RenderParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.anchors = []
        self.images = []
        self.resources = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "a" and attrs.get("href"):
            self.anchors.append(attrs["href"])
        if tag == "img":
            self.images.append(attrs)
        if tag in ("img", "script", "iframe", "source") and attrs.get("src"):
            self.resources.append(attrs["src"])
        if tag == "link" and attrs.get("rel") == "stylesheet":
            self.resources.append(attrs.get("href", ""))


def validate_html(path):
    text = path.read_text()
    parser = RenderParser()
    parser.feed(text)
    errors = []
    if len(parser.images) < 25:
        errors.append(f"Expected executed curriculum figures; found only {len(parser.images)} images")
    for index, image in enumerate(parser.images, 1):
        if not image.get("alt", "").strip():
            errors.append(f"Image {index} has no informative alternative text")
        if not image.get("src", "").startswith("data:image/"):
            errors.append(f"Image {index} is not embedded")
    for source in parser.resources:
        if not source.startswith("data:"):
            errors.append(f"Non-embedded resource: {source}")
    for href in parser.anchors:
        parts = urlsplit(href)
        if href.startswith("#") and parts.fragment and unquote(parts.fragment) not in parser.ids:
            errors.append(f"Missing internal anchor: {href}")
        elif not parts.scheme and parts.path:
            if not (path.parent / unquote(parts.path)).exists():
                errors.append(f"Broken local HTML link: {href}")
    if 'class="cell-output-error"' in text or 'Traceback (most recent call last)' in text:
        errors.append("Rendered execution error found")
    for marker in ("uncertainty-every-register", "uncertainty-accessible-table", "gpt-6-astra"):
        if marker not in text:
            errors.append(f"Missing expected rendered content: {marker}")
    return errors, len(parser.images), len(parser.anchors)


def validate_markdown():
    errors = []
    checked = 0
    for name in DOCUMENTS:
        path = ROOT / name
        if not path.exists():
            errors.append(f"Missing review document: {name}")
            continue
        text = re.sub(r"```.*?```", "", path.read_text(), flags=re.S)
        targets = re.findall(r"\[[^\]]*\]\(([^\s)]+)\)", text)
        targets += re.findall(r'<img[^>]+src="([^"]+)"', text)
        for target in targets:
            parts = urlsplit(target)
            if parts.scheme or target.startswith("#"):
                continue
            if parts.path:
                checked += 1
                if not (path.parent / unquote(parts.path)).exists():
                    errors.append(f"{name}: missing local link {target}")
    return errors, checked


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "visualization-curriculum/index.html"
    errors, images, anchors = validate_html(path)
    markdown_errors, local_links = validate_markdown()
    errors += markdown_errors
    for error in errors:
        print(f"FAIL: {error}")
    print(f"{'FAIL' if errors else 'PASS'}: {images} embedded images with alt text; "
          f"{anchors} HTML anchors inspected; {local_links} local document links checked")
    print("External URLs are not fetched; human visual and assistive-technology review remains separate.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
