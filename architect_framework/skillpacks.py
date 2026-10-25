"""The skill resolver: every skill is a slot (khe), its expertise (ruột) is optional.

`specification` section 1 and section 5 (specification…specification). Every skill has two
separable halves:

* the **slot** — `skill-contract.yml`, `workspace-template.yml`: what the skill
  needs, where it writes, when it is done. The runtime, router, gates and review
  console read only this half. It is core: an installed package may carry it,
  and otherwise the core generates it from `architect_framework/data/` (the same
  generator that builds the pack, so the bytes are the same — `catalogue_root`);
* the **content** — `SKILL.md` (and `references/`): the expertise the agent is
  briefed with. It is optional: bought on agensi.io, written by the user, or absent.

So the plan, the sandbox and the schedule never depend on which skills are
installed; only the brief does.

**Search path** (section 5.1), first match wins:

1. every directory in ``$ARCHITECT_SKILLS_PATH`` (``os.pathsep``-separated);
2. ``<workspace>/.claude/skills/``, then ``<cwd>/.claude/skills/``;
3. ``~/.claude/skills/``, ``~/.codex/skills/``, ``~/.agents/skills/``;
4. the skills bundled with the plugin;
5. this repository's own catalogue (``exported_skills/``), unless
   ``$ARCHITECT_NO_DEFAULT_PACK=1`` — how a test plays a clean machine.

A folder matches an id when it holds a ``SKILL.md`` whose frontmatter ``name`` is
that id, whatever the folder is called (section 5.1). A ``skill-bindings.yml`` in the
workspace (or ``~/.architect-framework/``) may also point an id at any skill folder or id —
one skill of the user's own can fill several slots.

**Slot states** (section 1): ``licensed`` — the content carries ``metadata.edition:
agensi``; ``third-party`` — any other matching ``SKILL.md``; ``empty`` — none.
An empty slot does not write (specification, the plan's proposal): its pages stay missing
behind an open seam, so nothing reads as done that was not. With
``$ARCHITECT_ALLOW_BASE=1`` it writes from the slot alone (``base``), briefed with
the generated ``SKILL.md``. The SDD skills under ``vendor/sdd-agent`` are core and
are never a slot.
"""

from __future__ import annotations

import contextlib
import functools
import hashlib
import os
import shutil
import tempfile
from collections.abc import Iterator, Mapping
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from architect_framework.contracts import REPO_ROOT, VENDOR_ROOT

ENV_PATH = "ARCHITECT_SKILLS_PATH"
ENV_NO_DEFAULT = "ARCHITECT_NO_DEFAULT_PACK"
ENV_ALLOW_BASE = "ARCHITECT_ALLOW_BASE"
ENV_BINDINGS = "ARCHITECT_SKILL_BINDINGS"
ENV_HOME = "ARCHITECT_HOME"
BINDINGS_FILE = "skill-bindings.yml"
DEFAULT_PACK = REPO_ROOT / "exported_skills"
PLUGIN_SKILLS = (REPO_ROOT / "plugins" / "architect-agent-framework" / "skills") if (REPO_ROOT / "plugins" / "architect-agent-framework" / "skills").is_dir() else (REPO_ROOT / "skills")
CONTRACT = "skill-contract.yml"
MANIFEST = "workspace-template.yml"
PACKAGE = "package.yml"
SKILL_MD = "SKILL.md"
#: The slot files: shipped with the core, never overwritten by an install.
SLOT_FILES = frozenset({CONTRACT, MANIFEST, PACKAGE})
#: Prices and packs of every slot (`scripts/build_skill_slots.py`).
SLOT_OFFERS = Path(__file__).resolve().parent / "data" / "skill-slots.yml"
AGENSI_EDITION = "agensi"

#: Slot states (section 1), plus the two the runtime adds: core skills, and an empty
#: slot that runs from its contract alone because base mode is on.
LICENSED, THIRD_PARTY, EMPTY, BASE, CORE = "licensed", "third-party", "empty", "base", "core"

#: Inputs of the slot generation; their bytes key the cache.
_CATALOGUE_INPUTS = ("data", "exporter", "registry")


class BindingError(ValueError):
    """A binding names a skill that cannot be found."""


@dataclass(frozen=True)
class Package:
    """One skill folder on disk."""

    skill: str
    home: Path
    kind: str  # domain | task | orchestration | custom
    group: str  # cluster or task family; "" when the layout does not say
    edition: str = ""  # `metadata.edition` of its SKILL.md

    @property
    def contract(self) -> Path | None:
        path = self.home / CONTRACT
        return path if path.is_file() else None

    @property
    def manifest(self) -> Path | None:
        path = self.home / MANIFEST
        return path if path.is_file() else None


@dataclass(frozen=True)
class Slot:
    """One skill id: where its contract comes from, and its content, if any."""

    skill: str
    state: str  # licensed | third-party | empty | base | core
    content: Path | None  # the folder whose SKILL.md briefs the agent
    contract_home: Path | None  # the folder whose skill-contract.yml governs it

    @property
    def runs(self) -> bool:
        """The agent writes pages: it has content, or base mode stands in for it."""
        return self.state != EMPTY

    @property
    def filled(self) -> bool:
        return self.state in {LICENSED, THIRD_PARTY, CORE}


# --------------------------------------------------------------------------- #
# Settings
# --------------------------------------------------------------------------- #


def _flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def home_dir() -> Path:
    """User-level state: the generated slots and a user-wide `skill-bindings.yml`.

    Not `~/.architect`: the review console finds a project by walking up to the
    nearest `.architect/` folder, and one in the home directory would make every
    workspace below it look like part of a single project.
    """
    return Path(os.environ.get(ENV_HOME) or Path.home() / ".architect-framework")


def default_pack_enabled() -> bool:
    return not _flag(ENV_NO_DEFAULT)


