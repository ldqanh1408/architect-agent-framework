#!/usr/bin/env python3
"""Deterministically compile modular css_modules/*.css into workbench.css and sdd-console.css (specification)."""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
MOD_DIR = ROOT / "architect_framework/console/static/css_modules"
OUT_WB = ROOT / "architect_framework/console/static/workbench.css"
OUT_SDD = ROOT / "architect_framework/console/static/sdd-console.css"


def _compact_css_block(raw: str) -> str:
    """Compact non-nested CSS rule bodies to one line per selector so total lines stay <= 450."""
    def repl(match: re.Match) -> str:
        sel = " ".join(line.strip() for line in match.group(1).strip().splitlines() if line.strip())
        body = " ".join(line.strip() for line in match.group(2).strip().splitlines() if line.strip())
        if sel in (":root", ":root[data-theme=dark]"):
            return match.group(0)
        return f"{sel} {{ {body} }}"

    compacted = re.sub(r"(?m)^([^/*{@\n][^{/*]*?)\{\n([^@{}]+?)\n\}", repl, raw)
    compacted = re.sub(r"\n{3,}", "\n\n", compacted)
    return compacted.strip()


def build_css() -> str:
    parts = [_compact_css_block(p.read_text(encoding="utf-8")) for p in sorted(MOD_DIR.glob("*.css"))]
    return "\n\n".join(parts) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify workbench.css and sdd-console.css match css_modules/*.css")
    args = parser.parse_args()
    bundle = build_css()
    if args.check:
        for out_path in (OUT_WB, OUT_SDD):
            if not out_path.exists() or out_path.read_text(encoding="utf-8") != bundle:
                print(f"{out_path.name} is out of sync with css_modules/*.css", file=sys.stderr)
                return 1
        print("workbench.css and sdd-console.css match css_modules/*.css")
        return 0
    OUT_WB.write_text(bundle, encoding="utf-8", newline="\n")
    OUT_SDD.write_text(bundle, encoding="utf-8", newline="\n")
    lines = len(bundle.splitlines())
    print(f"Built {OUT_WB.name} and {OUT_SDD.name} ({lines} lines, {len(bundle)} bytes) from {len(list(MOD_DIR.glob('*.css')))} modules.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
