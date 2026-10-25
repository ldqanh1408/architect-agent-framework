"""specification — the subprocess backlog runs in this process.

Every `role: gate` script entry used to start a Python interpreter of its own.
`gate run --phase 1` started ~45 of them, each importing yaml and the contracts
again, and a test of one gate needed a child process to see a finding.

`InProcessGate` keeps everything a subprocess entry had: the argv derived from the
script's usage line, the registry's `roll_call` values, the finding and
denominator parsers, and the runner's class rule (it is a `SubprocessGate`, so
`runner.apply_classes` still treats the script's exit code as opaque). Only the
execution changes: the script is loaded fresh and its `main()` is called here,
with `sys.argv`, `sys.path`, the working directory and both output streams set
the way the child process had them, and restored afterwards.

WHY THE SCRIPTS STAY WHERE THEY ARE
    specification set the precedent (`absorbed.py`): a script run in-process keeps every
    code, message and threshold byte-for-byte, and its path stays valid for the
    tests, skill contracts and `run_hooks.py` flags that call it. Moving the files
    would retire 60 paths through specification for no change in behaviour.

WHY A FRESH MODULE PER RUN
    One script (`check_source_ingestion.py`) does its work at import, and others
    keep module-level caches. Reusing a loaded module would run the first and
    serve the second stale answers when the next call names another workspace.
    Sibling libraries a script imports by bare name stay cached in `sys.modules`,
    as they are pure.

WHAT IS LOST
    `timeout_s` cannot stop a function call, so `GATE-TIMEOUT` is no longer raised
    for these gates. A script that crashes reports exit 1 with its traceback on
    stderr, as the interpreter did.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import re
import sys
import traceback
from pathlib import Path

from architect_framework.gates.base import GateContext, GateResult
from architect_framework.gates.subprocess_gate import SubprocessGate


def run_script(path: Path, argv: list[str], cwd: Path) -> tuple[int, str, str]:
    """`(exit code, stdout, stderr)` of `path` run as `python path *argv` from `cwd`."""
    out, err = io.StringIO(), io.StringIO()
    name = "_inprocess_" + re.sub(r"\W", "_", path.as_posix())
    saved_argv, saved_path, saved_cwd = sys.argv, list(sys.path), os.getcwd()
    code = 0
    try:
        sys.argv = [str(path), *argv]
        sys.path.insert(0, str(path.parent))
        os.chdir(cwd)
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                spec = importlib.util.spec_from_file_location(name, path)
                if spec is None or spec.loader is None:
                    raise ImportError(f"cannot load {path}")
                module = importlib.util.module_from_spec(spec)
                # A dataclass in the script resolves annotations via sys.modules[__module__].
                sys.modules[name] = module
                spec.loader.exec_module(module)
                main = getattr(module, "main", None)
                result = main() if callable(main) else 0
                code = result if isinstance(result, int) else (0 if result is None else 1)
            except SystemExit as exc:
                if exc.code is None or isinstance(exc.code, int):
                    code = exc.code or 0
                else:
                    print(exc.code, file=sys.stderr)
                    code = 1
            except Exception:  # noqa: BLE001 -- an uncaught exception: what the interpreter prints and returns
                traceback.print_exc()
                code = 1
    finally:
        sys.argv = saved_argv
        sys.path[:] = saved_path
        os.chdir(saved_cwd)
        sys.modules.pop(name, None)
    return int(code), out.getvalue(), err.getvalue()


class InProcessGate(SubprocessGate):
    """A script gate (`kind: native`, entrypoint a `.py` path) run in this process."""

    def _execute(self, argv: list[str], ctx: GateContext) -> tuple[int, str, str] | GateResult:
        # `build_argv` starts with the interpreter and the script, as a command line does.
        return run_script(self.resolved_entrypoint(ctx.repo_root), argv[2:], Path(ctx.repo_root))


__all__ = ["InProcessGate", "run_script"]
