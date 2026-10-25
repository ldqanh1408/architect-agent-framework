from __future__ import annotations

from pathlib import Path
import os
import stat
import threading

from . import __version__
from .model import Finding, SddError, Snapshot, Status, digest
from .parsing import parse_artifact, parse_yaml, relative_path
from .schema import WORKSPACE, validate

CONFIG = "sdd-workspace.yml"
TEXT_SUFFIXES = {".md", ".markdown", ".yaml", ".yml", ".json", ".txt", ".mmd", ".puml"}

_SNAPSHOT_CACHE_LOCK = threading.Lock()
_SNAPSHOT_CACHE: dict[str, tuple[tuple[tuple[str, int, int], ...], Snapshot]] = {}


def build_snapshot(files: dict[str, str], engine_version=__version__) -> Snapshot:
    if CONFIG not in files:
        raise SddError("WORKSPACE_NOT_INITIALIZED", f"Missing {CONFIG}; use sdd init or sdd migrate --dry-run")
    config = parse_yaml(files[CONFIG])
    validate(config, WORKSPACE)
    artifacts, findings, paths, identities = {}, [], {}, set()
    attachments = {relative_path(p) for p in config.get("attachments", [])}
    controls = set(config.get("control_directories", []))
    for identifier, meta in config["artifacts"].items():
        path = relative_path(meta["path"])
        if path.split("/", 1)[0] in controls:
            findings.append(Finding("CONTROL_PATH_OVERLAP", path, (identifier,)))
        normalized = path.casefold()
        if normalized in paths:
            findings.append(Finding("PATH_COLLISION", f"{path} collides with {paths[normalized]}", (identifier,)))
        paths[normalized] = path
        if identifier in identities:
            findings.append(Finding("DUPLICATE_ID", identifier, (identifier,)))
        identities.add(identifier)
        if path not in files:
            findings.append(Finding("ARTIFACT_MISSING", path, (identifier,)))
            continue
        try:
            artifact = parse_artifact(identifier, meta, files[path])
            for clause_id in artifact.clauses:
                if clause_id in identities or clause_id in config["artifacts"]:
                    findings.append(Finding("DUPLICATE_ID", clause_id, (identifier, clause_id)))
                identities.add(clause_id)
            artifacts[identifier] = artifact
        except SddError as exc:
            findings.append(Finding(exc.code, str(exc), (identifier,), exc.status))
    declared = {m["path"] for m in config["artifacts"].values()}
    for path in files:
        if path != CONFIG and path not in declared and path not in attachments:
            findings.append(Finding("UNREGISTERED_ARTIFACT", f"Register identity, kind and owner for {path}", (path,), Status.INCOMPLETE))
    for collection in (config["obligations"], config.get("external_sources", [])):
        seen = set()
        for item in collection:
            if item["id"] in seen:
                findings.append(Finding("DUPLICATE_ID", item["id"], (item["id"],)))
            seen.add(item["id"])
    if not config["artifacts"]:
        findings.append(Finding("EMPTY_INVENTORY", "No artifacts have been declared", (), Status.INCOMPLETE))
    payload = {"files": files, "engine_version": engine_version}
    return Snapshot(digest(payload), dict(files), config, artifacts, findings, engine_version)


_IGNORED_DIRS = {
    ".sdd", ".git", ".venv", "venv", "node_modules", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".hypothesis",
    ".idea", ".vscode", ".claude", ".codex", ".dsh", ".agents",
    ".opencode", ".cursor", ".tox", ".eggs", ".architect", ".architect-runtime", ".architect-build",
}
_IGNORED_FILES = {".gitignore", ".gitattributes", ".DS_Store", "Thumbs.db", ".env"}


def fast_stat_fingerprint(root: Path, controls=()) -> tuple[tuple[str, int, int], ...] | None:
    """Fast O(N) stat signature ((rel_path, size, mtime_ns), ...) without reading file bodies (WO-R5.1)."""
    root = Path(root).resolve()
    if not root.is_dir():
        return None
    sig: list[tuple[str, int, int]] = []
    try:
        for parent, directories, files in os.walk(root, followlinks=False):
            excluded = _IGNORED_DIRS | (set(controls) if Path(parent) == root else set())
            directories[:] = sorted(d for d in directories if d not in excluded)
            for directory in directories:
                if (Path(parent) / directory).is_symlink():
                    return None
            for name in sorted(files):
                if name in _IGNORED_FILES:
                    continue
                file = Path(parent) / name
                if file.is_symlink():
                    return None
                st = file.stat()
                if not stat.S_ISREG(st.st_mode):
                    return None
                rel = relative_path(file.relative_to(root).as_posix())
                sig.append((rel, st.st_size, st.st_mtime_ns))
    except OSError:
        return None
    return tuple(sig)


