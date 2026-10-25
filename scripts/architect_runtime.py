#!/usr/bin/env python3
"""Launcher for the architect runtime, shared by every harness.

Finds `architect_framework` — a checkout named by `ARCHITECT_FRAMEWORK_HOME`, an
ancestor of this plugin when it is loaded straight from the repository, the
marketplace clone, `~/.architect-framework/host-config.json`, or an installed package —
and runs `runtime <args>`.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _state_dir() -> Path:
    return Path(
        os.environ.get("ARCHITECT_STATE_HOME")
        or os.environ.get("ARCHITECT_HOME")
        or (Path.home() / ".architect-framework")
    )


def register_home(repo_root: Path | None = None) -> dict[str, str]:
    """Write `~/.architect-framework/host-config.json` so any harness (`claude`, `codex`, `dsh`) finds the framework root (ISS-34 / WO-R3.6)."""
    here = Path(__file__).resolve()
    if repo_root:
        root = Path(repo_root).resolve()
    elif len(here.parents) > 3 and is_framework(here.parents[3]):
        root = here.parents[3]
    else:
        root = here.parents[1]
    plugin_dir = root / "plugins" / "architect-agent-framework"
    state = _state_dir()
    state.mkdir(parents=True, exist_ok=True)
    cfg = {
        "framework_home": str(root),
        "plugin_root": str(plugin_dir if plugin_dir.is_dir() else root),
        "python_executable": sys.executable,
    }
    (state / "host-config.json").write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8", newline="\n")
    return cfg


def framework_homes() -> list[str]:
    """Where a checkout of the framework may be, most specific first (ISS-34 / WO-R3.6)."""
    here = Path(__file__).resolve()
    candidates: list[Path] = []
    if os.environ.get("ARCHITECT_FRAMEWORK_HOME"):
        candidates.append(Path(os.environ["ARCHITECT_FRAMEWORK_HOME"]))
    for env_key in ("CLAUDE_PLUGIN_ROOT", "PLUGIN_ROOT", "CODEX_PLUGIN_ROOT", "DSH_PLUGIN_ROOT"):
        val = os.environ.get(env_key)
        if val:
            p = Path(val).resolve()
            candidates.append(p)
            if len(p.parents) >= 2:
                candidates.append(p.parents[1])
    if len(here.parents) > 3:
        candidates.append(here.parents[3])  # <clone>/plugins/<plugin>/scripts/<this file>
    if len(here.parents) > 1:
        candidates.append(here.parents[1])  # self-contained <plugin>/ with embedded architect_framework & vendor
    marketplace = own_marketplace(here)
    if marketplace:
        candidates.append(Path.home() / ".claude" / "plugins" / "marketplaces" / marketplace)
    host_cfg = _state_dir() / "host-config.json"
    if host_cfg.is_file():
        try:
            data = json.loads(host_cfg.read_text(encoding="utf-8"))
            if data.get("framework_home"):
                candidates.append(Path(data["framework_home"]))
        except (OSError, ValueError):
            pass
    seen: set[str] = set()
    valid: list[str] = []
    for c in candidates:
        s = str(c)
        if s not in seen and is_framework(c):
            seen.add(s)
            valid.append(s)
    return valid


def own_marketplace(here: Path) -> str | None:
    """The marketplace this copy was installed from: `…/plugins/cache/<marketplace>/<plugin>/<version>/scripts/`."""
    root = Path(os.environ["CLAUDE_PLUGIN_ROOT"]).resolve() if os.environ.get("CLAUDE_PLUGIN_ROOT") else here.parents[1]
    parts = root.parts
    if len(parts) >= 4 and parts[-4] == "cache":
        return parts[-3]
    return None


def is_framework(path: Path) -> bool:
    """A checkout of this framework: its package, and a pyproject that names it."""
    try:
        if not (path / "architect_framework" / "runtime" / "__init__.py").is_file():
            return False
        text = (path / "pyproject.toml").read_text(encoding="utf-8")
    except OSError:
        return False
    return 'name = "architect-agent-framework"' in text


#: Probe exit codes: the framework of the plugin's own version, only another version, none.
PROBE_MATCH, PROBE_OTHER_VERSION, PROBE_MISSING = 0, 10, 1
#: Set when running this file in an environment built from the package
#: index: the installed package is the one to use, whatever checkout lies around.
ENV_USE_INSTALLED = "ARCHITECT_USE_INSTALLED"
#: Commands that do not load the core engine.
_LIGHT = frozenset({"hook", "skills", "cli", "decision", "--help", "--version"})


def plugin_version() -> str | None:
    """The version in this plugin's manifest; the framework it runs must match it."""
    root = Path(__file__).resolve().parents[1]
    for manifest in (root / ".claude-plugin" / "plugin.json", root / ".codex-plugin" / "plugin.json"):
        try:
            return str(json.loads(manifest.read_text(encoding="utf-8"))["version"])
        except (OSError, ValueError, KeyError):
            continue
    return None


