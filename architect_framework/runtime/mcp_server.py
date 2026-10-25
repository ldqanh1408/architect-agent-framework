"""Core MCP tools. Humans sign gates and acceptance in the local workbench.

The remote transport exposes read tools for one workspace. Obsolete raw writes
and embedded document-tree resources are retired in the 2.0 candidate.
"""

from __future__ import annotations

import json
import sys
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import Any, TextIO

from architect_framework import __version__ as _AAF_VERSION
from architect_framework.runtime import service
from architect_framework.sdd_bridge import inspect as sdd_inspect, propose as sdd_propose

PROTOCOL_VERSION = "2025-06-18"
SERVER_INFO = {"name": "architect-runtime", "version": _AAF_VERSION}
_WS = {"workspace": {"type": "string", "description": "Current workspace root holding sdd-workspace.yml."}}
_RUN = {"run": {"type": "string", "description": "Run id; defaults to the latest run."}}


def _schema(props: dict, required: list[str]) -> dict:
    return {"type": "object", "properties": props, "required": required, "additionalProperties": False}


def _plan(args):
    return service.plan(args["workspace"], args.get("tasks"), args.get("only"), base_change=args.get("base_change"))


def _skills(args: dict) -> Any:
    from architect_framework import skillpacks

    return skillpacks.workspace_report(args["workspace"])


def _next(args):
    return service.tick(args["workspace"], args.get("run"))


def _console_url(args):
    from architect_framework.sdd_bridge.mode import classify
    from architect_framework.console.cli import DEFAULT_PORT
    port = int(args.get("port") or DEFAULT_PORT)
    return {"url": f"http://localhost:{port}/", "runs_url": f"http://localhost:{port}/runs", "setup": classify(args["workspace"]),
            "start_if_needed": {"command": "architect-runtime", "args": ["console", "serve", args["workspace"], "--port", str(port)]}}


def _runs():
    from . import core_runs
    return core_runs


