"""specification / W-22 — derive `contracts/gates.yml` from the scripts that exist.

WHY DERIVED
    Ninety-two hand-typed registry entries would be ninety-two more hand-typed
    strings, which is the problem the registry exists to remove. Every field
    below comes from the script itself: the entrypoint from the filesystem, the
    argv shape from the script's own argparse usage line, the scope from which
    positionals that usage declares.

    `--check` regenerates and diffs, so a hand-edit to the derived fields is a
    failing gate rather than a silent fork. Fields a human must decide — `phase`,
    `title`, `findings` — are preserved across regeneration by ID.

WHY USAGE INTROSPECTION AND NOT IMPORT
    Importing 92 modules to read their parsers runs their module-level code, and
    at least one of them builds a registry at import time. `--help` is what the
    scripts already promise to answer, and all 92 answer it.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from architect_framework import contracts
from architect_framework.gates.subprocess_gate import _utf8_env

REPO_ROOT = contracts.REPO_ROOT

#: Directories holding gate scripts, in registry order.
SCRIPT_ROOTS = (
    "scripts",
    "vendor/sdd-agent/scripts",
    "exported_skills/_shared/scripts",
    # specification. The vendored skill packages each ship their own scripts/, and
    # `run_sdd_phase.py` invokes two of them. Leaving them out meant 16 gate
    # scripts lived outside the roll-call, which is the E-4 failure the registry
    # exists to close. Registering them also makes their drift visible: all five
    # copies of check_output_docs.py are the same 248-line generation, 82 lines
    # behind the 330-line authoritative one in _shared. Tracked as specification.
    "vendor/sdd-agent/00-requirement-clarifier/scripts",
    "vendor/sdd-agent/01-system-architect/scripts",
    "vendor/sdd-agent/02-spec-critic/scripts",
)

#: A leading verb that says what the script does rather than what it is about.
#: Stripped from the ID so `check_doc_coverage.py` becomes `GATE-DOC-COVERAGE`,
#: matching the IDs the plan already writes by hand.
_VERBS = (
    "check", "validate", "audit", "eval", "measure",
    "build", "render", "scaffold", "extract", "compile",
    "migrate", "sync", "run", "rewrite", "classify",
)

#: Scripts whose name begins with one of these decide a pass/fail verdict.
_GATE_VERBS = {"check", "validate", "audit", "eval", "measure"}

#: A bracketed group in an argparse usage line, however many tokens it spans.
_BRACKETED = re.compile(r"\[[^\[\]]*\]")


def _strip_brackets(usage: str) -> str:
    """Remove optional groups, innermost first, until none remain."""
    previous = None
    while previous != usage:
        previous = usage
        usage = _BRACKETED.sub(" ", usage)
    return usage


@dataclass
class Derived:
    id: str
    role: str
    kind: str
    entrypoint: str
    scope: str
    argv: list[str]
    usage: str
    side_effects: str = "read-only"
    findings: list[str] = field(default_factory=list)
    phase: list[int] = field(default_factory=list)
    alias_of: str = ""


def side_effects_of(role: str) -> str:
    """``writes`` for a tool, ``read-only`` for a gate.

    specification learned this the expensive way. The first roll-call executed all 92
    entries and **dirtied 759 files**: `rewrite_descriptions.py` and
    `extract_research_basis.py` rewrote SKILL.md across the catalog,
    `build_plugin_skills.py` rewrote and deleted files under `plugins/`, and
    `render_workflow_contract.py` regenerated the vendored docs. Every one of the
    writers was `role: tool`; not one `role: gate` entry changed a file. So the
    split is not a guess — it is what the run measured.

    A curated `side_effects` in the registry overrides this, for the case of a
    checker that also writes a report.
    """
    return "writes" if role == "tool" else "read-only"


#: A finding code as the repo writes them: SCREAMING-KEBAB inside a string
#: literal or a list element. Derived rather than curated, so `gate explain`
#: cannot drift from what the gate actually prints.
#:
#: The `{2,}` segment width is deliberate and was **re-confirmed** when this
#: derivation was widened. Relaxing it to `{1,}` to catch `ROW-VERIFY-NOT-A-GATE`
#: and the `V-MAX-n` family adds 59 entries, of which most are not finding codes:
#: `A-Z`, `A-Z0-9`, `A-F0-9` and `UTF-8` fall out of regex character classes, and
#: `DC-1`, `BP-5`, `W-12`, `MOD-4` are rule and work-item ids cited in comments.
#: A derivation that reports a character class as a finding code is worse than one
#: that misses a code — it puts noise in front of every reader of `gate explain`.
#:
#: The one-character-segment codes are caught by `_CODE_EMITTED` below instead,
#: which reads the emitter *position* rather than the shape of the string.
#: `(?<![rR])`: a raw string is a regex, and `r"specification"` in a residue scanner is a
#: pattern the gate searches for, not a code it emits.
_CODE = re.compile(r"""(?<![rR])["'\[]([A-Z][A-Z0-9]+(?:-[A-Z0-9]{2,})+)['"\]:]""")

#: A code that opens a message, `f"TABLE-STALE {path}: …"`. `_CODE` wants a quote,
#: bracket or colon after the code, so every finding the V3 ratchet scripts print
#: this way read as "no findings" and `gate explain` could not place them.
_CODE_LEADING = re.compile(r"""\bf?["']([A-Z][A-Z0-9]+(?:-[A-Z0-9]{2,})+) """)