def checkout_version(path: Path) -> str | None:
    try:
        return (path / "VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        return None


def installed_version() -> str | None:
    try:
        from importlib.metadata import PackageNotFoundError, version
    except ImportError:  # pragma: no cover - Python < 3.8
        return None
    try:
        return version("architect-agent-framework")
    except PackageNotFoundError:
        return None


def needs(command: str) -> tuple[str, ...]:
    """The modules `command` imports beyond the framework itself."""
    mods = ("yaml", "pydantic", "packaging")
    if command not in _LIGHT:
        mods += ("cryptography", "httpx", "markdown_it", "jsonschema")
    return mods


def versions_match(actual, expected):
    if not actual or not expected:
        return False
    try:
        from packaging.version import Version
        return Version(actual) == Version(expected)
    except (ImportError, ValueError, TypeError):
        return False


def _importable(mods: tuple[str, ...]) -> bool:
    import importlib.util

    try:
        return all(importlib.util.find_spec(m) is not None for m in mods)
    except (ModuleNotFoundError, ValueError):
        return False


def _choose() -> tuple[str | None, int]:
    want = plugin_version()
    if os.environ.get(ENV_USE_INSTALLED):
        have = installed_version()
        return None, PROBE_MATCH if versions_match(have, want) else PROBE_OTHER_VERSION if have else PROBE_MISSING
    homes = framework_homes()
    for home in homes:
        if want is None or versions_match(checkout_version(Path(home)), want):
            return home, PROBE_MATCH
    have = installed_version()
    if have is not None and (want is None or versions_match(have, want)):
        return None, PROBE_MATCH
    if homes:
        return homes[0], PROBE_OTHER_VERSION
    if have is not None:
        return None, PROBE_OTHER_VERSION
    return None, PROBE_MISSING


def probe(command: str) -> int:
    """Whether this interpreter can run `command`: :data:`PROBE_MATCH`, :data:`PROBE_OTHER_VERSION` or :data:`PROBE_MISSING`."""
    home, code = _choose()
    if code == PROBE_MISSING:
        return code
    if home is not None:
        sys.path.insert(0, home)
        sys.path.insert(1, str(Path(home) / "vendor" / "sdd-agent"))
    return code if _importable(needs(command)) else PROBE_MISSING


def _locate() -> bool:
    """Put the chosen framework on the import path (:func:`_choose`); warn once when its version differs."""
    home, code = _choose()
    if code == PROBE_MISSING:
        return False
    if home is not None:
        sys.path.insert(0, home)
        sys.path.insert(1, str(Path(home) / "vendor" / "sdd-agent"))
    if code == PROBE_OTHER_VERSION:
        _warn_version_once(home)
    return True


def _warn_version_once(home: str | None) -> None:
    want = plugin_version()
    have = checkout_version(Path(home)) if home else installed_version()
    state = _state_dir()
    mark = state / f".version-warned-{want}-{have}"
    if mark.exists():
        return
    sys.stderr.write(f"architect-runtime: the framework found ({have}, {home or 'installed package'}) is not the "
                     f"version this plugin was released with ({want}); install uv to run the matching one.\n")
    try:
        state.mkdir(parents=True, exist_ok=True)
        mark.touch()
    except OSError:
        pass


def main(argv: list[str]) -> int:
    os.environ.setdefault("PYTHONUTF8", "1")
    if argv[:1] == ["--register-home"]:
        target = Path(argv[1]) if len(argv) > 1 else None
        print(json.dumps(register_home(target), ensure_ascii=False))
        return 0
    if argv[:1] == ["--bootstrap"]:
        return bootstrap(argv[1:])
    if argv[:1] == ["--probe"]:
        return probe(argv[1] if len(argv) > 1 else "")
    if not _locate():
        from_error = "Matching architect runtime unavailable; install the supplied wheel or set ARCHITECT_PYTHON"
        if argv[:1] == ["hook"]:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                    "permissionDecisionReason": from_error}}))
            return 0
        print("architect-runtime: " + from_error, file=sys.stderr)
        return 3
    from architect_framework.launcher import main as launch
    return launch(argv)