TOOLS: dict[str, tuple[str, dict, Callable[[dict], Any]]] = {
    "architect_sdd_init": (
        "Initialize a new SDD workspace in the target directory (supports solo-author and governed-team presets and existing source files).",
        _schema({**_WS, "workspace_id": {"type": "string"}, "reviewer": {"type": "string", "default": "lead-architect"},
                 "profile": {"type": "string", "enum": ["seed", "minimal", "standard", "maximal", "portfolio"], "default": "standard"},
                 "preset": {"type": "string", "enum": ["solo-author", "governed-team"], "default": "solo-author"},
                 "allow_existing_sources": {"type": "boolean", "default": True}}, ["workspace"]),
        lambda a: __import__("architect_framework.sdd_bridge", fromlist=["initialize"]).initialize(
            a["workspace"], a.get("workspace_id"), a.get("reviewer", "lead-architect"),
            profile=a.get("profile", "standard"), preset=a.get("preset", "solo-author"),
            allow_existing_sources=a.get("allow_existing_sources", True))),
    "architect_sdd_extract": (
        "Extract source requirements, ADRs, scenarios, and conflict records into .architect-build/harvest.json (auto-discovers sources when omitted).",
        _schema({**_WS, "sources": {"type": "array", "items": {"type": "string"}},
                 "audit": {"type": "boolean", "default": False}}, ["workspace"]),
        lambda a: __import__("architect_framework.sdd_bridge.scaffolder", fromlist=["extract_sources_to_harvest"]).extract_sources_to_harvest(
            Path(a.get("workspace", ".")), [Path(s) for s in a["sources"]] if a.get("sources") else None, audit_mode=a.get("audit", False))),
    "architect_sdd_materialize": (
        "Materialize the target architecture document tree, ledgers, wave micro-batches, and frozen basis_digest.",
        _schema({**_WS, "profile": {"type": "string", "enum": ["seed", "minimal", "standard", "maximal", "portfolio"], "default": "maximal"},
                 "preset": {"type": "string", "enum": ["solo-author", "governed-team"], "default": "solo-author"},
                 "reviewer": {"type": "string", "default": "lead-architect"}, "stub_only": {"type": "boolean", "default": False},
                 "sources": {"type": "array", "items": {"type": "string"}}, "harvest": {"type": "object"},
                 "workspace_id": {"type": "string"}}, ["workspace"]),
        lambda a: __import__("architect_framework.sdd_bridge.scaffolder", fromlist=["materialize_workspace"]).materialize_workspace(
            Path(a["workspace"]), harvest=a.get("harvest"),
            sources=[Path(s) for s in a["sources"]] if a.get("sources") else None,
            profile=a.get("profile", "maximal"), preset=a.get("preset", "solo-author"),
            reviewer=a.get("reviewer", "lead-architect"), workspace_id=a.get("workspace_id"),
            stub_only=a.get("stub_only", False))),
    "architect_sdd_prepare_check": (
        "Run the built-in post-processing pipeline (strip <think>, tighten lines, repair frontmatter, STE-80 style fix, stamp depth_witnesses, freeze digest).",
        _schema({**_WS, "tighten": {"type": "boolean", "default": True}, "style_fix": {"type": "boolean", "default": True},
                 "stamp": {"type": "boolean", "default": True}, "pad_to_min": {"type": "boolean", "default": True}}, ["workspace"]),
        lambda a: __import__("architect_framework.sdd_bridge.authoring_qa", fromlist=["prepare_check"]).prepare_check(
            Path(a["workspace"]), tighten=a.get("tighten", True), style_fix=a.get("style_fix", True),
            stamp=a.get("stamp", True), pad_to_min=a.get("pad_to_min", True))),
    "architect_execute_standalone": (
        "Execute a single Domain x Task skill pair in standalone mode (UC-05) without requiring sdd-workspace.yml.",
        _schema({"workspace": {"type": "string"}, "domain_skill": {"type": "string"}, "task_skill": {"type": "string"},
                 "domain": {"type": "string"}, "task": {"type": "string"},
                 "query": {"type": "string"}, "out_path": {"type": "string"}, "out": {"type": "string"}}, ["query"]),
        lambda a: __import__("architect_framework.sdd_bridge", fromlist=["execute_standalone"]).execute_standalone(
            a.get("domain_skill") or a.get("domain", ""), a.get("task_skill") or a.get("task", ""), a["query"],
            out_path=a.get("out_path") or a.get("out"), workspace=a.get("workspace"))),
    "architect_candidate_review": ("Review an exact candidate: checks, semantic judge and all-document language evidence. live=true explicitly permits configured paid calls within the shared budget. Never accepts.",
        _schema({**_WS, "change_id": {"type": "string"}, "live": {"type": "boolean", "default": False}, "force": {"type": "boolean", "default": False}}, ["workspace", "change_id"]),
        lambda a: __import__('architect_framework.sdd_bridge.language', fromlist=['review_candidate']).review_candidate(a['workspace'], a['change_id'], live=a.get('live', False), force=a.get('force', False))),
    "architect_language_review": ("Record revision-bound per-rule language findings. live=true sends complete context to configured Jev; false runs local checks. No qualification or approval authority.",
        _schema({**_WS, "change_id": {"type": "string"}, "live": {"type": "boolean", "default": False}, "force": {"type": "boolean", "default": False}}, ["workspace", "change_id"]),
        lambda a: __import__('architect_framework.sdd_bridge.language', fromlist=['review']).review(a['workspace'], a['change_id'], live=a.get('live', False), force=a.get('force', False))),
    "architect_language_repair": ("Propose a targeted host-authored repair under an accepted grant. Preserves facts and live files; at most two repair attempts per document lineage. Candidate still needs review.",
        _schema({**_WS, "change_id": {"type": "string"}, "artifact_id": {"type": "string"}, "text": {"type": "string", "maxLength": 50000}, "skill": {"type": "string"}, "expected_snapshot": {"type": "string"}, "operation_id": {"type": "string"}},
                ["workspace", "change_id", "artifact_id", "text", "skill", "expected_snapshot"]),
        lambda a: __import__('architect_framework.sdd_bridge.language', fromlist=['repair']).repair(a['workspace'], a['change_id'], a['artifact_id'], a['text'], a['skill'], a['expected_snapshot'], a.get('operation_id'))),
    "architect_capabilities": ("Read supported host actions, coverage and authority boundaries.", _schema({}, []), lambda a: __import__('architect_framework.runtime.capabilities',fromlist=['describe']).describe()),
    "architect_doctor": ("Read bounded redacted diagnostics without modifying run state.", _schema(_WS,['workspace']), lambda a: __import__('architect_framework.runtime.diagnostics',fromlist=['doctor']).doctor(a['workspace'])),
    "architect_style_check": ("Check declared STE-inspired subset for one exact registered revision; incomplete rules stay unknown. No approval authority.",
        _schema({**_WS,"artifact_id":{"type":"string"},"change_id":{"type":"string"}},["workspace","artifact_id"]),
        lambda a: __import__('architect_framework.document_style',fromlist=['inspect_artifact']).inspect_artifact(a['workspace'],a['artifact_id'],a.get('change_id'))),
    "architect_sdd_read": ("Read a bounded registered artifact slice with its exact live or candidate revision.",
        _schema({**_WS, "artifact_id": {"type": "string"}, "change_id": {"type": "string"}, "offset": {"type": "integer", "minimum": 0}, "limit": {"type": "integer", "minimum": 1, "maximum": 50000}}, ["workspace", "artifact_id"]),
        lambda a: __import__("architect_framework.sdd_bridge", fromlist=["read_artifact"]).read_artifact(a["workspace"], a["artifact_id"], a.get("change_id"), a.get("offset", 0), a.get("limit", 20000))),
    "architect_runs_start": ("Start a bounded, revision-bound core task plan; human decisions remain separate.",
        _schema({**_WS, "tasks": {"type": "array", "items": {"type": "object"}}, "run_id": {"type": "string"}, "base_change": {"type": "string", "description": "Checked initial candidate; its exact snapshot is frozen into the plan."}}, ["workspace", "tasks"]),
        lambda a: _runs().start(a["workspace"], a["tasks"], a.get("run_id"), base_change=a.get("base_change"))),
    "architect_runs_observe": ("Read durable core events and task snapshots; starts no work.",
        _schema({**_WS, "after": {"type": "integer", "minimum": 0}, "database_id": {"type": "string"}}, ["workspace"]),
        lambda a: _runs().observe(a["workspace"], a.get("after", 0), database_id=a.get("database_id"))),
    "architect_runs_control": ("Pause, resume, cancel or retry scheduling; no approval authority.",
        _schema({**_WS, "run_id": {"type": "string"}, "task_id": {"type": "string"}, "action": {"enum": ["pause", "resume", "cancel", "retry"]}}, ["workspace", "run_id", "action"]),
        lambda a: _runs().control(a["workspace"], a["run_id"], a["action"], a.get("task_id"))),
    "architect_task_claim": ("Claim a ready core task and its private attempt lease.",
        _schema({**_WS, "run_id": {"type": "string"}, "task_id": {"type": "string"}}, ["workspace", "run_id", "task_id"]),
        lambda a: _runs().claim(a["workspace"], a["run_id"], a["task_id"])),
    "architect_task_heartbeat": ("Renew the exact active attempt lease.",
        _schema({**_WS, "run_id": {"type": "string"}, "task_id": {"type": "string"}, "lease_token": {"type": "string"}}, ["workspace", "run_id", "task_id", "lease_token"]),
        lambda a: _runs().heartbeat(a["workspace"], a["run_id"], a["task_id"], a["lease_token"])),
    "architect_task_complete": ("Submit scoped proposal operations; never accepts or publishes documents.",
        _schema({**_WS, "run_id": {"type": "string"}, "task_id": {"type": "string"}, "lease_token": {"type": "string"}, "operations": {"type": "array", "items": {"type": "object"}}}, ["workspace", "run_id", "task_id", "lease_token", "operations"]),
        lambda a: _runs().complete(a["workspace"], a["run_id"], a["task_id"], a["lease_token"], a["operations"])),
    "architect_sdd_check": (
        "Read deterministic checks, regression readiness and freshness without accepting or changing state.",
        _schema({**_WS, "change_id": {"type": "string"}}, ["workspace"]),
        lambda a: sdd_inspect(a["workspace"], a.get("change_id"))),
    "architect_sdd_propose": (
        "Create an isolated candidate under a configured skill grant and expected live snapshot. Never accepts.",
        _schema({**_WS, "operations": {"type": "array", "minItems": 1, "items": {"type": "object"}},
                 "skill": {"type": "string"}, "expected_snapshot": {"type": "string"},
                 "operation_id": {"type": "string"}, "base_change": {"type": "string"}},
                ["workspace", "operations", "skill", "expected_snapshot"]),
        lambda a: sdd_propose(a["workspace"], a["operations"], a["skill"], a["expected_snapshot"], a.get("operation_id"), a.get("base_change"))),
    "architect_runtime_plan": (
        "Preview a revision-bound task plan and gates without creating a run.",
        _schema({**_WS, "tasks": {"type": "array", "items": {"type": "object"}}, "only": {"type": "array", "items": {"type": "string"}}, "base_change": {"type": "string"}}, ["workspace"]), _plan),
    "architect_runtime_start": (
        "Start a run in harness mode: the host agent is the executor. Returns what waits.",
        _schema({**_WS, "only": {"type": "array", "items": {"type": "string"},
                                 "description": "Optional job keys to restrict the run to."}}, ["workspace"]),
        lambda a: service.start(a["workspace"], only=a.get("only"))),
    "architect_runtime_status": (
        "Run state, per-agent lifecycle state and every pending wait.",
        _schema({**_WS, **_RUN}, ["workspace"]), lambda a: service.status(a["workspace"], a.get("run"))),
    "architect_runtime_next": (
        "What to do now: jobs to execute (with brief and allowed paths) and what waits for a human.",
        _schema({**_WS, **_RUN}, ["workspace"]), _next),
    "architect_runtime_tick": (
        "Continue `notify` waits whose deadline passed.",
        _schema({**_WS, **_RUN}, ["workspace"]), lambda a: service.tick(a["workspace"], a.get("run"))),
    "architect_runtime_recheck": (
        "Re-read the ledgers after a human decided. Carries no authority: an unapproved wait just waits again.",
        _schema({**_WS, **_RUN}, ["workspace"]), lambda a: service.recheck(a["workspace"], a.get("run"))),
    "architect_runtime_scorecard": (
        "Read the current core task summary; document acceptance is separate.",
        _schema({**_WS, **_RUN}, ["workspace"]),
        lambda a: service.scorecard_text(a["workspace"], a.get("run"))),
    "architect_runtime_skills": (
        "The skill slots this workspace needs: which have content, which are empty, what fills the empty ones "
        "(pack, price, store) and how to install a bought zip. Same JSON as `skills status --json`.",
        _schema(_WS, ["workspace"]), _skills),
    "architect_console_url": (
        "The current workbench link for task gates and document acceptance. Hand it to the "
        "user; they read and sign there with a passkey. Read-only: no tool decides.",
        _schema({**_WS, "wait": {"type": "string", "description": "A wait id such as HG-1; default: the first open one."},
                 "port": {"type": "integer"}}, ["workspace"]), _console_url),
}


