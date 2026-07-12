"""Accessible, self-contained SVG and HTML exports for Witness figures.

Matplotlib must save the source SVG with ``svg.fonttype = "none"``.  This
module deliberately performs no plotting and depends only on the standard
library: it adds the document-level accessibility metadata Matplotlib cannot
know, embeds the exact webfonts used by the figure, and wraps the result in a
no-JavaScript HTML document.

The post-processing pass parses and serializes the SVG but does not rebuild its
graphics tree.  In particular, ``gid`` values assigned to Matplotlib Artists
remain the ``id`` values on their SVG groups.
"""

from __future__ import annotations

import base64
import binascii
from collections import Counter
import dataclasses
import datetime as dt
import enum
import html
import io
import json
import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
import re
import tempfile
from typing import Any
import xml.etree.ElementTree as ET


SVG_NAMESPACE = "http://www.w3.org/2000/svg"
XLINK_NAMESPACE = "http://www.w3.org/1999/xlink"

_KNOWN_NAMESPACES = {
    "": SVG_NAMESPACE,
    "xlink": XLINK_NAMESPACE,
    "dc": "http://purl.org/dc/elements/1.1/",
    "cc": "http://creativecommons.org/ns#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
}


@dataclass(frozen=True, slots=True)
class FontFace:
    """One WOFF2 face to embed in an SVG.

    ``weight`` may be a single CSS weight (``400``, ``"bold"``) or a range for
    a variable font (``"100 700"``).  ``style`` is commonly ``"normal"`` or
    ``"italic"``.  Font families are quoted and escaped when CSS is emitted.
    """

    path: str | os.PathLike[str]
    family: str
    style: str = "normal"
    weight: str | int = "normal"


