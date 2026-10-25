"""One lightweight workspace discriminator, also safe on the hook path."""
from pathlib import Path


def workspace_mode(workspace) -> str:
    marker = Path(workspace) / "sdd-workspace.yml"
    return "core" if marker.exists() or marker.is_symlink() else "unconfigured"


def classify(workspace):
    """Read the workspace state. Classification creates no files."""
    root = Path(workspace)
    marker = root / "sdd-workspace.yml"
    def result(state, code, action, **details):
        return {"state": state, "code": code, "next_action": action, **details}
    if root.is_symlink() or marker.is_symlink():
        return result("invalid", "WORKSPACE_SYMLINK", "Select a regular directory and marker")
    if not root.exists() or root.is_dir() and not any(root.iterdir()):
        return result("uninitialized", "WORKSPACE_UNINITIALIZED", "Initialize a new empty workspace explicitly")
    if not root.is_dir(): return result("invalid", "WORKSPACE_NOT_DIRECTORY", "Select a directory")
    if not marker.exists():
        return result("migration-required", "WORKSPACE_MIGRATION_REQUIRED", "Plan migration into a separate destination")
    try:
        from sdd_core.model import SddError
    except ImportError as error:
        return result("unavailable", "SDD_ENGINE_UNAVAILABLE", "Install or vendor sdd_core", message=str(error))
    try:
        from sdd_core.parsing import parse_yaml
        data = parse_yaml(marker.read_text(encoding="utf-8"))
        if not isinstance(data, dict): raise ValueError("Marker must be a record")
        if data.get("version") != 1:
            return result("unsupported", "WORKSPACE_VERSION_UNSUPPORTED", "Use a compatible runtime or explicit migration")
        from sdd_core.workspace import capture
        capture(root)
    except (ValueError, OSError, UnicodeError, SddError) as error:
        return result("invalid", getattr(error, "code", "WORKSPACE_INVALID"), "Repair the reported workspace error", message=str(error))
    return result("current", "WORKSPACE_CURRENT", "Inspect or propose a revision-bound candidate", version=1)
