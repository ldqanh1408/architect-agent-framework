"""specification / W-22 — the registry: gate IDs resolve here or they do not resolve.

`contracts/gates.yml` is the single list of every gate this repository has. Two
things depend on that being *the* list rather than *a* list:

  * `build_checklist.py` (specification) resolves each row's `verify` through
    :func:`get`, so a row citing an unregistered ID fails at generation time.
    E-1 stops being a discipline problem and becomes a lookup.
  * the roll-call (specification) iterates :func:`all_gates`, so a registered gate cannot
    quietly never run.

Read through :mod:`architect_framework.contracts` (R-3). Nothing here opens a
file.
"""

from __future__ import annotations

import functools
import re
import importlib
from pathlib import Path
from typing import Iterable, Iterator, Sequence

from architect_framework import contracts
from architect_framework.gates.base import Finding, Gate, GateContext, GateResult
from architect_framework.gates.subprocess_gate import SubprocessGate

REPO_ROOT = contracts.REPO_ROOT


class RegistryError(RuntimeError):
    """The registry is missing, malformed, or asked for an ID it does not hold."""


class UnknownGate(RegistryError):
    """An ID that is not registered.

    Raised rather than returning ``None`` on purpose: the caller most likely to
    ask is checklist generation, and a silent miss there is exactly the
    false-green row this registry exists to make impossible.
    """


_REQUIRED_KEYS = ("id", "kind", "entrypoint")
_KINDS = ("subprocess", "native")
_ROLES = ("gate", "tool")
_SCOPES = ("repo", "workspace", "catalog")
_SIDE_EFFECTS = ("read-only", "writes")


def _build(entry: dict) -> Gate:
    missing = [k for k in _REQUIRED_KEYS if not entry.get(k)]
    if missing:
        raise RegistryError(f"gates.yml entry {entry.get('id', '<no id>')!r} missing {missing}")
    kind = str(entry["kind"])
    if kind not in _KINDS:
        raise RegistryError(f"{entry['id']}: kind must be one of {_KINDS}, got {kind!r}")
    role = str(entry.get("role", "gate"))
    if role not in _ROLES:
        raise RegistryError(f"{entry['id']}: role must be one of {_ROLES}, got {role!r}")
    scope = str(entry.get("scope", "repo"))
    if scope not in _SCOPES:
        raise RegistryError(f"{entry['id']}: scope must be one of {_SCOPES}, got {scope!r}")
    effects = str(entry.get("side_effects") or ("writes" if role == "tool" else "read-only"))
    if effects not in _SIDE_EFFECTS:
        raise RegistryError(f"{entry['id']}: side_effects must be one of {_SIDE_EFFECTS}, got {effects!r}")

    # specification: a native entry whose entrypoint is a script runs that script in this
    # process (`inprocess.InProcessGate`); every other native names `module:Class`.
    script_native = kind == "native" and str(entry["entrypoint"]).endswith(".py")
    if kind == "subprocess" or script_native:
        from architect_framework.gates.inprocess import InProcessGate

        return (InProcessGate if script_native else SubprocessGate)(
            id=str(entry["id"]),
            entrypoint=str(entry["entrypoint"]),
            argv=tuple(entry.get("argv") or ()),
            scope=scope,
            role=role,
            phase=tuple(entry.get("phase") or ()),
            title=str(entry.get("title") or ""),
            timeout_s=int(entry.get("timeout_s") or 300),
            usage=str(entry.get("usage") or ""),
            roll_call=dict(entry.get("roll_call") or {}),
            side_effects=str(entry.get("side_effects") or ("writes" if role == "tool" else "read-only")),
            alias_of=str(entry.get("alias_of") or ""),
        )

    # native: `module.path:ClassName`
    target = str(entry["entrypoint"])
    if ":" not in target:
        raise RegistryError(f"{entry['id']}: native entrypoint must be 'module:Class', got {target!r}")
    module_name, class_name = target.split(":", 1)
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        raise RegistryError(f"{entry['id']}: cannot import {module_name}: {exc}") from exc
    try:
        cls = getattr(module, class_name)
    except AttributeError as exc:
        raise RegistryError(f"{entry['id']}: {module_name} has no {class_name}") from exc
    instance = cls()
    # A native gate must carry the same registry-declared attributes a subprocess
    # gate does, or callers have to special-case by kind. `read_only()` filters on
    # `side_effects`, and the roll-call asserts `.read_only` on what it returns —
    # the first native gate (GATE-SEAM-LEDGER) broke that test by not having it.
    # Set them here rather than in each gate class, so a future native gate cannot
    # forget.
    for attribute, value in (
        ("role", role),
        ("scope", scope),
        ("side_effects", effects),
        ("phase", tuple(entry.get("phase") or ())),
        ("title", str(entry.get("title") or "")),
        ("timeout_s", int(entry.get("timeout_s") or 300)),
        ("roll_call", dict(entry.get("roll_call") or {})),
        ("alias_of", str(entry.get("alias_of") or "")),
    ):
        if not hasattr(instance, attribute):
            setattr(instance, attribute, value)
    if not hasattr(type(instance), "read_only"):
        setattr(instance, "read_only", effects == "read-only")
    if not hasattr(instance, "roll_call_context"):
        from architect_framework.gates import base as _base

        setattr(instance, "roll_call_context",
                lambda ctx, _g=instance: _base.roll_call_context(_g, ctx))
    return instance  # type: ignore[no-any-return]