#: A code emitted through a call, where the code is the call's first argument:
#: `add("ORPHAN", …)`, `self.add(…)`, `Finding("ROW-VERIFY-NOT-A-GATE", …)`.
#:
#: This is the pattern that catches a **single-word** code. `_CODE` cannot: it
#: requires a hyphen, and loosening it to accept any quoted SCREAMING word would
#: sweep in every constant, dict key and format token in the file. Requiring the
#: code to sit in the emitter position keeps the signal — a string only becomes a
#: finding code by being *reported* as one.
#:
#: `ORPHAN` was the miss that motivated this: `check_doc_coverage.py` emits it at
#: two call sites, `ORPHAN 0` is the condition the site build waits on, and it was
#: absent from `GATE-DOC-COVERAGE`'s derived `findings` for the registry's whole
#: existence.
#:
#: `_add(` is the same emitter with a private name; `check_doc_slot_claims.py`
#: emits `DOC-SLOT-IS-A-FILE` through it, and specification found that code missing.
_CODE_EMITTED = re.compile(
    r"""\b(?:self\.)?_?(?:add|finding|emit|report|Finding)\(\s*["']"""
    r"""([A-Z][A-Z0-9]*(?:[-][A-Z0-9]+)*)["']"""
)

#: A rule-named finding: the lower-case kebab id a `Finding(...)` opens with,
#: `Finding("self-graded-pass", "error", …)`.
#:
#: specification. Five vendored gates name their findings this way and print them in the
#: columnar house format (`ERROR   self-graded-pass   path:line  message`), which
#: the runner already parses. None of the three patterns above reads a lower-case
#: code, so `GATE-AUDIT-HONESTY`, `GATE-TRACEABILITY-GRAPH`, `GATE-DENSITY` and
#: `GATE-CLONE-PAGES` were registered with no findings at all, and
#: `GATE-EVIDENCE-DISCIPLINE` with only the `SHA-256` it mentions in a comment.
#: Restricted to the `Finding(` constructor: a lower-case string in any other
#: call's first argument is a key, a path or a format, not a code.
_CODE_RULE = re.compile(r"""\b_?Finding\(\s*["']([a-z][a-z0-9]*(?:-[a-z0-9]+)+)["']""")

#: A rule named in the second argument of a report method, after the subject:
#: `report.error(skill_id, "manifest-drift", …)`, `report.fail(skill, "placeholder", …)`.
#: `validate_catalog.py` and `check_authored_sections.py` print these as
#: `[rule]`; before specification both gates were registered with no findings.
_CODE_RULE_ARG2 = re.compile(
    r"""\breport\.(?:fail|error|warn)\(\s*(?:[^,()"']+|"[^"]*"|'[^']*'),\s*"""
    r"""["']([a-z][a-z0-9]*(?:-[a-z0-9]+)*)["']"""
)

