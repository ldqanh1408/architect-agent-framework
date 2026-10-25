"""Current shared loading, package assets and vocabulary. No phase or tree authority."""
from __future__ import annotations
import ast
import functools
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping
import yaml
ENV_FRAMEWORK_HOME = 'ARCHITECT_FRAMEWORK_HOME'
BUNDLED_HOME = Path(__file__).resolve().parent / '_home'

def framework_home() -> Path:
    """The folder holding `contracts/`, `scripts/`, `vendor/sdd-agent/` and `exported_skills/`.

    Derived, never a hard-coded path: `check_slot_coverage.py` once shipped with one
    developer's absolute drive path baked in, and ran on exactly one machine (specification M2).
    In order:

    1. `ARCHITECT_FRAMEWORK_HOME`, a checkout an installed package is pointed at;
    2. the checkout this package sits in, `<repo>/architect_framework/`;
    3. the copy a wheel carries in `architect_framework/_home/`, staged at build time by
       `scripts/stage_package_home.py` (specification, DG-specification (c)). Without it an installed
       package has no gate registry and no vendored skills.
    """
    override = os.environ.get(ENV_FRAMEWORK_HOME)
    if override and (Path(override) / 'contracts').is_dir():
        return Path(override).resolve()
    checkout = Path(__file__).resolve().parents[1]
    if (checkout / 'contracts').is_dir() or not BUNDLED_HOME.is_dir():
        return checkout
    return BUNDLED_HOME
REPO_ROOT = framework_home()

def documentation_path(name: str, root: Path | None=None) -> Path:
    """Locate a document after its execution plan has been archived.

    Archived plans remain regression/design evidence; they are no longer active
    work queues. Resolve their actual file instead of leaving a duplicate plan
    at the old location. A missing private document stays missing in a public
    distribution and must be reported as unavailable by its caller.
    """
    if Path(name).name != name or '\\' in name or ':' in name or (not name.endswith('.md')):
        raise ValueError('documentation name must be a Markdown basename')
    docs = (root or REPO_ROOT) / 'docs'
    current, archived = (docs / name, docs / 'archive' / name)
    if current.is_file() and archived.is_file():
        raise ValueError(f'two document authorities for {name}')
    return archived if archived.is_file() else current
VENDOR_ROOT = REPO_ROOT / 'vendor' / 'sdd-agent'
PACKAGE_DATA_DIR = Path(__file__).resolve().parent / 'data'
CONTRACT_PATHS: dict[str, Path] = {'page-classes': VENDOR_ROOT / 'contracts' / 'page-classes.yml', 'page-class-semantics': VENDOR_ROOT / 'contracts' / 'page-class-semantics.yml', 'docs-as-code-policy': VENDOR_ROOT / 'contracts' / 'docs-as-code-policy.yml', 'evidence-vocabulary': REPO_ROOT / 'contracts' / 'evidence-vocabulary.yml', 'gates': REPO_ROOT / 'contracts' / 'gates.yml', 'ui-glossary': REPO_ROOT / 'contracts' / 'ui-glossary.yml', 'workspace-skeleton': PACKAGE_DATA_DIR / 'workspace_skeleton.yaml' if (PACKAGE_DATA_DIR / 'workspace_skeleton.yaml').is_file() else REPO_ROOT / 'architect_framework' / 'data' / 'workspace_skeleton.yaml', 'skeleton-profiles': PACKAGE_DATA_DIR / 'skeleton_profiles.yaml' if (PACKAGE_DATA_DIR / 'skeleton_profiles.yaml').is_file() else REPO_ROOT / 'architect_framework' / 'data' / 'skeleton_profiles.yaml'}

class ContractError(RuntimeError):
    """A contract is missing, unparseable, or missing a required key."""

@functools.lru_cache(maxsize=None)
def _load(name: str) -> Mapping[str, Any]:
    try:
        path = CONTRACT_PATHS[name]
    except KeyError:
        known = ', '.join(sorted(CONTRACT_PATHS))
        raise ContractError(f'unknown contract {name!r}; known: {known}') from None
    if not path.is_file():
        raise ContractError(f'contract {name!r} not found at {path}')
    try:
        data = yaml.safe_load(path.read_text(encoding='utf-8'))
    except yaml.YAMLError as exc:
        raise ContractError(f'contract {name!r} is not valid YAML: {exc}') from exc
    if not isinstance(data, Mapping):
        raise ContractError(f'contract {name!r} must be a mapping, got {type(data).__name__}')
    return data

