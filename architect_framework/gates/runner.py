"""specification / W-24 — run gates by ID: one report, one exit code.

This is the only place that decides "did the gates pass". Before it, each caller
built its own list of script paths and its own idea of what a non-zero exit meant
— `run_sdd_phase.py --postflight` held twenty such paths inline, one of which
(`scripts/check_checklist.py`) does not resolve under `vendor/sdd-agent/` at all,
so that check had never run.

Two rules the report obeys, both from the failure that started this work:

  * **The exit code of every gate is printed.** W-12 makes a checklist row carry
    the recorded exit code, and a report that prints only PASS/FAIL gives the row
    nothing true to quote.
  * **A skip is printed as a skip, with its reason.** Silence and "nothing to
    check here" must not look the same.
"""

from __future__ import annotations

import json
from pathlib import Path

from architect_framework import contracts, skillpacks
from architect_framework.gates import registry
from architect_framework.gates.base import Finding, Gate, GateContext, GateResult
from architect_framework.gates.subprocess_gate import SubprocessGate

REPO_ROOT = contracts.REPO_ROOT


def select_gates(
    *,
    gate_id: str | None = None,
    run_all: bool = False,
    include_writers: bool = False,
    scope: str | None = None,
    stage: str | None = None,
) -> list[Gate]:
    """The gates a run executes.

    specification: `scope` selects by the registry's `scope` field, alone or narrowed by
    `phase`. `gate run --scope workspace <ws>` replaces the vendored aggregate
    script that kept its own hard-coded list of workspace checks — the registry
    is the one list, so a new workspace gate is in the run by being registered.
    """
    if gate_id:
        return [registry.get(gate_id)]
    if stage is not None:
        # specification: a `stage: ci` gate checks the repository or the catalogue; CI runs it.
        chosen = registry.select(stage=stage)
    elif scope is not None:
        chosen = registry.select(scope=scope)
    elif run_all:
        chosen = list(registry.all_gates())
    else:
        raise ValueError("name a gate ID, or pass --scope S, --stage ci or --all")
    if include_writers:
        return chosen
    keep = {g.id for g in registry.read_only()}
    return [g for g in chosen if g.id in keep]


def build_context(workspace: str | None, catalog: str | None = None,
                  against: str | None = None) -> GateContext:
    return GateContext(
        repo_root=REPO_ROOT,
        workspace=Path(workspace).resolve() if workspace else None,
        catalog=Path(catalog).resolve() if catalog else skillpacks.installed_catalogue(),
        against=Path(against).resolve() if against else None,
    )


def run_gates(gates: list[Gate], ctx: GateContext) -> list[GateResult]:
    if ctx.workspace is not None:
        from architect_framework.sdd_bridge.mode import classify
        if classify(ctx.workspace)["state"] == "current":
            skillpacks.activate(ctx.workspace)
    return [run_one(gate, ctx) for gate in gates]


def run_one(gate: Gate, ctx: GateContext) -> GateResult:
    if ctx.workspace is not None:
        from architect_framework.sdd_bridge.mode import classify
        state = classify(ctx.workspace)
        if state["state"] != "current":
            return GateResult(gate.id, 3, findings=[Finding("CURRENT_WORKSPACE_REQUIRED", state["next_action"], "error")])
    return apply_denominator(apply_classes(gate.run(ctx), gate))