def _inventory(root: Path, maximum: int, controls=(), *, single_pass: bool = False) -> dict[str, str]:
    result = {}
    for parent, directories, files in os.walk(root, followlinks=False):
        excluded = _IGNORED_DIRS | (set(controls) if Path(parent) == root else set())
        directories[:] = sorted(d for d in directories if d not in excluded)
        for directory in directories:
            if (Path(parent) / directory).is_symlink():
                raise SddError("SYMLINK_UNSUPPORTED", str(Path(parent) / directory))
        for name in sorted(files):
            if name in _IGNORED_FILES:
                continue
            file = Path(parent) / name
            relative = relative_path(file.relative_to(root).as_posix())
            if file.is_symlink():
                raise SddError("SYMLINK_UNSUPPORTED", relative)
            if not stat.S_ISREG(file.stat().st_mode):
                raise SddError("FILE_TYPE_UNSUPPORTED", relative)
            if file.stat().st_size > maximum:
                raise SddError("FILE_TOO_LARGE", relative, Status.INCOMPLETE)
            try:
                before = file.stat()
                raw = file.read_bytes()
                after = file.stat()
            except FileNotFoundError as exc:
                raise SddError("WORKSPACE_MUTATING", relative, Status.STALE) from exc
            if not single_pass and (before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                raise SddError("WORKSPACE_MUTATING", relative, Status.STALE)
            try:
                result[relative] = raw.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise SddError("BINARY_UNSUPPORTED", f"{relative}: keep binary assets outside the v1 spec workspace", Status.INCOMPLETE) from exc
    return result


_ORIG_INVENTORY = _inventory


def capture(root: Path, attempts: int = 3, *, use_cache: bool = True, allow_live_read: bool = False) -> Snapshot:
    root = Path(root).resolve()
    if not root.is_dir():
        raise SddError("WORKSPACE_MISSING", str(root))
    cache_key = str(root)
    for _ in range(attempts):
        try:
            marker = root / CONFIG
            if marker.is_symlink():
                raise SddError("SYMLINK_UNSUPPORTED", CONFIG)
            if use_cache and _inventory is _ORIG_INVENTORY and marker.is_file():
                with _SNAPSHOT_CACHE_LOCK:
                    cached = _SNAPSHOT_CACHE.get(cache_key)
                if cached is not None:
                    cached_controls = cached[1].config.get("control_directories", [])
                    sig1 = fast_stat_fingerprint(root, cached_controls)
                    if sig1 is not None and cached[0] == sig1:
                        return cached[1]
            config_text = marker.read_bytes().decode("utf-8") if marker.is_file() else None
            config = parse_yaml(config_text) if config_text is not None else {}
            if config_text is not None:
                validate(config, WORKSPACE)
            controls = config.get("control_directories", [])
            first = _inventory(root, 8 * 1024 * 1024, controls, single_pass=True) if allow_live_read else _inventory(root, 8 * 1024 * 1024, controls)
            second = first if allow_live_read else _inventory(root, 8 * 1024 * 1024, controls)
            if config_text is not None and second.get(CONFIG) != config_text and not allow_live_read:
                continue
        except SddError as exc:
            if exc.code == "WORKSPACE_MUTATING":
                continue
            raise
        if first == second:
            snapshot = build_snapshot(second)
            maximum = snapshot.config["policy"].get("max_file_bytes", 2 * 1024 * 1024)
            for name, text in second.items():
                if len(text.encode()) > maximum:
                    raise SddError("FILE_TOO_LARGE", name, Status.INCOMPLETE)
            sig = fast_stat_fingerprint(root, controls)
            if sig is not None:
                with _SNAPSHOT_CACHE_LOCK:
                    _SNAPSHOT_CACHE[cache_key] = (sig, snapshot)
            return snapshot
    raise SddError("WORKSPACE_MUTATING", "Unable to capture a stable candidate; retry after edits settle", Status.STALE)


def diff(before: Snapshot | None, after: Snapshot) -> dict:
    old = before.artifacts if before else {}
    new = after.artifacts
    added, deleted = sorted(new.keys() - old.keys()), sorted(old.keys() - new.keys())
    updated, renamed, metadata = [], [], []
    for identifier in sorted(old.keys() & new.keys()):
        if old[identifier].revision != new[identifier].revision:
            updated.append(identifier)
        if old[identifier].path != new[identifier].path:
            renamed.append(identifier)
        if old[identifier].metadata != new[identifier].metadata:
            metadata.append(identifier)
    return {"added": added, "deleted": deleted, "updated": updated, "renamed": renamed, "metadata_changed": metadata,
            "config_changed": before is None or before.config != after.config,
            "changed": sorted(set(added + deleted + updated + renamed + metadata))}