def allow_base() -> bool:
    """`ARCHITECT_ALLOW_BASE=1`: an empty slot writes from its contract alone."""
    return _flag(ENV_ALLOW_BASE)


_ACTIVE_WORKSPACE: ContextVar[Path | None] = ContextVar("architect_skill_workspace", default=None)


def activate(workspace: str | Path | None) -> None:
    """Make `workspace`'s `.claude/skills/` and `skill-bindings.yml` part of every lookup."""
    _ACTIVE_WORKSPACE.set(Path(workspace).resolve() if workspace else None)


ENV_TRUST_WORKSPACE = "ARCHITECT_TRUST_WORKSPACE_CONTRACTS"


def contract_trusted(home: Path) -> bool:
    """May a `skill-contract.yml` in `home` govern an agent's sandbox?

    A contract sets what an agent may write. One shipped with the framework, in
    the install tree, on ARCHITECT_SKILLS_PATH or in the person's own skills
    folders, yes. Any other folder — the workspace's `.claude/skills/`, a binding
    into a repository — may have been written by someone else, so its contract
    does not govern, unless the person sets ARCHITECT_TRUST_WORKSPACE_CONTRACTS=1
    (LP 20, L-2, N-2). Its SKILL.md still briefs the agent under the slot's contract.
    """
    if os.environ.get(ENV_TRUST_WORKSPACE) == "1":
        return True
    try:
        real = Path(home).resolve()
    except OSError:
        return False
    # Only the listed roots: a binding into `../another-clone/` is a folder some other
    # repository wrote, as much as one inside this workspace is (LP 20, N-2).
    home = Path.home()
    trusted = [r.resolve() for r in (install_root(), DEFAULT_PACK, PLUGIN_SKILLS, home / ".claude" / "skills",
                                     home / ".codex" / "skills", home / ".agents" / "skills", home / ".dsh" / "skills")]
    trusted += [Path(p).expanduser().resolve() for p in os.environ.get(ENV_PATH, "").split(os.pathsep) if p.strip()]
    return any(real == t or t in real.parents for t in trusted)


@contextlib.contextmanager
def activated(workspace: str | Path | None) -> Iterator[None]:
    """`activate(workspace)` for one call, then the previous state back.

    A long-lived MCP server answers for many workspaces; one call's bindings must
    not stay active for the next (LP 20, L-4).
    """
    token = _ACTIVE_WORKSPACE.set(Path(workspace).resolve() if workspace else None)
    try:
        yield
    finally:
        _ACTIVE_WORKSPACE.reset(token)


def install_root() -> Path:
    """Where `install()` puts bought skills: the shape of `exported_skills/`, in the
    user's folder so that updating the plugin never removes them."""
    return home_dir() / "exported_skills"


def search_path() -> tuple[Path, ...]:
    """The content search path of section 5.1, existing folders only, in lookup order.

    The install tree comes right after ``$ARCHITECT_SKILLS_PATH``: a skill the
    user bought and installed wins over a copy found in an agent's own folders.
    """
    roots = [Path(p).expanduser() for p in os.environ.get(ENV_PATH, "").split(os.pathsep) if p.strip()]
    roots.append(install_root())
    if _ACTIVE_WORKSPACE.get() is not None:
        ws_root = _ACTIVE_WORKSPACE.get()
        roots += [ws_root / ".claude" / "skills", ws_root / ".agents" / "skills", ws_root / ".dsh" / "skills"]
    cwd = Path.cwd()
    roots += [cwd / ".claude" / "skills", cwd / ".agents" / "skills", cwd / ".dsh" / "skills"]
    home = Path.home()
    roots += [home / ".claude" / "skills", home / ".codex" / "skills", home / ".agents" / "skills", home / ".dsh" / "skills"]
    roots.append(PLUGIN_SKILLS)
    if default_pack_enabled():
        roots.append(DEFAULT_PACK)
    out: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        resolved = root.resolve()
        if resolved not in out:
            out.append(resolved)
    return tuple(out)


# --------------------------------------------------------------------------- #
# Scanning
# --------------------------------------------------------------------------- #


#: The frontmatter is at the top of a SKILL.md; a 2 GB file is not read whole to find it (L-3).
FRONTMATTER_BYTES = 64 * 1024


def _frontmatter(skill_md: Path) -> Mapping[str, Any]:
    try:
        with open(skill_md, "rb") as handle:
            text = handle.read(FRONTMATTER_BYTES).decode("utf-8", errors="replace")
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    try:
        data = yaml.safe_load(parts[1]) if len(parts) == 3 else {}
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, Mapping) else {}


def _package_contract(home: Path) -> Mapping:
    path=home / CONTRACT
    if not path.is_file(): return {}
    with path.open('rb') as stream: raw=stream.read(2*1024*1024+1)
    if len(raw)>2*1024*1024: raise BindingError('SKILL_CONTRACT_LIMIT: contract exceeds 2 MiB')
    try: data=yaml.safe_load(raw.decode('utf-8')) or {}
    except (yaml.YAMLError, UnicodeError) as error: raise BindingError('SKILL_CONTRACT_INVALID: malformed package contract') from error
    if not isinstance(data, Mapping): raise BindingError('SKILL_CONTRACT_INVALID: expected a mapping')
    return data


def _identity(home: Path) -> tuple[str, str]:
    """`(skill id, edition)`: the frontmatter `name` first, as section 5.1 matches on it."""
    front = _frontmatter(home / SKILL_MD)
    metadata = front.get("metadata") if isinstance(front.get("metadata"), Mapping) else {}
    edition = str((metadata or {}).get("edition") or "")
    if front.get("name"):
        return str(front["name"]), edition
    contract = home / CONTRACT
    if contract.is_file():
        data = _package_contract(home)
        if isinstance(data, Mapping) and data.get("skill"):
            return str(data["skill"]), edition
    return home.name, edition


