"""`GATE-DOCS-CURRENT` — the documentation is graded like everything else.

WHY THIS EXISTS
    `docs/` is where a reader learns which command to run, which gate emits a
    code, and what a word means here. Every one of those is a claim about the
    repository, and until this gate existed not one of them was checked.

    That is the same shape as every failure recorded in this directory. A
    checklist cited argv that printed `No such file or directory` (specification). A test
    asserted `92` after the registry grew to 108 (specification). The repo's own reference
    samples carried **seven** dead script paths, and the drift was being
    propagated *by the documentation*. Prose drifts exactly like a hard-coded
    path; the only difference is that nothing was failing when it did.

    So the documentation is now derived where it can be, and graded where it
    cannot.

WHAT IT CHECKS

  ``DOCS-LINK-BROKEN``       a relative link in `docs/` that resolves to nothing.
  ``DOCS-GATE-UNKNOWN``      a `GATE-*` / `TOOL-*` token that is neither a registry
                             ID, nor a finding code, nor a reasoned illustration.
  ``DOCS-CODE-UNKNOWN``      a code the docs *present as a finding code* that no
                             gate emits — so `gate explain` would fail on it.
  ``DOCS-CLI-UNKNOWN``       an `architect-cli` command or subcommand the parser
                             does not define.
  ``DOCS-REFERENCE-DRIFT``   `docs/REFERENCE-GATES.md` is not a fresh generation.

WHAT IT DOES NOT CHECK, AND WHY
    Not every SCREAMING-KEBAB token in a document is a finding code: `W-15`,
    `CLR-004`, `BSA-FIT-03`, `VERIFIED-BY-SCRIPT` and `CR-001-DDD-CONTAINER-MAPPING`
    all match the shape. Measured across `docs/`, a blanket check reports **70**
    such tokens, of which the overwhelming majority are work-item ids, fitness
    ids and verdict vocabularies.

    So `DOCS-CODE-UNKNOWN` is scoped to the two places a reader looks a code *up*
    and expects `architect-cli gate explain` to answer: the code tables in
    `REFERENCE-GATES.md`, and the `###` headings of `TROUBLESHOOTING.md`. A check
    that reports 70 false positives is a check nobody runs — the same reasoning
    that kept the finding-code derivation narrow in `bootstrap.py`.

    `docs/samples/workspace-template/**` is excluded entirely. Those are page
    *templates*: their links carry `{{INDEX_PATH}}` placeholders and resolve
    inside a materialized workspace, not inside `docs/`. Grading a template as if
    it were a document would report five findings that are all correct behaviour.

READ-ONLY
    This gate writes nothing. `scripts/build_docs_reference.py` is the writer, and
    specification's rule holds: a writer is never executed by the roll-call.
"""

from __future__ import annotations

import re
import runpy
import hashlib
import json
from pathlib import Path

from architect_framework.gates.base import Finding, GateContext, GateResult
from architect_framework.gates import registry

DOCS = "docs"

#: Template bodies, not documentation. Their links resolve in a materialized
#: workspace; here they are placeholders by design.
_EXCLUDED_DIRS = ("workspace-template",)

#: A `GATE-…` / `TOOL-…` token as the documentation writes them. The lookbehind
#: stops the pattern matching a *suffix* of a longer code — without it
#: `DOCS-GATE-UNKNOWN` reports a phantom gate called `GATE-UNKNOWN`, which is the
#: check inventing its own findings.
_GATE_TOKEN = re.compile(r"(?<![A-Z0-9-])((?:GATE|TOOL)-[A-Z0-9][A-Z0-9-]*)\b")

#: A relative markdown link. The fragment is dropped: an anchor into an existing
#: file is a different (and much weaker) claim than the file existing at all.
_LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")

#: A fence opener or closer.
_FENCE = re.compile(r"^\s*```")

#: `architect-cli <command> [<subcommand>]` inside prose or a fenced block.
_CLI = re.compile(r"architect-cli\s+([a-z][a-z-]*)(?:\s+([a-z][a-z-]*))?")

