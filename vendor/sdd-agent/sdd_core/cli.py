from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path
import sys

from . import __version__
from .adapters.framework import FrameworkAdapter
from .changes import export_snapshot, propose, reconcile
from .engine import Engine
from .evaluation import evaluate
from .freshness import freshness, observe
from .model import SddError, Status, utc_now
from .parsing import parse_json
from .policy import record_decision
from .projections import derive
from .reporting import report
from .skills import start_task, finish_task
from .workspace import capture


def parser():
    parser = argparse.ArgumentParser(prog="sdd", description="Revision-bound spec lifecycle and regression")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ["status", "reconcile", "check", "review", "regression", "freshness", "accept", "recover", "export", "changes", "decision", "observe", "task", "init", "doctor", "derive", "eval", "report", "plan-waves"]:
        command = commands.add_parser(name)
        if name == "changes":
            command.add_argument("action", choices=["inspect", "propose"])
        if name == "decision":
            command.add_argument("action", choices=["record"])
        if name == "task":
            command.add_argument("action", choices=["start", "finish"])
        command.add_argument("workspace", type=Path)
        command.add_argument("--json", action="store_true", help="Output is machine-readable JSON in all modes")
        command.add_argument("--out", type=Path, help="Write UTF-8 JSON output (without BOM) to file")
        if name in {"check", "review", "regression", "accept", "decision", "export", "status", "report", "observe"}:
            command.add_argument("--change")
        if name in {"check", "regression", "status"}:
            command.add_argument("--allow-live-read", action="store_true", help="Use single-pass live read for non-acceptance preview checks")
        if name in {"check", "regression"}:
            command.add_argument("--compare-incremental", action="store_true")
            command.add_argument("--full", action="store_true")
            command.add_argument("--mode", choices=["deterministic", "readiness"], default="deterministic" if name == "check" else "readiness")
            command.add_argument("--against", choices=["accepted"], default="accepted")
        if name == "review":
            command.add_argument("--force", action="store_true")
            command.add_argument("--provider", choices=["configured"], default="configured")
        if name in {"accept", "changes"}:
            command.add_argument("--expect-snapshot")
            command.add_argument("--operation-id")
        if name in {"changes", "decision"}:
            command.add_argument("--file", type=Path)
        if name == "changes":
            command.add_argument("--id")
            command.add_argument("--skill")
            command.add_argument("--base-change", help="Extend a candidate sharing this live origin and accepted baseline")
        if name == "export":
            command.add_argument("--to", type=Path, required=True)
            command.add_argument("--candidate", action="store_true", help="Export a draft; it is not a readiness certificate")
        if name in {"freshness", "observe"}:
            command.add_argument("--due", action="store_true")
        if name == "observe":
            command.add_argument("--source", required=True)
        if name in {"init"}:
            command.add_argument("--workspace-id", required=True)
            command.add_argument("--reviewer", required=True)
            command.add_argument("--profile", choices=["seed", "minimal", "standard", "maximal", "portfolio"])
            command.add_argument("--preset", choices=["solo-author", "governed-team"])
            command.add_argument("--allow-existing-sources", action="store_true")
        if name == "reconcile":
            command.add_argument("--base", choices=["accepted"], default="accepted")
            command.add_argument("--dry-run", action="store_true")
        if name == "task":
            command.add_argument("--skill")
            command.add_argument("--capability", choices=["author", "review"], default="author")
            command.add_argument("--id")
        if name == "doctor":
            command.add_argument("--framework-root", type=Path)
        if name == "plan-waves":
            command.add_argument("--batch-size", type=int, default=4)
            command.add_argument("--waves-dir", type=Path)
        if name == "derive":
            command.add_argument("--artifact", required=True)
            command.add_argument("--operation-id")
            command.add_argument("--skill")
        if name == "eval":
            command.add_argument("--corpus", type=Path, required=True)
            command.add_argument("--responses", type=Path)
            command.add_argument("--stage-labels", action="store_true")
            command.add_argument("--live", action="store_true")
            command.add_argument("--to", type=Path)
            command.add_argument("--operation-id")
    return parser


