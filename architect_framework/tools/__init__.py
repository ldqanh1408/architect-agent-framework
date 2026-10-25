"""Tier-D utility tools exposed as subcommands of the CLI.

A utility script whose only caller was the
registry's roll-call (tier D) was a file nobody could discover except by listing
a directory. Each one now lives here and runs as

    python -m architect_framework.cli.main tool <name> [its own arguments]

`architect-cli --help` names every tool, and `architect-cli tool --help` lists them
with what they do. The old paths are retired in the gate registry and in the
retired-scripts contract, each with the argv that replaces it.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

from architect_framework import contracts

#: name -> (module, one line, retired registry id, retired path)
TOOLS: dict[str, tuple[str, str, str, str]] = {
    "domain-contracts": (
        "domain_contracts", "M0: rewrite domain contract paths to the catalog-mirror shape",
        "TOOL-DOMAIN-CONTRACTS", "scripts/rewrite_domain_contracts.py"),
    "claude-code-skills": (
        "claude_code_skills", "generate Claude Code skill packages from exported_skills/domains/",
        "TOOL-GENERATE-CLAUDE-CODE-SKILLS", "scripts/generate_claude_code_skills.py"),

}

VENDOR_SCRIPTS = contracts.VENDOR_ROOT / "scripts"


def vendor_module(name: str) -> ModuleType:
    """A library of the vendored SDD agent, loaded by path.

    `import scripts.x` is ambiguous here: the repository has its own `scripts/`
    directory, so whichever is first on `sys.path` wins. Loading the file by path
    under a private name removes the ambiguity.
    """
    key = f"_sdd_vendor_{name}"
    if key in sys.modules:
        return sys.modules[key]
    spec = importlib.util.spec_from_file_location(key, VENDOR_SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


def register(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("tool", help="Utility tools: " + ", ".join(TOOLS),
                              description="Run one tool with its own arguments. Tools: "
                                          + "; ".join(f"{n} — {row[1]}" for n, row in TOOLS.items()))
    p.add_argument("name", choices=sorted(TOOLS), help="the tool to run")
    p.add_argument("args", nargs=argparse.REMAINDER, help="the tool's own arguments (try: tool <name> --help)")


def run(args: argparse.Namespace) -> int:
    module = importlib.import_module(f"architect_framework.tools.{TOOLS[args.name][0]}")
    return int(module.main(list(args.args)) or 0)
