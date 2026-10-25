"""Apply an explicit migration plan. Runtime bootstrap does not import this module."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

from .model import SddError, Status, digest
from .storage import Store, atomic_write
from .parsing import relative_path
from .workspace import CONFIG


def _check_source(source, expected):
    if not isinstance(expected, dict):
        raise SddError("MIGRATION_PLAN_INVALID", "A reviewed source manifest is required")
    root = Path(source)
    try:
        if root.is_symlink() or not root.is_dir():
            raise SddError("MIGRATION_SOURCE_CHANGED", "Source directory changed", Status.STALE)
        observed = {}
        for path in sorted(root.rglob("*")):
            if path.is_symlink():
                raise SddError("MIGRATION_SOURCE_CHANGED", "Source now contains a symlink", Status.STALE)
            if path.is_file():
                observed[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise SddError("MIGRATION_SOURCE_CHANGED", "Source is no longer readable", Status.STALE) from error
    if observed != expected:
        raise SddError("MIGRATION_SOURCE_CHANGED", "Source changed after the reviewed plan", Status.STALE)


def _check_target(destination, files, journal, store, report_bytes, complete=False):
    allowed_state = {".sdd/writer.lock", ".sdd/migration/transaction.json", ".sdd/migration.json"}
    for path in destination.rglob("*"):
        relative = path.relative_to(destination).as_posix()
        if path.is_symlink():
            raise SddError("MIGRATION_TARGET_CHANGED", relative, Status.STALE)
        if not path.is_file():
            continue
        if relative.startswith(".sdd/"):
            if relative not in allowed_state or (relative == ".sdd/migration.json" and path.read_bytes() != report_bytes):
                raise SddError("MIGRATION_TARGET_CHANGED", relative, Status.STALE)
            continue
        if relative not in files or path.read_bytes() != files[relative].encode("utf-8"):
            raise SddError("MIGRATION_TARGET_CHANGED", relative, Status.STALE)
    if store.read("migration", "transaction") != journal:
        raise SddError("MIGRATION_TARGET_CHANGED", "Migration journal changed during copy", Status.STALE)
    if complete:
        for relative, text in files.items():
            path = destination / relative_path(relative)
            if not path.is_file() or path.read_bytes() != text.encode("utf-8"):
                raise SddError("MIGRATION_TARGET_CHANGED", relative, Status.STALE)


def apply_migration_plan(source, destination, plan, resume=False, fault=None):
    from .schema import WORKSPACE, validate
    validate(plan["config"], WORKSPACE)
    if destination is None or plan["status"] == "ALREADY_MIGRATED":
        return {k: v for k, v in plan.items() if k != "files"}
    if plan["unsupported"]:
        raise SddError("MIGRATION_UNSUPPORTED", "Resolve the dry-run unsupported-file list before migration")
    _check_source(source, plan.get("source_manifest"))
    destination = Path(destination).absolute()
    if destination.resolve().is_relative_to(Path(source).resolve()):
        raise SddError("MIGRATION_WITHIN_SOURCE", "Choose a destination outside the original source tree")
    if destination.is_symlink() or any(p.is_symlink() for p in destination.parents):
        raise SddError("MIGRATION_SYMLINK", str(destination))
    if destination.exists() and not resume:
        raise SddError("MIGRATION_DESTINATION_EXISTS", "Migration writes only to a new directory")
    destination.mkdir(parents=True, exist_ok=True)
    store = Store(destination)
    files = plan["files"] | {CONFIG: yaml.safe_dump(plan["config"], sort_keys=False, allow_unicode=True)}
    binding = {"source": str(Path(source).resolve()), "plan_digest": digest(plan),
               "file_digests": {p: digest(t.encode("utf-8")) for p, t in files.items()}}
    report_bytes = json.dumps({k: v for k, v in plan.items() if k not in {"files", "config"}}, ensure_ascii=False).encode("utf-8")
    with store.lock():
        journal = store.read("migration", "transaction")
        if journal is not None:
            if not isinstance(journal, dict) or set(journal) != {"binding", "phase"} or journal["phase"] not in {"COPYING", "COMPLETED_UNVERIFIED"}:
                raise SddError("MIGRATION_JOURNAL_INVALID", "Preserve the damaged transaction before recovery")
            if not resume or journal["binding"] != binding:
                raise SddError("MIGRATION_SOURCE_CHANGED", "Resume requires the original source and mapping", Status.STALE)
        elif resume:
            raise SddError("MIGRATION_NOT_RESUMABLE", "Target has no migration journal")
        else:
            journal = {"binding": binding, "phase": "COPYING"}
            store.write("migration", "transaction", journal)
        # Check before and after copying. A late edit must not become a completed import.
        _check_target(destination, files, journal, store, report_bytes)
        for index, (relative, text) in enumerate(files.items()):
            if index == len(files) // 2:
                _check_source(source, plan["source_manifest"])
            path = destination / relative_path(relative)
            if any(parent.is_symlink() for parent in (path, *path.parents)):
                raise SddError("MIGRATION_TARGET_CHANGED", relative, Status.STALE)
            if path.exists() and (not path.is_file() or path.read_bytes() != text.encode("utf-8")):
                raise SddError("MIGRATION_TARGET_CHANGED", relative, Status.STALE)
            if not path.exists():
                atomic_write(path, text.encode("utf-8"))
            if fault:
                fault(relative)
        _check_source(source, plan["source_manifest"])
        _check_target(destination, files, journal, store, report_bytes, complete=True)
        journal["phase"] = "COMPLETED_UNVERIFIED"
        store.write("migration", "transaction", journal)
        atomic_write(destination / ".sdd" / "migration.json", report_bytes)
    return {k: v for k, v in plan.items() if k != "files"} | {"destination": str(destination.resolve())}