def execute(args, engine_factory=Engine):
    name = args.command
    if name == "init":
        from .bootstrap import initialize
        return initialize(
            args.workspace,
            args.workspace_id,
            args.reviewer,
            profile=getattr(args, "profile", None),
            preset=getattr(args, "preset", None),
            allow_existing_sources=bool(getattr(args, "allow_existing_sources", False)),
        )
    if name == "plan-waves":
        from architect_framework.sdd_bridge.authoring_qa import plan_waves
        return plan_waves(args.workspace, batch_size=getattr(args, "batch_size", 4), out_dir=getattr(args, "waves_dir", None))
    if engine_factory is Engine:
        try:
            from architect_framework.sdd_bridge import engine_for
            engine = engine_for(args.workspace)
        except ImportError:
            engine = engine_factory(args.workspace)
    else:
        engine = engine_factory(args.workspace)
    store = engine.store
    if name == "doctor":
        result = {"status": "PASS", "engine_version": __version__, "python": sys.version.split()[0],
                  "dependencies": {p: importlib.metadata.version(p) for p in ["PyYAML", "markdown-it-py", "jsonschema", "httpx"]},
                  "filesystem_support": "local POSIX/Windows locking; network filesystems are not certified"}
        if args.framework_root:
            result["framework"] = FrameworkAdapter(args.framework_root).capabilities()
            result["status"] = result["framework"]["status"]
        return result
    if name == "reconcile":
        if args.dry_run:
            snapshot = capture(args.workspace)
            baseline = store.baseline()
            from .workspace import diff
            return {"status": "PASS", "snapshot_digest": snapshot.digest, "diff": diff(store.load_snapshot(baseline["snapshot_digest"]) if baseline else None, snapshot)}
        return reconcile(store, args.workspace)
    if name in {"check", "regression"}:
        if getattr(args, "allow_live_read", False) and not args.change and args.mode == "deterministic":
            from .validation import check_snapshot
            snap = capture(args.workspace, allow_live_read=True)
            baseline = store.baseline()
            before = store.load_snapshot(baseline["snapshot_digest"]) if baseline else None
            return check_snapshot(snap, before, store.history(), args.compare_incremental or args.full).to_dict()
        return (engine.readiness(args.change) if args.mode == "readiness" else engine.check(args.change, args.compare_incremental or args.full)).to_dict()
    if name == "status":
        baseline = store.baseline()
        result = engine.readiness(args.change).to_dict()
        return {**result, "baseline": baseline, "baseline_is_historical": True}
    if name == "report":
        return report(engine, args.change)
    if name == "review":
        return engine.review(args.change, force=args.force)
    if name == "accept":
        if not args.change or not args.expect_snapshot:
            raise SddError("INVOCATION_ERROR", "accept requires --change and --expect-snapshot")
        return engine.accept(args.change, args.expect_snapshot, args.operation_id)
    if name == "recover":
        return engine.recover()
    if name == "changes":
        if args.action == "inspect":
            change = store.read("changes", args.id) if args.id else None
            if change is None:
                raise SddError("CHANGE_UNKNOWN", "Supply --id with an existing change")
            return change
        if not args.file:
            raise SddError("INVOCATION_ERROR", "propose requires --file with a JSON operation array")
        return propose(store, args.workspace, parse_json(args.file.read_text(encoding="utf-8")), args.operation_id, args.skill, args.expect_snapshot, args.base_change)
    if name == "decision":
        if not args.file:
            raise SddError("INVOCATION_ERROR", "decision record requires --file")
        change, snapshot, before = engine.context(args.change)
        return record_decision(store, snapshot, parse_json(args.file.read_text(encoding="utf-8")), before, base_acceptance=change["base_acceptance"])
    if name == "freshness":
        snapshot = capture(args.workspace)
        findings, details = freshness(store, snapshot)
        return {"status": "INCOMPLETE" if findings else "PASS", "sources": details, "findings": [f.to_dict() for f in findings]}
    if name == "observe":
        snapshot = engine.context(args.change)[1] if args.change else capture(args.workspace)
        source = next((s for s in snapshot.config.get("external_sources", []) if s["id"] == args.source), None)
        if source is None:
            raise SddError("SOURCE_UNKNOWN", args.source)
        return observe(store, source)
    if name == "task":
        if args.action == "start":
            if not args.skill:
                raise SddError("INVOCATION_ERROR", "task start requires --skill")
            return start_task(store, args.workspace, args.skill, args.capability)
        if not args.id:
            raise SddError("INVOCATION_ERROR", "task finish requires --id")
        return finish_task(store, args.workspace, args.id)
    if name == "derive":
        return derive(store, args.workspace, args.artifact, args.operation_id, args.skill)
    if name == "eval":
        if args.stage_labels:
            if args.live or args.responses:
                raise SddError("EVAL_MODE_INVALID", "Label staging starts no provider calls")
            from .label_review import stage
            return stage(store, parse_json(args.corpus.read_text(encoding="utf-8")))
        snapshot = capture(args.workspace)
        provider_cfg = resolve_provider_config(snapshot.config.get("provider"), args.workspace)
        return evaluate(store, provider_cfg, parse_json(args.corpus.read_text(encoding="utf-8")), args.to,
                        args.live, parse_json(args.responses.read_text(encoding="utf-8")) if args.responses else None, operation_id=args.operation_id)
    if name == "export":
        destination = args.to.resolve()
        if destination.is_relative_to(engine.workspace) and not destination.is_relative_to(engine.workspace / ".sdd" / "exports"):
            raise SddError("EXPORT_WITHIN_INVENTORY", "Export outside the spec workspace or into .sdd/exports; output must not enter its own inventory")
        if args.candidate:
            _, snapshot, _ = engine.context(args.change)
        else:
            baseline = store.baseline()
            if baseline is None:
                raise SddError("BASELINE_MISSING", "Accept a snapshot before an official export")
            snapshot = store.load_snapshot(baseline["snapshot_digest"])
            readiness = engine.baseline_readiness()
            if readiness.status != Status.PASS:
                raise SddError("EXPORT_NOT_READY", json.dumps(readiness.to_dict(), ensure_ascii=False), readiness.status)
            live = capture(args.workspace)
            origin = store.load_snapshot(store.read("changes", readiness.details["change_id"])["origin_snapshot"])
            if any(live.config.get(k) not in (snapshot.config.get(k), origin.config.get(k)) for k in ("policy", "provider")):
                raise SddError("EXPORT_POLICY_STALE", "Reconcile policy/provider changes before official export", Status.STALE)
        result = export_snapshot(snapshot, args.to, None if args.candidate else store, None if args.candidate else baseline)
        return result | {"export_kind": "DRAFT" if args.candidate else "ACCEPTED", "baseline_is_historical": not args.candidate}
    raise SddError("INVOCATION_ERROR", name)


def _write_out(out_path: Path | None, payload: dict) -> None:
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def main(argv=None, engine_factory=Engine):
    args = parser().parse_args(argv)
    out_path = getattr(args, "out", None)
    try:
        result = execute(args, engine_factory=engine_factory)
        _write_out(out_path, result)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        status = result.get("status", result.get("verdict", "PASS"))
        if status in {"PASS", "COMPLETE", "ACCEPTED", "ACCEPTED_WITH_RISK", "planned", "discovered", "ALREADY_MIGRATED", "OBSERVED", "STAGED"}:
            return 0
        return 1 if status == "FAIL" else 3
    except SddError as exc:
        err_dict = exc.to_dict()
        _write_out(out_path, err_dict)
        print(json.dumps(err_dict, ensure_ascii=False, indent=2))
        return 2 if exc.code in {"INVOCATION_ERROR", "SCHEMA_INVALID", "WORKSPACE_NOT_INITIALIZED"} else 1 if exc.status == Status.FAIL else 3
    except (OSError, KeyError, TypeError, ValueError) as exc:
        err_dict = {"status": "ERROR", "code": "INPUT_OR_IO_ERROR", "message": str(exc)}
        _write_out(out_path, err_dict)
        print(json.dumps(err_dict, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