def bootstrap(argv: list[str]) -> int:
    """Portable manifest entry point; Python is required, runtime dependencies are optional."""
    here = Path(__file__).resolve()
    env = {**os.environ, "PYTHONPATH": "", "PYTHONSAFEPATH": "1", "PYTHONUTF8": "1"}
    override = os.environ.get("ARCHITECT_PYTHON")
    try:
        if override:
            return subprocess.run([override, str(here), *argv], env=env).returncode
        command = argv[0] if argv else ""
        code = probe(command)
        if code == PROBE_MATCH:
            return main(argv)
        uv = shutil.which("uv")
        if uv:
            extras = [] if command in {"hook", "skills", "cli"} else ["console", "sdd"]
            if command not in {"hook", "skills", "cli", "console", "sdd"}:
                extras.insert(0, "runtime")
            homes = framework_homes()
            home = Path(homes[0]) if homes else None
            spec = os.environ.get("ARCHITECT_PACKAGE_SPEC")
            if home is None or spec:
                want = plugin_version()
                if not spec and not want:
                    raise RuntimeError("Plugin version unavailable; repair the plugin manifest")
                suffix = f"[{','.join(extras)}]" if extras else ""
                spec = spec or f"architect-agent-framework{suffix}=={want}"
                env[ENV_USE_INSTALLED] = "1"
                args = [uv, "run", "--quiet", "--no-project", "--with", spec]
            elif not (home / "setup.py").is_file() and not (home / "uv.lock").is_file():
                deps = ["pyyaml>=6.0.1", "jsonschema>=4.22.0", "pydantic>=2.7.0", "packaging>=24.0"]
                if "console" in extras or "sdd" in extras:
                    deps.extend(["cryptography>=42.0.0", "markdown-it-py>=3.0.0", "httpx>=0.27.0"])
                args = [uv, "run", "--quiet", "--no-project"]
                for dep in deps:
                    args.extend(["--with", dep])
            else:
                plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA")
                environment = (os.environ.get("ARCHITECT_VENV") or
                               str(Path(plugin_data) / "venv" if plugin_data else Path.home() / ".architect-framework/venv"))
                env["UV_PROJECT_ENVIRONMENT"] = environment
                args = [uv, "run", "--quiet"]
                if (home / "uv.lock").is_file():
                    args.append("--frozen")
                args.extend(["--project", str(home)])
                for extra in extras:
                    args.extend(["--extra", extra])
            return subprocess.run([*args, "python", str(here), *argv], env=env).returncode
        if code == PROBE_OTHER_VERSION:
            return main(argv)
        raise RuntimeError("No usable runtime dependencies; install uv or set ARCHITECT_PYTHON")
    except (OSError, RuntimeError) as exc:
        message = "architect-runtime: " + str(exc)
        print(message, file=sys.stderr)
        if argv[:1] == ["hook"]:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                    "permissionDecisionReason": message}}))
            return 0
        return 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