FontInput = FontFace | Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class SvgInspection:
    """Machine-readable result of a strict post-export SVG inspection.

    ``issues`` contains stable, compact issue codes suitable for a receipt or
    CI assertion.  ``details`` carries the corresponding counts and offending
    values, and contains only JSON-serializable standard-library types.
    """

    passed: bool
    issues: tuple[str, ...]
    details: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-ready copy of the inspection result."""

        return {
            "passed": self.passed,
            "issues": list(self.issues),
            "details": dict(self.details),
        }


def inspect_svg(
    path: str | os.PathLike[str],
    *,
    expected_semantic_gids: Iterable[str] = (),
    required_font_families: Iterable[str] = (),
) -> SvgInspection:
    """Inspect an exported SVG's accessibility and self-containment contract.

    The inspection is deliberately independent of Matplotlib and uses only the
    standard library.  It verifies that:

    - the SVG root is an image whose ``aria-labelledby`` references its direct
      ``title`` and ``desc`` children;
    - visible labels remain selectable SVG ``text`` rather than paths;
    - every requested semantic Matplotlib ``gid`` survived as a document ID;
    - all IDs in the document are unique;
    - every required family has a decodable embedded WOFF2 ``@font-face``; and
    - CSS and font declarations do not depend on external resources.

    A malformed SVG is reported as a failed :class:`SvgInspection`; filesystem
    errors still propagate because they indicate that no artifact was available
    to inspect.
    """

    source = Path(path)
    expected_gids = _unique_required_values(
        expected_semantic_gids,
        "expected_semantic_gids",
    )
    required_families = _unique_required_values(
        required_font_families,
        "required_font_families",
    )
    raw_svg = source.read_text(encoding="utf-8")

    try:
        tree = _parse_svg(source)
    except (ET.ParseError, ValueError) as error:
        return SvgInspection(
            passed=False,
            issues=("invalid-svg",),
            details={"path": str(source), "parse_error": str(error)},
        )

    root = tree.getroot()
    issue_codes: list[str] = []

    def report(code: str) -> None:
        if code not in issue_codes:
            issue_codes.append(code)

    if root.get("role") != "img":
        report("wrong-root-role")

    document_elements = list(root.iter())
    id_values = [
        element_id
        for element in document_elements
        if (element_id := element.get("id")) is not None
    ]
    id_counts = Counter(id_values)
    duplicate_ids = {
        element_id: count
        for element_id, count in sorted(id_counts.items())
        if count > 1
    }
    if duplicate_ids:
        report("duplicate-document-id")

    root_titles = [child for child in root if _local_name(child.tag) == "title"]
    root_descriptions = [
        child for child in root if _local_name(child.tag) == "desc"
    ]
    if not root_titles:
        report("missing-root-title")
    elif len(root_titles) > 1:
        report("multiple-root-titles")
    if not root_descriptions:
        report("missing-root-description")
    elif len(root_descriptions) > 1:
        report("multiple-root-descriptions")

    title_id = root_titles[0].get("id") if len(root_titles) == 1 else None
    description_id = (
        root_descriptions[0].get("id") if len(root_descriptions) == 1 else None
    )
    if len(root_titles) == 1 and not title_id:
        report("missing-accessible-id")
    if len(root_descriptions) == 1 and not description_id:
        report("missing-accessible-id")

    aria_value = root.get("aria-labelledby", "")
    aria_references = tuple(aria_value.split())
    if not aria_references:
        report("invalid-aria-labelledby")
    unresolved_aria_references = sorted(
        {reference for reference in aria_references if reference not in id_counts}
    )
    if unresolved_aria_references:
        report("unresolved-aria-reference")
    expected_aria_references = (
        (title_id, description_id)
        if title_id is not None and description_id is not None
        else None
    )
    if (
        expected_aria_references is not None
        and aria_references != expected_aria_references
    ):
        report("aria-label-mismatch")

    text_nodes = [
        element
        for element in document_elements
        if _local_name(element.tag) == "text"
        and "".join(element.itertext()).strip()
    ]
    if not text_nodes:
        report("no-selectable-text")

    missing_gids = [gid for gid in expected_gids if gid not in id_counts]
    if missing_gids:
        report("missing-semantic-gid")

    css_sources = [
        element.text or ""
        for element in document_elements
        if _local_name(element.tag) == "style"
    ]
    css_sources.extend(
        style
        for element in document_elements
        if (style := element.get("style")) is not None
    )
    embedded_families, invalid_font_data = _embedded_font_families(css_sources)
    if invalid_font_data:
        report("invalid-embedded-font-data")
    embedded_by_casefold = {
        family.casefold(): family for family in embedded_families
    }
    missing_families = [
        family
        for family in required_families
        if family.casefold() not in embedded_by_casefold
    ]
    if missing_families:
        report("missing-embedded-font-family")

    external_resources = _external_css_and_font_resources(
        root,
        css_sources,
        raw_svg,
    )
    if external_resources:
        report("external-css-or-font-resource")

    details: dict[str, Any] = {
        "path": str(source),
        "role": root.get("role"),
        "aria_labelledby": list(aria_references),
        "title_id": title_id,
        "description_id": description_id,
        "selectable_text_nodes": len(text_nodes),
        "selectable_text_characters": sum(
            len("".join(element.itertext()).strip()) for element in text_nodes
        ),
        "document_id_count": len(id_values),
        "unique_document_id_count": len(id_counts),
        "duplicate_ids": duplicate_ids,
        "expected_semantic_gids": list(expected_gids),
        "missing_semantic_gids": missing_gids,
        "required_font_families": list(required_families),
        "embedded_font_families": sorted(embedded_families),
        "missing_font_families": missing_families,
        "invalid_embedded_font_data": invalid_font_data,
        "external_resources": external_resources,
    }
    return SvgInspection(
        passed=not issue_codes,
        issues=tuple(issue_codes),
        details=details,
    )


def make_accessible_svg(
    path: str | os.PathLike[str],
    title: str,
    description: str,
    fonts: Iterable[FontInput] = (),
    *,
    output_path: str | os.PathLike[str] | None = None,
    require_text: bool = True,
) -> Path:
    """Add accessibility metadata and embedded fonts to a Matplotlib SVG.

    Parameters
    ----------
    path:
        SVG written by Matplotlib with ``svg.fonttype = "none"``.
    title, description:
        Concise accessible name and fuller text alternative.  They become the
        first two children of the root SVG and are referenced by
        ``aria-labelledby``.
    fonts:
        An iterable of :class:`FontFace` objects or mappings with ``path``,
        ``family``, and optional ``style`` / ``weight`` keys.  Each file is
        embedded as a base64 WOFF2 data URL in an ``@font-face`` rule.
    output_path:
        Destination SVG.  The source is replaced atomically when omitted.
    require_text:
        Raise when the source contains no SVG ``<text>`` nodes.  This catches a
        forgotten ``svg.fonttype = "none"`` before an inaccessible export is
        published.

    Returns
    -------
    pathlib.Path
        The processed SVG path.
    """

    source = Path(path)
    destination = Path(output_path) if output_path is not None else source
    clean_title = _required_text(title, "title")
    clean_description = _required_text(description, "description")
    font_faces = [_coerce_font_face(font) for font in fonts]

    _register_source_namespaces(source)
    tree = _parse_svg(source)
    root = tree.getroot()
    namespace = _tag_namespace(root.tag)

    if require_text and not any(
        _local_name(element.tag) == "text" for element in root.iter()
    ):
        raise ValueError(
            "SVG contains no <text> nodes; save with matplotlib rcParam "
            "svg.fonttype='none' before making an accessible export"
        )

    # Replace only document-level metadata.  Nested title/desc elements, if any,
    # belong to individual marks and remain untouched.
    for child in list(root):
        if _local_name(child.tag) in {"title", "desc"}:
            root.remove(child)

    existing_ids = {
        element_id
        for element in root.iter()
        if (element_id := element.get("id")) is not None
    }
    title_id = _unique_id("witness-title", existing_ids)
    existing_ids.add(title_id)
    description_id = _unique_id("witness-description", existing_ids)

    title_element = ET.Element(_qualified(namespace, "title"), {"id": title_id})
    title_element.text = clean_title
    description_element = ET.Element(
        _qualified(namespace, "desc"), {"id": description_id}
    )
    description_element.text = clean_description
    root.insert(0, title_element)
    root.insert(1, description_element)
    root.set("role", "img")
    root.set("aria-labelledby", f"{title_id} {description_id}")

    _install_font_css(root, namespace, font_faces)
    _atomic_write(destination, _serialize_tree(tree))
    return destination


def write_html(
    svg_path: str | os.PathLike[str],
    html_path: str | os.PathLike[str],
    caption: str,
    summary: str,
    receipt: Any,
    *,
    lang: str = "en",
    figure_id: str = "witness-figure",
    receipt_label: str = "Evidence receipt",
) -> Path:
    """Write a self-contained HTML document containing an inline SVG figure.

    Caption and summary are treated as plain text.  A mapping or sequence passed
    as ``receipt`` is rendered as indented JSON; a string is rendered verbatim;
    and an explicit :class:`~pathlib.Path` is read as UTF-8 text.  All of these
    values are HTML-escaped.  The output has no scripts or external resources.
    """

    source = Path(svg_path)
    destination = Path(html_path)
    clean_caption = _required_text(caption, "caption")
    clean_summary = _required_text(summary, "summary")
    clean_lang = _required_text(lang, "lang")
    clean_figure_id = _html_id(figure_id)
    clean_receipt_label = _required_text(receipt_label, "receipt_label")

    _register_source_namespaces(source)
    tree = _parse_svg(source)
    svg_root = tree.getroot()
    inline_svg = ET.tostring(svg_root, encoding="unicode", short_empty_elements=True)
    receipt_text = _receipt_text(receipt)

    caption_id = f"{clean_figure_id}-caption"
    summary_id = f"{clean_figure_id}-summary"
    page_title = html.escape(clean_caption, quote=False)
    document = f"""<!doctype html>