@functools.lru_cache(maxsize=1)
def _entries() -> tuple[dict, ...]:
    if not contracts.available("gates"):
        raise RegistryError(
            f"gates.yml not found at {contracts.path_of('gates')}. "
            "Generate it with `architect-cli gate bootstrap` (specification)."
        )
    rows = contracts.raw("gates").get("gates") or []
    if not rows:
        raise RegistryError("gates.yml declares no gates")
    seen: dict[str, str] = {}
    for row in rows:
        gid = str(row.get("id", ""))
        if gid in seen:
            raise RegistryError(
                f"duplicate gate id {gid!r}: {seen[gid]} and {row.get('entrypoint')}. "
                "One concept, one ID — see W-27."
            )
        seen[gid] = str(row.get("entrypoint"))
    return tuple(dict(r) for r in rows)


@functools.lru_cache(maxsize=1)
def all_gates() -> tuple[Gate, ...]:
    """Every registered gate, in file order. Order is stable so reports diff."""
    return tuple(_gate(str(e["id"])) for e in _entries())


@functools.lru_cache(maxsize=None)
def _gate(gate_id: str) -> Gate:
    return _build(dict(next(e for e in _entries() if e["id"] == gate_id)))


def raw_entries() -> tuple[dict, ...]:
    """The registry rows as data — for `gate list` and the roll-call."""
    return _entries()


@functools.lru_cache(maxsize=1)
def retired() -> dict[str, dict]:
    """`{retired id: row}` — IDs that were gates once and are not any more.

    specification retire IDs by merging or deleting their scripts. An ID that was
    published — in a checklist row, a run log, a handoff — does not stop being
    cited the day its gate goes, so it stays answerable here: with the
    `successor` gate that now does its job, or with the `reason` it has none.
    Each row: ``id``, ``successor`` (a live ID or null), ``replacement`` (what a
    caller runs now), ``script`` (the file it ran), ``reason``, ``work_order``.
    """
    if not contracts.available("gates"):
        return {}
    rows = contracts.raw("gates").get("retired") or []
    return {str(r.get("id")): dict(r) for r in rows if isinstance(r, dict) and r.get("id")}


def clear_cache() -> None:
    _entries.cache_clear()
    all_gates.cache_clear()
    _gate.cache_clear()
    _code_meta.cache_clear()
    retired.cache_clear()
    contracts.clear_cache()


def ids() -> list[str]:
    """Every ID the registry answers for: live gates, then retired IDs.

    A retired ID is known — a document or a run log naming it names something
    that was real — but it is not runnable on its own: :func:`get` returns its
    reasoned error; a successor is guidance and never an execution alias.
    """
    live = [str(e["id"]) for e in _entries()]
    return live + [rid for rid in retired() if rid not in live]


