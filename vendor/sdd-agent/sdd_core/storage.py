from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
import tempfile

from .model import SddError, Snapshot, Status, canonical, digest
from .parsing import parse_json
from .workspace import build_snapshot


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".sdd-write-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as file:
            file.write(data)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
        if hasattr(os, "O_DIRECTORY"):
            descriptor = os.open(path.parent, os.O_DIRECTORY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class Store:
    def __init__(self, workspace: Path, decision_verifier=None):
        self.decision_verifier = decision_verifier
        self.root = Path(workspace).resolve() / ".sdd"
        if self.root.is_symlink():
            raise SddError("STATE_SYMLINK", str(self.root))

    def path(self, category: str, identifier: str) -> Path:
        if not category or not category[0].islower() or any(c not in "abcdefghijklmnopqrstuvwxyz_" for c in category):
            raise SddError("STATE_CATEGORY_INVALID", category)
        if not identifier or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:-" for c in identifier):
            raise SddError("STATE_ID_INVALID", identifier)
        result = self.root / category / (identifier + ".json")
        for ancestor in (result, *result.parents):
            if ancestor == self.root.parent:
                break
            if ancestor.is_symlink():
                raise SddError("STATE_SYMLINK", str(ancestor))
        return result

    @contextmanager
    def lock(self, name="writer"):
        self.root.mkdir(parents=True, exist_ok=True)
        if not name or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:-" for c in name):
            raise SddError("STATE_ID_INVALID", name)
        lock = self.root / (name + ".lock")
        if lock.is_symlink():
            raise SddError("STATE_SYMLINK", str(lock))
        with lock.open("a+b") as file:
            windows = os.name == "nt"
            if windows:
                import msvcrt
                # Windows permits locking beyond EOF. Reading a locked byte
                # first would fail before contention can become WORKSPACE_BUSY.
                file.seek(0)
            else:
                try:
                    import fcntl
                except ImportError as exc:
                    raise SddError("FILESYSTEM_UNSUPPORTED", "Local OS file locks are required") from exc
            try:
                if windows:
                    msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                import errno
                if exc.errno in {errno.EACCES, errno.EAGAIN, errno.EDEADLK}:
                    raise SddError("WORKSPACE_BUSY", "Another engine writer holds the lock", Status.STALE) from exc
                raise SddError("FILESYSTEM_UNSUPPORTED", "Cannot acquire a local file lock") from exc
            try:
                yield
            finally:
                if windows:
                    file.seek(0)
                    msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(file, fcntl.LOCK_UN)

    def read(self, category: str, identifier: str, default=None):
        path = self.path(category, identifier)
        if not path.exists():
            return default
        return parse_json(path.read_text(encoding="utf-8"))

    def write(self, category: str, identifier: str, value, immutable=False):
        path = self.path(category, identifier)
        encoded = canonical(value)
        if immutable and path.exists():
            if path.read_bytes() != encoded:
                raise SddError("IMMUTABLE_RECORD_CONFLICT", f"{category}/{identifier}")
            return
        atomic_write(path, encoded)

    def list(self, category: str) -> list[dict]:
        self.path(category, "inventory")
        directory = self.root / category
        if directory.is_symlink():
            raise SddError("STATE_SYMLINK", str(directory))
        return [self.read(category, p.stem) for p in sorted(directory.glob("*.json"))] if directory.exists() else []

    def save_snapshot(self, snapshot: Snapshot):
        self.write("snapshots", snapshot.digest,
                   {"files": snapshot.files, "engine_version": snapshot.engine_version}, immutable=True)

    def load_snapshot(self, identifier: str) -> Snapshot:
        record = self.read("snapshots", identifier)
        if record is None or digest(record) != identifier:
            raise SddError("SNAPSHOT_CORRUPT", identifier)
        snapshot = build_snapshot(record["files"], record["engine_version"])
        if snapshot.digest != identifier:
            raise SddError("SNAPSHOT_CORRUPT", identifier)
        return snapshot

    def baseline(self) -> dict | None:
        pointer = self.read("state", "baseline")
        if pointer:
            certificate = self.read("acceptances", pointer["acceptance_id"])
            if certificate is None or digest(certificate) != pointer["certificate_digest"]:
                raise SddError("BASELINE_CORRUPT", "Acceptance pointer does not match its certificate")
            if certificate["snapshot_digest"] != pointer["snapshot_digest"]:
                raise SddError("BASELINE_CORRUPT", "Snapshot mismatch")
        return pointer

    def decisions(self):
        return self.list("decisions")

    def history(self):
        pointer = self.baseline()
        identifier = pointer["acceptance_id"] if pointer else None
        expected_digest = pointer["certificate_digest"] if pointer else None
        history, seen = [], set()
        while identifier:
            if identifier in seen:
                raise SddError("HISTORY_CORRUPT", "Acceptance history contains a cycle")
            seen.add(identifier)
            record = self.read("acceptances", identifier)
            if record is None or digest(record) != expected_digest:
                raise SddError("HISTORY_CORRUPT", identifier)
            history.append(record)
            identifier = record.get("previous_acceptance")
            expected_digest = record.get("previous_certificate_digest")
        return history