def _classify(home: Path, root: Path) -> tuple[str, str]:
    parts = home.relative_to(root).parts
    if len(parts) == 3 and parts[0] == "domains":
        return "domain", parts[1]
    if len(parts) == 3 and parts[0] == "tasks":
        return "task", parts[1]
    if len(parts) == 2 and parts[0] == "orchestration":
        return "orchestration", ""
    # A flat skills folder (`~/.claude/skills/<id>/`, the plugin's) says nothing by
    # its layout; a contract the folder carries does.
    contract = home / CONTRACT
    if contract.is_file():
        data = _package_contract(home)
        kind = str(data.get("kind") or "") if isinstance(data, Mapping) else ""
        if kind in {"domain", "task", "orchestration"}:
            return kind, str(data.get("cluster_id") or data.get("family_id") or "")
    return "custom", ""


#: How deep a skills folder is walked: `exported_skills/domains/<cluster>/<id>/` is three.
MAX_DEPTH = 6


def _walk(root: Path, depth: int = 0, seen: set[tuple[int, int]] | None = None) -> Iterator[Path]:
    """Folders under `root` holding a SKILL.md; never descends into a package.

    Each real folder is visited once and the depth is capped: `a -> .` and
    `b -> .` symlinks once made the walk exponential (LP 20, L-3).
    """
    seen = set() if seen is None else seen
    try:
        st = root.stat()
    except OSError:
        return
    if (st.st_dev, st.st_ino) in seen and st.st_ino:
        return
    seen.add((st.st_dev, st.st_ino))
    if (root / SKILL_MD).is_file():
        yield root
        return
    if depth >= MAX_DEPTH:
        return
    try:
        children = sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith((".", "_")))
    except OSError:
        return
    for child in children:
        yield from _walk(child, depth + 1, seen)


def _stamp(root: Path) -> int:
    try:
        return root.stat().st_mtime_ns
    except OSError:
        return 0


@functools.lru_cache(maxsize=32)
def _scan_root(root: Path, _signature: tuple) -> dict[str, Package]:
    out: dict[str, Package] = {}
    for home in _walk(root):
        skill, edition = _identity(home)
        if skill in out:
            raise BindingError(f"SKILL_PACKAGE_DUPLICATE: {skill}: {out[skill].home} and {home}")
        kind, group = _classify(home, root)
        out[skill] = Package(skill, home, kind, group, edition)
    return out


def _scan_signature(root: Path) -> tuple:
    """Nested discovery changes invalidate lookup even when root mtime is unchanged."""
    try:
        resolved = root.resolve()
        if resolved == DEFAULT_PACK.resolve() or resolved == PLUGIN_SKILLS.resolve():
            return (("builtin", _stamp(resolved)),)
    except OSError:
        pass
    rows = []
    for home in _walk(root):
        for name in (SKILL_MD, CONTRACT):
            path = home / name
            if not path.is_file():
                continue
            with path.open('rb') as stream:
                raw = stream.read(FRONTMATTER_BYTES if name == SKILL_MD else 2 * 1024 * 1024 + 1)
            if name == CONTRACT and len(raw) > 2 * 1024 * 1024:
                raise BindingError('SKILL_CONTRACT_LIMIT: ' + str(path))
            rows.append((path.relative_to(root).as_posix(), hashlib.sha256(raw).hexdigest()))
    return tuple(rows)


def installed() -> dict[str, Package]:
    """Every skill folder on the search path, first root wins per id."""
    out: dict[str, Package] = {}
    for root in search_path():
        for skill, pkg in _scan_root(root, _scan_signature(root)).items():
            out.setdefault(skill, pkg)
    return out


@functools.lru_cache(maxsize=4)
def _shipped(_mtime: int) -> dict[str, Package]:
    import re as _re
    out: dict[str, Package] = {}
    root = DEFAULT_PACK.resolve()
    for pattern in ("domains/*/*/", "tasks/*/*/", "orchestration/*/"):
        for contract in sorted(root.glob(pattern + CONTRACT)):
            home = contract.parent
            raw_txt = contract.read_text(encoding="utf-8", errors="replace")
            m = _re.search(r"(?m)^skill:\s*([^\s#]+)", raw_txt)
            skill = m.group(1).strip("'\"") if m else str((yaml.safe_load(raw_txt) or {}).get("skill") or home.name)
            kind, group = _classify(home, root)
            out.setdefault(skill, Package(skill, home, kind, group, _identity(home)[1]
                                          if (home / SKILL_MD).is_file() else ""))
    return out


def shipped() -> dict[str, Package]:
    """The slots the release ships under `exported_skills/`, content or not.

    A slot folder carries its contract and manifest; its `SKILL.md` is there only
    for a free skill (or in the authoring repository). The slots are core, so this
    is read whether or not the folder is on the content search path.
    """
    return dict(_shipped(_stamp(DEFAULT_PACK)))


def installed_catalogue() -> Path | None:
    """The bundled `exported_skills/` when every slot it ships has its content.

    That is the authoring repository, whose catalogue gates validate the pack. A
    release ships slots with no content (four free skills aside), which is not a pack.
    """
    if not default_pack_enabled() or offers().get('distribution',{}).get('private_skill_count'):
        return None
    slots = shipped()
    if not slots or not all((pkg.home / SKILL_MD).is_file() for pkg in slots.values()):
        return None
    return DEFAULT_PACK


# --------------------------------------------------------------------------- #
# The slots: generated from core data
# --------------------------------------------------------------------------- #


@functools.lru_cache(maxsize=1)
def _registries() -> tuple[Any, Any]:
    # Identity lookup needs these two registries, not the template/pattern/tech
    # catalogue or a package generator on the first dispatch.
    from architect_framework.registry.domain_registry import DomainRegistry
    from architect_framework.registry.task_registry import TaskRegistry

    return DomainRegistry(include_installed=False), TaskRegistry(include_installed=False)


