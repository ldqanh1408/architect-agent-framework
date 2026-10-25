"""Host pre-tool guard for current proposals, engine state, and human authority.

Direct writes to a marked workspace use revision-bound core APIs. Human decisions
and key enrollment require the human channel. The hook loads no retired run ledger
or graph sandbox. It is a host guard, not an OS process isolation boundary.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from architect_framework.i18n import tr, trf

WRITE_TOOLS = frozenset({
    "Write", "Edit", "MultiEdit", "NotebookEdit", "write_file", "edit_file", "apply_patch",
    "write", "edit", "multiedit", "notebookedit", "create_file", "replace_in_file",
})
SHELL_TOOLS = frozenset({
    "Bash", "PowerShell", "shell", "exec_command", "local_shell",
    "pwsh", "bash", "sh", "zsh", "cmd", "terminal",
})
_WRITE_TOOLS_LOWER = frozenset(t.lower() for t in WRITE_TOOLS)
_SHELL_TOOLS_LOWER = frozenset(t.lower() for t in SHELL_TOOLS)
# Retired authority paths are immutable. Recognizing their names loads no old reader.
_RETIRED_AUTHORITY = {"human-gate-ledger.yml", "agent-question-ledger.yml"}
_LEDGERS = "(?:" + "|".join(re.escape(name) for name in sorted(_RETIRED_AUTHORITY)) + ")"
#: Reading a ledger is fine; deciding, or writing one by shell, is not. This
#: guards against an agent approving itself out of habit — a determined local
#: process can still write the file, which is why the gate also refuses any row
#: whose `by` is a skill id or a process name.
#: specification (review console plan section 2.3) closed three ways around it: `approve-tree` and
#: `human_decision record` were not matched, the TTY bypass variable could be set by
#: the agent itself, and nothing stopped a shell write into `decisions/` or into the
#: reviewers file that is the passkey trust root.
_PROTECTED = (r"(?:" + _LEDGERS + r"|\bdecisions(?:[\\/]|\b)|\.architect[\\/]reviewers\.yml"
              r"|\.architect-framework\b|\.architect-runtime\b|\.sdd(?:[\\/]|\b))")
_HUMAN_ONLY = re.compile(
    r"(?i)runtime(?:\.sh)?\s+(approve|approve-tree|answer|defer)\b"
    r"|human_decision\s+record\b"
    r"|runtime(?:\.sh)?\s+decision\s+record\b"
    r"|ARCHITECT_ALLOW_NONTTY_DECISION"
    r"|console\s+serve\b[^\n]*--enroll"
    r"|console\s+trust-reviewers\b"
    r"|(?:sdd(?:_core(?:\.cli)?)?|sdd_cli\.py)\s+(accept|decision|recover|host-init|host-recover)\b"
    # EMB-08: opening the workspace to a remote host is the person's call, never the agent's.
    r"|runtime(?:\.sh)?\s+mcp\b[^\n]*--http"
    r"|(>>?|\btee\b|sed\s+-i|Set-Content|Out-File|Add-Content|\bcp\b|\bmv\b|\brm\b|\bln\b|\bdel\b"
    r"|Copy-Item|Move-Item|Remove-Item|New-Item|open\()[^\n]*" + _PROTECTED
    + r"|" + _PROTECTED + r"[^\n]*(Set-Content|Out-File|Add-Content)"
)
#: Write targets only a person's console or terminal may produce.
_PROTECTED_WRITE = re.compile(r"(^|[\\/])decisions[\\/]|(^|[\\/])\.architect[\\/]reviewers\.yml$", re.IGNORECASE)
_PROTECTED_NAMES = frozenset(_RETIRED_AUTHORITY)
_STREAM = re.compile(r"::\$DATA$", re.IGNORECASE)


def canonical(target: Path) -> Path:
    """The path the file system will write, for matching protected names (LP 20, H-2).

    Windows and macOS file systems ignore case, Windows drops trailing dots and
    spaces and accepts an `::$DATA` stream suffix, and a symlinked folder leads
    somewhere else: `Human-Gate-Ledger.yml.` is the ledger. Resolve what exists,
    strip what the file system strips; callers compare case-folded.
    """
    try:
        target = target.resolve()
    except OSError:
        pass
    parts = [_STREAM.sub("", part).rstrip(" .") or part for part in target.parts]
    return Path(*parts)
_PATCH_FILE = re.compile(r"^\*\*\* (Add|Update|Delete) File: (.+)$")


@dataclass(frozen=True)
class WriteOperation:
    """A host write, including both sides of a move. This grants no authority."""

    kind: str
    path: str
    destination: str | None = None


def _path(value: Any) -> str:
    if not isinstance(value, str) or not value.strip() or any(c in value for c in "\x00\r\n"):
        raise ValueError("missing or malformed write path")
    return value.strip()


def write_operations(tool: str, data: dict[str, Any]) -> list[WriteOperation]:
    if tool.lower() != "apply_patch":
        paths = [_path(data[k]) for k in ("file_path", "path", "notebook_path") if k in data]
        if "edits" in data:
            if not isinstance(data["edits"], list) or not data["edits"]:
                raise ValueError("malformed multi-edit")
            for edit in data["edits"]:
                if not isinstance(edit, dict):
                    raise ValueError("malformed multi-edit item")
                paths.extend(_path(edit[k]) for k in ("file_path", "path", "notebook_path") if k in edit)
        if not paths:
            raise ValueError("write tool did not declare a target")
        return [WriteOperation("write", path) for path in dict.fromkeys(paths)]
    patch = data.get("patch", data.get("input"))
    if not isinstance(patch, str) or len(patch.encode("utf-8")) > 2 * 1024 * 1024:
        raise ValueError("missing or oversized patch")
    lines = patch.strip().splitlines()
    if len(lines) < 3 or lines[0] != "*** Begin Patch" or lines[-1] != "*** End Patch":
        raise ValueError("unsupported patch envelope")
    operations: list[WriteOperation] = []
    current: WriteOperation | None = None
    moved = False
    for line in lines[1:-1]:
        match = _PATCH_FILE.fullmatch(line)
        if match:
            current = WriteOperation(match[1].lower(), _path(match[2]))
            operations.append(current)
            moved = False
        elif line.startswith("*** Move to: "):
            if current is None or current.kind != "update" or moved:
                raise ValueError("move must belong to an update")
            current = WriteOperation("move", current.path, _path(line[len("*** Move to: "):]))
            operations[-1] = current
            moved = True
        elif current is None or (line.startswith("*** ") and line != "*** End of File"):
            raise ValueError("unrecognized patch operation")
        elif current.kind == "delete" and line:
            raise ValueError("unexpected delete body")
        elif current.kind == "add" and not line.startswith("+"):
            raise ValueError("unexpected add body")
        elif current.kind in {"update", "move"} and line and not line.startswith((" ", "+", "-", "@@", "*** End of File")):
            raise ValueError("unexpected update body")
    if not operations:
        raise ValueError("empty patch")
    return operations


def _deny(reason: str) -> dict[str, Any]:
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                   "permissionDecisionReason": reason}}


#: Shell commands that only read. While a job is in flight every other command asks the
#: person: guessing which commands write lost to `python x.py` on a script the agent had
#: just written into its own folder (LP 20, M-1). An allow list fails closed instead, and
#: it holds only commands with no option that writes a file or runs another program:
#: not `sort -o`, `env cmd`, `rg --pre`, nor git, whose config can name a program to run.
_READ_ONLY_COMMANDS = frozenset({
    "ls", "dir", "cat", "type", "head", "tail", "wc", "pwd", "grep", "egrep", "fgrep", "findstr", "echo",
    "printf", "true", "basename", "dirname", "realpath", "whoami",
    "get-childitem", "gci", "get-content", "gc", "get-item", "gi", "select-string", "sls", "test-path",
    "resolve-path", "get-location", "gl",
})
#: Anything that redirects, substitutes, groups or expands makes a command more than the
#: read it names; such a part is never read-only, whatever its first word.
_SHELL_ESCAPE = re.compile(r"[<>`(){}%$]")
_PARTS = re.compile(r"&&|\|\||[;&|\r\n]")


def read_only(command: str) -> bool:
    """True when every part of `command` is a known read with nothing that redirects or substitutes."""
    text = normalise(command)
    if _SHELL_ESCAPE.search(text):
        return False
    parts = [p.strip() for p in _PARTS.split(text) if p.strip()]
    for part in parts:
        words = part.split()
        # ASCII names only: casefold() would take a lookalike letter for the real one (I-2).
        if words[0].isascii() and words[0].lower() == "git":
            if len(words) < 2 or words[1] not in {"status", "diff", "log", "show", "branch"}:
                return False
            if any(w in {"-c", "--exec-path", "--upload-pack", "--output", "-o"} or w.startswith("-c") or w.startswith("--exec-path=") or w.startswith("--output=") for w in words[1:]):
                return False
            if words[1] == "branch":
                # A subcommand is not a read capability: -D/-m/-u and even a
                # bare branch name mutate repository state.
                if any(w not in {"--show-current", "--list", "--all", "-a", "--remotes", "-r", "--no-color"} for w in words[2:]):
                    return False
            if any(w.startswith(("--ext-diff", "--textconv", "--output", "--exec", "--config", "--paginate")) for w in words[2:]):
                return False
        elif not (words[0].isascii() and words[0].lower() in _READ_ONLY_COMMANDS):
            return False
        # A UNC path reads from another host and sends it this machine's credentials (I-1),
        # however PowerShell binds it: `-Path:\\h\s`, `x,\\h\s`. So anywhere in the part.
        if "//" in part or "\\\\" in part:
            return False
    return bool(parts)


def _framework_homes() -> tuple[Path, ...]:
    from architect_framework import skillpacks
    from architect_framework.runtime.host_state import state_home
    return skillpacks.home_dir(), state_home()


def _within(path: Path, root: Path) -> bool:
    try:
        p, r = path.resolve(), root.resolve()
    except OSError:
        return False
    if os.name == "nt":
        p, r = Path(str(p).casefold()), Path(str(r).casefold())
    return p == r or r in p.parents


def _targets(tool_input: dict[str, Any], tool: str = "apply_patch") -> list[str]:
    return [p for operation in write_operations(tool, tool_input)
            for p in (operation.path, operation.destination) if p is not None]


#: A line continuation in sh (`\`), PowerShell (backtick) or cmd (`^`) followed by a newline.
_CONTINUATION = re.compile(r"[\\`^]\r?\n")


def normalise(command: str) -> str:
    """The command as the shell will run it, for matching: continuations joined, quotes dropped.

    `runtime "mcp" --http` and `runtime mcp \\<newline> --http` run the same program as the
    plain spelling; the guard must see them as the same (EMB-08 review). Prefix
    abbreviations (`--ht`) are closed at the parser instead (`allow_abbrev=False`).
    """
    return re.sub(r"[\"']", "", _CONTINUATION.sub(" ", command))


def _core_api(command: str, env: dict[str, str]) -> bool:
    """Allow one trusted engine or read-only console invocation."""
    import shlex
    roots = {name: env[name] for name in ("CLAUDE_PLUGIN_ROOT", "PLUGIN_ROOT") if env.get(name)}
    for name in roots:
        command = re.sub(r"\$(?:\{" + name + r"\}|" + name + r"\b)", "__ARCHITECT_" + name + "__", command)
    command = re.sub(r"\s+&\s*$", "", command)  # one background server/API, no shell chain
    if _SHELL_ESCAPE.search(command) or _PARTS.search(command):
        return False
    try:
        lexer = shlex.shlex(command, posix=True)
        lexer.whitespace_split = True
        lexer.commenters = ""
        if os.name == "nt":
            lexer.escape = ""  # Preserve native drive paths passed by cmd/PowerShell.
        words = list(lexer)
    except ValueError:
        return False
    via_launcher = False
    via_framework_cli = False
    if len(words) > 2 and words[0] in {"sh", "bash", "python", "python3", "python.exe", "py"} and words[1] != "-m":
        from architect_framework import contracts
        script_name = "runtime.sh" if words[0] in {"sh", "bash"} else "architect_runtime.py"
        trusted = [
            contracts.REPO_ROOT / "plugins/architect-agent-framework/scripts" / script_name,
            contracts.REPO_ROOT / "scripts" / script_name,
        ]
        trusted.extend(Path(root) / "scripts" / script_name for root in roots.values())
        script = words[1]
        for name, root in roots.items():
            script = script.replace("__ARCHITECT_" + name + "__", root)
        if Path(script).resolve() not in {p.resolve() for p in trusted}:
            return False
        words = words[2:]
        if script_name == "architect_runtime.py" and words[:1] == ["--bootstrap"]:
            words = words[1:]
        via_launcher = True
    elif words[:1] == ["architect-runtime"]:
        words = words[1:]
        via_launcher = True
    elif words[:3] in (["python", "-m", "sdd_core"], ["python3", "-m", "sdd_core"],
                      ["python", "-m", "sdd_core.cli"], ["python3", "-m", "sdd_core.cli"]):
        words = ["sdd", *words[3:]]
    elif words[:3] in (["python", "-m", "architect_framework.launcher"],
                      ["python3", "-m", "architect_framework.launcher"]):
        words = words[3:]
        via_launcher = True
    elif words[:3] in (["python", "-m", "architect_framework.cli.main"],
                      ["python3", "-m", "architect_framework.cli.main"]):
        words = words[3:]
        via_framework_cli = True
    if via_launcher and words and words[0] not in {"sdd", "console", "skills", "cli"}:
        words = ["runtime", *words]
    if len(words) < 2:
        return False
    if words[0] == "console":
        return words[1] in {"serve", "url", "verify"} and not any(w.startswith("--en") for w in words[2:])
    if words[0] == "skills":
        return (via_launcher or via_framework_cli) and words[1] in {"status", "offer", "doctor", "explain", "list"}
    if words[0] == "cli":
        return (via_launcher or via_framework_cli) and words[1] in {"route-skills"}
    if words[0] == "runtime":
        return (via_launcher or via_framework_cli) and words[1] in {"plan", "start", "status", "next", "tick", "recheck", "scorecard", "check", "claim", "heartbeat", "complete", "control", "observe"}
    return words[0] == "sdd" and words[1] in {"status", "check", "review", "review-candidate", "language-review", "language-repair", "regression", "freshness", "report", "doctor", "observe", "reconcile", "changes", "task", "scaffold-plan", "materialize", "extract-sources", "prepare-check", "plan-waves", "freeze-digest", "probe-models", "status-probe", "execute-standalone"}


def _core_project(cwd: Path) -> bool:
    from architect_framework.sdd_bridge.mode import workspace_mode
    if any(workspace_mode(p) == "core" for p in (cwd, *cwd.parents)):
        return True
    # A markerless monorepo root can still contain the spec being edited. Opaque
    # shell writers cannot establish which descendant they will modify.
    for _root, dirs, files in os.walk(cwd, followlinks=False):
        if "sdd-workspace.yml" in files or "sdd-workspace.yml" in dirs:
            return True
        dirs[:] = [d for d in dirs if d not in {".git", ".venv", "venv", "node_modules", "__pycache__", ".sdd", "examples", "fixtures", "tests", "vendor", "plugins", "exported_skills"}]
    return False


def decide(event: dict[str, Any], *, env: dict[str, str] | None = None) -> dict[str, Any] | None:
    env = dict(os.environ if env is None else env)
    if not isinstance(event, dict) or not isinstance(event.get("tool_name"), str) or not event["tool_name"]:
        return _deny("Malformed host event: a tool name is required.")
    tool = event["tool_name"]
    tool_lower = tool.lower()
    tool_input = event.get("tool_input", {})
    if tool_lower == "apply_patch" and isinstance(tool_input, str):
        tool_input = {"input": tool_input}
    if not isinstance(tool_input, dict) or ("cwd" in event and not isinstance(event["cwd"], str)):
        return _deny("Malformed host event: tool_input must be an object and cwd a path.")
    cwd = Path(str(event.get("cwd") or env.get("CLAUDE_PROJECT_DIR") or os.getcwd()))

    if tool_lower in _SHELL_TOOLS_LOWER:
        command = tool_input.get("command", tool_input.get("cmd"))
        if not isinstance(command, str) or not command.strip():
            return _deny("Malformed shell event: command is required.")
        if _HUMAN_ONLY.search(command) or _HUMAN_ONLY.search(normalise(command)):
            return _deny(tr("Quyết định của người (approve/answer/defer) và hai ledger quyết định chỉ do người "
                         "ghi, trong terminal của chính họ. Agent không được tự duyệt hay tự trả lời."))
        if not read_only(command) and not _core_api(command, env) and _core_project(cwd):
            return _deny("Use architect_sdd_propose or the SDD CLI for this core workspace; arbitrary shell writers bypass revision and ownership checks.")
        return None
    if tool_lower not in _WRITE_TOOLS_LOWER:
        return None

    try:
        paths = _targets(tool_input, tool)
        if os.name != "nt" and any(re.match(r"^[A-Za-z]:", t) or t.startswith(("\\\\", "//")) for t in paths):
            raise ValueError("foreign absolute paths require a native host resolver")
        targets = [Path(t.replace("\\", "/")) if Path(t.replace("\\", "/")).is_absolute() else cwd / t.replace("\\", "/") for t in paths]
    except ValueError as error:
        return _deny(f"Cannot validate write operation: {error}; use a supported revision-bound proposal.")
    for target in targets:
        target = canonical(target)
        if ".sdd" in [p.casefold() for p in target.parts]:
            return _deny("Engine state is written only through SDD APIs; use architect_sdd_propose.")
        from architect_framework.sdd_bridge.mode import workspace_mode
        core_root = next((p for p in (target.parent, *target.parents) if workspace_mode(p) == "core"), None)
        if core_root is not None:
            return _deny("Use architect_sdd_propose for this core workspace so revision and ownership checks run.")
        if target.name.lower() in _PROTECTED_NAMES:
            return _deny(trf("{0} chỉ do người ghi, qua lệnh runtime chạy trong terminal của họ.", target.name))
        if _PROTECTED_WRITE.search(target.as_posix()):
            return _deny(trf("{0} là quyết định của người hoặc danh sách khoá của người duyệt; chỉ bàn duyệt (passkey) hoặc terminal của người được ghi.", target.as_posix()))
        if any(_within(target, home) for home in _framework_homes()):
            # The run records, installed skills and pinned reviewer keys: written by the
            # framework's own commands in the person's terminal, never by a tool call.
            return _deny(trf("{0} thuộc ~/.architect-framework; chỉ lệnh của framework được ghi vào đó.", target.as_posix()))


    return None


def main(stdin_text: str) -> tuple[int, str]:
    try:
        event = json.loads(stdin_text or "{}")
    except (json.JSONDecodeError, TypeError):
        return 0, json.dumps(_deny("Malformed hook JSON; the write was not authorized."))
    verdict = decide(event)
    return 0, (json.dumps(verdict, ensure_ascii=False) if verdict else "")