#: Prefixes that are file-shape assertions in this repo's helper scripts rather
#: than finding codes a reader would look up.
_CODE_NOISE = ("SKILL-MD", "README-", "PY-")

#: `(script filename, string)` pairs of a finding code's shape that the specification
#: review read in context and found are not codes the script prints. Keyed by
#: file, because the same string can be a code in one script and data in
#: another (`BLOCKED-ON` is a finding class the workflow manager routes, and
#: only a regex fragment in the semantic-rules gate). Each carries its reason:
#: an entry here is invisible to `gate explain`, so a wrong one costs what a
#: missed code costs.
_CODE_NOT_A_FINDING: dict[tuple[str, str], str] = {
    ("check_evidence_discipline.py", "SHA-256"): "a hash algorithm in the recognised-technology vocabulary",
    ("check_sdd_semantic_rules.py", "PCI-DSS"): "a regulated-scope keyword the rules match on",
    ("check_sdd_semantic_rules.py", "BLOCKED-ON"): "the `[BLOCKED-ON:` placeholder fragment of a regex",
    ("check_output_docs.py", "RI-10"): "the rule id a docstring cites",
    ("build_checklist.py", "CK-RUN-001"): "the id of a checklist row the tool writes",
    ("check_module_identity.py", "STABLE-ID"): "a `[STABLE-ID]` title suffix the name normaliser drops",
    **{("check_skill_fixture_matrix.py", marker): "a golden-prompt marker the fixture must contain"
       for marker in ("APP-FIT", "BE-FIT", "DATA-FIT", "DOM-FIT", "EXT-FIT", "FE-FIT",
                      "INFRA-FIT", "INT-FIT", "LIB-FIT", "OBS-FIT")},
}


def findings_of(path: Path) -> list[str]:
    """Finding codes the gate can emit, read out of its own source.

    Three patterns, unioned. `_CODE` reads the hyphenated codes wherever they are
    written; `_CODE_EMITTED` reads whatever sits in the first argument of an
    emitter call, which is the only way a code with no hyphen can be told apart
    from an ordinary constant; `_CODE_LEADING` reads a code that opens a message.

    A code the gate prints but this function misses is worse than it sounds: it is
    invisible to `gate explain`, so the one command that tells a reader which gate
    to run reports an unknown code for a finding they are looking at.
    """
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    codes = {m.group(1) for m in _CODE.finditer(src)}
    codes |= {m.group(1) for m in _CODE_EMITTED.finditer(src)}
    codes |= {m.group(1) for m in _CODE_LEADING.finditer(src)}
    codes |= {m.group(1) for m in _CODE_RULE.finditer(src)}
    codes |= {m.group(1) for m in _CODE_RULE_ARG2.finditer(src)}
    return sorted(
        c for c in codes
        if not c.startswith(_CODE_NOISE) and (path.name, c) not in _CODE_NOT_A_FINDING
    )








def gate_id(path: Path, role: str) -> str:
    stem = path.stem
    for verb in _VERBS:
        if stem.startswith(verb + "_"):
            stem = stem[len(verb) + 1 :]
            break
    slug = stem.replace("_", "-").upper()
    prefix = "GATE" if role == "gate" else "TOOL"
    return f"{prefix}-{slug}"


def role_of(path: Path) -> str:
    verb = path.stem.split("_", 1)[0]
    return "gate" if verb in _GATE_VERBS else "tool"


class UsageUnavailable(RuntimeError):
    """`--help` could not be read, so no argv may be derived from it.

    Raised rather than returning a placeholder. This fixes a defect this module
    shipped: `usage_of` used to swallow **any** failure into ``'usage: (none)'``,
    and the caller then recorded `scope: repo` with an empty `argv`. Two entries
    were degraded that way during Phase II — `GATE-CATALOG-ISOMORPHISM` and
    `TOOL-SITE-LAYOUT` — both of which use argparse and both of which answer
    `--help` with exit 0. Their `--help` almost certainly timed out under load.
    The registry then asserted, permanently, that a gate needing `--workspace`
    takes no arguments.

    A transient failure must not become a committed fact. `gate bootstrap` now
    fails loudly and the previous entry survives.
    """


_HELP_TIMEOUT_S = 90

