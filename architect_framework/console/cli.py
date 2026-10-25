"""`console` — the review console's commands (specification, specification).

    console serve <workspace> [--port N] [--enroll]   run the console on 127.0.0.1
    console url   <workspace> [--wait ID] [--port N]  the link an agent hands a person
    console verify <workspace>                        re-check every passkey signature offline
    console trust-reviewers <workspace>               trust here the keys reviewers.yml lists (HUMAN ONLY)

`--enroll` opens the one door that changes the trust root; the plugin hook refuses
it to an agent's shell, so only the person's own terminal can pass it (plan section 4.4).
"""

from __future__ import annotations

import argparse
from pathlib import Path

DEFAULT_PORT = 8767


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("console", help="Review console: read the tree and sign decisions on 127.0.0.1")
    cs = p.add_subparsers(dest="console_command", required=True)
    # allow_abbrev=False: `--enr` must not mean `--enroll` behind the hook's back (EMB-08 review).
    serve = cs.add_parser("serve", help="Serve the review console for one workspace (loopback only)",
                          allow_abbrev=False)
    serve.add_argument("workspace", type=Path)
    serve.add_argument("--port", type=int, default=DEFAULT_PORT)
    serve.add_argument("--enroll", action="store_true",
                       help="HUMAN ONLY: allow registering a reviewer passkey during this session")
    link = cs.add_parser("url", help="Print the console link for a wait (what an agent gives the person)")
    link.add_argument("workspace", type=Path)
    link.add_argument("--wait", default=None)
    link.add_argument("--port", type=int, default=DEFAULT_PORT)
    verify = cs.add_parser("verify", help="Re-check every console signature in a workspace, offline")
    verify.add_argument("workspace", type=Path)
    trust = cs.add_parser("trust-reviewers", allow_abbrev=False,
                          help="HUMAN ONLY: trust on this machine the reviewer keys .architect/reviewers.yml lists")
    trust.add_argument("workspace", type=Path)


def _say(what: str, do: str) -> int:
    """specification: one line for what went wrong, one for what to do; never a traceback."""
    import sys

    print(f"console: {what}\n  {do}", file=sys.stderr)
    return 2


def run(args: argparse.Namespace) -> int:
    cmd = args.console_command
    if cmd == "url":
        suffix = f"#wait={args.wait}" if args.wait else ""
        print(f"http://localhost:{args.port}/{suffix}")
        return 0
    if not args.workspace.is_dir():
        return _say(f"no workspace folder at {args.workspace}",
                    "Give the folder that holds the plan and the architecture/ tree, e.g. `console serve .`")
    if cmd == "verify":
        return _verify(args.workspace.resolve())
    if cmd == "trust-reviewers":
        return _trust(args.workspace.resolve())
    from architect_framework.console import server
    import sys
    if args.enroll and not sys.stdin.isatty():
        return _say("reviewer enrollment requires an interactive operator terminal",
                    "Start console serve --enroll in your own terminal")

    try:
        srv = server.make_server(args.workspace, port=args.port, enroll=args.enroll)
        if args.enroll:
            import threading
            confirming = threading.Lock()
            def confirm_key(candidate):
                with confirming:
                    fingerprint = candidate["key_fingerprint"]
                    print("New reviewer key: " + repr(candidate["name"]) + " · SHA256 " + fingerprint, flush=True)
                    print("Confirm the passkey you just registered in the browser. Type the first 8 fingerprint characters: ",
                          end="", flush=True)
                    return sys.stdin.readline().strip() == fingerprint[:8]
            srv.state.enrollment_approver = confirm_key
    except OSError as exc:
        # 10013: Windows answers a port another socket holds exclusively with "access forbidden".
        busy = getattr(exc, "winerror", None) in (10048, 10013) or getattr(exc, "errno", None) in (98, 48)
        if busy or "in use" in str(exc).lower():
            return _say(f"port {args.port} is already in use — another console may be open at "
                        f"http://localhost:{args.port}/", f"Open that link, or pick another port: --port {args.port + 1}")
        return _say(f"could not start the console: {exc}", "Check the folder can be read, then run the command again")
    print(f"review console: {server.url(srv)}  (workspace {srv.state.workspace}"
          f"{', enrolment ON' if args.enroll else ''}) — Ctrl+C to stop", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


def _trust(ws: Path, *, stdin=None) -> int:
    """Trust, on this machine, the keys a reviewers file lists — after the person has read them.

    A teammate's key arrives in a commit; this is how it starts to count here. It
    reads the answer from a terminal, so an agent's shell cannot confirm for the
    person (and the plugin hook refuses the command to an agent).
    """
    import sys

    from architect_framework.console import attest
    from architect_framework.sdd_bridge import require_core
    require_core(ws)

    stdin = stdin or sys.stdin
    trusted = attest.trusted_credentials(ws) or set()
    new = [r for r in attest.listed_reviewers(ws) if r.credential_id not in trusted]
    if not new:
        print("every key in .architect/reviewers.yml is already trusted here")
        return 0
    if not stdin.isatty():
        print("trust-reviewers reads the answer from a terminal; run it yourself", file=sys.stderr)
        return 2
    for r in new:
        print(f"  {r.name}  credential {r.credential_id}  enrolled {r.enrolled_at or '?'}")
    print("Type 'trust' to count signatures from these keys on this machine: ", end="", flush=True)
    if stdin.readline().strip() != "trust":
        print("nothing trusted")
        return 1
    path = attest.trust(ws, [r.credential_id for r in new])
    print(f"trusted {len(new)} key(s) for {attest.project_root(ws)} in {path}")
    return 0


def _verify(ws: Path) -> int:
    """Audit current document, run-gate and corpus signatures without granting authority."""
    from architect_framework.console import attest
    from architect_framework.sdd_bridge import engine_for, require_core
    from architect_framework.runtime.core_runs import decision_records
    from sdd_core.model import SddError
    require_core(ws)
    engine = engine_for(ws); reviewers = attest.load_reviewers(ws)
    records, bad = [], []
    try:
        records = [*engine.store.decisions(), *engine.store.list("label_approvals"), *decision_records(ws)]
        for record in records:
            problem = attest.verify(record, reviewers, decided_by_field="actor", when_field="created_at")
            if problem: bad.append(f"{record.get('decision_id', 'malformed decision')}: {problem}")
        for certificate in engine.store.history(): engine.store.load_snapshot(certificate["snapshot_digest"])
    except (SddError, OSError, ValueError, RuntimeError, TypeError, KeyError, AttributeError) as exc:
        bad.append(f"Current decisions or acceptance history [{getattr(exc, 'code', 'ATTESTATION')}]: {exc}")
    for line in bad: print(f"  [ATTESTATION] {line}")
    print(f"console verify: {len(records)} current decision record(s), {len(bad)} failing")
    return 1 if bad else 0