#: Commands whose second word is a subcommand rather than an argument.
_TWO_LEVEL = {"gate", "seam", "plan", "evidence", "charter", "tree-plan"}

#: Tokens that are deliberately not real IDs. Each carries a reason, for the same
#: rule the seam ledger and `roll_call.skip` already apply: an exemption without a
#: reason is indistinguishable from an oversight.
_ILLUSTRATIVE: dict[str, str] = {
    "GATE-TIMEOUT": (
        "a **finding code**, not a gate. `subprocess_gate.py` emits it for whichever gate "
        "exceeded its budget, so it belongs to no single entry's `findings:` list and the "
        "registry cannot know it. A document describing a gate that timed out has to be "
        "able to name the code it saw"
    ),
    "GATE-NOPE": "specification's negative control — a row citing a gate nobody registered must fail generation",
    "GATE-X": "a stand-in in `gate_script(\"GATE-X\")`, quoted from run_hooks.py's call shape",
    "GATE-ID": "the literal placeholder in `cite it by ID`-style instructions",
    "GATE-ARROW-FIXTURE": "a throwaway gate built inside a test to prove non-ASCII output decodes",
    "GATE-FIXTURE": "a throwaway gate built inside a test to prove an invented flag is never passed",
    "GATE-SOURCE-MAP-TYPED--VENDOR": (
        "historical. specification registered the vendored wrapper under this ID and specification retired it to "
        "`GATE-SOURCE-MAP-TYPED--SDD-AGENT`. The mention sits in an Evidence cell, which is a record "
        "of what was true then; rewriting it would falsify the history the checklist exists to keep"
    ),
    "GATE-SUBMODULE-FITNESS": (
        "evidence of fabrication, never a gate. specification section 1.3 quotes "
        "it verbatim from 51 Verification rows an agent wrote into a materialized workspace; the "
        "document's point is that no registry entry has ever carried this ID"
    ),
}

#: A trailing `*` makes the token a glob over a family (`GATE-WORKSPACE-*`), not a
#: claim that one ID exists. Two characters are read, not one: the greedy token
#: pattern gives back the trailing hyphen to satisfy `\b`, so the tail seen here is
#: `-*` rather than `*`.
_GLOB_SUFFIX = ("*", "-*")


def _docs_root(ctx: GateContext) -> Path:
    return Path(str(ctx.repo_root)) / DOCS


def _documents(root: Path) -> list[Path]:
    out = []
    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(root)
        if any(part in _EXCLUDED_DIRS for part in rel.parts):
            continue
        out.append(path)
    return out


def _historical_records(repo_root):
    """Pinned history has no executable guidance. Links still require validation."""
    path = repo_root / "docs/document-lifecycle.json"
    if not path.is_file(): return set(), []
    valid, findings = set(), []
    try:
        records = json.loads(path.read_text(encoding="utf-8"))["historical_records"]
        if not isinstance(records, list): raise ValueError("Historical records must be a list")
        for record in records:
            relative = record["path"]
            target = repo_root / relative
            if (not isinstance(relative, str) or not relative.startswith("docs/") or ".." in Path(relative).parts
                    or relative in valid or not record["owner"] or not record["reason"] or record["status"] != "historical"
                    or not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != record["sha256"]):
                raise ValueError("Historical records must be distinct, reasoned and bound to exact bytes")
            valid.add(relative)
    except (OSError, ValueError, TypeError, KeyError) as error:
        findings.append(Finding(code="DOCS-REFERENCE-DRIFT", path="docs/document-lifecycle.json", message=str(error)))
        return set(), findings
    return valid, findings


#: Modules whose `register(subparsers)` the CLI calls to add a top-level command.
_CLI_DELEGATES = ("architect_framework/runtime/cli.py", "architect_framework/tools/__init__.py",
                  "architect_framework/console/cli.py")