def raw(name: str) -> Mapping[str, Any]:
    """The parsed contract, cached. Prefer a typed accessor below."""
    return _load(name)

def available(name: str) -> bool:
    """True when the contract file exists — for contracts that land later."""
    return name in CONTRACT_PATHS and CONTRACT_PATHS[name].is_file()

def path_of(name: str) -> Path:
    if name not in CONTRACT_PATHS:
        raise ContractError(f'unknown contract {name!r}')
    return CONTRACT_PATHS[name]

def clear_cache():
    _load.cache_clear()
_PLACEHOLDER = re.compile('\\{([a-z][a-z0-9_-]*)\\}')

def substitute(path: str, **values: str) -> str:
    """Fill `{slug}`/`{module}`/`{submodule}`/`{cluster}`/`{skill}` in a slot path.

    A placeholder with no value is left intact rather than blanked, so an
    unresolved path is visibly unresolved instead of silently becoming a
    different real path.
    """

    def repl(match: re.Match[str]) -> str:
        name = match.group(1)
        if name in values and values[name]:
            return str(values[name])
        if name == 'slug' and values.get('module'):
            return str(values['module'])
        if name == 'module' and values.get('slug'):
            return str(values['slug'])
        return match.group(0)
    return _PLACEHOLDER.sub(repl, path)

def has_placeholder(path: str) -> bool:
    return bool(_PLACEHOLDER.search(path))

def page_classes() -> Mapping[str, Any]:
    out = _load('page-classes').get('page_classes')
    if not isinstance(out, Mapping):
        raise ContractError('page-classes declares no page_classes mapping')
    return out

def page_class_semantics() -> Mapping[str, Any]:
    return _load('page-class-semantics').get('page_classes') or {}

def evidence_tokens() -> dict[str, Mapping[str, Any]]:
    """`{token: definition}` from `contracts/evidence-vocabulary.yml`.

    Raises `ContractError` while the file does not exist. That is deliberate:
    the seam ledger validates `missing_evidence` against this vocabulary (plan
    section 5d.4 F-1), and silently accepting unvalidated token strings is the failure
    the ledger exists to prevent.
    """
    rows = _load('evidence-vocabulary').get('tokens') or []
    out: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        token = str(row.get('id', '')).strip()
        if not token:
            raise ContractError('evidence-vocabulary has a token with no id')
        if token in out:
            raise ContractError(f'evidence-vocabulary defines {token!r} twice')
        out[token] = row
    return out


def workspace_skeleton() -> Mapping[str, Any]:
    """Return the parsed `workspace_skeleton.yaml` contract."""
    return _load('workspace-skeleton')


def skeleton_slots() -> list[Mapping[str, Any]]:
    """Return all system/global slot definitions from `workspace_skeleton.yaml`."""
    return list(_load('workspace-skeleton').get('slots') or [])


def skeleton_module_slots() -> list[Mapping[str, Any]]:
    """Return all module/bounded-context slot definitions from `workspace_skeleton.yaml`."""
    return list(_load('workspace-skeleton').get('module_slots') or [])


def skeleton_archetypes() -> Mapping[str, Any]:
    """Return the 21 archetype definitions from `workspace_skeleton.yaml`."""
    return _load('workspace-skeleton').get('archetypes') or {}


def skeleton_profiles() -> Mapping[str, Any]:
    """Return all 5 profile definitions (`seed`, `minimal`, `standard`, `maximal`, `portfolio`) from `skeleton_profiles.yaml`."""
    return _load('skeleton-profiles').get('profiles') or {}


def profile_spec(profile: str = 'maximal') -> Mapping[str, Any]:
    """Return the configuration dictionary for a specific skeleton profile."""
    profiles = skeleton_profiles()
    return profiles.get(profile) or profiles.get('maximal') or {}
