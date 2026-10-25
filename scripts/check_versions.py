#!/usr/bin/env python3
"""Verify that every place declaring a version agrees with ``VERSION``.

Version drift is the quietest way a release goes wrong: a tag says v1.1.0, the
wheel says 1.0.0, and the plugin manifest says something else again. Users then
report bugs against a version that never existed. This check runs in CI so the
drift is caught before a tag is pushed rather than after.

Two version namespaces exist on purpose and are checked separately:

  * **Release version** (``VERSION``) -- the repository/tag version. Must match
    ``pyproject.toml`` and ``plugins/architect-agent-framework/.claude-plugin/plugin.json``.
  * **Catalog version** -- the ``version:`` field inside each ``SKILL.md``.
    Skill packages evolve on their own cadence, so they are only required to be
    *internally consistent*, not equal to the release version.

Usage::

    python scripts/check_versions.py            # exit 1 on any mismatch
    python scripts/check_versions.py --json     # machine-readable report
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from packaging.version import Version

REPO_ROOT = Path(__file__).resolve().parents[1]

SEMVER = re.compile(r"^\d+\.\d+\.\d+([-+][0-9A-Za-z.-]+)?$")


def read_release_version() -> str:
    path = REPO_ROOT / "VERSION"
    if not path.is_file():
        raise SystemExit("missing VERSION file at repository root")
    return path.read_text(encoding="utf-8").strip()


def read_pyproject_version() -> str | None:
    path = REPO_ROOT / "pyproject.toml"
    if not path.is_file():
        return None
    match = re.search(r'(?m)^version\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def read_lock_version() -> str | None:
    path=REPO_ROOT/'uv.lock'
    if not path.is_file():return None
    for block in path.read_text(encoding='utf-8').split('[[package]]')[1:]:
        if re.search(r'(?m)^name = "architect-agent-framework"$',block):
            match=re.search(r'(?m)^version = "([^"]+)"$',block)
            return match.group(1) if match else '<missing>'
    return '<missing>'


def read_readme_vi_version() -> str | None:
    path = REPO_ROOT / "README.vi.md"
    if not path.is_file():
        return None
    match = re.search(r"(?m)^Bản bàn giao: \*\*([^*]+)\*\*", path.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def read_init_version() -> str | None:
    path = REPO_ROOT / "architect_framework" / "__init__.py"
    if not path.is_file():
        return None
    match = re.search(r'(?m)^__version__\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def read_mcp_server_version() -> str | None:
    path = REPO_ROOT / "architect_framework" / "runtime" / "mcp_server.py"
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    if "_AAF_VERSION" in text:
        return read_init_version()
    match = re.search(r'SERVER_INFO\s*=\s*\{[^}]*"version":\s*"([^"]+)"', text)
    return match.group(1) if match else None


def read_plugin_readme_version() -> str | None:
    path = REPO_ROOT / "plugins" / "architect-agent-framework" / "README.md"
    if not path.is_file():
        return None
    match = re.search(r"(?m)^Candidate:\s*\**([0-9A-Za-z.-]+)\**", path.read_text(encoding="utf-8"))
    return match.group(1).rstrip(".") if match else None


def read_readme_version() -> str | None:
    path=REPO_ROOT/'README.md'
    if not path.is_file():return None
    match=re.search(r'(?m)^Candidate:\s*\**([0-9A-Za-z.-]+)\**',path.read_text(encoding='utf-8'))
    return match.group(1).rstrip(".") if match else None


def read_support_profile_version() -> str | None:
    path = REPO_ROOT / "contracts" / "release-support-profile.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8")).get("candidate")


def read_plugin_version() -> str | None:
    for rel in ("plugins/architect-agent-framework/.claude-plugin/plugin.json", ".claude-plugin/plugin.json"):
        path = REPO_ROOT / rel
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8")).get("version")
    return None


def read_codex_version() -> str | None:
    for rel in ("plugins/architect-agent-framework/.codex-plugin/plugin.json", ".codex-plugin/plugin.json"):
        path = REPO_ROOT / rel
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8")).get("version")
    return None


def read_marketplace_metadata_version() -> str | None:
    path = REPO_ROOT / ".claude-plugin" / "marketplace.json"
    if not path.is_file():
        return None
    return (json.loads(path.read_text(encoding="utf-8")).get("metadata") or {}).get("version")


def read_marketplace_version() -> str | None:
    path = REPO_ROOT / ".claude-plugin" / "marketplace.json"
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    plugins = data.get("plugins") or []
    return plugins[0].get("version") if plugins else None


def read_plugin_root_version() -> str | None:
    path = REPO_ROOT / "plugins" / "architect-agent-framework" / "VERSION"
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8").strip()


def read_plugin_pyproject_version() -> str | None:
    path = REPO_ROOT / "plugins" / "architect-agent-framework" / "pyproject.toml"
    if not path.is_file():
        return None
    match = re.search(r'(?m)^version\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def read_package_json_version() -> str | None:
    path = REPO_ROOT / "package.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8")).get("version")


def read_package_lock_version() -> str | None:
    path = REPO_ROOT / "package-lock.json"
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    top = data.get("version")
    pkg_root = (data.get("packages") or {}).get("", {}).get("version")
    if top and pkg_root and top != pkg_root:
        return f"{top}!={pkg_root}"
    return top or pkg_root


def collect_catalog_versions() -> dict[str, list[str]]:
    """Map each observed SKILL.md version to the skill ids declaring it."""
    versions: dict[str, list[str]] = {}
    exported = REPO_ROOT / "exported_skills"
    if exported.is_dir():
        skill_mds = sorted(exported.rglob("SKILL.md"))
    else:
        bundled = ("architect-skill-orchestrator", "adr-authoring", "agent-workflow-design", "arch-review-task")
        skill_mds = [REPO_ROOT / "skills" / s / "SKILL.md" for s in bundled if (REPO_ROOT / "skills" / s / "SKILL.md").is_file()]
    for skill_md in skill_mds:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"(?m)^version:\s*(\S+)\s*$", text)
        value = match.group(1).strip("'\"") if match else "<missing>"
        versions.setdefault(value, []).append(skill_md.parent.name)
    return versions


def collect_schema_versions() -> dict[str, str]:
    """R6.4: Check schema_version in published contracts and derived artifacts."""
    schema_versions: dict[str, str] = {}
    contract_files = [
        REPO_ROOT / "contracts" / "archetype-vocabulary.yml",
        REPO_ROOT / "contracts" / "evidence-vocabulary.yml",
        REPO_ROOT / "contracts" / "gates.yml",
        REPO_ROOT / "contracts" / "seam-ledger.schema.yml",
    ]
    for c_file in contract_files:
        if c_file.is_file():
            text = c_file.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"(?m)^schema_version:\s*['\"]?([^'\"\s]+)['\"]?", text)
            rel = str(c_file.relative_to(REPO_ROOT)).replace("\\", "/")
            schema_versions[rel] = m.group(1) if m else "<missing>"
    return schema_versions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", action="store_true", help="emit a machine-readable report")
    args = parser.parse_args(argv)

    release = read_release_version()
    declared = {
        "VERSION": release,
        "pyproject.toml": read_pyproject_version(),
        "plugins/architect-agent-framework/.claude-plugin/plugin.json": read_plugin_version(),
        ".claude-plugin/marketplace.json": read_marketplace_version(),
        ".claude-plugin/marketplace.json#metadata": read_marketplace_metadata_version(),
        "plugins/architect-agent-framework/.codex-plugin/plugin.json": read_codex_version(),
        'uv.lock':read_lock_version(),
        'README.md#candidate':read_readme_version(),
        'README.vi.md#candidate':read_readme_vi_version(),
        'architect_framework/__init__.py':read_init_version(),
        'architect_framework/runtime/mcp_server.py':read_mcp_server_version(),
        'plugins/architect-agent-framework/README.md':read_plugin_readme_version(),
        'contracts/release-support-profile.json':read_support_profile_version(),
        'plugins/architect-agent-framework/VERSION':read_plugin_root_version(),
        'plugins/architect-agent-framework/pyproject.toml':read_plugin_pyproject_version(),
        'package.json':read_package_json_version(),
        'package-lock.json':read_package_lock_version(),
    }
    catalog = collect_catalog_versions()
    schemas = collect_schema_versions()

    errors: list[str] = []

    if not SEMVER.match(release):
        errors.append(f"VERSION '{release}' is not valid semver (expected MAJOR.MINOR.PATCH)")

    for source, value in declared.items():
        if source == "VERSION":
            continue
        if value is None:
            continue  # optional file absent; not an error
        equal=(Version(value)==Version(release)) if source=='uv.lock' and value!='<missing>' else value==release
        if not equal:
            errors.append(f"{source} declares {value}, expected {release} (from VERSION)")

    if "<missing>" in catalog:
        missing = catalog["<missing>"]
        errors.append(
            f"{len(missing)} SKILL.md files have no version field, e.g. {', '.join(sorted(missing)[:5])}"
        )
    real_versions = {k: v for k, v in catalog.items() if k != "<missing>"}
    if len(real_versions) > 1:
        summary = ", ".join(f"{ver} ({len(ids)} skills)" for ver, ids in sorted(real_versions.items()))
        errors.append(f"catalog version is not uniform: {summary}")

    # R6.4: Schema version drift check
    if "<missing>" in schemas.values():
        missing_schemas = [f for f, v in schemas.items() if v == "<missing>"]
        errors.append(f"contract artifacts missing schema_version: {', '.join(missing_schemas)}")

    report = {
        "release_version": release,
        "declared": declared,
        "catalog_versions": {k: len(v) for k, v in catalog.items()},
        "schema_versions": schemas,
        "errors": errors,
        "ok": not errors,
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"release version: {release}")
        for source, value in declared.items():
            mark = "ok" if source == "VERSION" or value in (None, release) or source=='uv.lock' and value!='<missing>' and Version(value)==Version(release) else "MISMATCH"
            print(f"  [{mark:>8}] {source}: {value if value is not None else '(absent)'}")
        for ver, ids in sorted(catalog.items()):
            print(f"  [ catalog ] SKILL.md version {ver}: {len(ids)} packages")
        for f, s_ver in sorted(schemas.items()):
            s_mark = "ok" if s_ver != "<missing>" else "MISSING"
            print(f"  [{s_mark:>8}] schema {f}: {s_ver}")
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        if not errors:
            print("all versions consistent")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
