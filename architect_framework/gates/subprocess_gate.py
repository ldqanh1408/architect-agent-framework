"""specification / W-22 — the migration path: an existing script, wrapped and resolved.

The concern that stops a registry from being adopted is losing the 92 scripts
already written. Nothing here rewrites one. A ``subprocess`` gate is a *resolved,
tested reference*: the registry test asserts the entrypoint exists on disk, runs
it, and keeps the exit code. That alone closes two of the four failures in plan
section 5c.2 — E-1 (a checklist citing a gate that does not exist) and E-4 (a gate that
exists and never runs) — for all 92 in one pass.

Findings are parsed back out of stdout where the script emits the repo's house
format, so a wrapped gate still reports codes rather than an opaque exit code.
Where it does not, the exit code stands alone and that is honest: the gate is
registered and roll-called, just not yet structured. Promotion to ``native`` is
per-gate and reversible.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from architect_framework import contracts, skillpacks
from architect_framework.gates.base import Finding, GateContext, GateResult


def _utf8_env() -> dict[str, str]:
    """The parent environment with the child's text streams pinned to UTF-8.

    A gate's output is data this process parses, so its encoding is not a display
    preference — it is part of the contract between a gate and the runner. Leaving
    it to the console's active code page makes a gate's verdict depend on which
    machine ran it, which is the one property this whole registry exists to remove.

    `PYTHONUTF8=1` is the interpreter-wide switch (PEP 540); `PYTHONIOENCODING` is
    set alongside it for any child that re-execs a non-Python tool. Both are
    inherited, so a gate that shells out again keeps the guarantee.
    """
    env = dict(os.environ)
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env

#: `[ERROR] CODE path:line: message` / `[ERROR] CODE: message` — the format most
#: of the repo's validators already print.
_BRACKETED = re.compile(
    r"^\[(?P<sev>ERROR|WARNING|INFO)\]\s+(?P<code>[A-Z][A-Z0-9-]{2,})"
    r"(?:\s+(?P<path>[^\s:]+)(?::(?P<line>\d+))?)?\s*:?\s*(?P<msg>.*)$"
)
#: `ERROR   code-name  path:line  message` — the columnar variant used by
#: check_evidence_discipline.py and check_audit_honesty.py.
_COLUMNAR = re.compile(
    r"^(?P<sev>ERROR|WARNING)\s+(?P<code>[a-z][a-z0-9-]{2,})\s+"
    r"(?P<path>\S+?)(?::(?P<line>\d+))?\s+(?P<msg>.*)$"
)


#: W-35 / GT-1 — the denominator protocol a script prints, one line each:
#:   ``scanned: <N> <unit>``        how many units the script actually examined
#:   ``witness: <text>``            one unit really graded, nearest its threshold
#:   ``not-applicable: <reason>``   the script's premise does not hold here
#: The last ``scanned:`` line wins, so a script may print running totals.
_SCANNED = re.compile(r"^scanned:\s*(?P<n>\d+)(?:\s+(?P<unit>\S.*))?$", re.M)
_WITNESS = re.compile(r"^witness:\s*(?P<w>\S.*)$", re.M)
_NOT_APPLICABLE = re.compile(r"^not-applicable:\s*(?P<r>\S.*)$", re.M)


#: Per-rule denominators — the same protocol, keyed by the rule inside the gate:
#:   ``scanned[<rule>]: <N> <unit>``        what that one rule examined
#:   ``not-applicable[<rule>]: <reason>``   that rule's input is absent here
#: A gate total of 52 pages hides a rule that read none of them; these do not.
_RULE_SCANNED = re.compile(r"^scanned\[(?P<rule>[a-z0-9-]+)\]:\s*(?P<n>\d+)(?:\s+(?P<unit>\S.*))?$", re.M)
_RULE_NA = re.compile(r"^not-applicable\[(?P<rule>[a-z0-9-]+)\]:\s*(?P<r>\S.*)$", re.M)


def parse_rule_denominators(text: str) -> dict[str, dict]:
    """``{rule: {"scanned": n, "unit": u}}`` or ``{rule: {"not_applicable": reason}}``."""
    rules: dict[str, dict] = {}
    for m in _RULE_SCANNED.finditer(text):
        rules[m.group("rule")] = {"scanned": int(m.group("n")), "unit": (m.group("unit") or "").strip()}
    for m in _RULE_NA.finditer(text):
        rules[m.group("rule")] = {"not_applicable": m.group("r").strip()}
    return rules


def parse_denominator(text: str) -> tuple[int | None, str, str | None, str | None]:
    """``(scanned, unit, witness, not_applicable_reason)`` from a script's stdout."""
    scanned = list(_SCANNED.finditer(text))
    witness = _WITNESS.search(text)
    na = _NOT_APPLICABLE.search(text)
    last = scanned[-1] if scanned else None
    return (
        int(last.group("n")) if last else None,
        (last.group("unit") or "").strip() if last else "",
        witness.group("w").strip() if witness else None,
        na.group("r").strip() if na else None,
    )


