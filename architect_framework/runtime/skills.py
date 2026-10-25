"""Load a skill's contract as the agent's runtime definition.

An agent is `(skill package, scope, run-id)`; its identity is the `skill` field of
the contract, and nothing here adds configuration the contract does not declare.

Every skill is a slot (:mod:`architect_framework.skillpacks`): its contract is
core, its content is optional. Every slot id loads; `AgentContract.slot_state`
says whether it has content to brief the agent with.
"""

from __future__ import annotations

import dataclasses
import functools
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from architect_framework import skillpacks
from architect_framework.contracts import REPO_ROOT

#: The bundled pack. Read it through :mod:`skillpacks`, never directly: it may be
#: absent, switched off, or shadowed by a pack the user installed first.
EXPORTED = skillpacks.DEFAULT_PACK
#: The vendored SDD phase-1 skills — the core, always present. The V3 workspace
#: plan names `01-system-architect` as owner of the global pages.
SDD_ROOT = REPO_ROOT / "vendor" / "sdd-agent"
_CONTRACT_NAME = "skill-contract.yml"


class UnknownSkill(KeyError):
    """No installed, bound or vendored package declares this skill id."""


@dataclass(frozen=True)
class Output:
    path: str  # relative to output_root, placeholders intact
    page_class: str

    @property
    def name(self) -> str:
        return PurePosixPath(self.path).name


@dataclass(frozen=True)
class AgentContract:
    skill: str
    kind: str  # domain | task | orchestration
    group: str  # task family id, or domain cluster id
    owns: tuple[str, ...]
    read_only: tuple[str, ...]
    forbidden_writes: tuple[str, ...]
    required_inputs: tuple[str, ...]
    anti_triggers: tuple[str, ...]
    required_outputs: tuple[Output, ...]
    completion_evidence: tuple[str, ...]
    blocking_conditions: tuple[str, ...]
    resume_states: tuple[str, ...]
    compatible_task_families: tuple[str, ...] = ()
    compatible_domain_clusters: tuple[str, ...] = ()
    validators: tuple[str, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)
    contract_source: str = field(default="", repr=False, compare=False)
    home: str = field(default="", repr=False, compare=False)  # the folder whose SKILL.md briefs it
    #: The slot's state (`skillpacks`): licensed, third-party, base, empty, or core.
    slot_state: str = field(default="", compare=False)

    @property
    def skill_text(self) -> str:
        """The package's SKILL.md, or empty when it ships none."""
        path = Path(self.home) / "SKILL.md" if self.home else None
        return _brief_text(path) if path and path.is_file() else ""

    def skill_text_for(self, workspace: Path | str) -> str:
        """Resolve the active brief, including its method and selected lifecycle.

        The executor cannot assume a model will open Markdown links. Missing or
        escaping references are contract errors, never an empty successful brief.
        Conditional references are included too: their applicability remains a
        domain decision, but the executor always makes their instructions available.
        """
        if not self.home:
            return ""
        home = Path(self.home).resolve()
        contract_path = home / "workflow-contract.yml"
        if not contract_path.is_file():
            return self.skill_text
        from architect_framework.sdd_bridge.mode import classify
        if classify(workspace)["state"] != "current":
            raise ValueError("Initialize or migrate a current workspace before loading this workflow")
        contract = _load_yaml(contract_path)
        if not contract.get("workflow"):
            raise ValueError(f"{self.skill}: missing core workflow")
        refs = [contract["workflow"], *contract.get("required_references", [])]
        refs += [r["path"] for r in contract.get("conditional_references", [])]
        if len(refs) > 64:
            raise ValueError("Skill brief exceeds 64 references")
        parts = [self.skill_text]
        for ref in dict.fromkeys(refs):
            path = (home / ref).resolve()
            if home not in path.parents or not path.is_file():
                raise ValueError(f"{self.skill}: invalid required reference {ref!r}")
            parts.append(f"\n\n## Runtime reference: {ref}\n\n" + _brief_text(path))
        if sum(len(part.encode("utf-8")) for part in parts) > 8 * 1024 * 1024:
            raise ValueError("Skill brief exceeds 8 MiB")
        return "".join(parts)

    @property
    def family(self) -> str | None:
        return self.group if self.kind == "task" else None

    @property
    def cluster(self) -> str | None:
        return self.group if self.kind == "domain" else None


