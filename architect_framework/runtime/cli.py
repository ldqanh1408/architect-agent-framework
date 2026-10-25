"""Current core runtime commands. Human decisions use the signed workbench."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from collections.abc import Callable
from architect_framework.i18n import trf

NON_TTY_ENV = "ARCHITECT_ALLOW_NONTTY_DECISION"  # No authority is derived from this variable.


def _confirm_human(expected, what):
    if not sys.stdin.isatty():
        sys.stderr.write(f"{what} requires a human terminal. Use the signed workbench.\n")
        return False
    sys.stderr.write(f"{what}: type the first eight digest characters ({expected[:4]}…): ")
    sys.stderr.flush()
    return sys.stdin.readline().strip() == expected[:8]


def register(parsers):
    runtime = parsers.add_parser("runtime", help="Core tasks: plan, start, inspect, observe and control")
    sub = runtime.add_subparsers(dest="runtime_command")
    for name in ["plan", "status", "next", "tick", "recheck", "scorecard", "check", "doctor"]:
        command = sub.add_parser(name); workspace_arg(command)
        if name == "status": command.add_argument("--json", action="store_true")
        if name == "plan":
            command.add_argument("--tasks-file")
            command.add_argument("--only", action="append", default=[])
            command.add_argument("--base-change")
    start = sub.add_parser("start"); workspace_arg(start, run=False)
    start.add_argument("--run-id"); start.add_argument("--tasks-file"); start.add_argument("--only", action="append", default=[])
    start.add_argument("--base-change", help="Start from this checked candidate without publishing it")
    for name in ["claim", "heartbeat", "complete", "control", "observe"]:
        command = sub.add_parser(name); workspace_arg(command)
        if name == "observe": command.add_argument("--after", type=int, default=0)
        elif name == "control":
            command.add_argument("--action", choices=["pause", "resume", "cancel", "retry"], required=True)
            command.add_argument("--task")
        else:
            command.add_argument("--task", required=True)
            if name != "claim": command.add_argument("--lease", required=True)
            if name == "complete": command.add_argument("--operations-file", required=True)
    register_skills(sub, workspace_arg)
    hook = sub.add_parser("hook"); hook.add_argument("event", choices=["pre-tool-use"])
    mcp = sub.add_parser("mcp", allow_abbrev=False)
    mcp.add_argument("--http", action="store_true"); mcp.add_argument("--workspace")
    mcp.add_argument("--port", type=int, default=8768); mcp.add_argument("--token")


def status_text(result, workspace):
    import shlex
    tasks = result.get("tasks", [])
    waiting = [task for task in tasks if task["state"] == "waiting-for-human"]
    lines = [f"Run: {result.get('run_id') or 'not started'} · {result['state']}",
             f"Tasks: {sum(task['state'] == 'complete' for task in tasks)}/{len(tasks)} complete; {len(waiting)} waiting for a human"]
    ws_path = Path(str(workspace))
    if (ws_path / "sdd-workspace.yml").is_file():
        try:
            from sdd_core.workspace import capture
            from sdd_core.validation import check_snapshot
            snap = capture(ws_path, allow_live_read=True)
            chk = check_snapshot(snap)
            lines.append(f"SDD Workspace: {len(snap.artifacts)} artifact(s) · Check: {chk.status.value} ({len(chk.findings)} finding(s))")
        except Exception:
            pass
    lines += [f"- {task['id']}: {task.get('reason', 'Human decision required')}" for task in waiting[:10]]
    if len(waiting) > 10: lines.append(f"- {len(waiting) - 10} more; use --json or the workbench")
    lines += ["Review, acceptance and publication are separate.", "Cost: unavailable from host.",
              "Next: architect-runtime " + ("console serve " if tasks else "start ") + shlex.quote(str(workspace))]
    return "\n".join(lines)


def _print(value) -> None:
    if isinstance(value, str):
        sys.stdout.write(value if value.endswith("\n") else value + "\n")
    else:
        sys.stdout.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def _skills(args: argparse.Namespace) -> int:
    """`skills status | install | offer | doctor` (specification section 5.4, specification)."""
    import json

    from architect_framework import skillpacks

    command = getattr(args, "skills_command", None)
    if command == "install":
        try:
            rows = [r for source in args.source
                    for r in skillpacks.install(source, replace_licensed=args.replace)]
        except skillpacks.InstallError as exc:
            sys.stderr.write(f"skills install: {exc}\n")
            return 2
        for row in rows:
            print(f"{row.skill:<34} {row.state:<11} {'replaced' if row.replaced else 'installed'}  {row.dest}")
        print(f"{len(rows)} skill(s) installed into {skillpacks.install_root()}. "
              "The next run briefs their agents with them; `skills status <workspace>` shows what is left.")
        return 0
    if command == "offer":
        views = [skillpacks.slot_view(s) for s in args.skill]
        if getattr(args, "json", False):
            print(json.dumps(views, ensure_ascii=False, indent=2))
            return 0
        for view in views:
            print(f"{view['skill']:<34} {view['state']:<11} {view.get('advice') or view['content']}")
        return 0
    if command == "doctor":
        findings = skillpacks.doctor()
        if getattr(args, "json", False):
            print(json.dumps(findings, ensure_ascii=False, indent=2))
        else:
            for f in findings:
                print(f"[{f['code']}] {f['path']}: {f['message']}")
            print(f"skills doctor: {len(findings)} finding(s) on {len(skillpacks.search_path())} skills folder(s)")
        return 1 if findings else 0
    if command != "status":
        sys.stderr.write("usage: skills {status,install,offer,doctor} …\n")
        return 2
    report = skillpacks.workspace_report(args.workspace)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1 if any(r["state"] == "error" for r in report["slots"]) else 0
    rows = report["slots"]
    width = max((len(r["skill"]) for r in rows), default=5)
    for row in rows:
        print(f"{row['skill']:<{width}}  {row['state']:<11}  {row['content']}")
    print(f"Workspace {Path(report['workspace']).name} needs {report['required']} skills: "
          f"{report['filled']} installed, {len(report['empty'])} empty.")
    cover = report["cheapest_cover"]
    if cover:
        offers = skillpacks.offers()
        named = {p["id"]: p for p in offers.get("packs") or []}
        if offers.get("suite"):
            named[offers["suite"]["id"]] = offers["suite"]
        bought = sum(named[p]["price_usd"] for p in cover["packs"])
        parts = [f"{named[p]['title']} ${named[p]['price_usd']}" for p in cover["packs"]]
        if cover["singles"]:
            parts.append(f"{len(cover['singles'])} single skill(s) ${cover['total'] - bought}")
        print(f"  cheapest cover: {' + '.join(parts)} = ${cover['total']} (all singles: ${cover['singles_total']})")
        print(f"  buy at {report['store']}, then `skills install <zip>`; "
              f"or bind your own skills in {Path(report['workspace']) / skillpacks.BINDINGS_FILE}.")
        print("  An empty slot writes nothing; ARCHITECT_ALLOW_BASE=1 writes it from the contract alone.")
    return 1 if any(r["state"] == "error" for r in rows) else 0


def register_skills(sub: argparse._SubParsersAction, ws: Callable[..., None]) -> None:
    """The `skills` command, shared by `runtime skills` and the top-level `skills`."""
    skl = sub.add_parser("skills", help="Skill slots: which a workspace needs, what fills them, how to fill the rest")
    skl_sub = skl.add_subparsers(dest="skills_command")
    st = skl_sub.add_parser("status", help="Every slot the workspace plan needs, its state, and the cheapest packs "
                                           "that fill the empty ones")
    ws(st, run=False)
    st.add_argument("--json", action="store_true", help="the report as one JSON object (as the MCP tool returns it)")
    ins = skl_sub.add_parser("install", help="Install bought (or your own) skills — a zip, a zip of zips, or a "
                                             "folder — each into its slot folder under ~/.architect-framework")
    ins.add_argument("source", nargs="+", type=Path)
    ins.add_argument("--replace", action="store_true",
                     help="replace a bought (licensed) skill with one that is not")
    off = skl_sub.add_parser("offer", help="Whether a skill's slot is filled, and if not, what fills it and for how much")
    off.add_argument("skill", nargs="+")
    off.add_argument("--json", action="store_true")
    doc = skl_sub.add_parser("doctor", help="Skill folders placed where no slot reads them, or named unlike their SKILL.md")
    doc.add_argument("--json", action="store_true")


def workspace_arg(parser: argparse.ArgumentParser, run: bool = True) -> None:
    parser.add_argument("workspace", nargs="?", default=".", help="workspace root (default: .)")
    if run:
        parser.add_argument("--run", default=None, help="run id (default: latest)")



def run(args):
    cmd = args.runtime_command
    if cmd == "hook":
        from architect_framework.runtime import hook

        code, out = hook.main(sys.stdin.read())
        if out:
            sys.stdout.write(out + "\n")
        return code
    if cmd == "mcp":
        from architect_framework.runtime import mcp_server

        for stream in (sys.stdin, sys.stdout, sys.stderr):
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8")
        if getattr(args, "http", False):
            import os

            # The hook refuses the flag to an agent; this refuses it to any non-interactive shell,
            # which is what an agent has. A person starts it in their own terminal.
            if not sys.stdin.isatty():
                sys.stderr.write("runtime mcp --http runs only from an interactive terminal; refusing" + chr(10))
                return 2
            token = args.token or os.environ.get("ARCHITECT_MCP_TOKEN") or ""
            if not args.workspace or not token:
                sys.stderr.write("runtime mcp --http needs --workspace and a token (--token or ARCHITECT_MCP_TOKEN); "
                                 "refusing to expose anything without both" + chr(10))
                return 2
            if len(token) < 32:
                # A guessable token is no token (LP 20, L-5). Prefer the variable: --token shows in
                # the process list.
                sys.stderr.write("runtime mcp --http needs a token of at least 32 characters, e.g. "
                                 "`python -c \"import secrets; print(secrets.token_urlsafe(32))\"`" + chr(10))
                return 2
            ws = str(Path(args.workspace).resolve())
            sys.stderr.write(trf("CẢNH BÁO: workspace {ws} đang đọc được qua http://127.0.0.1:{0}/mcp — chỉ công cụ đọc, cần bearer token. Dừng bằng Ctrl+C.", args.port, ws=ws) + chr(10))
            return mcp_server.serve_http(ws, token, port=args.port)
        return mcp_server.serve()
    if cmd == "skills":
        return _skills(args)
    if cmd is None:
        sys.stderr.write("runtime: choose a subcommand; see --help\n")
        return 2
    workspace = str(Path(args.workspace).absolute())
    if cmd == "doctor":
        from .diagnostics import doctor
        result=doctor(workspace);_print(result);return 0 if result["status"]=="PASS" else 3
    from architect_framework.sdd_bridge.mode import workspace_mode
    if workspace_mode(workspace) != "core":
        from architect_framework.sdd_bridge.mode import classify
        _print(classify(workspace)); return 3
    if workspace_mode(workspace) == "core":
        from architect_framework.sdd_bridge import inspect, reject_legacy_write
        from architect_framework.runtime import core_runs, service
        from sdd_core.model import SddError
        try:
            if cmd == "check":
                if getattr(args, "write", False):
                    reject_legacy_write(workspace)
                report = inspect(workspace)
                _print(report)
                state = report["check"]["status"]
                return 0 if state == "PASS" else 1 if state == "FAIL" else 3
            if cmd == "plan":
                tasks = json.loads(Path(args.tasks_file).read_text(encoding="utf-8")) if args.tasks_file else None
                _print(service.plan(workspace, tasks, args.only or None, base_change=args.base_change)); return 0
            if cmd == "start":
                tasks = json.loads(Path(args.tasks_file).read_text(encoding="utf-8")) if args.tasks_file else None
                _print(core_runs.start(workspace, tasks, args.run_id, args.only or None, base_change=args.base_change)); return 0
            if cmd in {"status", "next", "tick", "recheck", "scorecard"}:
                result = core_runs.status(workspace, args.run) if cmd in {"status", "scorecard"} else core_runs.tick(workspace, args.run)
                if cmd == "scorecard":
                    from architect_framework.sdd_bridge import status_probe
                    result = {**result, "sdd": status_probe(workspace)}
                _print(status_text(result, workspace) if cmd == "status" and not args.json else result); return 0
            if cmd == "observe":
                _print(core_runs.observe(workspace, args.after, run_id=args.run)); return 0
            if cmd in {"claim", "heartbeat", "complete", "control"}:
                rid = args.run or core_runs.status(workspace)["run_id"]
                if cmd == "claim": result = core_runs.claim(workspace, rid, args.task)
                elif cmd == "heartbeat": result = core_runs.heartbeat(workspace, rid, args.task, args.lease)
                elif cmd == "control": result = core_runs.control(workspace, rid, args.action, args.task)
                else: result = core_runs.complete(workspace, rid, args.task, args.lease, json.loads(Path(args.operations_file).read_text(encoding="utf-8")))
                _print(result); return 0
        except (SddError, ValueError, OSError) as error:
            _print(error.to_dict() if hasattr(error,"to_dict") else {"status":"ERROR","message":str(error)}); return 3
        if cmd in {"plan", "start", "status", "next", "tick", "recheck", "scorecard", "check"}:
            if getattr(args, "write", False):
                reject_legacy_write(workspace)
            report = inspect(workspace)
            _print(report)
            state = report["check"]["status"]
            return (0 if state == "PASS" else 1 if state == "FAIL" else 3) if cmd == "check" else 0
        reject_legacy_write(workspace)
    return 3
