"""Windows path-length escape hatch for workspace I/O.

Windows refuses to open a path longer than 260 characters (``MAX_PATH``) unless
either the machine sets ``LongPathsEnabled=1`` in the registry or the caller
passes the extended-length form ``\\\\?\\C:\\...``. The registry switch is a
machine-wide setting that a framework cannot assume and should not require its
users to flip, so every writer that lands inside a generated workspace goes
through here instead.

This is not a hypothetical limit. The D-1 module path form
``02-domains/<cluster>/<submodule>/<skill>/`` nests four segments below the
workspace root before a page name is appended, and specification's page-family expansion
pushed the node count from 118 to 149. A realistic workspace under a normal
temp directory produced a 261-character path -- one character over -- and the
scaffolder died with ``FileNotFoundError`` on a ``mkdir(parents=True)`` that had
already run correctly. The directory was fine; the open was not.

The failure mode matters more than the length: an over-long path does not raise
from ``Path.exists()``, it returns ``False``. A guard that reads "leave authored
content alone" silently becomes "overwrite it" on a deep tree, which is why the
read and probe helpers live here too rather than only the write ones.

On every non-Windows platform each function is the identity plus the ordinary
pathlib call, so callers do not branch.
"""

from __future__ import annotations

import os
from pathlib import Path

_EXTENDED_PREFIX = "\\\\?\\"
_UNC_PREFIX = "\\\\?\\UNC"


def extended(path: Path | str) -> Path:
    """Return `path` in a form the Windows API will accept at any length.

    The extended-length form only works on a fully-qualified path with no `..`
    or `.` components and no forward slashes, so the path is normalised first.
    Returned unchanged on POSIX, and unchanged if it already carries the prefix.
    """
    if os.name != "nt":
        return Path(path)
    raw = os.fspath(path)
    if raw.startswith(_EXTENDED_PREFIX):
        return Path(raw)
    absolute = os.path.abspath(raw)
    if absolute.startswith("\\\\"):
        # A UNC share \\server\share becomes \\?\UNC\server\share -- the leading
        # pair of separators collapses into the UNC marker rather than stacking.
        return Path(_UNC_PREFIX + absolute[1:])
    return Path(_EXTENDED_PREFIX + absolute)


def mkdir(path: Path, *, parents: bool = True, exist_ok: bool = True) -> None:
    """Create `path`, tolerating a total length past MAX_PATH."""
    extended(path).mkdir(parents=parents, exist_ok=exist_ok)


def write_text(path: Path, data: str, *, encoding: str = "utf-8", newline: str = "\n") -> None:
    """Write `data` to `path`, creating parents, at any path length.

    UTF-8 and `\\n` are the defaults because the alternative on Windows is
    cp1252 plus CRLF, which is how a byte-identical-rerun guarantee quietly
    stops holding across platforms.
    """
    target = extended(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(data, encoding=encoding, newline=newline)


def atomic_write_text(path: Path, data: str, *, encoding: str = "utf-8", newline: str | None = "\n",
                      attempts: int = 20) -> Path:
    """Write `data` to `path` via a sibling temp file and `os.replace`.

    A process killed mid-write leaves the old file or the new one, never half
    of either — a derived ledger read back as the next run's input must not be
    torn. The temp name carries the process and the thread, so two writers
    never share it. On Windows a reader holding the target for a moment makes
    `os.replace` raise `PermissionError`; that is retried with a short backoff.
    `newline=None` keeps the platform's own translation, for writers whose
    bytes must not change by becoming atomic.
    """
    import threading
    import time

    target = extended(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(f".{target.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    try:
        tmp.write_text(data, encoding=encoding, newline=newline)
        for attempt in range(attempts):
            try:
                os.replace(tmp, target)
                return Path(path)
            except PermissionError:
                if attempt == attempts - 1:
                    raise
                time.sleep(0.02 * (attempt + 1))
    finally:
        if tmp.exists():
            tmp.unlink()
    return Path(path)


def read_bytes(path: Path, *, attempts: int = 20) -> bytes:
    """Read `path` while another thread may be replacing it.

    The reader's half of :func:`atomic_write_text`: on Windows, opening a file at
    the instant another writer's `os.replace` lands on it raises
    `PermissionError`. That is retried with the same short backoff.
    """
    import time

    target = extended(path)
    for attempt in range(attempts):
        try:
            return target.read_bytes()
        except PermissionError:
            if attempt == attempts - 1:
                raise
            time.sleep(0.02 * (attempt + 1))
    return target.read_bytes()


def read_text(path: Path, *, encoding: str = "utf-8", errors: str = "strict") -> str:
    """Read `path` at any length, with an explicit encoding rather than the locale's."""
    return extended(path).read_text(encoding=encoding, errors=errors)


def exists(path: Path) -> bool:
    """Report whether `path` exists, without the silent `False` an over-long path returns."""
    return extended(path).exists()