def get(gate_id: str) -> Gate:
    if any(e["id"] == gate_id for e in _entries()):
        return _gate(gate_id)
    row = retired().get(gate_id)
    if row is not None:
        raise UnknownGate(
            f"{gate_id} was retired: {row.get('reason')}. "
            f"Use instead: {row.get('replacement')}"
        )
    from difflib import get_close_matches
    close = get_close_matches(gate_id.upper(), ids(), n=5, cutoff=0.6)
    hint = f" Did you mean: {', '.join(close[:5])}?" if close else ""
    raise UnknownGate(f"no gate registered as {gate_id!r}.{hint}")


def exists(gate_id: str) -> bool:
    """Only current IDs are executable; retired IDs remain historical metadata."""
    return any(e["id"] == gate_id for e in _entries())


def absorbed_scripts() -> dict[str, str]:
    """`{script path: native gate id}` for scripts a native gate runs in-process (specification).

    Such a script is not a registry entry of its own — its native gate is — but
    it is in the roll-call through that gate, and its entrypoint must resolve.
    """
    out: dict[str, str] = {}
    for entry in _entries():
        for path in entry.get("absorbs") or []:
            out[str(path)] = str(entry["id"])
    return out


def select(
    *,
    kind: str | None = None,
    role: str | None = None,
    scope: str | None = None,
    phase: int | None = None,
    stage: str | None = None,
) -> list[Gate]:
    out: list[Gate] = []
    for entry, gate in zip(_entries(), all_gates()):
        if kind and str(entry.get("kind")) != kind:
            continue
        if stage and str(entry.get("stage") or "") != stage:
            continue
        if role and str(entry.get("role", "gate")) != role:
            continue
        if scope and str(entry.get("scope", "repo")) != scope:
            continue
        if phase is not None and phase not in (entry.get("phase") or []):
            continue
        out.append(gate)
    return out


def unresolved(repo_root: Path | None = None) -> list[str]:
    """IDs whose entrypoint does not resolve on disk.

    The roll-call fails on a non-empty list. This is the closure of E-1: an ID in
    the registry that points at nothing is a defect the registry itself reports,
    rather than a string in a markdown table that nobody checks.
    """
    root = repo_root or REPO_ROOT
    is_standalone_plugin = not (root / "scripts").is_dir() or ((root / "skills" / "architect-runtime").is_dir() and not (root / "exported_skills").is_dir())
    out: list[str] = []
    for entry, gate in zip(_entries(), all_gates()):
        if is_standalone_plugin and str(entry.get("scope", "repo")) in {"repo", "catalog"}:
            continue
        if str(entry.get("kind")) != "subprocess" and not str(entry["entrypoint"]).endswith(".py"):
            # A native gate that absorbed scripts (specification) resolves only if they do.
            if any(not (root / str(p)).is_file() for p in entry.get("absorbs") or []):
                out.append(str(entry["id"]))
            continue
        if hasattr(gate, "exists") and gate.exists(root):
            continue
        if not (root / str(entry["entrypoint"])).is_file():
            out.append(str(entry["id"]))
    return out


def run(gate_id: str, ctx: GateContext) -> GateResult:
    from architect_framework.gates.runner import run_one
    return run_one(get(gate_id), ctx)


def run_many(gates: Iterable[Gate], ctx: GateContext) -> Iterator[GateResult]:
    for gate in gates:
        from architect_framework.gates.runner import run_one
        yield run_one(gate, ctx)