#: Scripts that do not use argparse and legitimately have no usage line. Declared,
#: so "this script takes no argv" is a recorded fact rather than an inference from
#: a failed subprocess. Add to this list only after reading the script's source.
NO_ARGPARSE = frozenset({
    "check_skill_structure.py",
    "doc_rules.py",
    "puml_parser.py",
    "sdd_layout.py",
    "source_ingestion.py",
    "spec_text_normalization.py",
    "sync_registry.py",
    "clarification_state.py",
})

NO_USAGE = "usage: (none)"


def usage_of(path: Path, timeout: int = _HELP_TIMEOUT_S, retries: int = 2) -> str:
    """The script's argparse usage line.

    Retries before giving up, because the failure being fixed here was a timeout
    under parallel load rather than a broken script. Raises
    :class:`UsageUnavailable` when there is no usage line **and** the script is not
    in :data:`NO_ARGPARSE`.
    """
    last = "no output"
    for _ in range(retries + 1):
        try:
            proc = subprocess.run(
                [sys.executable, str(path), "--help"],
                capture_output=True, text=True, encoding="utf-8", errors="replace", env=_utf8_env(), timeout=timeout, cwd=str(REPO_ROOT),
            )
        except subprocess.TimeoutExpired:
            last = f"--help exceeded {timeout}s"
            continue
        text = (proc.stdout or "") + (proc.stderr or "")
        lines: list[str] = []
        started = False
        for line in text.splitlines():
            if line.lower().startswith("usage:"):
                started = True
            elif started and (not line.startswith(" ") or not line.strip()):
                break
            if started:
                lines.append(line.strip())
        usage = " ".join(lines).strip()
        if usage:
            return usage
        last = (text.strip().splitlines() or ["no output"])[-1][:160]
        if path.name in NO_ARGPARSE:
            return NO_USAGE
    if path.name in NO_ARGPARSE:
        return NO_USAGE
    raise UsageUnavailable(
        f"{path.name}: no usage line after {retries + 1} attempt(s). Last output: {last!r}\n"
        "Recording an empty argv would tell the registry, permanently, that this gate "
        "takes no arguments. Either the script is broken, or it does not use argparse — "
        "in which case add its filename to bootstrap.NO_ARGPARSE after reading its source."
    )


def _required_tokens(usage: str) -> list[str]:
    """Tokens outside every optional group, after the program name.

    Bracket stripping must be balanced and iterative: a single pass reads
    ``[--contract CONTRACT]`` as two tokens and yields argv like ``{contract]}``.
    """
    bare = _strip_brackets(usage)
    bare = re.sub(r"^usage:\s*\S+\s*", "", bare).strip()
    return [t for t in bare.split() if t not in {"...", "|"}]


def required_flags(usage: str) -> list[tuple[str, str]]:
    """`[(--flag, METAVAR)]` for flags argparse declares **required**.

    argparse prints a required option unbracketed: ``usage: prog [-h] --fixture
    FIXTURE workspace``. Treating ``FIXTURE`` as a positional is why 25 of 92
    registry entries produced an argparse usage error on the first roll-call —
    the value was passed in the wrong position and the flag never appeared.
    """
    out: list[tuple[str, str]] = []
    tokens = _required_tokens(usage)
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token.startswith("--"):
            metavar = ""
            if index + 1 < len(tokens) and not tokens[index + 1].startswith("-"):
                candidate = tokens[index + 1]
                # A metavar is UPPER_CASE or {a,b,c}; a following positional is not.
                if candidate.isupper() or candidate.startswith("{"):
                    metavar = candidate
                    index += 1
            out.append((token, metavar))
        index += 1
    return out


def positionals(usage: str) -> list[str]:
    """Required positionals — bare tokens that are not a flag or a flag's metavar."""
    consumed: set[int] = set()
    tokens = _required_tokens(usage)
    for i, token in enumerate(tokens):
        if token.startswith("-"):
            consumed.add(i)
            if i + 1 < len(tokens) and (tokens[i + 1].isupper() or tokens[i + 1].startswith("{")):
                consumed.add(i + 1)
    out: list[str] = []
    for i, token in enumerate(tokens):
        if i in consumed or token.startswith("-"):
            continue
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", token):
            continue
        out.append(token)
    return out


