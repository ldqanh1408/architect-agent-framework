"""Validate explicit active references instead of imposing legacy prose headings."""
from pathlib import Path

import yaml


def validate_active(skill_dir):
    root = Path(skill_dir).resolve()
    path = root / "workflow-contract.yml"
    if not path.is_file():
        return None
    try:
        contract = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return [f"workflow contract cannot be read: {exc}"]
    if not isinstance(contract, dict) or contract.get("schema_version") != "sdd-skill/v2":
        return ["workflow contract must declare sdd-skill/v2"]
    errors = []
    try:
        text = (root / "SKILL.md").read_text(encoding="utf-8")
        parts = text.split("---", 2)
        metadata = yaml.safe_load(parts[1]) if text.startswith("---\n") and len(parts) == 3 else None
        if not isinstance(metadata, dict) or metadata.get("name") != root.name:
            errors.append("SKILL.md name must match the canonical workflow skill identity")
        if not isinstance(metadata, dict) or not isinstance(metadata.get("description"), str) or not 1 <= len(metadata["description"]) <= 1024:
            errors.append("SKILL.md needs a nonempty description of at most 1024 characters")
    except (OSError, yaml.YAMLError) as exc:
        errors.append(f"SKILL.md frontmatter cannot be read: {exc}")
    if contract.get("skill") != root.name:
        errors.append("workflow contract identity differs from the skill directory")
    if not contract.get("required_references"):
        errors.append("workflow contract must declare its active domain method")
    if contract.get("state_authority") != "sdd_core.engine":
        errors.append("workflow contract must identify the engine state authority")
    if any(key.startswith("legacy_") for key in contract):
        errors.append("Active contracts cannot declare a legacy workflow")
    refs = [contract.get("workflow"), *contract.get("required_references", [])]
    refs.extend(row.get("path") for row in contract.get("conditional_references", []))
    for ref in refs:
        if not isinstance(ref, str) or not ref:
            errors.append("workflow reference is missing")
            continue
        target = (root / ref).resolve()
        if root not in target.parents or target.is_symlink() or not target.is_file():
            errors.append(f"required reference does not resolve inside the skill: {ref}")
        elif not target.read_text(encoding="utf-8").strip():
            errors.append(f"required reference is empty: {ref}")
        if "legacy-workflow-v1" in ref:
            errors.append("historical archives cannot replace an active domain method")
    return errors
