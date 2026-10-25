#!/usr/bin/env python3
"""M0: Rewrite domain skill-contract `owns:`/`required_outputs:` paths to the catalog-mirror shape.

Old shape:  02-domains/{slot}-<skill>/**            (sequence-ordered customer-module naming)
New shape:  02-domains/<cluster>/<skill>/**         (catalog cluster + skill, the emergent mirror)

Mechanical and safe because every domain contract (110/110, verified) uses the identical pattern:
    owns:             - <output_root>/architecture/02-domains/{slot}-<skill>/**
    required_outputs: - architecture/02-domains/{slot}-<skill>/README.md
                      - architecture/02-domains/{slot}-<skill>/00-overview/<skill>-overview.md
                      - architecture/02-domains/{slot}-<skill>/verification/fitness-self-check.md

The replacement is per-file, derived from the file's OWN directory path (cluster + skill folder
name), never a hard-coded list — so it is correct even if a skill moves cluster.

Usage:
    python -m architect_framework.cli.main tool domain-contracts --dry-run   # print the diff, change nothing
    python -m architect_framework.cli.main tool domain-contracts             # apply the rewrite in place
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from architect_framework.contracts import REPO_ROOT

DOMAINS = REPO_ROOT / "exported_skills" / "domains"


def rewrite_file(path: Path, dry_run: bool) -> tuple[bool, list[str]]:
    """Rewrite one contract. Returns (changed, diff_lines)."""
    rel = path.relative_to(DOMAINS)
    parts = rel.parts  # (<cluster>, <skill>, skill-contract.yml)
    if len(parts) != 3 or parts[2] != "skill-contract.yml":
        return False, []
    cluster, skill = parts[0], parts[1]

    text = path.read_text(encoding="utf-8")
    old_slot = f"02-domains/{{slot}}-{skill}"
    old_flat = f"02-domains/{cluster}/{skill}"
    new = f"02-domains/{cluster}/{{submodule}}/{skill}"
    if old_slot in text:
        new_text = text.replace(old_slot, new)
    elif old_flat in text and new not in text:
        new_text = text.replace(old_flat, new)
    else:
        return False, []  # already rewritten to v2 {submodule} shape — leave it
    diff = []
    if dry_run:
        diff.append(f"{path.relative_to(REPO_ROOT)}")
        for i, (a, b) in enumerate(zip(text.splitlines(), new_text.splitlines()), 1):
            if a != b:
                diff.append(f"  {i}: - {a.strip()}")
                diff.append(f"  {i}: + {b.strip()}")
    else:
        path.write_text(new_text, encoding="utf-8", newline="\n")
        diff.append(f"rewrote {path.relative_to(REPO_ROOT)}")
    return True, diff


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="architect-cli tool domain-contracts", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="print the diff, change nothing")
    args = parser.parse_args(argv)

    contracts = sorted(DOMAINS.rglob("skill-contract.yml"))
    changed, skipped, diffs = 0, 0, []
    for p in contracts:
        ok, lines = rewrite_file(p, args.dry_run)
        if ok:
            changed += 1
            diffs.extend(lines)
        else:
            skipped += 1

    print(f"{'DRY-RUN: ' if args.dry_run else ''}domain contracts: {len(contracts)} | "
          f"to rewrite: {changed} | unchanged/skipped: {skipped}")
    if diffs:
        print("\n".join(diffs[:120]))
        if len(diffs) > 120:
            print(f"… ({len(diffs) - 120} more lines)")
    print("\nexit: " + ("0 (dry-run; nothing written)" if args.dry_run else "0 (rewrite applied)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