def subcommands(usage: str) -> list[str]:
    """The verbs of a dispatcher such as ``sdd_workflow_manager {intake,route,resolve}``.

    A dispatcher cannot be roll-called without one, which is a fact about the
    tool rather than a defect; the registry records it and the roll-call skips
    with that reason.
    """
    match = re.search(r"\{([a-z0-9-]+(?:,[a-z0-9-]+)+)\}", usage)
    return match.group(1).split(",") if match else []


#: A sole positional with one of these names is the root a skill wrote its output
#: into — a workspace. specification: `check_output_docs.py` takes `output_root` (or
#: `output_dir` in the vendored copy), so it derived as `scope: repo` and a
#: workspace run never selected it. The vendored aggregate script passed it the
#: workspace; deleting that script without this would have dropped the only
#: place the output-docs check ran on a workspace.
_OUTPUT_ROOT_POSITIONALS = frozenset({"output_root", "output_dir"})


def _is_output_root(pos: list[str]) -> bool:
    return len(pos) == 1 and pos[0].lower() in _OUTPUT_ROOT_POSITIONALS


def scope_of(pos: list[str], usage: str) -> str:
    lowered = [p.lower() for p in pos]
    if any(p in {"workspace", "ws"} for p in lowered) or _is_output_root(pos):
        return "workspace"
    if any("catalog" in p for p in lowered):
        return "catalog"
    if "--workspace" in usage:
        return "workspace"
    if "--catalog" in usage:
        return "catalog"
    return "repo"


def argv_of(usage: str, pos: list[str], scope: str) -> list[str]:
    """The argv template: required flags as `--flag {value}` pairs, then positionals."""
    out: list[str] = []
    for flag, metavar in required_flags(usage):
        out.append(flag)
        if not metavar:
            continue
        if metavar.startswith("{"):
            # A choice metavar (`--phase {0,1,2,3}`) is not a name. Use the flag's
            # own name, so the placeholder is `{phase}` rather than `{0_1_2_3}`.
            name = flag.lstrip("-").replace("-", "_")
        else:
            name = re.sub(r"[^a-z0-9_]", "_", metavar.lower())
        out.append("{" + name + "}")
    if _is_output_root(pos):
        out.append("{workspace}")
        return out
    out.extend(f"{{{p.lower()}}}" for p in pos)
    if out:
        return out
    # No required argument at all. The scope was inferred from an *optional*
    # `--workspace`/`--catalog` flag, so the value must be passed as that flag.
    # Emitting a bare positional here produced "unrecognized arguments" on four
    # gates in the first roll-call.
    if scope == "workspace" and "--workspace" in usage:
        return ["--workspace", "{workspace}"]
    if scope == "catalog" and "--catalog" in usage:
        return ["--catalog", "{catalog}"]
    if scope == "workspace":
        return ["{workspace}"]
    return out




def derive() -> list[Derived]:
    """Derive metadata only for explicitly registered current script entry points.

    Discovery never promotes a Python file into executable product policy.
    Native core gates stay explicit in the registry.
    """
    rows = []
    for entry in load_existing():
        relative = entry["entrypoint"]
        if not relative.endswith(".py"):
            continue
        path = REPO_ROOT / relative
        if not path.is_file():
            raise ValueError(f"Registered entrypoint is missing: {relative}")
        usage = usage_of(path)
        rows.append(Derived(id=entry["id"], role=entry.get("role", "gate"),
            kind=entry["kind"], entrypoint=relative, scope=entry.get("scope", "repo"),
            argv=entry.get("argv", []), usage=usage[:200],
            side_effects=entry.get("side_effects", "read-only"),
            findings=findings_of(path), phase=[], alias_of=entry.get("alias_of", "")))
    return rows


