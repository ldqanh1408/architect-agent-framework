#!/usr/bin/env python3
"""R6.1 / GATE-PROSE-LINT — prose and markdown structure linting with ratcheted rules.

Implements style & structure checks following the Vale / Datadog / GitLab ratchet model:
- Promoted ERROR rules (must be clean, regression fails build):
  * UNCLOSED-FENCE: unclosed code fence blocks (```).
  * HEADING-JUMP: heading levels skipping steps (e.g. # followed by ###).
  * EMPTY-SECTION: heading followed immediately by equal/higher heading with no content.
- Warning / suggestion rules (advisory):
  * REPEATED-WORD: accidental consecutive duplicate words (e.g. "the the").
  * UNBOUND-TODO: dangling TODO/FIXME without issue or clause reference.

The two warning rules read prose only: :func:`strip_markup` removes frontmatter,
fenced code, code spans and link targets first (specification / specification G-2).

Usage:
    python scripts/lint_prose.py [--target PATH] [--json] [--strict]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

#: A fence opener or closer: three or more backticks or tildes, at any indentation.
#:
#: WHY ANY INDENTATION
#:     The first version matched only column 0, so a fence nested in a list item —
#:     `   ```console` under a numbered step — was not a fence at all. Its body was
#:     linted as prose, and a `# comment` line inside a shell block read as a heading.
#:     CommonMark lets a list item indent its fence; the closer must use the same
#:     character and be at least as long as the opener.
_RE_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
_RE_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_RE_REPEATED_WORD = re.compile(r"\b([A-Za-z]{3,})\s+\1\b", re.IGNORECASE)

#: Words this rule must not flag when written twice in a row.
#:
#: WHY A VOCABULARY AND NOT A WEAKER RULE
#:     `REPEATED-WORD` looks for an accidental "the the". Vietnamese builds words by
#:     writing the same syllable twice on purpose — `song song` (in parallel),
#:     `chung chung` (vague) — so on a Vietnamese corpus the rule reports a defect for
#:     every correct use of a whole class of words. Measured on `docs/` before this
#:     list existed: 14 findings, all of them this false positive, all in prose that
#:     was right.
#:
#:     Vale solves this with a per-project vocabulary (`accept.txt`) rather than by
#:     relaxing the rule, because a relaxed rule stops catching the typo it exists for.
#:     This set is that vocabulary. Add a word only with a measured false positive
#:     behind it. `fixture fixture` and `contract contract` in `docs/CHECKLIST-E2E.md`
#:     were deliberately kept out; specification checked them, and both are an argparse flag
#:     and its metavar inside a code span (`--fixture FIXTURE`), which the rule no
#:     longer reads — so the fix was stripping markup, not widening this set.
#:
#: The English entries predate this comment and are kept as they were.
_REPEATED_WORD_ALLOWED = {
    "that", "had", "can",       # English: "that that", "had had", "can can"
    "song",                     # Vietnamese: `song song` — in parallel
    "chung",                    # Vietnamese: `chung chung` — vague, unspecific
}
#: A bare `TODO` / `FIXME` with nothing tracking it.
#:
#: WHY THE LOOKBEHIND
#:     `\b` treats a hyphen as a boundary, so `\bTODO\b` also matches the tail of
#:     `UNBOUND-TODO` — this rule's own finding code. Every document that cites the
#:     code by ID therefore reported itself as defective, which is the one thing a
#:     finding code must never do: `specification` took
#:     two warnings for naming the rule it was explaining. The lookbehind requires the
#:     token to start a word rather than end a compound identifier, so `TODO: fix this`
#:     still fires and `UNBOUND-TODO`, `TODO-123-STATE` do not.
#:
#: WHY UPPER CASE AND WHY AT THE START OF A UNIT (specification)
#:     The rule used to match `todo` anywhere, in any case. On `docs/` it reported
#:     179 findings and not one was a dangling marker (specification section 1.1):
#:     the `todo` value of a Status column, `todo` defined inside a code span, and
#:     sentences *about* the word (`is not a todo`, `5 todo`). A marker is a
#:     convention, and the convention is the upper-case word opening a note — the
#:     same reading ESLint's `no-warning-comments` takes with `location: "start"`.
#:     So the rule now matches upper-case `TODO`/`FIXME` at the start of a unit of
#:     text — a line, a list item, a table cell, or a sentence — after
#:     :func:`strip_markup` has removed code and link targets. `TODO: fix this`
#:     still fires; a Status cell reading `todo` does not.
_RE_UNBOUND_TODO = re.compile(
    r"(?<![-\w])(TODO|FIXME)\b(?!-)(?!\s*[:(]?\s*(\bISSUE-\d+|\bCLR-|\bWO-|\bFIT-|\bR\d+))"
)

#: What may precede a marker inside its unit: list bullets, an ordered-list number,
#: a task checkbox, a blockquote marker, and emphasis.
_RE_UNIT_LEAD = re.compile(r"^(?:\s|>|[-*+](?=\s)|\d+[.)](?=\s)|\[[ xX]\]|[*_]{1,3})*")

#: Unit boundaries: a table-cell pipe, or the space after a sentence's end.
_RE_UNIT_SPLIT = re.compile(r"\s*\|\s*|(?<=[.!?;])\s+")

_RE_CODE_SPAN = re.compile(r"(`+)(?:(?!\1).)+?\1")
_CODE_PLACEHOLDER = " ‹code› "
_RE_LINK_TARGET = re.compile(r"(\]\s*)\([^)\s]*(?:\s+\"[^\"]*\")?\)")
_RE_AUTOLINK = re.compile(r"<(?:https?|mailto):[^>\s]*>")
_RE_HTML_COMMENT = re.compile(r"<!--.*?-->")


def _fence_run(line: str) -> str | None:
    """The fence characters a line opens or closes with, or ``None``."""
    m = _RE_FENCE.match(line)
    return m.group(1) if m else None


def strip_markup(lines: list[str]) -> list[str]:
    """The prose of a markdown file, one entry per input line (specification / G-2).

    Heuristic prose rules must read what a person wrote, not the markup around
    it. Blanked: YAML frontmatter, fenced code (at any indentation, so a fence in
    a list item counts), code spans, link targets, autolinks and HTML comments.
    Table rows keep their cell text and their pipes, so a rule can treat each
    cell as its own unit instead of reading a whole row as one sentence.

    Line count and line numbers are preserved: entry ``i`` is line ``i + 1``,
    so a finding still points at the line the reader opens. Structure rules
    (fences, headings) read the raw lines; only prose rules read this.
    """
    out: list[str] = []
    in_frontmatter = bool(lines) and lines[0].strip() == "---"
    fence: str | None = None
    for index, line in enumerate(lines):
        if in_frontmatter:
            out.append("")
            if index > 0 and line.strip() in {"---", "..."}:
                in_frontmatter = False
            continue
        run = _fence_run(line)
        if fence is not None:
            out.append("")
            if run and run[0] == fence[0] and len(run) >= len(fence) and not line.strip()[len(run):].strip():
                fence = None
            continue
        if run:
            fence = run
            out.append("")
            continue
        text = _RE_HTML_COMMENT.sub(" ", line)
        # A placeholder, not a blank: blanking `a` in "`a` and `b` and c" would
        # leave "and  and" for REPEATED-WORD to report — a false positive made by
        # the stripping itself.
        text = _RE_CODE_SPAN.sub(_CODE_PLACEHOLDER, text)
        text = _RE_LINK_TARGET.sub(r"\1", text)
        text = _RE_AUTOLINK.sub(" ", text)
        out.append(text)
    return out


def unbound_todo(prose: str) -> bool:
    """True when a unit of `prose` opens with an untracked `TODO`/`FIXME`."""
    for unit in _RE_UNIT_SPLIT.split(prose):
        body = unit[_RE_UNIT_LEAD.match(unit).end():]
        if _RE_UNBOUND_TODO.match(body):
            return True
    return False


@dataclass
class Finding:
    file: str
    line: int
    severity: str  # "ERROR" or "WARN"
    code: str
    message: str


def lint_markdown_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    path = path.resolve()
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as e:
        rel = str(path)
        return [Finding(rel, 1, "ERROR", "READ-ERROR", str(e))]

    try:
        rel_path = str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        rel_path = str(path)

    prose_lines = strip_markup(lines)
    fence: str | None = None
    fence_start_line = 0
    prev_heading_level = 0
    prev_heading_line = 0
    prev_heading_has_content = True

    for idx, line in enumerate(lines, start=1):
        # Code fence tracking
        run = _fence_run(line)
        if fence is not None:
            prev_heading_has_content = True
            if run and run[0] == fence[0] and len(run) >= len(fence) and not line.strip()[len(run):].strip():
                fence = None
            continue
        if run:
            prev_heading_has_content = True
            fence = run
            fence_start_line = idx
            continue

        # Check headings
        m_head = _RE_HEADING.match(line)
        if m_head:
            curr_level = len(m_head.group(1))
            # If current heading is equal or higher level (<= curr_level number), and previous had no content/subsections
            if not prev_heading_has_content and prev_heading_level > 0 and curr_level <= prev_heading_level:
                findings.append(
                    Finding(rel_path, prev_heading_line, "ERROR", "EMPTY-SECTION", f"Heading level {prev_heading_level} has no content before next heading")
                )
            if prev_heading_level > 0 and curr_level > prev_heading_level + 1:
                findings.append(
                    Finding(rel_path, idx, "WARN", "HEADING-JUMP", f"Heading jumped from #{'#' * (prev_heading_level - 1)} to #{'#' * (curr_level - 1)}")
                )
            prev_heading_level = curr_level
            prev_heading_line = idx
            # If next heading is a subsection (curr_level > prev_heading_level), that counts as having structure
            prev_heading_has_content = False
            continue

        # Content line
        if line.strip():
            prev_heading_has_content = True

            # Warning checks read the prose only (specification): code, link targets and
            # frontmatter are not something a person wrote as a sentence.
            prose = prose_lines[idx - 1]
            for m in _RE_REPEATED_WORD.finditer(prose):
                word = m.group(1)
                if word.lower() not in _REPEATED_WORD_ALLOWED:
                    findings.append(
                        Finding(rel_path, idx, "WARN", "REPEATED-WORD", f"Possible duplicate consecutive word '{word}'")
                    )

            if unbound_todo(prose):
                findings.append(
                    Finding(rel_path, idx, "WARN", "UNBOUND-TODO", "Dangling TODO/FIXME without issue or clause tracking ID")
                )

    if fence is not None:
        findings.append(
            Finding(rel_path, fence_start_line, "ERROR", "UNCLOSED-FENCE", f"Unclosed code fence starting at line {fence_start_line}")
        )

    return findings


def lint_docs(target_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    if target_dir.is_file():
        if target_dir.suffix == ".md":
            findings.extend(lint_markdown_file(target_dir))
        return findings

    for md_file in sorted(target_dir.rglob("*.md")):
        # Skip node_modules, .git, venv
        parts = md_file.parts
        if any(p.startswith(".") or p in {"node_modules", "venv", "__pycache__", "dist", "build"} for p in parts):
            continue
        findings.extend(lint_markdown_file(md_file))
    return findings


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default="docs", help="Target directory or file to lint (default: docs)")
    parser.add_argument("--json", action="store_true", help="Emit findings as JSON")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    args = parser.parse_args(argv)

    target_path = (REPO_ROOT / args.target).resolve() if not Path(args.target).is_absolute() else Path(args.target)
    if not target_path.exists():
        print(f"lint_prose: target not found {target_path}", file=sys.stderr)
        return 1

    findings = lint_docs(target_path)
    errors = [f for f in findings if f.severity == "ERROR"]
    warns = [f for f in findings if f.severity == "WARN"]

    if args.json:
        print(json.dumps([f.__dict__ for f in findings], indent=2))
    else:
        for f in findings:
            print(f"{f.file}:{f.line} [{f.severity}] {f.code}: {f.message}")
        print(f"\nlint_prose: {len(errors)} errors, {len(warns)} warnings in {args.target}")

    if errors or (args.strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
