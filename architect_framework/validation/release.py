from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

import yaml

from architect_framework import contracts
from architect_framework.registry.domain_registry import DomainRegistry
from architect_framework.registry.task_registry import TaskRegistry
from architect_framework.orchestrator.skill_router import ORCHESTRATOR_SKILL_ID


class ReleaseValidationError(ValueError):
    """Raised when an exported skill release is incomplete, stale, or tampered."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def registry_skill_ids() -> set[str]:
    return {ORCHESTRATOR_SKILL_ID} | {item.id for item in DomainRegistry().list_all_skills()} | {
        item.id for item in TaskRegistry().list_all_tasks()
    }


def tree_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): _sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def validate_release_manifest(skill_dir: Path, repo_root: Path | None = None) -> dict[str, Any]:
    skill_dir = Path(skill_dir).resolve()
    repo_root = (repo_root or contracts.REPO_ROOT).resolve()
    manifest_path = skill_dir / "release-manifest.yml"
    if not manifest_path.is_file():
        raise ReleaseValidationError("missing release-manifest.yml")
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ReleaseValidationError("release manifest must be a mapping")
    records = manifest.get("files")
    if not isinstance(records, list) or not records:
        raise ReleaseValidationError("release manifest files must be a non-empty list")

    errors: list[str] = []
    expected_ids = registry_skill_ids()
    actual_ids = {path.parent.name for path in skill_dir.rglob("skill-contract.yml")}
    if actual_ids != expected_ids:
        errors.append(
            f"registry coverage mismatch: missing={sorted(expected_ids-actual_ids)}, extra={sorted(actual_ids-expected_ids)}"
        )
    if manifest.get("package_count") != len(expected_ids):
        errors.append(
            f"package_count={manifest.get('package_count')} does not match registry count={len(expected_ids)}"
        )

    declared: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            errors.append("manifest file record must be a mapping")
            continue
        relative = record.get("path")
        if not isinstance(relative, str) or not relative or relative.startswith(("/", "\\")) or ".." in Path(relative).parts:
            errors.append(f"unsafe manifest path: {relative!r}")
            continue
        if relative in declared:
            errors.append(f"duplicate manifest path: {relative}")
            continue
        declared.add(relative)
        path = skill_dir / relative
        if not path.is_file():
            errors.append(f"missing declared file: {relative}")
            continue
        if record.get("sha256") != _sha256(path):
            errors.append(f"hash mismatch: {relative}")
        if record.get("bytes") != path.stat().st_size:
            errors.append(f"size mismatch: {relative}")

    actual = {
        path.relative_to(skill_dir).as_posix()
        for path in skill_dir.rglob("*")
        if path.is_file() and path != manifest_path
    }
    if declared != actual:
        errors.append(
            f"manifest coverage mismatch: missing={sorted(actual-declared)}, stale={sorted(declared-actual)}"
        )

    for relative in manifest.get("canonical_inputs", []):
        if not isinstance(relative, str) or not (repo_root / relative).is_file():
            errors.append(f"missing canonical input: {relative}")

    for package_manifest in skill_dir.rglob("package.yml"):
        package = package_manifest.parent
        data = yaml.safe_load(package_manifest.read_text(encoding="utf-8"))
        if data.get("skill") != package.name:
            errors.append(f"package identity mismatch: {package_manifest}")
        contract = package / "skill-contract.yml"
        if data.get("contract", {}).get("sha256") != _sha256(contract):
            errors.append(f"package contract hash mismatch: {package.name}")
        package_declared = {entry["path"] for entry in data.get("files", []) if isinstance(entry, dict) and "path" in entry}
        package_actual = {
            path.relative_to(package).as_posix()
            for path in package.rglob("*")
            if path.is_file() and path.name != "package.yml"
        }
        if package_declared != package_actual:
            errors.append(f"package manifest coverage mismatch: {package.name}")

    for required in ("sbom.cdx.json", "provenance.intoto.jsonl"):
        if not (skill_dir / required).is_file():
            errors.append(f"missing supply-chain artifact: {required}")

    if errors:
        raise ReleaseValidationError("; ".join(errors))
    return manifest


def is_core_tree(skill_dir: Path) -> bool:
    """A tree that carries the slots but not the pack: no release manifest, as in the public tree (specification)."""
    return not (Path(skill_dir) / "release-manifest.yml").is_file()


def validate_core_tree(skill_dir: Path) -> int:
    """Check a tree of slots without the paid content; return how many slots it holds.

    The public tree ships every slot's contract and package manifest but leaves the pack's
    content, release manifest, SBOM and provenance out. What can be checked there: the slots are
    exactly the registry's, each package manifest names its folder and the hash of its
    contract, and the shared validators are present (specification).
    """
    skill_dir = Path(skill_dir).resolve()
    errors: list[str] = []
    expected = registry_skill_ids()
    contracts_found = {p.parent.name: p.parent for p in skill_dir.rglob("skill-contract.yml")}
    actual = set(contracts_found)
    if actual != expected:
        errors.append(f"registry coverage mismatch: missing={sorted(expected - actual)}, extra={sorted(actual - expected)}")
    for name, package in sorted(contracts_found.items()):
        manifest = package / "package.yml"
        if not manifest.is_file():
            errors.append(f"slot without package.yml: {name}")
            continue
        data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
        if data.get("skill") != name:
            errors.append(f"package identity mismatch: {name}")
        if (data.get("contract") or {}).get("sha256") != _sha256(package / "skill-contract.yml"):
            errors.append(f"package contract hash mismatch: {name}")
        if (package / "SKILL.md").is_file():
            for entry in data.get("files") or []:
                if not isinstance(entry, dict) or "path" not in entry:
                    continue
                f_path = package / entry["path"]
                if not f_path.is_file():
                    errors.append(f"free package missing declared file {name}/{entry['path']}")
                elif entry.get("sha256") != _sha256(f_path):
                    errors.append(f"free package hash mismatch {name}/{entry['path']}")
                elif entry.get("bytes") != f_path.stat().st_size:
                    errors.append(f"free package size mismatch {name}/{entry['path']}")
    for required in ("_shared/scripts/check_skill_package.py",):
        if not (skill_dir / required).is_file():
            errors.append(f"missing shared validator: {required}")
    if errors:
        raise ReleaseValidationError("; ".join(errors[:20]) + (f"; … {len(errors) - 20} more" if len(errors) > 20 else ""))
    return len(actual)


def compare_with_fresh_generation(skill_dir: Path) -> None:
    """Fail if the *generated* part of the catalog drifted from the generator.

    This gate exists to catch a scaffolding file edited by hand instead of at its
    source, which would be silently reverted by the next export. It deliberately
    ignores the authored files: ``SKILL.md`` and ``references/research-basis.md``
    are written by people and exist nowhere but this catalog, so a fresh
    generation into an empty directory emits a template for them and *must*
    differ. Comparing those would make the gate fail permanently while proving
    nothing -- their integrity is covered by the package and release manifests
    instead.
    """
    from architect_framework.exporter.production_package_generator import (
        PRESERVED_FILES,
        PRESERVED_ROOT_FILES,
        SkillPackageGenerator,
    )

    skill_dir = Path(skill_dir).resolve()
    if not skill_dir.is_dir():
        raise ReleaseValidationError(f"skill directory does not exist: {skill_dir}")

    # Manifests record a hash for every file in the package, authored ones
    # included, so they differ whenever the authored content does. Their
    # correctness is checked directly against the files they describe by
    # validate_package_manifests and each package's check_skill_package.py.
    derived_from_authored = ("package.yml", "release-manifest.yml")

    def generated_only(snapshot: dict) -> dict:
        skip = set(PRESERVED_ROOT_FILES)
        tails = tuple(PRESERVED_FILES) + derived_from_authored
        return {
            path: digest
            for path, digest in snapshot.items()
            if path not in skip
            and not any(path == name or path.endswith(f"/{name}") for name in tails)
        }

    with tempfile.TemporaryDirectory(prefix="architect-skills-check-") as temp_dir:
        fresh = Path(temp_dir) / "exported_skills"
        SkillPackageGenerator().generate_all_packages(fresh)
        live_snapshot = generated_only(tree_snapshot(skill_dir))
        fresh_snapshot = generated_only(tree_snapshot(fresh))
        if live_snapshot != fresh_snapshot:
            missing = sorted(fresh_snapshot.keys() - live_snapshot.keys())
            extra = sorted(live_snapshot.keys() - fresh_snapshot.keys())
            changed = sorted(
                path for path in fresh_snapshot.keys() & live_snapshot.keys()
                if fresh_snapshot[path] != live_snapshot[path]
            )
            raise ReleaseValidationError(
                f"live export differs from fresh generation: missing={missing}, extra={extra}, changed={changed}"
            )


def write_supply_chain_artifacts(output_dir: Path, sources_file: Path) -> None:
    output_dir = Path(output_dir)
    source_data = yaml.safe_load(Path(sources_file).read_text(encoding="utf-8"))
    sources = source_data.get("sources", [])
    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "component": {
                "type": "application",
                "name": "architect-agent-framework-exported-skills",
                "version": "2026.07",
                "licenses": [{"license": {"id": "MIT"}}],
            }
        },
        "components": [
            {
                "type": "data",
                "name": source["id"],
                "version": source.get("revision", "unversioned-reference"),
                "externalReferences": [{"type": "vcs", "url": source["url"]}],
                "licenses": [{"expression": source["license_expression"]}],
                "properties": [
                    {"name": "architect-framework:usage", "value": source["usage"]},
                    {"name": "architect-framework:retrieved-at", "value": str(source["retrieved_at"])},
                ],
            }
            for source in sources
        ],
    }
    (output_dir / "sbom.cdx.json").write_text(
        json.dumps(sbom, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    statements = []
    for source in sources:
        statements.append({
            "_type": "https://in-toto.io/Statement/v1",
            "subject": [{"name": source["id"], "digest": {"sha256": "idea-only-no-vendored-bytes"}}],
            "predicateType": "https://architect-agent-framework.dev/provenance/idea-reference/v1",
            "predicate": {
                "source": source["url"],
                "license_expression": source["license_expression"],
                "usage": source["usage"],
                "retrieved_at": str(source["retrieved_at"]),
                "copied_bytes": False,
            },
        })
    (output_dir / "provenance.intoto.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in statements),
        encoding="utf-8",
        newline="\n",
    )