_HEADER = """\
# Gate registry — declarative gate and tool catalog.
#
# A gate is an ID in this file. It is never a file path typed into a checklist:
# 16 of 45 argv cited across docs/ and the workspaces did not resolve, and four
# of the unresolvable ones were cited as the evidence that closed Phase 0.
#
# DERIVED FIELDS — regenerate, do not hand-edit:
#     id · kind · entrypoint · scope · argv · usage · findings
#     `architect-cli gate bootstrap --check` fails when they differ from a fresh
#     derivation. `argv` and `scope` come from each script's own argparse usage
#     line; `id` strips the leading verb so check_doc_coverage.py is
#     GATE-DOC-COVERAGE.
#
# CURATED FIELDS — safe to edit, preserved across regeneration by id:
#     title · timeout_s · roll_call · side_effects · phase · alias_of · codes · no_findings · stage
#     `phase` is curated per workspace verification stage and is
#     curated from here on: the runner now selects by phase, so re-deriving it
#     from the runner would unassign every gate.
#     `codes.<CODE>` gives each derived finding code its `class` (derived ·
#     contract · heuristic · style — only the first two count toward an exit
#     code) and its `remedy` (imperative; never "remove"/"delete"). An entry with
#     no code declares `no_findings: {kind, reason}` instead. `gate bootstrap
#     --check` fails while any code lacks a class or any entry lacks both.
#
# kind: native with a `.py` entrypoint is a script run in this process (
# `architect_framework/gates/inprocess.py`): same argv, same parsers, no child
# interpreter. kind: subprocess is left for `role: tool` entries.
"""


#: Fields a human decides. Preserved across regeneration by id, so re-deriving
#: never silently discards a curated value.
#:
#: `codes` (specification, specification) holds, per finding code, how it is proven (`class`) and
#: what to do about it (`remedy`). `no_findings` (specification) is the declared reason an
#: entry has no finding code at all. Both are judgements, so both are curated;
#: :func:`problems` is what keeps them in step with the derived `findings`.
#: specification — where a `role: gate` entry with no workspace phase runs. Modelled on
#: pre-commit's `stages`: `ci` is the repository/catalogue battery the CI workflow
#: runs (`gate run --stage ci`); `manual` needs an input only a person or a live
#: run provides (a per-skill check, a fixture of a live run) and runs when invoked.
STAGES = ("ci", "manual")

CURATED_FIELDS = (
    "title", "timeout_s", "roll_call", "side_effects", "phase", "alias_of", "codes", "no_findings", "stage", "workspace_modes",
)

#: specification / specification G-1 — how a finding is proven. Classified by what
#: makes the finding true or false, not by how much it matters: a guess that is
#: "important" is still a guess.
FINDING_CLASSES: dict[str, str] = {
    "derived": "a fact read off the files: a path exists, a link resolves, a key is present, "
               "a regenerated artifact matches",
    "contract": "a line of a contract: a declared slot, a vocabulary token, a registered id",
    "heuristic": "a judgement: a threshold on density or similarity, a pattern over prose",
    "style": "house style: how a page reads, not whether it is right",
}

#: Classes that count toward a gate's exit code. `heuristic` and `style` are
#: printed as notes and never fail a run on their own (G-1). specification
#: section 9 decision 1 adds the condition this registry keeps: a rule is not demoted
#: while no `derived`/`contract` rule measures the same fault — so a code that
#: fails a gate today is classified blocking until the owner decides (specification).
BLOCKING_CLASSES = frozenset({"derived", "contract"})

#: specification — why an entry declares no finding code, each with a predicate
#: :func:`problems` checks rather than trusts.
NO_FINDINGS_KINDS: dict[str, str] = {
    "tool": "a tool writes, renders or reports; it does not grade, so it has no finding "
            "vocabulary (predicate: role is tool)",
    "exit-code": "a gate whose verdict is its exit code and a prose summary; it prints no "
                 "finding code for `gate explain` to look up (predicate: role is gate and no "
                 "code is derivable from its source)",
}

#: specification / G-3 — a remedy never opens with a deleting verb. The one way a finding
#: can make content disappear is by telling its reader to delete, and a finding
#: whose only fix is deletion erodes the document even when it is right.
DELETE_VERBS = ("remove", "delete", "drop", "strip", "erase", "purge")