def parse_findings(text: str) -> list[Finding]:
    """Best-effort recovery of structured findings from a script's stdout.

    Deliberately best-effort: a line that does not match is not invented into a
    finding. An unparsed failure shows up as a non-zero exit with no findings,
    which reads as "this gate failed and has not been structured yet" — true, and
    more useful than a fabricated code.
    """
    out: list[Finding] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        for pattern in (_BRACKETED, _COLUMNAR):
            m = pattern.match(line)
            if not m:
                continue
            out.append(
                Finding(
                    code=m.group("code"),
                    message=(m.group("msg") or "").strip() or line,
                    severity=m.group("sev").lower(),
                    path=m.group("path"),
                    line=int(m.group("line")) if m.group("line") else None,
                )
            )
            break
    return out


#: Where the bundled pack keeps its packages, as a roll-call fixture path spells it.
_PACK_DIRS = ("exported_skills/domains/", "exported_skills/tasks/", "exported_skills/orchestration/")


def _pack_installed(repo_root: Path) -> bool:
    """`<repo>/exported_skills` holds skill packages, not only the core `_shared/`."""
    root = Path(repo_root) / "exported_skills"
    if Path(repo_root).resolve() == contracts.REPO_ROOT.resolve():
        return skillpacks.installed_catalogue() is not None
    return any((root / kind).is_dir() for kind in ("domains", "tasks", "orchestration"))