@functools.lru_cache(maxsize=1)
def catalogue_ids() -> frozenset[str]:
    """Every slot id the core declares: domains, tasks, the orchestrator."""
    from architect_framework.exporter.production_package_generator import (
        ORCHESTRATOR_SKILL_ID,
    )

    domains, tasks = _registries()
    ids = {s.id for c in domains.list_all_clusters() for s in c.skills}
    ids |= {t.id for f in tasks.list_all_families() for t in f.tasks}
    # Installed private descriptors are discovered separately and do not turn
    # into shipped slots or justify generating a missing purchased skill.
    return frozenset(ids | {ORCHESTRATOR_SKILL_ID})


@functools.lru_cache(maxsize=1)
def catalogue_domains() -> dict[str, str]:
    """`{domain slot id: cluster}`."""
    domains, _ = _registries()
    return {s.id: c.id for c in domains.list_all_clusters() for s in c.skills}


def _catalogue_key() -> str:
    digest = hashlib.sha256()
    for rel in _CATALOGUE_INPUTS:
        for path in sorted((Path(__file__).resolve().parent / rel).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and path != SLOT_OFFERS:
                digest.update(path.relative_to(Path(__file__).resolve().parent).as_posix().encode())
                digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


@functools.lru_cache(maxsize=1)
def catalogue_root() -> Path:
    """The generated slots, built once per core version under ``~/.architect-framework``.

    The generator that builds the pack, without its authored files: every slot's
    contract and manifest, and a generated `SKILL.md` that base mode briefs with.
    Built in a staging folder and moved into place, so an interrupted build never
    leaves half a catalogue behind.
    """
    target = home_dir() / "catalogue" / _catalogue_key()
    if (target / ".complete").is_file():
        return target
    from architect_framework.exporter.production_package_generator import (
        SkillPackageGenerator,
    )

    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="building-", dir=target.parent))
    try:
        build = staging / "catalogue"
        SkillPackageGenerator(regenerate_skill_md=True).generate_all_packages(build)
        (build / ".complete").write_text("generated by architect_framework.skillpacks\n", encoding="utf-8", newline="\n")
        if not (target / ".complete").is_file():
            shutil.rmtree(target, ignore_errors=True)
            os.replace(build, target)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return target


def catalogue() -> dict[str, Package]:
    """The generated package of every slot id."""
    root = catalogue_root()
    return dict(_scan_root(root, _stamp(root)))


def slot_home(skill: str) -> Path | None:
    """The folder whose contract governs `skill` (see :func:`_slot_home`)."""
    return _slot_home(skill)


def _slot_home(skill: str) -> Path | None:
    """The folder whose contract governs `skill`: an installed package carrying
    one, the slot the release ships, else the generated catalogue."""
    found = installed().get(skill)
    if found is not None and found.contract is not None:
        return found.home
    ship = shipped().get(skill)
    if ship is not None:
        return ship.home
    if skill in catalogue_ids():
        generated = catalogue().get(skill)
        return generated.home if generated is not None else None
    return None


def manifest_path(skill: str) -> Path | None:
    """`skill`'s `workspace-template.yml`: from its binding, an installed package, or the slot."""
    bound = _bound_home(skill)
    if bound is not None and (bound / MANIFEST).is_file():
        return bound / MANIFEST
    home = _slot_home(skill)
    return home / MANIFEST if home is not None and (home / MANIFEST).is_file() else None


@functools.lru_cache(maxsize=1)
def vendored() -> dict[str, Path]:
    """The SDD skills shipped with the core: `{skill: home}`."""
    out: dict[str, Path] = {}
    contracts_list = sorted(VENDOR_ROOT.glob(f"*/{CONTRACT}"))
    if not contracts_list:
        contracts_list = sorted(PLUGIN_SKILLS.glob(f"0[012]-*/{CONTRACT}"))
    for contract in contracts_list:
        # The registry id (`01-system-architect`) is the contract's `skill`; the
        # SKILL.md `name` is the client-facing one (`system-architect`).
        data = _package_contract(contract.parent)
        out[str(data.get("skill") or contract.parent.name)] = contract.parent
    return out


def domain_ids() -> frozenset[str]:
    """Every id that may own a module: catalogue domains, installed domains, bindings.

    Answered from data and folder names alone: asking never generates the slots.
    """
    ids = set(catalogue_domains())
    ids |= {k for k, p in installed().items() if p.kind == "domain"}
    return frozenset(ids | set(bindings()))


def known_owner(skill: str) -> bool:
    return skill in domain_ids()


def cluster_of(skill: str) -> str:
    found = installed().get(skill)
    if found is not None and found.kind == "domain":
        return found.group
    return catalogue_domains().get(skill, "")


# --------------------------------------------------------------------------- #
# Bindings
# --------------------------------------------------------------------------- #


def binding_files() -> tuple[tuple[Path, str], ...]:
    """`(file, content digest)` pairs, lowest precedence first; a later file wins per id."""
    files = []
    env = os.environ.get(ENV_BINDINGS, "").strip()
    if env:
        files.append(Path(env).expanduser())
    files.append(home_dir() / BINDINGS_FILE)
    if _ACTIVE_WORKSPACE.get() is not None:
        files.append(_ACTIVE_WORKSPACE.get() / BINDINGS_FILE)
    out = []
    for path in files:
        if not path.is_file():
            continue
        with path.open('rb') as stream:
            raw = stream.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            raise BindingError('SKILL_BINDING_LIMIT: binding file exceeds 1 MiB')
        out.append((path.resolve(), hashlib.sha256(raw).hexdigest()))
    return tuple(out)


class _BindingLoader(yaml.SafeLoader):
    pass