def apply_classes(result: GateResult, gate: Gate | None = None) -> GateResult:
    """specification / G-1: only `derived` and `contract` findings count toward the exit code.

    A subprocess gate that failed with nothing but `heuristic`/`style` findings
    passes; its findings stay in the report as notes. The flip is deliberately
    narrow, so a real failure cannot turn green by it:

      * only a ``subprocess`` gate. A native gate sets its exit code from its own
        findings under its own severity policy — the tier-2 judges route a
        heuristic code to a warning until calibration promotes it — so the runner
        does not second-guess it. A script's exit code is opaque; this is the
        one place the class can reach it;
      * at least one finding must be error-severity, so the non-zero exit is
        explained by what was parsed — a script that failed for a reason the
        parser did not read keeps its exit code;
      * every finding must be declared non-blocking. A code with no class counts
        (:func:`registry.is_blocking`), and so does every code the runner raises.
    """
    if gate is not None and not isinstance(gate, SubprocessGate):
        return result
    if result.skipped or result.exit_code == 0 or not result.findings:
        return result
    if not any(f.severity == "error" for f in result.findings):
        return result
    if any(registry.is_blocking(result.gate_id, f.code) for f in result.findings):
        return result
    result.exit_code = 0
    return result


#: Exit code of a gate that applied, exited 0, and examined nothing.
VACUOUS_EXIT = 3


def apply_denominator(result: GateResult) -> GateResult:
    """W-35 / GT-1: a PASS over zero units is not a PASS.

    Beer et al. call it *antecedent failure*: `files scanned: 0 → exit 0` is true
    of every workspace the gate cannot see, so it says nothing about this one.
    The result keeps its findings and gains `GATE-VACUOUS`; its exit code becomes
    non-zero so the run fails for the reason it should.

    A gate that has not reported a denominator (`scanned is None`) is left as is:
    it prints `scanned=?`, which is true, and `tests/test_gate_denominator.py`
    is the ratchet that keeps the phase-1 set from containing one.
    """
    if result.skipped or result.exit_code != 0:
        return result
    # Per rule: a gate total can be non-zero while one rule inside it read
    # nothing. A rule whose input is absent says so (`not-applicable[rule]`);
    # a rule that applied and read nothing is the same antecedent failure.
    empty_rules = sorted(r for r, d in (result.rules or {}).items() if d.get("scanned") == 0)
    if empty_rules and result.scanned != 0:
        result.vacuous = True
        result.exit_code = VACUOUS_EXIT
        result.findings.append(Finding(
            code="GATE-VACUOUS",
            message=f"rule(s) {', '.join(empty_rules)} applied and examined nothing; declare "
                    "`not-applicable[<rule>]: <reason>` if their input is absent",
        ))
        return result
    if result.scanned != 0:
        return result
    result.vacuous = True
    result.exit_code = VACUOUS_EXIT
    unit = result.unit or "units"
    result.findings.append(Finding(
        code="GATE-VACUOUS",
        message=f"exit 0 over 0 {unit}: the gate applied and examined nothing, so it "
                "cannot pass (SARIF kind notApplicable, level error)",
    ))
    return result


def render(results: list[GateResult]) -> str:
    lines: list[str] = []
    for result in results:
        lines.append(result.summary())
        if result.passed and result.witness:
            lines.append(f"    witness: {result.witness}")
        if result.rules:
            counted = [f"{r}={d['scanned']}" for r, d in sorted(result.rules.items()) if "scanned" in d]
            skipped = sorted(r for r, d in result.rules.items() if "not_applicable" in d)
            lines.append("    rules: " + " ".join(counted)
                         + (f" · n/a: {', '.join(skipped)}" if skipped else ""))
        if result.usage:
            lines.append("    judge: " + judge_line([result]))
        for finding in result.findings[:20]:
            note = "" if registry.is_blocking(result.gate_id, finding.code) else (
                f"  (note: {registry.code_meta(result.gate_id, finding.code).get('class')}, "
                "not counted)")
            lines.append(f"    {finding.render()}{note}")
        if len(result.findings) > 20:
            lines.append(f"    … {len(result.findings) - 20} more")
    ran = [r for r in results if not r.skipped]
    failed = [r for r in ran if not r.passed]
    skipped = [r for r in results if r.skipped]
    lines.append("")
    lines.append(
        f"gates: {len(results)} · ran {len(ran)} · passed {len(ran) - len(failed)} · "
        f"failed {len(failed)} · skipped {len(skipped)}"
        + (f" · vacuous {sum(1 for r in ran if r.vacuous)}" if any(r.vacuous for r in ran) else "")
    )
    if failed:
        lines.append("failed: " + ", ".join(f"{r.gate_id}(exit {r.exit_code})" for r in failed))
    if any(r.usage for r in results):
        lines.append("judge cost: " + judge_line(results))
    return "\n".join(lines)