#: Codes whose remedy may open with a deleting verb, each with the reason. Only a
#: code that catches something that should never have been written qualifies — a
#: secret, a generated file committed by mistake — never one about content.
DELETE_REMEDY_ALLOWED: dict[str, str] = {
    "STALE-PENDING": "the PENDING entry names a finding that has closed; that list is a debt "
                     "register, not document content",
    "PHASE-SEAM-STALE": "the SEAMED entry names a gap that producers now fill; that list is a debt "
                        "register, not document content",
    "TABLE-STALE": "the classification row names a path that is no longer a candidate: registry "
                   "residue, not document content",
}


def problems(entries: list[dict], retired: list[dict] | None = None) -> list[str]:
    """What keeps the registry from answering `gate explain` for every code.

    Empty means: every entry declares codes or a checked reason for having none
    (specification); every code has a class from :data:`FINDING_CLASSES` and a remedy
    (specification, specification); no remedy opens with a deleting verb outside
    :data:`DELETE_REMEDY_ALLOWED`; no curated block describes a code the gate no
    longer emits; and every retired ID says where its job went.
    """
    out: list[str] = []
    live = {str(e.get("id")) for e in entries}
    for row in retired or []:
        rid = str(row.get("id") or "")
        if rid in live:
            out.append(f"retired {rid} is still a live entry")
        successor = row.get("successor")
        if successor and str(successor) not in live:
            out.append(f"retired {rid}: successor {successor} is not a live entry")
        for key in ("replacement", "reason"):
            if not str(row.get(key) or "").strip():
                out.append(f"retired {rid}: `{key}` is empty")
    for entry in entries:
        gid = str(entry.get("id"))
        # specification: a gate runs in a workspace phase, in CI, or on demand — one, declared.
        stage = entry.get("stage")
        if stage is not None and stage not in STAGES:
            out.append(f"{gid}: stage {stage!r} is not one of {sorted(STAGES)}")
        if stage and entry.get("phase"):
            out.append(f"{gid}: has both a phase and stage {stage!r}; a gate runs in one place")
        if stage == "ci" and entry.get("scope") == "workspace":
            out.append(f"{gid}: stage ci needs no workspace, but the gate's scope is workspace")
        findings = [str(c) for c in entry.get("findings") or []]
        codes = entry.get("codes") or {}
        declared = entry.get("no_findings")
        if findings and declared:
            out.append(f"{gid}: declares no_findings but emits {', '.join(findings[:4])}")
        if not findings and not declared:
            out.append(f"{gid}: no finding code and no `no_findings` declaration (specification)")
        if declared:
            kind = str((declared or {}).get("kind") or "")
            reason = str((declared or {}).get("reason") or "").strip()
            role = str(entry.get("role", "gate"))
            if kind not in NO_FINDINGS_KINDS:
                out.append(f"{gid}: no_findings.kind {kind!r} is not one of {sorted(NO_FINDINGS_KINDS)}")
            elif kind == "tool" and role != "tool":
                out.append(f"{gid}: no_findings.kind tool on an entry whose role is {role}")
            elif kind == "exit-code" and role != "gate":
                out.append(f"{gid}: no_findings.kind exit-code on an entry whose role is {role}")
            if len(reason.split()) < 4:
                out.append(f"{gid}: no_findings.reason must say what the entry prints instead")
        if not isinstance(codes, dict):
            out.append(f"{gid}: codes must be a mapping of code -> {{class, remedy}}")
            continue
        for code in findings:
            meta = codes.get(code)
            if not isinstance(meta, dict):
                out.append(f"{gid}: {code} has no class and remedy (specification)")
                continue
            klass = str(meta.get("class") or "")
            if klass not in FINDING_CLASSES:
                out.append(f"{gid}: {code} class {klass!r} is not one of {sorted(FINDING_CLASSES)}")
            remedy = str(meta.get("remedy") or "").strip()
            if not remedy:
                out.append(f"{gid}: {code} has no remedy (specification)")
            elif remedy.split()[0].lower().strip(":,.`'\"") in DELETE_VERBS \
                    and code not in DELETE_REMEDY_ALLOWED:
                out.append(f"{gid}: {code} remedy opens with a deleting verb: {remedy[:60]!r} (G-3)")
        for code in codes:
            if str(code) not in findings:
                out.append(f"{gid}: codes.{code} describes a code the gate no longer emits")
    return out


