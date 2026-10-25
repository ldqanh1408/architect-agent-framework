"""Freeze bounded skill inputs; accepted workspace grants alone authorize writes."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

from architect_framework import skillpacks
from architect_framework.runtime import skills
from sdd_core.model import SddError, Status, digest


def _package_digest(home):
    home = Path(home)
    if home.is_symlink() or not home.is_dir():
        raise ValueError("Skill package must be a regular directory")
    files, total = {}, 0
    for directory, folders, names in os.walk(home, followlinks=False):
        folders[:] = sorted(name for name in folders if name not in {".git", "__pycache__", "node_modules", ".pytest_cache"})
        if any((Path(directory) / name).is_symlink() for name in folders):
            raise ValueError("Skill package contains a directory symlink")
        for name in sorted(names):
            path = Path(directory) / name
            if path.is_symlink() or not path.is_file():
                raise ValueError("Skill package contains a nonregular file")
            with path.open("rb") as handle:
                raw = handle.read(2 * 1024 * 1024 + 1)
            total += len(raw)
            if len(raw) > 2 * 1024 * 1024 or len(files) >= 1024 or total > 16 * 1024 * 1024:
                raise ValueError("Skill package exceeds bounded input limits")
            files[path.relative_to(home).as_posix()] = hashlib.sha256(raw).hexdigest()
    return digest(files)


def resolve(workspace, identity):
    try:
        with skillpacks.activated(workspace):
            try:
                contract = skills.load(identity)
            except skills.UnknownSkill:
                from sdd_core.workspace import capture
                declaration=capture(workspace).config.get('skills',{}).get(identity,{})
                if declaration.get('source')!='host':
                    raise SddError("PACK_NOT_INSTALLED", "Install or bind this package, or explicitly declare a host-provided skill with source: host", Status.INCOMPLETE)
                return {"source": "host", "slot_state": "host-provided", "brief_sha256": None,
                        "contract_sha256": None, "package_sha256": None}, None
            if contract.slot_state == skillpacks.EMPTY:
                raise SddError("SKILL_SLOT_EMPTY", "Install or bind skill content before preparing a run", Status.INCOMPLETE)
            before = _package_digest(contract.home)
            body = contract.skill_text_for(workspace)
            if not body.strip():
                raise ValueError("Skill brief is empty")
            brief = ("Package directory (read-only input): " + str(Path(contract.home).resolve())
                     + "\nAccepted workspace grants control all writes.\n\n" + body)
            contract_hash = (hashlib.sha256(Path(contract.contract_source).read_bytes()).hexdigest()
                             if contract.contract_source else digest(contract.raw))
            if before != _package_digest(contract.home):
                raise SddError("SKILL_INPUT_MUTATING", "Skill inputs changed while reading", Status.STALE)
            return {"source": "package", "slot_state": contract.slot_state,
                    "package_sha256": before, "contract_sha256": contract_hash,
                    "brief_sha256": hashlib.sha256(brief.encode("utf-8")).hexdigest()}, brief
    except (OSError, ValueError, TypeError, KeyError) as error:
        raise SddError("SKILL_INPUT_INVALID", str(error), Status.INCOMPLETE) from error


def require_current(workspace, task):
    try:
        current, brief = resolve(workspace, task["skill"])
    except SddError as error:
        raise SddError("RUN_SKILL_STALE", "Skill inputs are unavailable or changed; prepare a new run", Status.STALE) from error
    if current != task["skill_input"]:
        raise SddError("RUN_SKILL_STALE", "Skill inputs changed; preserve results and prepare a new run", Status.STALE)
    return brief