REMOTE_TOOLS = frozenset({"architect_style_check","architect_sdd_check", "architect_sdd_read", "architect_runs_observe", "architect_runtime_plan", "architect_runtime_skills", "architect_console_url", "architect_capabilities", "architect_doctor"})


def tool_list(allowed=None):
    readonly = REMOTE_TOOLS | {"architect_runtime_status", "architect_runtime_scorecard"}
    return [{"name": name, "description": description, "inputSchema": schema,
             "annotations": {"readOnlyHint": name in readonly, "destructiveHint": False, "idempotentHint": name in readonly, "openWorldHint": name in {"architect_candidate_review", "architect_language_review"}}}
            for name, (description, schema, _) in TOOLS.items() if allowed is None or name in allowed]


#: Tools that take a workspace argument but create nothing in it.
_ANY_FOLDER = frozenset({"architect_console_url", "architect_capabilities", "architect_doctor", "architect_sdd_init", "architect_sdd_extract", "architect_sdd_materialize", "architect_execute_standalone"})
#: Any one of these makes a folder an architect workspace.
_WORKSPACE_MARKS = ("brief.md", "clarified-requirements.md", "charter-proposal.yml", "module-charter.yml",
                    "workspace-plan.yml", ".architect-runtime", "sdd-workspace.yml")