def _curated(existing: dict) -> dict:
    return {
        key: existing[key]
        for key in CURATED_FIELDS
        if key in existing and existing[key] not in (None, "", [], {})
    }


def render(rows: list[Derived], existing: list[dict] | None = None,
           retired: list[dict] | None = None) -> str:
    """The registry text: derived rows, curated fields kept by id, natives, retired IDs.

    `retired` is curated: an ID leaves `gates:` when its script is merged or
    deleted, and its row there keeps the ID answerable (see `registry.retired`).
    """
    if retired is None:
        retired = load_retired()
    keep ={ str(e.get("id")): _curated(e) for e in (existing or []) }
    # A registered gate's ID quoted in a script — `GATE-SEAM-LEDGER` as the default
    # of a scaffolded page — is a reference to that gate, not a code it emits.
    gate_ids = {row.id for row in rows} | {str(e.get("id")) for e in (existing or [])}
    gate_ids |= {str(r.get("id")) for r in retired or []}
    out: list[dict] = []
    for row in rows:
        row.findings = [c for c in row.findings if c not in gate_ids]
        entry = {
            "id": row.id,
            "role": row.role,
            "kind": row.kind,
            "entrypoint": row.entrypoint,
            "scope": row.scope,
            "argv": row.argv,
            "usage": row.usage,
            "side_effects": row.side_effects,
            "findings": row.findings,
            "phase": [],
        }
        if row.alias_of:
            entry["alias_of"] = row.alias_of
        entry.update(keep.get(row.id, {}))
        out.append(entry)
    retired_ids = {str(r.get("id")) for r in retired or []}
    if existing:
        for e in existing:
            # A native entry the scan does not derive (a gate class in the framework) is
            # kept; one whose ID moved to `retired:` leaves, or it could never retire.
            if str(e.get("id")) in retired_ids:
                continue
            if e.get("kind") == "native" and not any(o["id"] == e["id"] for o in out):
                out.append(e)
    document: dict = {"schema_version": "2026.08", "kind": "gate-registry"}
    if retired:
        # Before `gates:`, so an entry appended at the end of the file by hand
        # still lands in the gate list.
        document["retired"] = retired
    document["gates"] = out
    body = yaml.safe_dump(document, sort_keys=False, width=100, allow_unicode=True)
    return _HEADER + body


def load_existing() -> list[dict]:
    if not contracts.available("gates"):
        return []
    return list(contracts.raw("gates").get("gates") or [])


def load_retired() -> list[dict]:
    if not contracts.available("gates"):
        return []
    return [dict(r) for r in contracts.raw("gates").get("retired") or [] if isinstance(r, dict)]


def write(path: Path | None = None) -> Path:
    target = path or contracts.path_of("gates")
    target.parent.mkdir(parents=True, exist_ok=True)
    text = render(derive(), load_existing())
    target.write_text(text, encoding="utf-8", newline="\n")
    contracts.clear_cache()
    return target


def check(path: Path | None = None) -> tuple[bool, str]:
    """True when the file on disk matches a fresh derivation."""
    target = path or contracts.path_of("gates")
    if not target.is_file():
        return False, f"{target} does not exist"
    fresh = render(derive(), load_existing())
    current = target.read_text(encoding="utf-8")
    # specification: a code with no class, or an entry with neither codes nor a reason,
    # fails the check even when the derived fields match — "fresh" is not the
    # same as "explainable".
    document = yaml.safe_load(fresh) or {}
    issues = problems(list(document.get("gates") or []), list(document.get("retired") or []))
    if current == fresh and not issues:
        return True, "gates.yml matches a fresh derivation"
    parts: list[str] = []
    if current != fresh:
        import difflib

        diff = "\n".join(
            difflib.unified_diff(
                current.splitlines(), fresh.splitlines(), "on-disk", "derived", lineterm="", n=1
            )
        )
        parts.append(diff[:4000])
    if issues:
        shown = issues[:40]
        parts.append(
            f"{len(issues)} registry problem(s) (specification):\n  " + "\n  ".join(shown)
            + (f"\n  … {len(issues) - len(shown)} more" if len(issues) > len(shown) else "")
        )
    return False, "\n".join(parts)