def resolve_reference(text: str) -> str | None:
    """The gate ID a `Verify` cell refers to, or ``None``.

    specification. A checklist row's `Verify` was free-form argv, so a row could cite a
    path that does not exist and still read as evidence — `CK-0.1`, `CK-0.2` and
    `CK-0.3` closed Phase 0 that way. Resolution accepts, in order:

      1. a bare gate ID                       ``GATE-DOC-COVERAGE``
      2. an `architect-cli gate run <ID>` argv
      3. a repository-relative script path     ``scripts/check_doc_coverage.py``
      4. a bare script filename               ``check_doc_coverage.py``

    Form 4 is accepted because that is what the existing rows and the 110
    manifests carry; it is resolved through the registry rather than the
    filesystem, so a filename with no registered gate behind it is unresolvable
    instead of merely unusual. When one filename has several entries the
    repository-root copy wins, which is the authoritative implementation in every
    case the roll-call examined.
    """
    if not text:
        return None
    blob = str(text).strip()

    for token in re.findall(r"\b(?:GATE|TOOL)-[A-Z0-9-]+\b", blob):
        if exists(token):
            return token

    by_path: dict[str, str] = {}
    by_name: dict[str, str] = {}
    # A script a native gate absorbed (specification), or one a retired ID ran, resolves
    # to the gate that does its job now — the row citing it stays checkable.
    carried = list(absorbed_scripts().items()) + [
        (str(r["script"]), str(r["successor"]))
        for r in retired().values() if r.get("script") and r.get("successor")
    ]
    for entrypoint, gid in [(str(e["entrypoint"]), str(e["id"])) for e in _entries()] + carried:
        by_path.setdefault(entrypoint, gid)
        name = entrypoint.rsplit("/", 1)[-1]
        # Prefer the repository-root implementation over a vendored or packaged copy.
        if name not in by_name or not entrypoint.startswith("vendor/"):
            by_name[name] = gid

    for path in sorted(by_path, key=len, reverse=True):
        if path in blob:
            return by_path[path]
    for match in re.findall(r"[\w./-]+\.py", blob):
        name = match.rsplit("/", 1)[-1]
        if name in by_name:
            return by_name[name]
    return None


def findings_owners() -> dict[str, list[str]]:
    """`{finding code: [gate id, …]}` — a code may have more than one emitter.

    Four do today, and each is legitimate rather than a mistake:
    `BROKEN-LINK` is checked both per-workspace and per-page; `TREE-specification`
    is raised by the tree-plan gate and, since specification, by the level resolver that
    now owns the arithmetic. Collapsing to one owner made `gate explain` name
    whichever entry happened to be later in the file, so a reader chasing a code
    was sent to the wrong gate half the time.
    """
    out: dict[str, list[str]] = {}
    for entry in _entries():
        for code in entry.get("findings") or []:
            out.setdefault(str(code), []).append(str(entry["id"]))
    return out


@functools.lru_cache(maxsize=1)
def _code_meta() -> dict[tuple[str, str], dict]:
    out: dict[tuple[str, str], dict] = {}
    for entry in _entries():
        for code, meta in (entry.get("codes") or {}).items():
            if isinstance(meta, dict):
                out[(str(entry["id"]), str(code))] = dict(meta)
    return out


def code_meta(gate_id: str, code: str) -> dict:
    """`{class, remedy}` the registry declares for `code` as emitted by `gate_id` (specification)."""
    try:
        return dict(_code_meta().get((gate_id, code)) or {})
    except RegistryError:
        return {}


#: specification / G-1 — the finding classes that count toward an exit code. Mirrors
#: `bootstrap.BLOCKING_CLASSES`, which validates the registry against it.
BLOCKING_CLASSES = frozenset({"derived", "contract"})


def is_blocking(gate_id: str, code: str) -> bool:
    """False only for a code the registry declares `heuristic` or `style`.

    A code with no declared class counts. That is the conservative reading G-1
    needs: an unclassified code is one nobody has shown to be a mere judgement,
    and `GATE-VACUOUS`, `GATE-TIMEOUT` and the other codes the runner itself
    raises are never in a gate's `codes` block, so they always fail the run.
    """
    klass = code_meta(gate_id, code).get("class")
    return klass is None or str(klass) in BLOCKING_CLASSES


def findings_index() -> dict[str, str]:
    """`{finding code: gate id}`, first owner only.

    Kept for callers that want a single answer. Prefer :func:`findings_owners`.
    """
    return {code: owners[0] for code, owners in findings_owners().items()}


def read_only(**kw) -> list[Gate]:
    """Gates safe to execute in a test.

    A `writes` entry is never executed by the roll-call: the first specification run did
    execute them and dirtied 759 files. Their behaviour is covered by their own
    fixture in specification; the roll-call proves only that they resolve and answer
    `--help`.
    """
    return [g for g in select(**kw) if getattr(g, "side_effects", "read-only") == "read-only"]


def writers(**kw) -> list[Gate]:
    return [g for g in select(**kw) if getattr(g, "side_effects", "read-only") == "writes"]