def looks_like_workspace(path: str | Path) -> bool:
    root = Path(path)
    return root.is_dir() and any(((root / mark).exists() or (root / mark).is_symlink()) for mark in _WORKSPACE_MARKS)


def _redacted(value: Any, workspace: str) -> Any:
    """`value` with local paths replaced: the workspace by `<workspace>`, the home folder by `~` (LP 20, L-5)."""
    ws, home = str(Path(workspace).resolve()), str(Path.home())
    variants = [(ws, "<workspace>"), (ws.replace("\\", "/"), "<workspace>"), (home, "~"), (home.replace("\\", "/"), "~")]
    if isinstance(value, str):
        for local, shown in variants:
            value = value.replace(local, shown).replace(local.replace("\\", "\\\\"), shown)
        return value
    if isinstance(value, dict):
        return {k: _redacted(v, workspace) for k, v in value.items()}
    if isinstance(value, list):
        return [_redacted(v, workspace) for v in value]
    return value


def handle(message: dict, *, allowed: frozenset[str] | None = None, workspace: str | None = None) -> dict | None:
    if not isinstance(message, dict):
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "one JSON-RPC object per request"}}
    method = message.get("method")
    mid = message.get("id")
    if mid is None:  # a notification
        return None
    try:
        if method == "initialize":
            requested = (message.get("params") or {}).get("protocolVersion") or PROTOCOL_VERSION
            result: Any = {"protocolVersion": requested,
                           "capabilities": {"tools": {"listChanged": False}},
                           "serverInfo": SERVER_INFO}
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": tool_list(allowed)}
        elif method == "resources/list":
            result = {"resources": []}
        elif method == "resources/read":
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32002, "message": "The old embedded resource is retired; open architect_console_url"}}
        elif method == "tools/call":
            params = message.get("params") or {}
            name = params.get("name")
            if name not in TOOLS or (allowed is not None and name not in allowed):
                return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": f"unknown tool {name}"}}
            args = dict(params.get("arguments") or {})
            if workspace is not None and "workspace" in TOOLS[name][1]["properties"]:
                # EMB-08: a remote host sees exactly one workspace, whatever it asks for.
                if args.get("workspace") and (not isinstance(args["workspace"], str) or Path(args["workspace"]).resolve() != Path(workspace).resolve()):
                    return {"jsonrpc": "2.0", "id": mid,
                            "error": {"code": -32602, "message": "this server exposes one workspace only"}}
                args["workspace"] = workspace
            from jsonschema import Draft202012Validator
            violations = list(Draft202012Validator(TOOLS[name][1]).iter_errors(args))
            if violations:
                return {"jsonrpc":"2.0","id":mid,"error":{"code":-32602,"message":"Arguments do not match the advertised input schema"}}
            if "workspace" in args:
                args["workspace"] = str(Path(args["workspace"]).absolute())
                if name in TOOLS and name not in _ANY_FOLDER and not looks_like_workspace(args["workspace"]):
                    # The runtime tools create state where they are pointed; a folder with
                    # none of a workspace's files is not one (LP 20, L-4).
                    return {"jsonrpc": "2.0", "id": mid, "error": {
                        "code": -32602, "message": "not an architect workspace: no brief, requirement, charter, "
                                                   "plan or run in it"}}
            from architect_framework import skillpacks

            try:
                if "workspace" in args and name not in _ANY_FOLDER:
                    from architect_framework.sdd_bridge import require_core
                    require_core(args["workspace"])
                with skillpacks.activated(args.get("workspace")):
                    value = TOOLS[name][2](args)
                    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)
                    result = {"content": [{"type": "text", "text": text}],
                              **({"structuredContent": value} if isinstance(value, dict) else {}),
                              "isError": isinstance(value, dict) and value.get("status") in {"ERROR", "INCOMPLETE", "STALE"}}
                if workspace is not None:
                    result = _redacted(result, workspace)
            except Exception as exc:  # noqa: BLE001 — a tool error is a result, not a protocol error
                # A remote host gets the kind of failure, never local paths in its text (L-5).
                detail = f"{type(exc).__name__}: {exc}" if workspace is None else f"{type(exc).__name__}: the tool failed"
                structured = exc.to_dict() if hasattr(exc, "to_dict") and workspace is None else {"status": "ERROR", "message": detail}
                result = {"content": [{"type": "text", "text": json.dumps(structured, ensure_ascii=False)}],
                          "structuredContent": structured, "isError": True}
        else:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not found: {method}"}}
        return {"jsonrpc": "2.0", "id": mid, "result": result}
    except Exception as exc:  # noqa: BLE001 — last resort: answer, never crash the server
        return {"jsonrpc": "2.0", "id": mid,
                "error": {"code": -32603, "message": str(exc),
                          # A remote host never sees local paths from a traceback (EMB-08).
                          **({} if workspace is not None else {"data": traceback.format_exc()[-800:]})}}


