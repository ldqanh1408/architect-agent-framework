"""New workspace defaults. No legacy reader is loaded on the runtime path."""

def initial_config(workspace_id, reviewer, *, profile=None, preset=None):
    mode = "enforce" if preset == "governed-team" else "advisory"
    policy = {
        "mode": mode,
        "reviewers": [reviewer] if isinstance(reviewer, str) else list(reviewer),
        "require_human_acceptance": True,
        "max_rejected_rounds": 2,
        "allow_waivers": False,
        "require_requirement_obligations": True,
        "require_system_review": True,
    }
    if preset == "solo-author":
        policy["runtime"] = {
            "max_tasks": 200,
            "max_concurrency": 4,
            "max_task_attempts": 2,
            "deadline_seconds": 86400,
            "lease_seconds": 1800,
            "first_run_gate": "auto",
        }
    elif preset == "governed-team":
        policy["runtime"] = {
            "max_tasks": 200,
            "max_concurrency": 4,
            "max_task_attempts": 2,
            "deadline_seconds": 86400,
            "lease_seconds": 1800,
            "first_run_gate": "approve",
        }
    cfg = {
        "version": 1,
        "workspace_id": workspace_id,
        "artifacts": {},
        "obligations": [],
        "policy": policy,
        "control_directories": [".architect", ".architect-runtime", ".architect-build"],
    }
    if profile in {"seed", "minimal", "standard", "maximal", "portfolio"}:
        cfg["selected_profile"] = profile
    return cfg


def initialize(root, workspace_id, reviewer, *, profile=None, preset=None, allow_existing_sources=False):
    """Initialize a new directory. Existing input requires separate migration unless allow_existing_sources=True."""
    from pathlib import Path
    import yaml
    from .model import SddError
    from .parsing import relative_path
    from .schema import WORKSPACE, validate
    from .storage import atomic_write
    from .workspace import CONFIG, _IGNORED_DIRS, _IGNORED_FILES
    root = Path(root)
    if root.is_symlink() or any(parent.is_symlink() for parent in root.parents):
        raise SddError("WORKSPACE_SYMLINK", "Select a regular new directory")
    if root.exists() and not root.is_dir():
        raise SddError("WORKSPACE_NOT_EMPTY", "Initialize a new empty directory")
    if (root / CONFIG).exists():
        raise SddError("WORKSPACE_NOT_EMPTY", "Workspace is already initialized")
    if root.exists() and any(root.iterdir()) and not allow_existing_sources:
        raise SddError("WORKSPACE_NOT_EMPTY", "Initialize a new empty directory")
    config = initial_config(workspace_id, reviewer, profile=profile, preset=preset)
    if allow_existing_sources and root.exists():
        attachments = []
        for item in sorted(root.iterdir()):
            if item.name in _IGNORED_DIRS or item.name in _IGNORED_FILES or item.name == CONFIG:
                continue
            if item.is_file():
                attachments.append(relative_path(item.name))
        if attachments:
            config["attachments"] = attachments
    validate(config, WORKSPACE)
    root.mkdir(parents=True, exist_ok=True)
    atomic_write(root / CONFIG, yaml.safe_dump(config, sort_keys=False, allow_unicode=True).encode())
    atomic_write(root / ".sdd" / ".gitignore", b"*.lock\n")
    return {"status": "INCOMPLETE", "workspace": str(root.resolve()), "next_action": "register artifacts and obligations"}
