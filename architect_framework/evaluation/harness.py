from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


class ScenarioValidationError(ValueError):
    """Raised when a deterministic scenario contract is invalid or fails."""


VALID_ROUTES = {"complete", "blocked", "resumable", "rejected"}
VALID_KINDS = {"golden", "adversarial", "resume", "stale", "ownership", "wrong-route"}


def validate_scenario(data: dict[str, Any], path: Path) -> None:
    required = {"schema_version", "scenario_id", "skill", "kind", "setup", "request", "expect", "oracle", "evidence_class"}
    missing = required - set(data)
    errors: list[str] = []
    if missing:
        errors.append(f"missing keys: {sorted(missing)}")
    if data.get("kind") not in VALID_KINDS:
        errors.append(f"invalid kind: {data.get('kind')}")
    request = data.get("request", {})
    expect = data.get("expect", {})
    if expect.get("status") not in VALID_ROUTES:
        errors.append(f"invalid expected status: {expect.get('status')}")
    if request.get("expected_route") and request.get("expected_route") != data.get("skill"):
        errors.append("expected_route must match scenario skill")
    for field in ("required_artifacts", "forbidden_artifacts", "diagnostic_codes"):
        if not isinstance(expect.get(field), list):
            errors.append(f"expect.{field} must be a list")
    oracle = data.get("oracle", {})
    if oracle.get("shell") is not False or not isinstance(oracle.get("argv"), list) or not oracle.get("argv"):
        errors.append("oracle must use non-empty argv with shell=false")
    if not isinstance(oracle.get("expected_exit"), int):
        errors.append("oracle.expected_exit must be an integer")
    setup = data.get("setup", {})
    if setup.get("network") not in {"none", "allowlisted"}:
        errors.append("setup.network must be none or allowlisted")
    if errors:
        raise ScenarioValidationError(f"{path}: " + "; ".join(errors))


def validate_scenario_tree(skill_dir: Path) -> int:
    skill_dir = Path(skill_dir)
    scenarios = sorted(skill_dir.rglob("evaluations/*.yml"))
    if not scenarios:
        raise ScenarioValidationError("no evaluation scenarios found")
    from architect_framework.validation.release import is_core_tree
    if is_core_tree(skill_dir):
        package_ids = {path.parent.name for path in skill_dir.rglob("SKILL.md") if (path.parent / "skill-contract.yml").is_file()}
    else:
        package_ids = {path.parent.name for path in skill_dir.rglob("skill-contract.yml")}
    seen: set[str] = set()
    covered: dict[str, set[str]] = {skill: set() for skill in package_ids}
    for path in scenarios:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ScenarioValidationError(f"{path}: scenario must be a mapping")
        validate_scenario(data, path)
        scenario_id = data["scenario_id"]
        if scenario_id in seen:
            raise ScenarioValidationError(f"duplicate scenario_id: {scenario_id}")
        seen.add(scenario_id)
        if data["skill"] not in package_ids:
            raise ScenarioValidationError(f"unknown scenario skill: {data['skill']}")
        covered[data["skill"]].add(data["kind"])
    missing = {skill: sorted({"golden", "adversarial"} - kinds) for skill, kinds in covered.items() if not {"golden", "adversarial"}.issubset(kinds)}
    if missing:
        raise ScenarioValidationError(f"missing required scenario kinds: {missing}")
    return len(scenarios)


def _catalog_root(package: Path) -> Path:
    """The catalog directory above a package, identified by its shared tree.

    Found by searching rather than by counting parents: domain and task packages
    sit three levels below the catalog root and the orchestrator sits two.
    """
    for parent in package.parents:
        if (parent / "_shared").is_dir():
            return parent
    raise ScenarioValidationError(f"no _shared/ directory above {package}; oracles cannot resolve their validators")


def run_fixture_oracle(scenario_path: Path, workspace: Path, package: Path, python: str = sys.executable) -> subprocess.CompletedProcess[str]:
    """Run a scenario oracle against a caller-prepared fixture workspace.

    This deliberately does not invoke an LLM. It proves only the deterministic
    scenario/oracle boundary and must not be reported as live-agent evidence.
    """
    data = yaml.safe_load(Path(scenario_path).read_text(encoding="utf-8"))
    validate_scenario(data, Path(scenario_path))
    package_path = Path(package).resolve()
    substitutions = {
        "{python}": python,
        "{workspace}": str(Path(workspace).resolve()),
        "{package}": str(package_path),
        # Validators are shared by the whole catalog, so an oracle addresses them
        # from the catalog root while its contract stays package-relative.
        "{catalog}": str(_catalog_root(package_path)),
    }
    argv = []
    for value in data["oracle"]["argv"]:
        rendered = str(value)
        for token, replacement in substitutions.items():
            rendered = rendered.replace(token, replacement)
        argv.append(rendered)
    result = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        encoding="utf-8",
        shell=False,
        timeout=int(data["limits"]["timeout_seconds"]),
    )
    if result.returncode != data["oracle"]["expected_exit"]:
        raise ScenarioValidationError(
            f"oracle exit mismatch for {scenario_path}: expected={data['oracle']['expected_exit']} actual={result.returncode} stdout={result.stdout} stderr={result.stderr}"
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("skilldir", type=Path)
    args = parser.parse_args()
    try:
        count = validate_scenario_tree(args.skilldir)
    except ScenarioValidationError as exc:
        print(f"[FAILED] {exc}")
        raise SystemExit(1)
    print(f"[PASSED] {count} deterministic scenario contracts are valid.")


if __name__ == "__main__":
    main()