def judge_line(results: list[GateResult]) -> str:
    """J-8: calls, tokens and cost of every tier-2 judge in `results`, summed."""
    used = [r.usage for r in results if r.usage]
    models = sorted({str(u.get("model")) for u in used})
    calls = sum(int(u.get("calls") or 0) for u in used)
    hits = sum(int(u.get("cache_hits") or 0) for u in used)
    tokens = sum(int(u.get("input_tokens") or 0) for u in used)
    billed = sum(int(u.get("billed_tokens") or 0) for u in used)
    costs = [u.get("cost_usd") for u in used]
    cost = ("unpriced" if any(c is None for c in costs)
            else f"${sum(float(c) for c in costs):.6f}")
    return (f"{', '.join(models)} · {calls} calls ({hits} cached) · {tokens} input tokens "
            f"({billed} billed) · {cost}")


def as_json(results: list[GateResult]) -> str:
    return json.dumps(
        [
            {
                "gate": r.gate_id,
                "exit_code": r.exit_code,
                "passed": r.passed,
                "skipped": r.skipped,
                "skipped_reason": r.skipped_reason,
                "errors": r.errors,
                "warnings": r.warnings,
                "kind": r.sarif_kind,
                "level": "error" if r.vacuous else ("none" if r.skipped else None),
                "scanned": r.scanned,
                "unit": r.unit,
                "witness": r.witness,
                "rules": r.rules,
                **({"usage": r.usage} if r.usage else {}),
                "findings": [
                    {"code": f.code, "severity": f.severity, "path": f.path, "line": f.line,
                     "message": f.message,
                     **({"counted": False} if not registry.is_blocking(r.gate_id, f.code) else {})}
                    for f in r.findings
                ],
            }
            for r in results
        ],
        indent=2,
    )


#: The warning ratchet, ESLint `--max-warnings` per (gate, code): a warning that
#: never fails the run is a warning nobody reads, and one that always fails it
#: punishes phase 1 for being phase 1. The count may stay or fall; it may not rise.
BASELINE = "gate-baseline.yml"


