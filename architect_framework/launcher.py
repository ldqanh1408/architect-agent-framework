"""Canonical launcher for installed runtimes and thin plugin wrappers."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys


def _load_dotenv_if_present() -> None:
    """Auto-load .env credentials (JEV_KEY / JEV_API_KEY / SDD_JUDGE_API_KEY) without overwriting explicit env vars (WO-R3.1)."""
    candidates = [
        Path.cwd() / ".env",
        Path(os.environ.get("ARCHITECT_STATE_HOME") or os.environ.get("ARCHITECT_HOME") or (Path.home() / ".architect-framework")) / ".env",
    ]
    for env_file in candidates:
        try:
            if not env_file.is_file():
                continue
            for raw_line in env_file.read_text(encoding="utf-8", errors="replace").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k and v and k not in os.environ:
                    os.environ[k] = v
        except OSError:
            continue
    # Map JEV_KEY -> JEV_API_KEY if user set JEV_KEY in .env
    if not os.environ.get("JEV_API_KEY") and os.environ.get("JEV_KEY"):
        os.environ["JEV_API_KEY"] = os.environ["JEV_KEY"]
    if not os.environ.get("SDD_JUDGE_API_KEY") and os.environ.get("CLAUDE_PLUGIN_OPTION_JUDGE_API_KEY"):
        os.environ["SDD_JUDGE_API_KEY"] = os.environ["CLAUDE_PLUGIN_OPTION_JUDGE_API_KEY"]
    if not os.environ.get("JEV_API_KEY") and os.environ.get("CLAUDE_PLUGIN_OPTION_JUDGE_API_KEY"):
        os.environ["JEV_API_KEY"] = os.environ["CLAUDE_PLUGIN_OPTION_JUDGE_API_KEY"]


def _write_out_utf8(out_path: Path | None, payload: dict) -> None:
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    _load_dotenv_if_present()
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    try:
        if argv[:1] == ["--version"]:
            from architect_framework import __version__
            print(__version__)
            return 0
        if argv[:1] == ["probe"]:
            import yaml  # noqa: F401
            import pydantic  # noqa: F401
            if argv[1:2] != ["hook"]:
                import cryptography  # noqa: F401
                import sdd_core.engine  # noqa: F401
            return 0
        if argv[:1] == ["hook"]:
            from architect_framework.runtime.hook import main as hook_main
            code, output = hook_main(sys.stdin.read())
            if output:
                print(output)
            return code
        if argv[:1] == ["cli"]:
            from architect_framework.cli.main import main as cli_main
            sys.argv = ["architect-cli", *argv[1:]]
            try:
                return cli_main() or 0
            except SystemExit as exc:
                return exc.code if isinstance(exc.code, int) else 1
        if argv[:1] == ["decision"]:
            return _error(argv, "The old decision writer is retired. Inspect and sign current decisions in the review console.")
        if argv[:2] == ["sdd", "scaffold-plan"]:
            from architect_framework.sdd_bridge.scaffolder import scaffold_maximal_plan
            parser = argparse.ArgumentParser(prog="architect-runtime sdd scaffold-plan", allow_abbrev=False)
            parser.add_argument("--harvest", type=Path, required=True)
            parser.add_argument("--profile", choices=["seed", "minimal", "standard", "maximal", "portfolio"], default="maximal")
            parser.add_argument("--out", type=Path)
            args = parser.parse_args(argv[2:])
            data = json.loads(args.harvest.read_text(encoding="utf-8"))
            res = scaffold_maximal_plan(data, profile=args.profile)
            _write_out_utf8(args.out, res)
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0
        if argv[:2] == ["sdd", "extract-sources"]:
            from architect_framework.sdd_bridge.scaffolder import extract_sources_to_harvest
            parser = argparse.ArgumentParser(prog="architect-runtime sdd extract-sources", allow_abbrev=False)
            parser.add_argument("pos_workspace", nargs="?", type=Path, default=None)
            parser.add_argument("--workspace", type=Path, default=None)
            parser.add_argument("--sources", default="", help="Optional comma-separated list of source files or directories (auto-discovers when omitted)")
            parser.add_argument("--audit", action="store_true")
            parser.add_argument("--out", type=Path)
            args = parser.parse_args(argv[2:])
            ws = args.workspace or args.pos_workspace or Path(".")
            src_list = [Path(s.strip()) for s in args.sources.split(",") if s.strip()] if args.sources else None
            res = extract_sources_to_harvest(ws, src_list, audit_mode=args.audit)
            _write_out_utf8(args.out, res)
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0
        if argv[:2] == ["sdd", "materialize"]:
            from architect_framework.sdd_bridge.scaffolder import materialize_workspace
            parser = argparse.ArgumentParser(prog="architect-runtime sdd materialize", allow_abbrev=False)
            parser.add_argument("pos_workspace", nargs="?", type=Path, default=None)
            parser.add_argument("--workspace", type=Path, default=None)
            parser.add_argument("--sources", default="", help="Optional comma-separated source paths (auto-discovers when omitted)")
            parser.add_argument("--harvest", type=Path)
            parser.add_argument("--profile", choices=["seed", "minimal", "standard", "maximal", "portfolio"], default="maximal")
            parser.add_argument("--preset", choices=["solo-author", "governed-team"], default="solo-author")
            parser.add_argument("--reviewer", default="lead-architect")
            parser.add_argument("--workspace-id")
            parser.add_argument("--stub-only", action="store_true")
            parser.add_argument("--out", type=Path)
            args = parser.parse_args(argv[2:])
            ws = args.workspace or args.pos_workspace or Path(".")
            src_list = [Path(s.strip()) for s in args.sources.split(",") if s.strip()] if args.sources else None
            h_data = json.loads(args.harvest.read_text(encoding="utf-8")) if args.harvest and args.harvest.is_file() else None
            res = materialize_workspace(
                ws,
                h_data,
                sources=src_list,
                profile=args.profile,
                preset=args.preset,
                reviewer=args.reviewer,
                workspace_id=args.workspace_id,
                stub_only=args.stub_only,
            )
            _write_out_utf8(args.out, res)
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0
        if argv[:2] == ["sdd", "plan-waves"]:
            from architect_framework.sdd_bridge.authoring_qa import plan_waves
            parser = argparse.ArgumentParser(prog="architect-runtime sdd plan-waves", allow_abbrev=False)
            parser.add_argument("workspace", nargs="?", type=Path, default=Path("."))
            parser.add_argument("--batch-size", type=int, default=4)
            parser.add_argument("--waves-dir", type=Path, default=None)
            parser.add_argument("--out", type=Path)
            args = parser.parse_args(argv[2:])
            res = plan_waves(args.workspace, batch_size=args.batch_size, out_dir=args.waves_dir)
            _write_out_utf8(args.out, res)
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0
        if argv[:2] == ["sdd", "prepare-check"]:
            from architect_framework.sdd_bridge.authoring_qa import prepare_check
            parser = argparse.ArgumentParser(prog="architect-runtime sdd prepare-check", allow_abbrev=False)
            parser.add_argument("workspace", nargs="?", type=Path, default=Path("."))
            parser.add_argument("--tighten", action=argparse.BooleanOptionalAction, default=True)
            parser.add_argument("--style-fix", action=argparse.BooleanOptionalAction, default=True)
            parser.add_argument("--stamp", action=argparse.BooleanOptionalAction, default=True)
            parser.add_argument("--pad-to-min", action=argparse.BooleanOptionalAction, default=True)
            parser.add_argument("--out", type=Path)
            args = parser.parse_args(argv[2:])
            res = prepare_check(
                args.workspace,
                tighten=args.tighten,
                style_fix=args.style_fix,
                stamp=args.stamp,
                pad_to_min=args.pad_to_min,
            )
            _write_out_utf8(args.out, res)
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0
        if argv[:2] == ["sdd", "freeze-digest"]:
            from architect_framework.sdd_bridge.scaffolder import freeze_coverage_basis
            parser = argparse.ArgumentParser(prog="architect-runtime sdd freeze-digest", allow_abbrev=False)
            parser.add_argument("workspace", nargs="?", type=Path, default=Path("."))
            parser.add_argument("--out", type=Path)
            args = parser.parse_args(argv[2:])
            res = freeze_coverage_basis(args.workspace)
            _write_out_utf8(args.out, res)
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0
        if argv[:2] == ["sdd", "probe-models"]:
            from architect_framework.runtime.core_runs import probe_models
            parser = argparse.ArgumentParser(prog="architect-runtime sdd probe-models", allow_abbrev=False)
            parser.add_argument("--workspace", type=Path, default=Path("."))
            parser.add_argument("--out", type=Path)
            args = parser.parse_args(argv[2:])
            res = probe_models(args.workspace)
            _write_out_utf8(args.out, res)
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0
        if argv[:2] == ["sdd", "status-probe"]:
            from architect_framework.sdd_bridge import status_probe
            parser = argparse.ArgumentParser(prog="architect-runtime sdd status-probe", allow_abbrev=False)
            parser.add_argument("workspace", nargs="?", default=".")
            parser.add_argument("--out", type=Path)
            args = parser.parse_args(argv[2:])
            res = status_probe(args.workspace)
            _write_out_utf8(args.out, res)
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0
        if argv[:2] == ["sdd", "execute-standalone"]:
            from architect_framework.sdd_bridge import execute_standalone
            parser = argparse.ArgumentParser(prog="architect-runtime sdd execute-standalone", allow_abbrev=False)
            parser.add_argument("pos_query", nargs="*")
            parser.add_argument("--domain", default="")
            parser.add_argument("--task", default="")
            parser.add_argument("--query", default="")
            parser.add_argument("--out", type=Path)
            parser.add_argument("--workspace", type=Path, default=Path("."))
            args = parser.parse_args(argv[2:])
            q_str = args.query or " ".join(args.pos_query)
            res = execute_standalone(args.domain, args.task, q_str, out_path=args.out, workspace=args.workspace)
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0
        if argv[:2] == ["sdd", "host-init"]:
            from architect_framework.sdd_bridge import initialize
            parser = argparse.ArgumentParser(prog="architect-runtime sdd host-init", allow_abbrev=False)
            parser.add_argument("workspace")
            parser.add_argument("--workspace-id")
            parser.add_argument("--reviewer", default="lead-architect")
            parser.add_argument("--profile", choices=["seed", "minimal", "standard", "maximal", "portfolio"])
            parser.add_argument("--preset", choices=["solo-author", "governed-team"])
            parser.add_argument("--allow-existing-sources", action="store_true")
            parser.add_argument("--out", type=Path)
            args = parser.parse_args(argv[2:])
            res = initialize(
                args.workspace,
                args.workspace_id,
                args.reviewer,
                profile=args.profile,
                preset=args.preset,
                allow_existing_sources=args.allow_existing_sources,
            )
            _write_out_utf8(args.out, res)
            print(json.dumps(res, ensure_ascii=False))
            return 0
        if argv[:2] == ["sdd", "host-recover"]:
            from architect_framework.sdd_bridge.publication import recover
            parser = argparse.ArgumentParser(prog="architect-runtime sdd host-recover", allow_abbrev=False)
            parser.add_argument("workspace")
            args = parser.parse_args(argv[2:])
            print(json.dumps(recover(args.workspace), ensure_ascii=False))
            return 0
        if argv[:2] in (["sdd", "review-candidate"], ["sdd", "language-review"], ["sdd", "language-repair"]):
            from architect_framework.sdd_bridge import language
            from sdd_core.model import SddError
            action = argv[1]
            parser = argparse.ArgumentParser(prog="architect-runtime sdd " + action, allow_abbrev=False)
            parser.add_argument("workspace")
            parser.add_argument("--change", required=True)
            parser.add_argument("--out", type=Path)
            if action == "language-repair":
                parser.add_argument("--artifact", required=True)
                parser.add_argument("--draft", type=Path, required=True)
                parser.add_argument("--skill", required=True)
                parser.add_argument("--expect-snapshot", required=True)
                parser.add_argument("--operation-id")
            else:
                parser.add_argument("--live", action="store_true")
                parser.add_argument("--force", action="store_true")
            args = parser.parse_args(argv[2:])
            try:
                if action == "language-repair":
                    if args.draft.stat().st_size > 50_000: parser.error("Repair draft exceeds 50,000 bytes")
                    result = language.repair(args.workspace, args.change, args.artifact, args.draft.read_text(encoding="utf-8"), args.skill, args.expect_snapshot, args.operation_id)
                else:
                    fn = language.review_candidate if action == "review-candidate" else language.review
                    result = fn(args.workspace, args.change, live=args.live, force=args.force)
            except SddError as exc:
                return _error(argv, exc.code + ": " + str(exc))
            _write_out_utf8(args.out, result)
            print(json.dumps(result, ensure_ascii=False))
            return 0 if result["status"] in {"DRAFT", "NOT_APPLICABLE"} else 3
        if argv[:1] == ["sdd"]:
            from sdd_core.cli import main as sdd_main
            from architect_framework.sdd_bridge import engine_for
            return sdd_main(argv[1:], engine_factory=engine_for)
        if argv[:1] == ["console"]:
            from architect_framework.console import cli
            args = argv
        else:
            from architect_framework.runtime import cli
            args = ["runtime", *argv]
        parser = argparse.ArgumentParser(prog="architect-runtime", allow_abbrev=False)
        cli.register(parser.add_subparsers(dest="command"))
        return cli.run(parser.parse_args(args)) or 0
    except (ImportError, ModuleNotFoundError) as exc:
        message = "Missing runtime dependency; install architect-agent-framework[runtime,console,sdd] in this interpreter"
        return _error(argv, message + f" ({getattr(exc, 'name', 'dependency')})")
    except (OSError, ValueError, RuntimeError) as exc:
        return _error(argv, str(exc))


def _error(argv, message):
    if argv[:1] == ["hook"]:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                          "permissionDecisionReason": "Architect hook unavailable: " + message}}))
        return 0
    print("architect-runtime: " + message, file=sys.stderr)
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
