"""specification / W-22 — what a gate is.

A gate is an **ID in a registry**, not a path on disk. That is decision D-3
(plan section 5c), and it exists because a gate's identity was previously a string typed
by hand into markdown: 16 of 45 argv cited across `docs/` and the workspaces did
not resolve, and four of the unresolvable ones were cited as the evidence that
closed Phase 0.

Two kinds implement one protocol:

  ``native``      runs in this process. Either a class in this package
                  (``module:Class``; the six programs the plan adds are native
                  from birth), or — specification — a script entrypoint (``*.py``) whose
                  ``main()`` `inprocess.InProcessGate` calls here with the argv,
                  cwd and parsers the child process had.
  ``subprocess``  a script in an interpreter of its own. Since specification only a
                  ``role: tool`` entry is derived this way; ``gate list --kind
                  subprocess`` started at 92 and reached 0 gates on 2026-10-03.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Protocol, runtime_checkable

#: Severities a finding may carry. `error` fails the gate; `warning` does not.
SEVERITIES = ("error", "warning", "info")


@dataclass(frozen=True)
class Finding:
    """One thing a gate observed.

    `code` is stable and greppable (`TREE-specification`, `SUBTREE-THIN`), because a
    checklist row and a `gate explain` lookup both key on it.
    """

    code: str
    message: str
    severity: str = "error"
    path: str | None = None
    line: int | None = None

    def __post_init__(self) -> None:
        if self.severity not in SEVERITIES:
            raise ValueError(f"severity must be one of {SEVERITIES}, got {self.severity!r}")

    def render(self) -> str:
        where = f" {self.path}" + (f":{self.line}" if self.line else "") if self.path else ""
        return f"[{self.severity.upper()}] {self.code}{where}: {self.message}"


@dataclass
class GateContext:
    """Everything a gate is allowed to know about the run.

    A gate reads contracts through :mod:`architect_framework.contracts` (R-3) and
    everything else from here. Nothing else is in scope — a gate that needs a
    fact absent from this object is asking for a fact nobody has decided who
    owns.
    """

    repo_root: Path
    workspace: Path | None = None
    catalog: Path | None = None
    level: str | None = None
    against: Path | None = None
    extra: Mapping[str, Any] = field(default_factory=dict)

    def substitutions(self) -> dict[str, str]:
        """Values available to a subprocess gate's `argv` template."""
        out = {"repo_root": str(self.repo_root)}
        if self.workspace is not None:
            out["workspace"] = str(self.workspace)
        if self.catalog is not None:
            out["catalog"] = str(self.catalog)
        if self.level:
            out["level"] = self.level
        if self.against is not None:
            out["against"] = str(self.against)
        out.update({str(k): str(v) for k, v in self.extra.items()})
        return out


@dataclass
class GateResult:
    """The outcome, with the exit code kept rather than collapsed to a bool.

    W-12 makes a checklist row require the recorded exit code. Discarding it here
    and re-deriving it from `errors` would let a gate that crashed look like a
    gate that found nothing — the shape of the failure that started this work.
    """

    gate_id: str
    exit_code: int
    findings: list[Finding] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    skipped_reason: str | None = None

    #: W-35 / GT-1. How many units (pages, clauses, modules, rules) the gate
    #: actually examined. ``None`` means the gate has not reported one yet, which
    #: the report prints as ``scanned=?`` rather than letting it read as a count.
    #: ``0`` on an exit-0 run is vacuity: the runner turns it into ``VACUOUS``.
    scanned: int | None = None
    #: What ``scanned`` counts, e.g. ``pages`` or ``clauses``.
    unit: str = ""
    #: Beer et al.'s *interesting witness*: one unit that was really graded,
    #: with the figure nearest the threshold, so a PASS shows it was exercised.
    witness: str | None = None
    #: Set by the runner when an exit-0 run examined nothing.
    vacuous: bool = False
    #: Per-rule denominators: ``{rule: {"scanned": n, "unit": u}}`` or
    #: ``{rule: {"not_applicable": reason}}``. Empty when the gate reports none.
    rules: dict = field(default_factory=dict)
    #: A tier-2 gate's judge meter (J-8): model, version, calls, input tokens,
    #: cost and every answer. Empty for a gate that asked no model.
    usage: dict = field(default_factory=dict)

    @property
    def errors(self) -> int:
        return sum(1 for f in self.findings if f.severity == "error")

    @property
    def warnings(self) -> int:
        return sum(1 for f in self.findings if f.severity == "warning")

    @property
    def passed(self) -> bool:
        return self.skipped_reason is None and self.exit_code == 0

    @property
    def skipped(self) -> bool:
        return self.skipped_reason is not None

    def summary(self) -> str:
        if self.skipped:
            return f"{self.gate_id}: SKIPPED ({self.skipped_reason})"
        verdict = "VACUOUS" if self.vacuous else ("PASS" if self.passed else "FAIL")
        scanned = "?" if self.scanned is None else str(self.scanned)
        return (
            f"{self.gate_id}: {verdict} exit={self.exit_code} "
            f"errors={self.errors} warnings={self.warnings} scanned={scanned}"
        )

    @property
    def sarif_kind(self) -> str:
        """SARIF 2.1.0 ``result.kind``: a skip and an empty run are ``notApplicable``.

        Two different outcomes share that kind and differ by ``level``: a gate that
        declared itself inapplicable is ``none`` (a recorded outcome), a gate that
        applied and examined nothing is ``error`` (vacuity, GT-1).
        """
        if self.skipped or self.vacuous:
            return "notApplicable"
        return "pass" if self.passed else "fail"


def roll_call_context(gate: Any, ctx: GateContext) -> GateContext:
    """`ctx` adjusted by a gate's registry-declared `roll_call` block.

    Shared by every kind of gate. `SubprocessGate` has its own copy for the argv
    substitution it also needs; native gates get this one bound onto them by the
    registry, so a new native gate cannot forget to support the roll-call — the
    first one (`GATE-SEAM-LEDGER`) did, and the roll-call failed on it with an
    `AttributeError` rather than a finding.
    """
    block = getattr(gate, "roll_call", {}) or {}
    values = dict(block.get("values") or {})
    workspace = block.get("workspace")
    return GateContext(
        repo_root=ctx.repo_root,
        workspace=(ctx.repo_root / str(workspace)) if workspace else ctx.workspace,
        catalog=ctx.catalog,
        level=ctx.level,
        against=ctx.against,
        extra={**dict(ctx.extra), **{str(k): str(v) for k, v in values.items()}},
    )


@runtime_checkable
class Gate(Protocol):
    """The whole interface. Three members, so a native gate is cheap to write."""

    id: str

    def applies_to(self, ctx: GateContext) -> str | None:
        """Return ``None`` to run, or a reason string to skip.

        A skip is a recorded outcome, not silence — the same rule the seam ledger
        applies to an unmet slot.
        """

    def run(self, ctx: GateContext) -> GateResult:
        ...