def warning_counts(results: list[GateResult]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for r in results:
        for f in r.findings:
            if f.severity == "warning":
                counts.setdefault(r.gate_id, {})
                counts[r.gate_id][f.code] = counts[r.gate_id].get(f.code, 0) + 1
    return counts


def apply_ratchet(results: list[GateResult], workspace: str | None) -> list[GateResult]:
    """Fail a gate whose warnings of some code outnumber the workspace baseline."""
    if not workspace:
        return results
    path = Path(workspace) / BASELINE
    if not path.is_file():
        return results
    import yaml

    baseline = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("warnings") or {}
    now = warning_counts(results)
    for r in results:
        if r.skipped or r.gate_id not in baseline:
            continue
        allowed = baseline[r.gate_id] or {}
        grew = {c: n for c, n in now.get(r.gate_id, {}).items() if n > int(allowed.get(c, 0))}
        if grew:
            r.findings.append(Finding(
                code="GATE-RATCHET",
                message="warnings rose above the baseline: " + ", ".join(
                    f"{c} {allowed.get(c, 0)}→{n}" for c, n in sorted(grew.items())),
            ))
            r.exit_code = r.exit_code or 1
    return results


def write_baseline(results: list[GateResult], workspace: str) -> Path:
    import yaml

    path = Path(workspace) / BASELINE
    body = {"kind": "gate-baseline", "warnings": warning_counts(results)}
    path.write_text(yaml.safe_dump(body, sort_keys=True), encoding="utf-8", newline="\n")
    return path


RUN_LOG_SCHEMA = "gate-run-log/1"


def write_run_log(results: list[GateResult], path: Path, *, workspace: str | None) -> str:
    """W-40 / G-4: the verdict is recorded by the runner, not typed by the author.

    The log is canonical JSON (sorted keys, fixed separators) so its sha256 is a
    stable citation: a closing report quotes `run-log: <path> sha256:<hex>`, and
    :func:`verify_run_log` recomputes it. A report that cites a hash nobody can
    reproduce — or a gate the registry does not know — cites nothing.
    """
    import datetime
    import hashlib
    import sys

    record = {
        "schema": RUN_LOG_SCHEMA,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "argv": sys.argv,
        "workspace": str(Path(workspace).resolve()) if workspace else None,
        "exit_code": exit_code_for(results),
        "results": json.loads(as_json(results)),
    }
    if any(r.usage for r in results):
        # J-8: model, version, answers, tokens and cost are part of the verdict.
        record["judge"] = judge_line(results)
    data = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def verify_run_log(path: Path, sha256: str) -> list[str]:
    """Problems with a cited run log; an empty list means the citation holds."""
    import hashlib

    if not path.is_file():
        return [f"{path} does not exist"]
    data = path.read_bytes()
    problems = []
    actual = hashlib.sha256(data).hexdigest()
    if actual != sha256.removeprefix("sha256:"):
        problems.append(f"sha256 mismatch: cited {sha256}, file is {actual}")
    try:
        record = json.loads(data)
    except ValueError:
        return problems + ["not a JSON run log"]
    if record.get("schema") != RUN_LOG_SCHEMA:
        problems.append(f"schema is {record.get('schema')!r}, not {RUN_LOG_SCHEMA!r}")
    known = set(registry.ids())
    for row in record.get("results") or []:
        if row.get("gate") not in known:
            problems.append(f"{row.get('gate')} is not a registered gate")
    return problems


def exit_code_for(results: list[GateResult]) -> int:
    """Non-zero when any gate that actually ran did not pass.

    A skip does not fail the run — it is a recorded outcome. A gate that failed to
    *start* does: `SubprocessGate` returns 127 with `GATE-ENTRYPOINT-MISSING`
    rather than skipping, so an unresolvable ID cannot pass by omission.
    """
    return 0 if any(not r.skipped for r in results) and all(r.passed or r.skipped for r in results) else 1


def run_selection(
    *,
    gate_id: str | None = None,
    workspace: str | None = None,
    run_all: bool = False,
    catalog: str | None = None,
    as_json_output: bool = False,
    include_writers: bool = False,
    against: str | None = None,
    log: str | None = None,
    update_baseline: bool = False,
    scope: str | None = None,
    stage: str | None = None,
    **legacy,
) -> int:
    if "as_json" in legacy:
        as_json_output = bool(legacy["as_json"])
    if update_baseline:
        print("Legacy warning baselines are retired. Use core signed acceptance.")
        return 3
    try:
        gates = select_gates(
            gate_id=gate_id, run_all=run_all, include_writers=include_writers,
            scope=scope, stage=stage,
        )
    except (ValueError, registry.RegistryError) as exc:
        print(str(exc))
        return 2
    if not gates:
        target = " and ".join(
            part for part in (f"scope {scope}" if scope else "",
                              f"stage {stage}" if stage else "") if part
        ) or "the selection"
        print(f"no gates registered for {target}")
        return 2

    results = run_gates(gates, build_context(workspace, catalog, against))
    if update_baseline and workspace:
        print(f"baseline: {write_baseline(results, workspace)}")
    results = apply_ratchet(results, workspace)
    print(as_json(results) if as_json_output else render(results))
    if log:
        digest = write_run_log(results, Path(log), workspace=workspace)
        print(f"run-log: {log} sha256:{digest}")
    return exit_code_for(results)
