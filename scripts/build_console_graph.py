#!/usr/bin/env python3
"""Deterministically bundle modular graph_modules/*.js into static/document-graph.js (specification)."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MOD_DIR = ROOT / "architect_framework/console/static/graph_modules"
OUT_FILE = ROOT / "architect_framework/console/static/document-graph.js"


def build_bundle() -> str:
    parts = [p.read_text(encoding="utf-8") for p in sorted(MOD_DIR.glob("*.js"))]
    return "".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify static/document-graph.js matches graph_modules/*.js")
    args = parser.parse_args()
    bundle = build_bundle()
    if args.check:
        current = OUT_FILE.read_text(encoding="utf-8")
        if current != bundle:
            print("static/document-graph.js is out of sync with graph_modules/*.js", file=sys.stderr)
            return 1
        print("static/document-graph.js matches graph_modules/*.js")
        return 0
    OUT_FILE.write_text(bundle, encoding="utf-8", newline="\n")
    print(f"Built {OUT_FILE} ({len(bundle)} bytes) from {len(list(MOD_DIR.glob('*.js')))} modules.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