def _brief_text(path: Path) -> str:
    with path.open("rb") as handle:
        raw = handle.read(2 * 1024 * 1024 + 1)
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError("Skill input exceeds 2 MiB: " + str(path))
    return raw.decode("utf-8")


def _tuple(value: Any) -> tuple[str, ...]:
    return tuple(str(v) for v in (value or []))


def _load_yaml(path: Path) -> Mapping[str, Any]:
    loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
    return yaml.load(path.read_text(encoding="utf-8"), Loader=loader) or {}


def _from_file(path: Path, *, kind: str | None = None, group: str | None = None) -> AgentContract:
    data = _load_yaml(path)
    kind = kind or {"domains": "domain", "tasks": "task"}.get(path.parts[-4], "orchestration")
    outputs = []
    for row in data.get("required_outputs") or []:
        if isinstance(row, Mapping):
            outputs.append(Output(str(row.get("path", "")), str(row.get("page_class", ""))))
        else:
            outputs.append(Output(str(row), ""))
    resume = data.get("resume_policy") or {}
    return AgentContract(
        skill=str(data.get("skill") or path.parent.name),
        kind=kind,
        group=path.parent.parent.name if group is None else group,
        owns=_tuple(data.get("owns")),
        read_only=_tuple(data.get("read_only")),
        forbidden_writes=_tuple(data.get("forbidden_writes")),
        required_inputs=_tuple(data.get("required_inputs")),
        anti_triggers=_tuple(data.get("anti_triggers")),
        required_outputs=tuple(outputs),
        completion_evidence=_tuple(data.get("completion_evidence")),
        blocking_conditions=_tuple(data.get("blocking_conditions")),
        resume_states=_tuple(resume.get("states") if isinstance(resume, Mapping) else ()),
        compatible_task_families=_tuple(data.get("compatible_task_families")),
        compatible_domain_clusters=_tuple(data.get("compatible_domain_clusters")),
        validators=_tuple(data.get("validators")),
        raw=data,
        contract_source=str(path),
        home=str(path.parent),
    )


def _contract_less(skill: str, home: Path, kind: str) -> AgentContract:
    """A skill that ships only a SKILL.md and stands behind no slot.

    It declares no outputs of its own, so every page it writes comes from the
    plan, and the sandbox scopes it to exactly those pages.
    """
    return AgentContract(
        skill=skill, kind=kind, group="", owns=(), read_only=(), forbidden_writes=(),
        required_inputs=(), anti_triggers=(), required_outputs=(), completion_evidence=(),
        blocking_conditions=(), resume_states=(), raw={}, home=str(home),
    )


_SLOT_KINDS = frozenset({"domain", "task", "orchestration"})


@functools.lru_cache(maxsize=4)
def _slot_contracts(search_path: tuple[Path, ...]) -> dict[str, AgentContract]:
    """Every slot's contract (the khe), keyed by id: from an installed package that
    carries one, else from the slots the core generates. No content attached."""
    out: dict[str, AgentContract] = {}
    for skill, pkg in skillpacks.installed().items():
        # A contract that came with the workspace does not set its own sandbox (LP 20, L-2).
        if pkg.kind in _SLOT_KINDS and pkg.contract is not None and skillpacks.contract_trusted(pkg.home):
            out[skill] = _from_file(pkg.contract, kind=pkg.kind, group=pkg.group)
    for skill, pkg in skillpacks.shipped().items():  # the slots the release ships
        if skill not in out and pkg.contract is not None:
            out[skill] = _from_file(pkg.contract, kind=pkg.kind, group=pkg.group)
    missing = skillpacks.catalogue_ids() - set(out)
    if missing:
        generated = skillpacks.catalogue()
        for skill in sorted(missing):
            pkg = generated.get(skill)
            if pkg is not None and pkg.contract is not None:
                out[skill] = _from_file(pkg.contract, kind=pkg.kind, group=pkg.group)
    return out