def serve(stdin: TextIO = sys.stdin, stdout: TextIO = sys.stdout) -> int:
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            reply: dict | None = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}
        else:
            reply = handle(message)
        if reply is not None:
            stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            stdout.flush()
    return 0


def serve_http(workspace: str, token: str, *, host: str = "127.0.0.1", port: int = 8768,
               ready: Callable[[Any], None] | None = None) -> int:
    """EMB-08 — Streamable HTTP for a remote host, behind a tunnel the person set up.

    One endpoint, `POST /mcp`, answering each JSON-RPC message with one JSON body.
    A request without `Authorization: Bearer <token>` gets 401. Only `REMOTE_TOOLS`
    exist here, and every call is pinned to `workspace`.
    """
    import hmac
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    ws = str(Path(workspace).resolve())

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a: Any) -> None:
            return

        def _send(self, status: int, body: dict | None) -> None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else b""
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:
            self._send(405, {"error": "POST JSON-RPC to /mcp"})

        def do_POST(self) -> None:
            auth = self.headers.get("Authorization", "")
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = -1
            if not hmac.compare_digest(auth.encode(), f"Bearer {token}".encode()):
                # A bounded body is read and dropped, so the client gets its 401 instead of a reset.
                if 0 < length <= 1_000_000:
                    self.rfile.read(length)
                self.close_connection = True
                self._send(401, {"error": "missing or wrong bearer token"})
                return
            if not 0 <= length <= 1_000_000:
                self.close_connection = True
                self._send(413, {"error": "body must be 0..1 MB"})
                return
            raw = self.rfile.read(length) if length else b""
            if self.path.split("?")[0] != "/mcp":
                self._send(404, {"error": "not found"})
                return
            try:
                message = json.loads(raw or b"{}")
            except json.JSONDecodeError:
                self._send(400, {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}})
                return
            reply = handle(message, allowed=REMOTE_TOOLS, workspace=ws)
            if reply is None:
                self._send(202, None)
            else:
                self._send(200, reply)

    httpd = ThreadingHTTPServer((host, port), Handler)
    if ready is not None:
        ready(httpd)
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
    return 0
