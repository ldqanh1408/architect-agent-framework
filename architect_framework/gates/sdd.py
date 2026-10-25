"""Translate current core checks into release gate results.

Missing setup, missing dependencies, and malformed markers are incomplete or errors.
They never authorize another workflow or turn a skipped check into success.
"""

from __future__ import annotations

from pathlib import Path

from architect_framework import sdd_bridge
from architect_framework.gates.base import Finding, GateContext, GateResult


class _SddGate:
    id = ""
    prefix = ""
    action = staticmethod(lambda workspace: {})

    def applies_to(self, ctx: GateContext) -> str | None:
        return None

    def run(self, ctx: GateContext) -> GateResult:
        if ctx.workspace is None:
            return GateResult(gate_id=self.id, exit_code=3,
                              findings=[Finding("CURRENT_WORKSPACE_REQUIRED", "Select a current workspace")])
        workspace = Path(str(ctx.workspace))
        answer = type(self).action(workspace)
        status = answer["status"]
        findings: list[Finding] = []
        if status == "UNAVAILABLE":
            findings.append(Finding("SDD-ENGINE-UNAVAILABLE", answer["hint"]))
        elif status not in {"PASS"}:
            findings.append(Finding(f"{self.prefix}-{'FAIL' if status == 'FAIL' else 'INCOMPLETE'}",
                                    answer["hint"] or f"the engine answered {status}"))
        for row in (answer.get("result") or {}).get("findings", []) if isinstance(answer.get("result"), dict) else []:
            if isinstance(row, dict):
                findings.append(Finding(f"{self.prefix}-FINDING", f"{row.get('code', '')}: {row.get('message', '')}".strip(": "),
                                        "error" if row.get("severity", "error") in {"error", "blocking", "blocker"} else "warning"))
        return GateResult(gate_id=self.id, exit_code=answer["exit_code"], findings=findings,
                          stdout=f"{self.id}: {status}", scanned=(answer.get("result") or {}).get("scanned"), unit="obligations/artifacts")


class SddCheckGate(_SddGate):
    id = "GATE-SDD-CHECK"
    prefix = "SDD-CHECK"
    action = staticmethod(sdd_bridge.check)


class SddRegressionGate(_SddGate):
    id = "GATE-SDD-REGRESSION"
    prefix = "SDD-REGRESSION"
    action = staticmethod(sdd_bridge.regression)
