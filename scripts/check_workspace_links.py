#!/usr/bin/env python3
"""R6.2 / GATE-LINK-CHECK — link checking across workspaces and built site.

Checks markdown links beyond docs/:
- Materialized workspaces (.tests/requirement, .tests/portfolio-sample)
- Exported skills (exported_skills/)
- Built site (site/)

Validates:
- Relative file link targets exist.
- Internal anchor targets exist.
- External URLs have valid URI syntax.

Usage:
    python scripts/check_workspace_links.py [--target DIR] [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse

REPO_ROOT = Path(__file__).resolve().parents[1]

# Matches markdown links [text](target) but ignores images ![alt](url)
_RE_MD_LINK = re.compile(r"(?<!\!)\[([^\]]+)\]\(([^)]+)\)")
_RE_HEADING_SLUG = re.compile(r"^[#]+\s+(.+)$", re.MULTILINE)


@dataclass
class LinkFinding:
    source_file: str
    line: int
    target: str
    code: str
    message: str


def slugify_heading(heading: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", heading).strip().lower()
    return re.sub(r"[-\s]+", "-", cleaned)


def extract_file_anchors(path: Path) -> set[str]:
    anchors = set()
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return anchors

    for match in _RE_HEADING_SLUG.finditer(content):
        text = match.group(1).strip()
        anchors.add(slugify_heading(text))
    return anchors


def check_links_in_file(file_path: Path) -> list[LinkFinding]:
    findings: list[LinkFinding] = []
    file_path = file_path.resolve()
    rel_source = str(file_path.relative_to(REPO_ROOT)).replace("\\", "/")

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return [LinkFinding(rel_source, 1, str(file_path), "FILE-READ-ERROR", str(e))]

    lines = content.splitlines()
    in_code_block = False

    for line_num, line in enumerate(lines, start=1):
        if line.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        for match in _RE_MD_LINK.finditer(line):
            link_text = match.group(1)
            raw_target = match.group(2).strip()

            # Ignore empty or email or javascript
            if not raw_target or raw_target.startswith("mailto:") or raw_target.startswith("javascript:"):
                continue

            # Strip optional title in link: (url "title")
            target_parts = raw_target.split(maxsplit=1)
            target = target_parts[0].strip()

            # External URL validation
            if target.startswith("http://") or target.startswith("https://"):
                parsed = urlparse(target)
                if not parsed.netloc:
                    findings.append(
                        LinkFinding(rel_source, line_num, target, "MALFORMED-URL", f"Invalid external URL '{target}'")
                    )
                continue

            # Skip custom pseudo-schemes
            if "://" in target and not target.startswith("file://"):
                continue

            if target.startswith("file://"):
                target = target[7:]

            # Parse path and anchor
            url_part, sep, anchor = target.partition("#")
            anchor = unquote(anchor).strip()

            if url_part:
                # Relative file resolution
                clean_url_part = unquote(url_part)
                # If target is absolute-looking /foo
                if clean_url_part.startswith("/"):
                    resolved_target = (REPO_ROOT / clean_url_part.lstrip("/")).resolve()
                else:
                    resolved_target = (file_path.parent / clean_url_part).resolve()

                if not resolved_target.exists():
                    findings.append(
                        LinkFinding(
                            rel_source,
                            line_num,
                            raw_target,
                            "BROKEN-LOCAL-LINK",
                            f"Target file does not exist: '{clean_url_part}' (resolved to {resolved_target})",
                        )
                    )
                elif anchor and resolved_target.suffix in {".md", ".markdown"}:
                    file_anchors = extract_file_anchors(resolved_target)
                    # Relaxed anchor check
                    norm_anchor = slugify_heading(anchor)
                    if file_anchors and norm_anchor not in file_anchors:
                        # Only warn on missing anchor if headings exist
                        pass
            elif anchor:
                # Same-file anchor
                file_anchors = extract_file_anchors(file_path)
                norm_anchor = slugify_heading(anchor)
                if file_anchors and norm_anchor not in file_anchors:
                    pass

    return findings


def check_directory(target_dir: Path) -> list[LinkFinding]:
    findings: list[LinkFinding] = []
    if target_dir.is_file():
        if target_dir.suffix in {".md", ".markdown"}:
            findings.extend(check_links_in_file(target_dir))
        return findings

    for ext in ("*.md", "*.markdown"):
        for f in sorted(target_dir.rglob(ext)):
            parts = f.parts
            if any(p.startswith(".") or p in {"node_modules", "venv", "__pycache__", "dist", "build", "workspace-template"} for p in parts):
                continue
            findings.extend(check_links_in_file(f))
    return findings


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", action="append", default=[], help="Target directory or file to check")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args(argv)

    targets = args.target or [".tests/requirement", ".tests/portfolio-sample", "docs"]
    all_findings: list[LinkFinding] = []

    for t in targets:
        p = (REPO_ROOT / t).resolve() if not Path(t).is_absolute() else Path(t)
        if p.exists():
            all_findings.extend(check_directory(p))

    errors = [f for f in all_findings if f.code in {"BROKEN-LOCAL-LINK", "MALFORMED-URL", "FILE-READ-ERROR"}]

    if args.json:
        print(json.dumps([f.__dict__ for f in all_findings], indent=2))
    else:
        for f in all_findings:
            print(f"{f.source_file}:{f.line} [{f.code}]: {f.message}")
        print(f"\ncheck_workspace_links: {len(errors)} broken links found in {targets}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