def _binding_mapping(loader, node):
    out = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if not isinstance(key, str):
            raise BindingError("SKILL_BINDING_KEY: mapping keys must be text")
        if key in out:
            raise BindingError("SKILL_BINDING_DUPLICATE: " + key)
        out[key] = loader.construct_object(value_node)
    return out


_BindingLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _binding_mapping)


@functools.lru_cache(maxsize=16)
def _read_bindings(files: tuple[tuple[Path, str], ...]) -> dict[str, tuple[str, Path | None, Path]]:
    """`{id: (target skill id or "", target folder or None, declaring file)}`."""
    out: dict[str, tuple[str, Path | None, Path]] = {}
    for path, expected in files:
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise BindingError("SKILL_BINDING_CHANGED: " + str(path))
        try:
            data = yaml.load(raw.decode("utf-8"), Loader=_BindingLoader) or {}
        except (yaml.YAMLError, UnicodeError) as error:
            raise BindingError("SKILL_BINDING_INVALID: " + str(path)) from error
        rows = data.get("bindings") if isinstance(data, Mapping) else None
        if not isinstance(rows, Mapping):
            raise BindingError(f"{path}: expected a `bindings:` mapping")
        for skill, target in rows.items():
            if isinstance(target, str) and target.strip():
                out[str(skill)] = (target.strip(), None, path)
            elif isinstance(target, Mapping) and target.get("path"):
                out[str(skill)] = ("", (path.parent / str(target["path"])).expanduser().resolve(), path)
            else:
                raise BindingError(f"{path}: binding for {skill!r} must be a skill id or {{path: …}}")
    return out


def bindings() -> dict[str, tuple[str, Path | None, Path]]:
    return dict(_read_bindings(binding_files()))


def _bound_home(skill: str, seen: tuple[str, ...] = ()) -> Path | None:
    if skill in seen:
        raise BindingError("SKILL_BINDING_CYCLE: " + " -> ".join((*seen, skill)))
    if len(seen) >= 64:
        raise BindingError("SKILL_BINDING_LIMIT: binding chain exceeds 64")
    row = _read_bindings(binding_files()).get(skill)
    if row is None:
        return None
    target, home, declared = row
    if home is not None:
        if not (home / SKILL_MD).is_file():
            raise BindingError(f"{declared}: {skill!r} is bound to {home}, which has no SKILL.md")
        return home
    if target in bindings():
        return _bound_home(target, (*seen, skill))
    if target in vendored():
        return vendored()[target]
    found = installed().get(target)
    if found is None:
        raise BindingError(f"{declared}: {skill!r} is bound to {target!r}, which no skills folder provides")
    return found.home


# --------------------------------------------------------------------------- #
# Resolution
# --------------------------------------------------------------------------- #


def _check_package_version(home: Path) -> None:
    metadata = _frontmatter(home / SKILL_MD).get('metadata') or {}
    version = metadata.get('framework_contract') if isinstance(metadata, Mapping) else None
    if version is not None and version not in {'sdd-core/v1', '1', '1.0'}:
        raise BindingError('SKILL_CONTRACT_UNSUPPORTED: ' + str(version))


def explain(skill: str, workspace: str | Path | None = None) -> dict[str, Any]:
    """Report precedence and pinned inputs without granting package authority."""
    with activated(workspace):
        selected = slot(skill)
        files = binding_files()
        return {'skill': skill, 'state': selected.state,
                'content': str(selected.content) if selected.content else None,
                'contract': str(selected.contract_home) if selected.contract_home else None,
                'search_path': [str(root) for root in search_path()],
                'binding_files': [{'path': str(path), 'sha256': stamp} for path, stamp in files],
                'precedence': 'Built-in core; explicit binding; first declared search root; shipped slot; optional base mode',
                'authority': 'Accepted workspace grants; package content grants no write capability'}


def slot(skill: str) -> Slot:
    """`skill`'s slot: its state, its content, and the contract that governs it."""
    if skill in vendored():
        return Slot(skill, CORE, vendored()[skill], vendored()[skill])
    bound = _bound_home(skill)
    if bound is not None:
        _check_package_version(bound)
        edition = _identity(bound)[1]
        own = bound if (bound / CONTRACT).is_file() else _slot_home(skill)
        return Slot(skill, LICENSED if edition == AGENSI_EDITION else THIRD_PARTY, bound, own)
    found = installed().get(skill)
    if found is not None:
        _check_package_version(found.home)
        state = LICENSED if found.edition == AGENSI_EDITION else THIRD_PARTY
        return Slot(skill, state, found.home, found.home if found.contract else _slot_home(skill))
    if skill not in catalogue_ids():
        return Slot(skill, EMPTY, None, None)
    if allow_base() and any(row['id']==skill and row.get('free') for row in offers().get('slots',[])):
        # The slot's contract as shipped; the brief is the generated SKILL.md,
        # which a shipped slot folder does not carry.
        generated = catalogue().get(skill)
        return Slot(skill, BASE, generated.home if generated else None, _slot_home(skill))
    return Slot(skill, EMPTY, None, _slot_home(skill))


def report(skills: list[str]) -> list[dict[str, Any]]:
    """One row per id: its slot state and where its content comes from."""
    rows = []
    for skill in sorted(set(skills)):
        try:
            s = slot(skill)
            rows.append({"skill": skill, "state": s.state, "content": str(s.content) if s.content else ""})
        except BindingError as exc:
            rows.append({"skill": skill, "state": "error", "content": str(exc)})
    return rows


# --------------------------------------------------------------------------- #
# Offers: what fills an empty slot, and for how much
# --------------------------------------------------------------------------- #


@functools.lru_cache(maxsize=2)
def _offers(_mtime: int) -> dict[str, Any]:
    if not SLOT_OFFERS.is_file():
        return {}
    return yaml.safe_load(SLOT_OFFERS.read_text(encoding="utf-8")) or {}