def _with_content(contract: AgentContract, slot: skillpacks.Slot) -> AgentContract:
    return dataclasses.replace(contract, home=str(slot.content) if slot.content else "", slot_state=slot.state)


def all_contracts() -> dict[str, AgentContract]:
    """Every slot, keyed by id, briefed from whatever fills it (`skillpacks.slot`)."""
    return dict(_all_contracts(skillpacks.search_path(), skillpacks.binding_files(), skillpacks.allow_base()))


@functools.lru_cache(maxsize=4)
def _all_contracts(search_path: tuple[Path, ...], _bindings: tuple, _base: bool) -> dict[str, AgentContract]:
    return {skill: _with_content(c, skillpacks.slot(skill))
            for skill, c in _slot_contracts(search_path).items()}


@functools.lru_cache(maxsize=1)
def sdd_contracts() -> dict[str, AgentContract]:
    """The vendored SDD skills, as agents the runtime can run.

    Kept apart from :func:`all_contracts`: that is the exported catalogue, whose
    counts the plan measures, and these packages are not part of it.
    """
    out: dict[str, AgentContract] = {}
    paths = sorted(SDD_ROOT.glob("*/" + _CONTRACT_NAME))
    if not paths:
        paths = sorted(skillpacks.PLUGIN_SKILLS.glob("0[012]-*/" + _CONTRACT_NAME))
    for path in paths:
        contract = dataclasses.replace(_from_file(path, kind="sdd"), slot_state=skillpacks.CORE)
        out[contract.skill] = contract
    return out


def load(skill: str) -> AgentContract:
    """The contract `skill` runs under, and the content it is briefed with.

    The contract is the slot's: a binding or an installed folder replaces it only
    when it ships its own `skill-contract.yml`. A folder with a SKILL.md alone
    keeps the slot's contract, so the pages, page classes and sandbox stay those
    the plan was built for — only the brief changes.
    """
    if skill in sdd_contracts():
        return sdd_contracts()[skill]
    slot = skillpacks.slot(skill)
    if slot.content is None and slot.contract_home is None:
        raise UnknownSkill(skill)
    governing = _slot_contracts(skillpacks.search_path()).get(skill)
    own = slot.contract_home / _CONTRACT_NAME if slot.contract_home is not None else None
    if (own is not None and own.is_file() and skillpacks.contract_trusted(own.parent)
            and (governing is None or Path(governing.home) != slot.contract_home)):
        # A bound folder that ships its own contract replaces the slot's.
        governing = _from_file(own, kind="bound", group="")
    if governing is None:
        if slot.content is None:
            raise UnknownSkill(skill)
        governing = _contract_less(skill, slot.content, "custom")
    return _with_content(governing, slot)


def slot_state(skill: str) -> str:
    """`skill`'s slot state: licensed, third-party, base, empty, or core."""
    return load(skill).slot_state


def skill_ids() -> frozenset[str]:
    return frozenset(all_contracts())


def agent_ids() -> frozenset[str]:
    """Every id the runtime can schedule: the slots, the SDD skills, and bindings.

    An empty slot is schedulable; whether its job writes is the slot's state.
    """
    return frozenset(all_contracts()) | frozenset(sdd_contracts()) | frozenset(skillpacks.bindings())


def domains() -> list[AgentContract]:
    return [c for c in all_contracts().values() if c.kind == "domain"]


def tasks() -> list[AgentContract]:
    return [c for c in all_contracts().values() if c.kind == "task"]
