"""YAML frontmatter parser / patcher for Method content.

Handles four frontmatter styles:
  1. Markdown with leading ``---`` ... ``---`` block (most common for .md).
  2. YAML files (entire file is YAML, frontmatter is the top-level dict).
  3. Python files via leading triple-quoted docstring containing a
     ``method-meta:`` tag.
  4. BPMN / XML files via XML comment ``<!-- method-meta: ... -->``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

MD_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
PY_META_RE = re.compile(r'"""[\s\S]*?method-meta:\s*\n(.*?)"""', re.DOTALL)
XML_META_RE = re.compile(r"<!--\s*method-meta:\s*\n(.*?)\s*-->", re.DOTALL)


@dataclass
class FrontmatterResult:
    style: str          # md | yaml | py | xml | none
    data: dict[str, Any]
    raw_block: str      # original raw text we captured (for replacement)
    body_after: str     # remaining file body after frontmatter


def detect_style(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown"}:
        return "md"
    if suffix in {".yaml", ".yml"}:
        # Some upstream templates wrap their YAML body with a ``---`` ... ``---``
        # leading block (Markdown-style frontmatter). Treat those as md so the
        # patcher targets the frontmatter block instead of the YAML body.
        try:
            head = path.read_text(encoding="utf-8")[:512]
        except OSError:
            head = ""
        if head.lstrip().startswith("---") and head.count("---") >= 2:
            return "md"
        return "yaml"
    if suffix == ".py":
        return "py"
    if suffix in {".bpmn", ".xml"}:
        return "xml"
    if suffix == ".json":
        return "json"
    return "none"


def parse(path: Path) -> FrontmatterResult:
    """Parse frontmatter from a Method content file. Returns FrontmatterResult.

    For unsupported file types or files without recognizable frontmatter,
    returns FrontmatterResult(style="none", data={}, raw_block="", body_after=<full text>).
    """
    text = path.read_text(encoding="utf-8")
    style = detect_style(path)

    if style == "md":
        m = MD_FRONTMATTER_RE.match(text)
        if m:
            data = yaml.safe_load(m.group(1)) or {}
            return FrontmatterResult("md", data, m.group(0), text[m.end():])
        return FrontmatterResult("none", {}, "", text)

    if style == "yaml":
        try:
            data = yaml.safe_load(text) or {}
        except yaml.YAMLError:
            data = {}
        # YAML body might fail to parse (Jinja placeholders such as {{X}}). Fall
        # back to a regex sweep so the labels are still detected when present in
        # plaintext at the top of the file.
        if not isinstance(data, dict) or not has_method_labels(data):
            top = text[:1024]
            plane_m = re.search(r"^plane:\s*['\"]?(internal|public|sample)['\"]?", top, re.MULTILINE)
            vis_m = re.search(r"^visibility:\s*['\"]?(full|abstract|redacted|id_only)['\"]?", top, re.MULTILINE)
            rp_m = re.search(r"^return_policy:\s*\n((?:\s+\w+:.*\n){3})", top, re.MULTILINE)
            if plane_m and vis_m and rp_m:
                rp = {}
                for line in rp_m.group(1).splitlines():
                    parts = line.strip().split(":", 1)
                    if len(parts) == 2:
                        rp[parts[0].strip()] = parts[1].strip().strip("'\"")
                data = {
                    "plane": plane_m.group(1),
                    "visibility": vis_m.group(1),
                    "return_policy": rp,
                }
        return FrontmatterResult("yaml", data if isinstance(data, dict) else {}, text, "")

    if style == "py":
        m = PY_META_RE.search(text[:2000])  # only check leading docstring
        if m:
            data = yaml.safe_load(m.group(1)) or {}
            return FrontmatterResult("py", data, m.group(0), text[m.end():])
        return FrontmatterResult("none", {}, "", text)

    if style == "xml":
        m = XML_META_RE.search(text[:2000])
        if m:
            data = yaml.safe_load(m.group(1)) or {}
            return FrontmatterResult("xml", data, m.group(0), text[m.end():])
        return FrontmatterResult("none", {}, "", text)

    return FrontmatterResult("none", {}, "", text)


def has_method_labels(data: dict[str, Any]) -> bool:
    """Check if a parsed frontmatter contains the required Method labels."""
    if not isinstance(data, dict):
        return False
    plane = data.get("plane")
    visibility = data.get("visibility")
    return_policy = data.get("return_policy")
    if plane not in {"internal", "public", "sample"}:
        return False
    if visibility not in {"full", "abstract", "redacted", "id_only"}:
        return False
    if not isinstance(return_policy, dict):
        return False
    for k in ("customer", "platform_admin", "tecnos_admin"):
        if k not in return_policy:
            return False
        if return_policy[k] not in {"full", "abstract", "id_only", "blocked"}:
            return False
    return True


def patch_md_frontmatter(text: str, labels: dict[str, Any]) -> str:
    """Insert / merge Method labels into a Markdown file's frontmatter."""
    m = MD_FRONTMATTER_RE.match(text)
    if m:
        existing = yaml.safe_load(m.group(1)) or {}
        existing.update(labels)
        new_block = "---\n" + yaml.safe_dump(existing, allow_unicode=True, sort_keys=False).rstrip() + "\n---\n"
        return new_block + text[m.end():]
    new_block = "---\n" + yaml.safe_dump(labels, allow_unicode=True, sort_keys=False).rstrip() + "\n---\n"
    return new_block + text