def offers() -> dict[str, Any]:
    """`skill-slots.yml`: every slot's price and pack, the packs, the suite, the store."""
    return dict(_offers(_stamp(SLOT_OFFERS)))


def offer(skill: str) -> dict[str, Any] | None:
    """What fills `skill`'s slot: its own price, and the pack that carries it."""
    data = offers()
    row = next((r for r in data.get("slots") or [] if r.get("id") == skill), None)
    if row is None:
        return None
    pack = next((p for p in data.get("packs") or [] if p.get("id") == row.get("pack")), None)
    return {"skill": skill, "price_usd": row.get("price_usd", 0), "free": bool(row.get("free")),
            "pack": row.get("pack") or "", "pack_title": (pack or {}).get("title", ""),
            "pack_price_usd": (pack or {}).get("price_usd", 0), "store": data.get("store", "")}


def advice(skill: str) -> str:
    """One line a user can act on: how to fill `skill`'s empty slot."""
    found = offer(skill)
    if found is None or found["free"]:
        return f"Install {skill} into {install_root()} (`skills install`), or bind your own in {BINDINGS_FILE}"
    via = f" or the {found['pack_title']} (${found['pack_price_usd']})" if found["pack"] else ""
    return (f"Buy {skill} (${found['price_usd']}){via} at {found['store']}, then `skills install <zip>`; "
            f"or bind your own in {BINDINGS_FILE}")


def cheapest_cover(skills: list[str]) -> dict[str, Any]:
    """The cheapest way to fill every slot in `skills`: packs, singles, or the suite.

    An exact search: at most a dozen packs touch any workspace, so every subset of
    them is priced, each with the singles it leaves uncovered.
    """
    data = offers()
    rows = {r["id"]: r for r in data.get("slots") or []}
    needed = sorted(s for s in set(skills) if s in rows and not rows[s].get("free"))
    packs = [p for p in data.get("packs") or [] if set(p.get("skills") or []) & set(needed)]
    singles_total = sum(rows[s]["price_usd"] for s in needed)
    best = {"total": singles_total, "packs": [], "singles": needed, "singles_total": singles_total}
    for mask in range(1, 1 << len(packs)):
        chosen = [p for i, p in enumerate(packs) if mask >> i & 1]
        covered = set().union(*(set(p["skills"]) for p in chosen))
        left = [s for s in needed if s not in covered]
        total = sum(p["price_usd"] for p in chosen) + sum(rows[s]["price_usd"] for s in left)
        if total < best["total"]:
            best = {"total": total, "packs": [p["id"] for p in chosen], "singles": left,
                    "singles_total": singles_total}
    suite = data.get("suite") or {}
    if needed and suite and suite.get("price_usd", 10**9) < best["total"]:
        best = {"total": suite["price_usd"], "packs": [suite["id"]], "singles": [], "singles_total": singles_total}
    return best


# --------------------------------------------------------------------------- #
# Install: put bought (or own) skills into their slot folders
# --------------------------------------------------------------------------- #


class InstallError(ValueError):
    """A skill cannot be installed: no SKILL.md, not a slot, or an unsafe archive."""


@dataclass(frozen=True)
class InstalledSkill:
    skill: str
    state: str  # the slot's state after installing: licensed or third-party
    dest: Path
    replaced: bool


#: Limits on what an archive may unpack to (LP 20, L-1): a skill pack is a few MB of text.
MAX_INSTALL_BYTES = 200 * 1024 * 1024
MAX_INSTALL_MEMBERS = 5000
MAX_COMPRESSION_RATIO = 100


def _extract(archive: Path, into: Path, budget: list[int]) -> None:
    """Unpack `archive` into `into`, refusing unsafe paths and anything bomb-shaped.

    `budget` is `[bytes, members]` left for the whole install, nested archives included.
    """
    import zipfile

    try:
        with zipfile.ZipFile(archive) as zf:
            infos = zf.infolist()
            for info in infos:
                parts = Path(info.filename).parts
                if Path(info.filename).is_absolute() or ".." in parts or (parts and ":" in parts[0]):
                    raise InstallError(f"{archive.name}: unsafe path {info.filename!r} in the archive")
                if info.compress_size and info.file_size > MAX_COMPRESSION_RATIO * info.compress_size \
                        and info.file_size > 1024 * 1024:
                    raise InstallError(f"{archive.name}: {info.filename!r} expands {info.file_size // info.compress_size}x; "
                                       "refusing what looks like a zip bomb")
            budget[0] -= sum(i.file_size for i in infos)
            budget[1] -= len(infos)
            if budget[0] < 0 or budget[1] < 0:
                raise InstallError(f"{archive.name}: more than {MAX_INSTALL_BYTES // (1024 * 1024)} MB or "
                                   f"{MAX_INSTALL_MEMBERS} files once unpacked; a skill pack is far smaller")
            zf.extractall(into)
    except zipfile.BadZipFile as exc:
        raise InstallError(f"{archive.name}: not a readable zip archive ({exc})") from exc


def _unpack(source: Path, work: Path) -> Path:
    """`source` as a folder: a folder as it is, an archive (and archives inside it) unpacked."""
    import zipfile

    budget = [MAX_INSTALL_BYTES, MAX_INSTALL_MEMBERS]
    if source.is_dir():
        root = source
    elif source.is_file() and zipfile.is_zipfile(source):
        root = work / "unpacked"
        _extract(source, root, budget)
    else:
        raise InstallError(f"{source} is neither a folder nor a zip archive")
    for i, inner in enumerate(sorted(p for p in root.rglob("*.zip") if not p.is_symlink())):
        _extract(inner, work / f"inner-{i}", budget)
    return work if root != source else root


