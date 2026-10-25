"""Gates — a gate is an ID in `contracts/gates.yml`, never a path on disk.

Plan section 5c decision D-3. See :mod:`architect_framework.gates.base` for why.
"""

from architect_framework.gates.base import (
    SEVERITIES,
    Finding,
    Gate,
    GateContext,
    GateResult,
)
from architect_framework.gates.subprocess_gate import SubprocessGate, parse_findings

__all__ = [
    "SEVERITIES",
    "Finding",
    "Gate",
    "GateContext",
    "GateResult",
    "SubprocessGate",
    "parse_findings",
]