def _cli_commands(repo_root: Path) -> tuple[set[str], set[str]]:
    """Top-level commands and subcommands, read out of the parser's source.

    Read statically rather than by importing: `main()` parses `sys.argv` at call
    time, and importing to introspect a parser is the mistake `bootstrap.py`
    already refused for the same reason (at least one module builds a registry at
    import time).
    """
    src = (repo_root / "architect_framework" / "cli" / "main.py").read_text(encoding="utf-8")
    # `main.py` hands two command groups to their own modules (`runtime`, and the
    # specification `tool` group); their `register()` adds the top-level command there.
    for delegate in _CLI_DELEGATES:
        path = repo_root / delegate
        if path.is_file():
            src += "\n" + path.read_text(encoding="utf-8")
    top = set(re.findall(r'subparsers\.add_parser\("([a-z][a-z-]*)"', src))
    sub = set(re.findall(r'_sub\.add_parser\("([a-z][a-z-]*)"', src))
    return top, sub


def _presented_codes(root: Path) -> list[tuple[Path, int, str]]:
    """Codes the documentation presents *as* finding codes.

    Two shapes, both unambiguous:

    * a table row in `REFERENCE-GATES.md` whose first cell is a backticked code;
    * a `###` heading in `TROUBLESHOOTING.md` beginning with a backticked code.
    """
    out: list[tuple[Path, int, str]] = []
    code = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*$")

    reference = root / "REFERENCE-GATES.md"
    if reference.is_file():
        # Only section 5. The earlier sections tabulate gate IDs in the same first-cell
        # position, and reading those as finding codes reported 130 phantom
        # findings on the first run — the check inventing work for itself, which is
        # exactly the noise `bootstrap.py` refused when it kept the code
        # derivation narrow.
        inside = False
        for number, line in enumerate(reference.read_text(encoding="utf-8").splitlines(), 1):
            if line.startswith("## "):
                inside = line.startswith("## 5 ")
                continue
            if not inside:
                continue
            match = re.match(r"^\|\s*`([^`]+)`\s*\|", line)
            if match and code.match(match.group(1)):
                out.append((reference, number, match.group(1)))

    trouble = root / "TROUBLESHOOTING.md"
    if trouble.is_file():
        for number, line in enumerate(trouble.read_text(encoding="utf-8").splitlines(), 1):
            match = re.match(r"^###\s+`([^`]+)`", line)
            if match and code.match(match.group(1)):
                out.append((trouble, number, match.group(1)))
    return out


def _reference_check(repo_root: Path) -> tuple[bool, str]:
    """Ask the generator whether the reference on disk is a fresh generation."""
    script = repo_root / "scripts" / "build_docs_reference.py"
    if not script.is_file():
        return True, "generator absent; nothing to diff against"
    module = runpy.run_path(str(script))
    return module["check"]()