<html lang="{html.escape(clean_lang, quote=True)}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{page_title}</title>
  <style>
    :root {{ color-scheme: light; font-family: system-ui, sans-serif; }}
    body {{ margin: 0; background: #fff; color: #171717; }}
    .witness-figure {{ max-inline-size: 76rem; margin: 0 auto; padding: 1rem; }}
    .witness-graphic > svg {{ display: block; inline-size: 100%; block-size: auto; }}
    .witness-figure figcaption {{ margin-block-start: .75rem; font-weight: 650; }}
    .witness-text-summary {{ max-inline-size: 72ch; line-height: 1.55; white-space: pre-line; }}
    .witness-receipt {{ max-inline-size: 76ch; margin-block-start: 1rem; }}
    .witness-receipt summary {{ cursor: pointer; font-weight: 650; }}
    .witness-receipt pre {{ overflow-x: auto; padding: .75rem; background: #f3f3f1; line-height: 1.45; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <main>
    <figure id="{html.escape(clean_figure_id, quote=True)}" class="witness-figure" aria-labelledby="{html.escape(caption_id, quote=True)}" aria-describedby="{html.escape(summary_id, quote=True)}">
      <div class="witness-graphic">
        {inline_svg}
      </div>
      <figcaption id="{html.escape(caption_id, quote=True)}">{html.escape(clean_caption)}</figcaption>
      <p id="{html.escape(summary_id, quote=True)}" class="witness-text-summary">{html.escape(clean_summary)}</p>
      <details class="witness-receipt">
        <summary>{html.escape(clean_receipt_label)}</summary>
        <pre>{html.escape(receipt_text)}</pre>
      </details>
    </figure>
  </main>
</body>
</html>
"""
    _atomic_write(destination, document.encode("utf-8"))
    return destination


def _unique_required_values(values: Iterable[str], name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{name} must be an iterable of strings, not one string")
    unique: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must contain only non-empty strings")
        clean_value = value.strip()
        if clean_value not in seen:
            seen.add(clean_value)
            unique.append(clean_value)
    return tuple(unique)


def _embedded_font_families(
    css_sources: Iterable[str],
) -> tuple[set[str], list[dict[str, str]]]:
    embedded: set[str] = set()
    invalid: list[dict[str, str]] = []
    for css_index, css in enumerate(css_sources):
        for face_index, match in enumerate(
            re.finditer(r"@font-face\s*\{([^{}]*)\}", css, flags=re.I | re.S)
        ):
            body = match.group(1)
            family_value = _css_property(body, "font-family")
            if (
                family_value is None
                or re.search(r"(?:^|;)\s*src\s*:", body, re.I) is None
            ):
                continue
            family = _css_family_name(family_value)
            # Parse URLs from the whole face.  A CSS declaration cannot be
            # split naively on semicolons because data-URL media descriptors
            # contain one themselves (``font/woff2;base64``).
            for target in _css_urls(body):
                payload = _woff2_data_payload(target)
                if payload is None:
                    continue
                try:
                    decoded = base64.b64decode(
                        re.sub(r"\s+", "", payload),
                        validate=True,
                    )
                except (ValueError, binascii.Error):
                    invalid.append(
                        {
                            "family": family,
                            "location": f"css[{css_index}] font-face[{face_index}]",
                            "reason": "invalid base64 payload",
                        }
                    )
                    continue
                if not decoded.startswith(b"wOF2"):
                    invalid.append(
                        {
                            "family": family,
                            "location": f"css[{css_index}] font-face[{face_index}]",
                            "reason": "payload is not a WOFF2 file",
                        }
                    )
                    continue
                embedded.add(family)
    return embedded, invalid


def _external_css_and_font_resources(
    root: ET.Element,
    css_sources: Iterable[str],
    raw_svg: str,
) -> list[dict[str, str]]:
    resources: list[dict[str, str]] = []

    def add(kind: str, target: str) -> None:
        record = {"kind": kind, "target": target[:240]}
        if record not in resources:
            resources.append(record)

    for css in css_sources:
        for target in _css_urls(css):
            if not _is_inline_resource(target):
                add("css-url", target)
        for import_match in re.finditer(
            r"@import\s+([^;]+)",
            css,
            flags=re.I,
        ):
            clause = import_match.group(1).strip()
            targets = _css_urls(clause)
            if not targets:
                token = clause.split(maxsplit=1)[0].strip("\"'")
                targets = [token]
            for target in targets:
                if not _is_inline_resource(target):
                    add("css-import", target)
        for local_match in re.finditer(
            r"\blocal\(\s*(?:\"([^\"]*)\"|'([^']*)'|([^)]*))\s*\)",
            css,
            flags=re.I,
        ):
            local_name = next(
                (part for part in local_match.groups() if part is not None),
                "",
            ).strip()
            add("local-font", local_name)

    for element in root.iter():
        element_name = _local_name(element.tag)
        if element_name == "link":
            relation = element.get("rel", "").casefold().split()
            if "stylesheet" in relation:
                target = _attribute_by_local_name(element, "href") or ""
                if not _is_inline_resource(target):
                    add("stylesheet-link", target)
        elif element_name == "font-face-uri":
            target = _attribute_by_local_name(element, "href") or ""
            if not _is_inline_resource(target):
                add("svg-font-face-uri", target)

    for instruction in re.finditer(
        r"<\?xml-stylesheet\b(.*?)\?>",
        raw_svg,
        flags=re.I | re.S,
    ):
        body = instruction.group(1)
        href_match = re.search(
            r"\bhref\s*=\s*(?:\"([^\"]*)\"|'([^']*)')",
            body,
            flags=re.I,
        )
        if href_match is None:
            continue
        target = next(
            part for part in href_match.groups() if part is not None
        )
        if not _is_inline_resource(target):
            add("xml-stylesheet", target)

    return sorted(resources, key=lambda record: (record["kind"], record["target"]))


def _css_property(body: str, name: str) -> str | None:
    match = re.search(
        rf"(?:^|;)\s*{re.escape(name)}\s*:\s*([^;}}]+)",
        body,
        flags=re.I | re.S,
    )
    return match.group(1).strip() if match is not None else None


def _css_urls(css: str) -> list[str]:
    targets: list[str] = []
    for match in re.finditer(
        r"url\(\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s)]*))\s*\)",
        css,
        flags=re.I | re.S,
    ):
        targets.append(next(part for part in match.groups() if part is not None))
    return targets


def _css_family_name(value: str) -> str:
    family = value.strip()
    if len(family) >= 2 and family[0] == family[-1] and family[0] in "\"'":
        family = family[1:-1]
    return family.replace(r"\"", '"').replace(r"\'", "'").replace(r"\\", "\\")


def _woff2_data_payload(target: str) -> str | None:
    if "," not in target:
        return None
    header, payload = target.split(",", 1)
    descriptors = header.casefold().split(";")
    if descriptors[0] not in {"data:font/woff2", "data:application/font-woff2"}:
        return None
    if "base64" not in descriptors[1:]:
        return None
    return payload


def _is_inline_resource(target: str) -> bool:
    clean_target = target.strip().casefold()
    return not clean_target or clean_target.startswith(("#", "data:"))


def _attribute_by_local_name(element: ET.Element, name: str) -> str | None:
    return next(
        (
            value
            for attribute, value in element.attrib.items()
            if _local_name(attribute) == name
        ),
        None,
    )


def _coerce_font_face(value: FontInput) -> FontFace:
    if isinstance(value, FontFace):
        face = value
    elif isinstance(value, Mapping):
        allowed = {"path", "family", "style", "weight"}
        unknown = set(value) - allowed
        if unknown:
            names = ", ".join(sorted(str(name) for name in unknown))
            raise TypeError(f"unknown font metadata: {names}")
        try:
            face = FontFace(**value)
        except TypeError as error:
            raise TypeError(
                "font mappings require 'path' and 'family' keys"
            ) from error
    else:
        raise TypeError("fonts must contain FontFace objects or mappings")

    _required_text(face.family, "font family")
    _css_descriptor(face.style, "font style")
    _css_descriptor(face.weight, "font weight")
    return face


def _install_font_css(
    root: ET.Element,
    namespace: str,
    fonts: list[FontFace],
) -> None:
    defs = next(
        (child for child in root if _local_name(child.tag) == "defs"),
        None,
    )

    if defs is not None:
        for child in list(defs):
            if _local_name(child.tag) == "style" and child.get("id") == "witness-fonts":
                defs.remove(child)

    if not fonts:
        return

    if defs is None:
        defs = ET.Element(_qualified(namespace, "defs"))
        # Accessibility title/description occupy slots zero and one.
        root.insert(2, defs)

    rules = []
    for face in fonts:
        font_path = Path(face.path)
        payload = font_path.read_bytes()
        encoded = base64.b64encode(payload).decode("ascii")
        family = _css_string(_required_text(face.family, "font family"))
        style = _css_descriptor(face.style, "font style")
        weight = _css_descriptor(face.weight, "font weight")
        rules.append(
            "@font-face { "
            f"font-family: {family}; "
            f"src: url(\"data:font/woff2;base64,{encoded}\") format(\"woff2\"); "
            f"font-style: {style}; font-weight: {weight}; font-display: swap; "
            "}"
        )

    style_element = ET.Element(
        _qualified(namespace, "style"),
        {"id": "witness-fonts", "type": "text/css"},
    )
    style_element.text = "\n" + "\n".join(rules) + "\n"
    defs.insert(0, style_element)


def _parse_svg(path: Path) -> ET.ElementTree:
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    tree = ET.parse(path, parser=parser)
    if _local_name(tree.getroot().tag) != "svg":
        raise ValueError(f"expected an SVG root element in {path}")
    return tree


def _register_source_namespaces(path: Path) -> None:
    """Retain source prefixes where ElementTree permits them."""

    namespaces = dict(_KNOWN_NAMESPACES)
    for _, declaration in ET.iterparse(path, events=("start-ns",)):
        prefix, uri = declaration
        namespaces[prefix or ""] = uri

    for prefix, uri in namespaces.items():
        if prefix == "xml" or re.fullmatch(r"ns\d+", prefix):
            continue
        try:
            ET.register_namespace(prefix, uri)
        except ValueError:
            # The URI is still retained by ElementTree even when a source prefix
            # is reserved and cannot be re-registered.
            continue


def _serialize_tree(tree: ET.ElementTree) -> bytes:
    buffer = io.BytesIO()
    tree.write(
        buffer,
        encoding="utf-8",
        xml_declaration=True,
        short_empty_elements=True,
    )
    return buffer.getvalue()


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary_path, mode)
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def _receipt_text(receipt: Any) -> str:
    if isinstance(receipt, os.PathLike):
        return Path(receipt).read_text(encoding="utf-8")
    if isinstance(receipt, str):
        return receipt
    return json.dumps(
        receipt,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        default=_json_default,
    )


def _json_default(value: Any) -> Any:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return dataclasses.asdict(value)
    if isinstance(value, os.PathLike):
        return os.fspath(value)
    if isinstance(value, (dt.date, dt.datetime, dt.time)):
        return value.isoformat()
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, (set, frozenset)):
        return sorted(value, key=repr)
    raise TypeError(f"{type(value).__name__} is not JSON serializable")


def _required_text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _css_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    escaped = escaped.replace("\n", "\\a ").replace("\r", "\\d ")
    return f'"{escaped}"'


def _css_descriptor(value: str | int, name: str) -> str:
    descriptor = str(value).strip()
    if not descriptor or any(character in descriptor for character in ";{}\r\n"):
        raise ValueError(f"{name} contains unsafe CSS syntax")
    return descriptor


def _unique_id(stem: str, existing_ids: set[str]) -> str:
    if stem not in existing_ids:
        return stem
    suffix = 2
    while f"{stem}-{suffix}" in existing_ids:
        suffix += 1
    return f"{stem}-{suffix}"


def _html_id(value: str) -> str:
    candidate = _required_text(value, "figure_id")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.:-]*", candidate):
        raise ValueError(
            "figure_id must start with a letter and contain only letters, "
            "numbers, '_', '-', '.', or ':'"
        )
    return candidate


def _tag_namespace(tag: Any) -> str:
    if isinstance(tag, str) and tag.startswith("{"):
        return tag[1:].split("}", 1)[0]
    return ""


def _local_name(tag: Any) -> str:
    if not isinstance(tag, str):
        return ""
    return tag.rsplit("}", 1)[-1]


def _qualified(namespace: str, name: str) -> str:
    return f"{{{namespace}}}{name}" if namespace else name


__all__ = [
    "FontFace",
    "SvgInspection",
    "inspect_svg",
    "make_accessible_svg",
    "write_html",
]