@dataclass
class SubprocessGate:
    """One registry entry of ``kind: subprocess``."""

    id: str
    entrypoint: str
    argv: Sequence[str] = field(default_factory=tuple)
    scope: str = "repo"
    role: str = "gate"
    phase: Sequence[int] = field(default_factory=tuple)
    title: str = ""
    timeout_s: int = 300
    repo_root: Path | None = None

    #: The script's own argparse usage line, as derived into the registry. Read by
    #: `_curated_optional_flags` to tell a flag the script accepts from one it does
    #: not — passing an invented flag turns a gate into an argparse error.
    usage: str = ""

    #: specification. What the roll-call needs that a generic context cannot supply.
    #: ``{"skip": "<reason>"}``     the gate is not roll-callable — a dispatcher
    #:                             needing a subcommand, say. A reason, not silence.
    #: ``{"values": {...}}``        fixture values for `{placeholders}` in `argv`.
    #: ``{"workspace": "<path>"}``  a workspace whose layout this gate accepts.
    roll_call: dict = field(default_factory=dict)

    #: ``read-only`` may be executed by a test; ``writes`` may not.
    side_effects: str = "read-only"

    #: Optional alias target ID if this entry is an alias for another gate.
    alias_of: str = ""

    @property
    def read_only(self) -> bool:
        return self.side_effects == "read-only"

    # -- resolution ------------------------------------------------------ #

    def resolved_entrypoint(self, repo_root: Path) -> Path:
        p = repo_root / self.entrypoint
        if p.is_file():
            return p.resolve()
        if self.entrypoint.startswith("exported_skills/_shared/"):
            alt = repo_root / self.entrypoint.replace("exported_skills/_shared/", "skills/_shared/", 1)
            if alt.is_file():
                return alt.resolve()
        if self.entrypoint.startswith("vendor/sdd-agent/0"):
            alt = repo_root / self.entrypoint.replace("vendor/sdd-agent/", "skills/", 1)
            if alt.is_file():
                return alt.resolve()
        return p.resolve()

    def exists(self, repo_root: Path) -> bool:
        return self.resolved_entrypoint(repo_root).is_file()

    # -- protocol -------------------------------------------------------- #

    def applies_to(self, ctx: GateContext) -> str | None:
        if not self.exists(ctx.repo_root):
            # Not a skip: an unresolvable entrypoint is the E-1 failure itself,
            # and the roll-call (specification) must fail on it rather than tolerate it.
            return None
        if self.scope == "workspace" and ctx.workspace is None:
            return "workspace-scoped gate invoked with no workspace"
        if self.scope == "catalog" and ctx.catalog is None and not _pack_installed(ctx.repo_root):
            # A catalogue gate checks a pack — its packages and authored SKILL.md
            # bodies. A core install has none; the generated catalogue is the
            # core's own output and carries no authored content to check.
            return "no skill pack installed: catalogue-scoped gates check an installed pack"
        fixtures = [str(v) for v in (self.roll_call.get("values") or {}).values()]
        if any(f.startswith(_PACK_DIRS) for f in fixtures) and not _pack_installed(ctx.repo_root):
            return "no skill pack installed: this gate's roll-call fixture is a pack package"
        return None

    def roll_call_context(self, ctx: GateContext) -> GateContext:
        """`ctx` adjusted by this gate's `roll_call` block.

        Fixture values live in the registry rather than in the test, so the
        roll-call has no per-gate special cases hidden in Python.
        """
        values = dict(self.roll_call.get("values") or {})
        workspace = self.roll_call.get("workspace")
        return GateContext(
            repo_root=ctx.repo_root,
            workspace=(ctx.repo_root / str(workspace)) if workspace else ctx.workspace,
            catalog=ctx.catalog,
            level=ctx.level,
            against=ctx.against,
            extra={**dict(ctx.extra), **{k: str(v) for k, v in values.items()}},
        )

    def build_argv(self, ctx: GateContext) -> list[str]:
        subs = ctx.substitutions()
        if self.scope == "catalog" and "catalog" not in subs:
            cat_dir = ctx.repo_root / "exported_skills" if (ctx.repo_root / "exported_skills").is_dir() else ctx.repo_root / "skills"
            subs["catalog"] = str(cat_dir)
        # Registry-declared fixture values fill placeholders a generic context has
        # no value for (`--fixture`, `--skill`, `--package`).
        for key, value in (self.roll_call.get("values") or {}).items():
            val_str = str(value)
            if not (ctx.repo_root / val_str).exists() and val_str.startswith("vendor/sdd-agent/0"):
                alt_val = val_str.replace("vendor/sdd-agent/", "skills/", 1)
                if (ctx.repo_root / alt_val).exists():
                    val_str = alt_val
            subs.setdefault(str(key), val_str)
        def fill(token: str) -> str:
            for key, value in subs.items():
                token = token.replace("{" + key + "}", value)
            return token

        def unfilled(token: str) -> bool:
            return "{" in token and "}" in token

        out = [sys.executable, str(self.resolved_entrypoint(ctx.repo_root))]
        tokens = list(self.argv)
        index = 0
        while index < len(tokens):
            token = tokens[index]
            nxt = tokens[index + 1] if index + 1 < len(tokens) else None
            # A flag and its value are one unit. Dropping the value but keeping
            # the flag is worse than dropping both: argparse then swallows the
            # NEXT argument as the flag's value and reports the wrong thing
            # missing. That mis-read accounted for 9 of the 24 argv failures on
            # the first roll-call.
            if token.startswith("-") and nxt is not None and unfilled(nxt):
                if unfilled(fill(nxt)):
                    index += 2
                    continue
            rendered = fill(token)
            if unfilled(rendered):
                # An unfilled placeholder is dropped rather than passed through
                # literally; passing `{workspace}` as a path is how a gate ends
                # up asserting against a directory that does not exist.
                index += 1
                continue
            out.append(rendered)
            index += 1
        # specification (W-15 harvest): `--against DIR` compares a catalog gate's coverage
        # against a materialized workspace. It is optional, so it is not in the
        # derived argv template — appended only when the user supplied it.
        if ctx.against is not None:
            out.append("--against")
            out.append(str(ctx.against))
        out.extend(self._curated_optional_flags(out))
        return out

    def _curated_optional_flags(self, argv: list[str]) -> list[str]:
        """Optional flags the registry has a value for, and the argv template lacks.

        `argv` is DERIVED from the script's own argparse usage line, and argparse
        prints an optional flag in brackets — so `[--phase {0..7}]` is stripped and
        never reaches the command. That is right for a flag nobody has a value for,
        and wrong for one the registry does: `check_phase_coverage.py` **requires**
        `--phase` whenever `--workspace` is given, so the derived argv could not run
        it at all (`PHASE-COV-CLI: --phase is required with --workspace`).

        The fix belongs here rather than in the derivation. `argv` is a derived
        field, so curating it by hand would fail `gate bootstrap --check` — and
        widening the derivation to keep every optional flag would pass flags nobody
        has values for. `roll_call.values` is already the curated place for "a value
        a generic context cannot supply"; this makes that value reach the command
        line even when the flag itself was optional.
        """
        extra: list[str] = []
        for key, value in sorted((self.roll_call.get("values") or {}).items()):
            flag = f"--{str(key).replace('_', '-')}"
            if flag in argv:
                continue
            # Only for a flag the script actually declares. A value that fills a
            # `{placeholder}` in the template has already been consumed above, and
            # inventing a flag the script does not accept turns a gate into an
            # argparse error.
            if flag not in (self.usage or ""):
                continue
            extra.extend([flag, str(value)])
        return extra

    def run(self, ctx: GateContext) -> GateResult:
        reason = self.applies_to(ctx)
        if reason is not None:
            return GateResult(gate_id=self.id, exit_code=0, skipped_reason=reason)

        target = self.resolved_entrypoint(ctx.repo_root)
        if not target.is_file():
            return GateResult(
                gate_id=self.id,
                exit_code=127,
                findings=[
                    Finding(
                        code="GATE-ENTRYPOINT-MISSING",
                        message=f"{self.entrypoint} does not resolve from {ctx.repo_root}",
                    )
                ],
            )

        executed = self._execute(self.build_argv(ctx), ctx)
        if isinstance(executed, GateResult):
            return executed
        returncode, stdout, stderr = executed
        scanned, unit, witness, not_applicable = parse_denominator(stdout)
        if not_applicable and returncode == 0:
            # The script says its premise does not hold here. That is a recorded
            # outcome with a reason (Scorecard's `?`), not a PASS.
            return GateResult(
                gate_id=self.id, exit_code=0, stdout=stdout,
                stderr=stderr, skipped_reason=f"not applicable: {not_applicable}",
                scanned=scanned, unit=unit,
            )
        return GateResult(
            gate_id=self.id,
            exit_code=returncode,
            findings=parse_findings(stdout + "\n" + stderr),
            stdout=stdout,
            stderr=stderr,
            scanned=scanned,
            unit=unit,
            witness=witness,
            rules=parse_rule_denominators(stdout),
        )

    def _execute(self, argv: list[str], ctx: GateContext) -> tuple[int, str, str] | GateResult:
        """`(exit code, stdout, stderr)` of the script, or a result when it could not finish."""
        try:
            proc = subprocess.run(
                argv,
                capture_output=True,
                # BOTH halves of the pipe are pinned to UTF-8, and both are needed.
                #
                # `encoding=` fixes the PARENT: without it `text=True` decodes with
                # `locale.getpreferredencoding()`, which is cp1252 on a default
                # Windows install. Two gates print `→` and `·` in their summary
                # lines, so reading them raised `UnicodeDecodeError: 0x9d` and the
                # gate read as a crash rather than as a verdict — a permanently red
                # pair that trains readers to ignore red.
                #
                # `PYTHONIOENCODING` fixes the CHILD: a gate writing `→` to a cp1252
                # stdout raises `UnicodeEncodeError` inside the gate, which would
                # turn a passing gate into a non-zero exit for a reason that has
                # nothing to do with what it checks.
                text=True, encoding="utf-8", errors="replace",
                env=_utf8_env(),
                timeout=self.timeout_s,
                cwd=str(ctx.repo_root),
            )
        except subprocess.TimeoutExpired:
            return GateResult(
                gate_id=self.id,
                exit_code=124,
                findings=[
                    Finding(code="GATE-TIMEOUT", message=f"exceeded {self.timeout_s}s")
                ],
            )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