class DocsCurrentGate:
    """`GATE-DOCS-CURRENT` — read-only. Nothing here writes a file."""

    id = "GATE-DOCS-CURRENT"

    def applies_to(self, ctx: GateContext) -> str | None:
        if not _docs_root(ctx).is_dir():
            return "no docs/ directory in this repository"
        return None

    def run(self, ctx: GateContext) -> GateResult:
        reason = self.applies_to(ctx)
        if reason is not None:
            return GateResult(gate_id=self.id, exit_code=0, skipped_reason=reason)

        repo_root = Path(str(ctx.repo_root))
        root = _docs_root(ctx)
        findings: list[Finding] = []
        historical, historical_findings = _historical_records(repo_root)
        findings.extend(historical_findings)

        known_ids = set(registry.ids())
        known_codes = set(registry.findings_owners())
        top, sub = _cli_commands(repo_root)

        for path in _documents(root):
            rel = path.relative_to(repo_root).as_posix()
            text = path.read_text(encoding="utf-8")
            lines = text.splitlines()

            in_fence = False
            for number, line in enumerate(lines, 1):
                if _FENCE.match(line):
                    in_fence = not in_fence
                    continue

                # A link inside a fenced block is SAMPLE CONTENT — a rendered page
                # showing what a materialized workspace looks like, where
                # `../index.md` and `../02-domains/…` resolve and here they never
                # could. Commands and gate IDs are *not* exempted: a fenced command
                # is precisely what a reader copies, so it is the one that most
                # needs to be real.
                for match in (() if in_fence else _LINK.finditer(line)):
                    target = match.group(1)
                    if target.startswith(("http://", "https://", "mailto:")):
                        continue
                    if "{{" in target or "{" in target:
                        continue  # a template placeholder, not a link
                    resolved = (path.parent / target).resolve()
                    exists = resolved.exists()
                    if not exists:
                        findings.append(Finding(
                            code="DOCS-LINK-BROKEN", path=rel, line=number,
                            message=f"link target {target!r} does not exist",
                        ))

                for match in (() if rel in historical else _GATE_TOKEN.finditer(line)):
                    token = match.group(1)
                    tail = line[match.end(): match.end() + 2]
                    if token in known_ids or token in known_codes:
                        continue
                    if token in _ILLUSTRATIVE:
                        continue
                    if tail.startswith(_GLOB_SUFFIX) or token.endswith("-"):
                        continue  # a family glob, not a claim about one ID
                    findings.append(Finding(
                        code="DOCS-GATE-UNKNOWN", path=rel, line=number,
                        message=(
                            f"{token} is not a registered gate, a finding code, or a declared "
                            "illustration. Cite an ID `architect-cli gate list` prints, or add it "
                            "to `_ILLUSTRATIVE` **with a reason**"
                        ),
                    ))

                for match in (() if rel in historical else _CLI.finditer(line)):
                    command, subcommand = match.group(1), match.group(2)
                    if command not in top:
                        findings.append(Finding(
                            code="DOCS-CLI-UNKNOWN", path=rel, line=number,
                            message=f"`architect-cli {command}` is not a command the parser defines",
                        ))
                        continue
                    if command in _TWO_LEVEL and subcommand and subcommand not in sub:
                        findings.append(Finding(
                            code="DOCS-CLI-UNKNOWN", path=rel, line=number,
                            message=(
                                f"`architect-cli {command} {subcommand}` — {command} takes a "
                                f"subcommand and {subcommand!r} is not one"
                            ),
                        ))

        for path, number, code in _presented_codes(root):
            if code in known_codes:
                continue
            findings.append(Finding(
                code="DOCS-CODE-UNKNOWN", path=str(path.relative_to(repo_root)), line=number,
                message=(
                    f"{code} is presented as a finding code, but no registered gate emits it — "
                    "`architect-cli gate explain` would report it unknown"
                ),
            ))

        fresh, message = _reference_check(repo_root)
        if not fresh:
            findings.append(Finding(
                code="DOCS-REFERENCE-DRIFT",
                path="docs/REFERENCE-GATES.md",
                message=message,
            ))

        errors = [f for f in findings if f.severity == "error"]
        return GateResult(
            gate_id=self.id,
            exit_code=1 if errors else 0,
            findings=findings,
            scanned=len(_documents(root)),
            unit="documents",
            # The counters are labelled with their FULL code names. Abbreviating
            # `DOCS-GATE-UNKNOWN` to `GATE-UNKNOWN` made this gate's own summary
            # line read as a claim about a gate by that name — and the gate then
            # reported itself. A label that looks like an identifier is an
            # identifier as far as any reader, human or regex, is concerned.
            stdout=(
                f"docs: {len(_documents(root))} document(s) · "
                + " · ".join(
                    f"{code} {sum(1 for f in findings if f.code == code)}"
                    for code in (
                        "DOCS-LINK-BROKEN", "DOCS-GATE-UNKNOWN", "DOCS-CODE-UNKNOWN",
                        "DOCS-CLI-UNKNOWN", "DOCS-REFERENCE-DRIFT",
                    )
                )
                + "\n"
            ),
        )