def _slot_layout(skill: str, package_home: Path | None = None) -> Path:
    """`domains/<cluster>/<id>`, `tasks/<family>/<id>` or `orchestration/<id>`."""
    pkg = shipped().get(skill)
    if pkg is None and skill in catalogue_ids():
        pkg = catalogue().get(skill)
    if pkg is None:
        if package_home is not None:
            _verify_private_descriptor(package_home,skill)
            kind,group=_classify(package_home,package_home)
            if kind=='orchestration':return Path('orchestration')/skill
            return Path('domains' if kind=='domain' else 'tasks')/group/skill
        raise InstallError(f"{skill!r} is not a skill slot of this framework; "
                           f"to use it for a slot, bind it in {BINDINGS_FILE}")
    if pkg.kind == "orchestration":
        return Path("orchestration") / skill
    return Path("domains" if pkg.kind == "domain" else "tasks") / pkg.group / skill


def _verify_private_descriptor(home: Path, skill: str) -> None:
    import re
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,95}',skill):raise InstallError('PACK_ID_INVALID')
    _check_package_version(home)
    data=_package_contract(home)
    kind,group=_classify(home,home)
    if data.get('skill')!=skill or kind not in {'domain','task','orchestration'} or kind!='orchestration' and not re.fullmatch(r'[a-zA-Z0-9_-]+',group):
        raise InstallError(f'PACK_DESCRIPTOR_REQUIRED: {skill!r} is not a skill slot of this public core; install the complete compatible pack')
    manifest=home/PACKAGE
    if not manifest.is_file():raise InstallError('PACK_INTEGRITY_REQUIRED: missing package.yml')
    meta=yaml.safe_load(manifest.read_text(encoding='utf-8'))
    if not isinstance(meta,Mapping) or meta.get('skill')!=skill or not isinstance(meta.get('files'),list):raise InstallError('PACK_MANIFEST_INVALID')
    from architect_framework.distribution_policy import safe_relative
    witnessed=set()
    for row in meta['files']:
        name=row.get('path') if isinstance(row,Mapping) else None
        if not isinstance(name,str) or not safe_relative(name):raise InstallError('PACK_MANIFEST_INVALID')
        path=home/name
        if path.is_symlink() or any(p.is_symlink() for p in path.parents if p!=home and home in p.parents) or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=row.get('sha256'):
            raise InstallError('PACK_HASH_MISMATCH: '+name)
        witnessed.add(name)
    if not {SKILL_MD,CONTRACT}<=witnessed:raise InstallError('PACK_INTEGRITY_REQUIRED: body and descriptor hashes are required')


def _copy_content(home: Path, dest: Path, *, descriptors: bool = False) -> None:
    """The skill's own files, never the slot files and never a symlink (it could point at ~/.aws)."""
    for file in home.rglob("*"):
        rel = file.relative_to(home)
        if file.is_symlink() or file.is_dir() or (not descriptors and len(rel.parts) == 1 and rel.name in SLOT_FILES):
            continue
        if any(part.is_symlink() for part in [home / Path(*rel.parts[:i]) for i in range(1, len(rel.parts))]):
            continue
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, target)


def _install_locked(source: Path, *, replace_licensed: bool = False) -> list[InstalledSkill]:
    """Install every skill in `source` (a zip, a zip of zips, or a folder).

    Each skill goes to the folder of the slot its SKILL.md `name` fills, under
    :func:`install_root`, laid out like `exported_skills/`. Only content is
    copied: the slot files a package may carry are the core's and are skipped.
    Every skill is checked, and every one copied into a staging folder, before
    any installed folder is touched; each then replaces its slot in one rename.
    So a bad archive installs nothing and an interrupted copy leaves the old
    skill in place. A bought (licensed) skill is not replaced by one that is not,
    unless `replace_licensed` (LP 20, L-1).
    """
    source = Path(source).expanduser().resolve()
    staging = install_root() / ".staging"
    with tempfile.TemporaryDirectory(prefix="skills-install-") as tmp:
        root = _unpack(source, Path(tmp))
        homes = [h for h in _walk(root)] + [h for p in Path(tmp).glob("inner-*") for h in _walk(p)]
        homes = list(dict.fromkeys(homes))
        if not homes:
            raise InstallError(f"{source}: no SKILL.md inside")
        plan = []
        for home in homes:
            skill, edition = _identity(home)
            dest = install_root() / _slot_layout(skill,home)
            if any(previous[0]==skill for previous in plan):raise InstallError('PACK_DUPLICATE_ID: '+skill)
            if dest.is_dir() and not replace_licensed and edition != AGENSI_EDITION:
                _, current = _identity(dest)
                if current == AGENSI_EDITION:
                    raise InstallError(f"{skill}: the installed copy is a bought (licensed) skill and this one is "
                                       "not; pass --replace to replace it anyway")
            plan.append((skill, edition, home, dest))
        staging.mkdir(parents=True, exist_ok=True)
        staged = []
        try:
            for skill, edition, home, dest in plan:
                stage = Path(tempfile.mkdtemp(prefix=f"{skill}-", dir=staging))
                private=skill not in catalogue_ids()
                _copy_content(home, stage, descriptors=private)
                staged.append((skill, edition, stage, dest))
            out = [InstalledSkill(skill,LICENSED if edition==AGENSI_EDITION else THIRD_PARTY,dest,dest.exists())
                   for skill,edition,stage,dest in staged]
            from architect_framework.pack_transaction import commit
            commit(install_root(),[(stage,dest) for skill,edition,stage,dest in staged])
            shared_dst = install_root() / "_shared"
            if not shared_dst.is_dir():
                for shared_src in (root / "_shared", PLUGIN_SKILLS / "_shared", DEFAULT_PACK / "_shared"):
                    if shared_src.is_dir():
                        _copy_content(shared_src, shared_dst, descriptors=True)
                        break
        finally:
            if not (install_root()/'.pack-transaction.json').exists():
                shutil.rmtree(staging, ignore_errors=True)
    clear_caches()
    return out


def install(source: Path, *, replace_licensed: bool = False) -> list[InstalledSkill]:
    from architect_framework.pack_transaction import install_lock,recover,PackTransactionError
    try:
        with install_lock(install_root()):
            recover(install_root())
            return _install_locked(source,replace_licensed=replace_licensed)
    except PackTransactionError as error:
        raise InstallError(str(error)) from error


def slot_view(skill: str) -> dict[str, Any]:
    """One slot as every interface reports it (CLI, MCP, router): the same JSON."""
    try:
        s = slot(skill)
    except BindingError as exc:
        return {"skill": skill, "state": "error", "content": "", "advice": str(exc)}
    row: dict[str, Any] = {"skill": skill, "state": s.state, "content": str(s.content) if s.content else ""}
    if s.state in {EMPTY, BASE}:
        if s.state==EMPTY:row['code']='PACK_NOT_INSTALLED'
        row["advice"] = advice(skill)
        found = offer(skill)
        if found is not None:
            row["offer"] = {k: found[k] for k in ("price_usd", "pack", "pack_title", "pack_price_usd", "store")}
    return row


def _workspace_grants(workspace: str | Path):
    """Accepted core grant identities only; old workspace ledgers are inert."""
    from architect_framework.sdd_bridge import require_core
    from sdd_core.workspace import capture
    from sdd_core.storage import Store
    require_core(workspace)
    root=Path(workspace);snapshot=capture(root);store=Store(root);baseline=store.baseline()
    authority=store.load_snapshot(baseline['snapshot_digest']) if baseline else snapshot
    return authority.config.get('skills',{})


def workspace_slots(workspace: str | Path) -> list[str]:
    return sorted(_workspace_grants(workspace))


def workspace_report(workspace: str | Path) -> dict[str, Any]:
    """specification: what the CLI, the MCP tool and the plugin command all return for a workspace.

    Every slot the plan needs with its state, how many are filled, and the
    cheapest way to fill the empty ones.
    """
    root = Path(workspace).resolve()
    activate(root)
    rows = [{**slot_view(identity), "grant":grant} for identity,grant in sorted(_workspace_grants(root).items())]
    empty = [r["skill"] for r in rows if r["state"] in {EMPTY, BASE}]
    return {
        "workspace": str(root),
        "slots": rows,
        "required": len(rows),
        "filled": sum(1 for r in rows if r["state"] in {LICENSED, THIRD_PARTY, CORE}),
        "empty": empty,
        "cheapest_cover": cheapest_cover(empty) if empty else None,
        "store": offers().get("store", ""),
        "install_root": str(install_root()),
    }


def doctor() -> list[dict[str, str]]:
    """specification `skills doctor`: skill folders that will not do what their owner expects.

    * ``MISPLACED`` — a folder in the install tree that is not where its slot is
      (`domains/<cluster>/<id>/`, `tasks/<family>/<id>/`), so it was copied by hand;
    * ``NAME-MISMATCH`` — a folder whose name differs from its SKILL.md `name`
      (it still fills the slot named in SKILL.md, which may surprise);
    * ``NOT-A-SLOT`` — a skill on the search path whose `name` is no slot; it is
      used only when a binding points at it;
    * ``SHADOWED`` — a slot provided by two folders; the first on the search path wins;
    * ``BINDING`` — a binding that does not resolve.
    """
    findings: list[dict[str, str]] = []
    slots = catalogue_ids()
    seen: dict[str, Path] = {}
    bound_targets = {t for t, _, _ in bindings().values() if t}
    # Folders that exist for this framework's skills. An agent's own skills folder
    # (`~/.claude/skills`) holds unrelated skills too; those are not findings.
    dedicated = {install_root().resolve()} | {
        Path(p).expanduser().resolve() for p in os.environ.get(ENV_PATH, "").split(os.pathsep) if p.strip()}
    for root in search_path():
        for home in _walk(root):
            skill, _edition = _identity(home)
            if skill in slots and home.name != skill and root != install_root().resolve():
                findings.append({"code": "NAME-MISMATCH", "path": str(home),
                                 "message": f"folder {home.name!r} fills slot {skill!r} (its SKILL.md name)"})
            if root in dedicated and skill not in slots and skill not in bound_targets:
                findings.append({"code": "NOT-A-SLOT", "path": str(home),
                                 "message": f"{skill!r} is not a skill slot; bind it to use it (skill-bindings.yml)"})
            if skill in seen and skill in slots and                     (seen[skill] / SKILL_MD).read_bytes() != (home / SKILL_MD).read_bytes():
                findings.append({"code": "SHADOWED", "path": str(home),
                                 "message": f"{skill!r} is also at {seen[skill]}, a different copy, which wins"})
            seen.setdefault(skill, home)
            if root == install_root().resolve() and skill in slots:
                try:
                    expected = (install_root() / _slot_layout(skill)).resolve()
                except InstallError:
                    continue
                if home.resolve() != expected:
                    findings.append({"code": "MISPLACED", "path": str(home),
                                     "message": f"{skill!r} belongs at {expected}; reinstall it with `skills install`"})
    for skill in bindings():
        try:
            _bound_home(skill)
        except BindingError as exc:
            findings.append({"code": "BINDING", "path": skill, "message": str(exc)})
    return findings


def clear_caches() -> None:
    """Forget every scan: after installing a skill or editing bindings."""
    _scan_root.cache_clear()
    _shipped.cache_clear()
    _offers.cache_clear()
    _read_bindings.cache_clear()
    vendored.cache_clear()
    catalogue_ids.cache_clear()
    catalogue_domains.cache_clear()
    _registries.cache_clear()
    catalogue_root.cache_clear()
    try:
        from architect_framework.orchestrator.skill_router import _CORPUS_CACHE
        _CORPUS_CACHE.clear()
    except Exception:
        pass
