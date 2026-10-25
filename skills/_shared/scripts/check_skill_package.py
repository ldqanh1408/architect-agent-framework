#!/usr/bin/env python3
"""Package integrity check, shared by every package in the catalog.

The skill id comes from the package directory name rather than a constant baked
in at generation time. That constant used to exist in 294 near-identical copies
of this file, and the drift it guarded against -- a package directory renamed
without regenerating -- is already caught by validate_catalog's name-mismatch
rule, which compares frontmatter to the directory for the whole catalog at once.
"""
from pathlib import Path
import argparse, hashlib, re, sys, yaml
REQUIRED_FILES = ['SKILL.md', 'README.md', 'skill-contract.yml', 'agents/openai.yaml', 'references/output-contract.md', 'references/domain-rules.md', 'references/research-basis.md', 'package.yml', 'evaluations/golden.yml', 'evaluations/adversarial.yml']
# B-2: required of one kind of package only, so the requirement is checked after
# the contract has said which kind this is. `workspace-template.yml` is domain-only
# -- a task skill has no concern-module axis to declare. Rendered from KIND_PACKAGE_FILES, not retyped.
KIND_REQUIRED_FILES = {'domain': ['workspace-template.yml']}
SHARED_DIR = '_shared'
REQUIRED_CONTRACT = {"schema_version", "skill", "kind", "role", "triggers", "anti_triggers", "required_inputs", "optional_inputs", "forbidden_inputs", "owns", "read_only", "forbidden_writes", "required_outputs", "completion_evidence", "blocking_conditions", "resume_policy", "context_loading", "engineering_discipline", "validators"}
# Each entry is one thing a reader must be able to find, plus every heading the
# catalog actually uses to say it. Authors word these differently by skill kind
# -- a routing skill draws boundaries under "Required Distinctions" where a
# design skill lists "Common Pitfalls" -- and demanding one fixed spelling
# rejects correct documents. The requirement is the section, not its title.
REQUIRED_SECTIONS = (
    ("overview", ("Overview",)),
    ("applicability", ("When to Use",)),
    ("anti-failure", ("Common Pitfalls", "Required Distinctions", "Core Distinctions", "Core Model and Distinctions")),
    ("verification", ("Verification Checklist",)),
)
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
def find_shared(package):
    """Walk up to the catalog root holding the shared tree.

    Searching rather than counting parents: domain and task packages sit three
    levels below the catalog and the orchestrator sits two.
    """
    for parent in package.parents:
        candidate = parent/SHARED_DIR
        if candidate.is_dir(): return candidate
    return None
def check_manifest(root, expected):
    """Verify package.yml describes the files actually present.

    package.yml declares validator_policy.fail_closed, but that promise is only
    worth anything if somebody reads the hashes it records. Without this check a
    package can ship content that contradicts its own provenance record and
    still report PASSED.
    """
    manifest_path = root/"package.yml"
    if not manifest_path.is_file(): return ["missing required file: package.yml"]
    try: manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc: return [f"package.yml is not parsable: {exc}"]
    errors = []
    if manifest.get("skill") != expected: errors.append("package.yml skill mismatch")
    for entry in manifest.get("files") or []:
        target = root/entry["path"]
        if not target.is_file(): errors.append(f"package.yml lists a missing file: {entry['path']}"); continue
        payload = target.read_bytes()
        if hashlib.sha256(payload).hexdigest() != entry.get("sha256"): errors.append(f"package.yml hash mismatch: {entry['path']}")
        elif len(payload) != entry.get("bytes"): errors.append(f"package.yml size mismatch: {entry['path']}")
    return errors
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("skill_dir", type=Path); root=ap.parse_args().skill_dir.resolve(); expected_skill=root.name; errors=[]
    shared=find_shared(root)
    if shared is None: return report([f"no {SHARED_DIR}/ found above {root}; a package is only valid inside its catalog"])
    for rel in REQUIRED_FILES:
        if not (root/rel).is_file(): errors.append(f"missing required file: {rel}")
    if errors: return report(errors)
    text=(root/"SKILL.md").read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]: errors.append("invalid SKILL.md frontmatter")
    else:
        end=text.find("\n---\n",4); fm=yaml.safe_load(text[4:end])
        if fm.get("name") != expected_skill: errors.append("frontmatter name mismatch")
        if not NAME_RE.fullmatch(fm.get("name", "")) or len(fm.get("name", "")) > 64: errors.append("frontmatter name violates Agent Skills specification")
        if not fm.get("description") or len(fm["description"])>1024: errors.append("description missing or too long")
        if not fm.get("license"): errors.append("frontmatter license is required by this project")
        if not fm.get("compatibility"): errors.append("frontmatter compatibility is required by this project")
    headings={m.group(1).strip() for m in re.finditer(r"(?m)^## (.+)$",text)}
    for section, accepted in REQUIRED_SECTIONS:
        if not headings.intersection(accepted): errors.append(f"missing SKILL.md {section} section: expected one of {', '.join(accepted)}")
    errors.extend(check_manifest(root, expected_skill))
    data=yaml.safe_load((root/"skill-contract.yml").read_text(encoding="utf-8"))
    missing=REQUIRED_CONTRACT-set(data or {})
    if missing: errors.append("contract missing keys: "+", ".join(sorted(missing)))
    if data.get("skill") != expected_skill: errors.append("contract skill mismatch")
    for rel in KIND_REQUIRED_FILES.get(data.get("kind"), []):
        if not (root/rel).is_file(): errors.append(f"missing required file: {rel}")
    for key in ("triggers","required_inputs","owns","required_outputs","completion_evidence","blocking_conditions","validators"):
        if not isinstance(data.get(key),list) or not data[key]: errors.append(f"contract {key} must be a non-empty list")
    # SKILL.md is authored and preserved across regeneration, so nothing in the
    # generator can correct a write root that drifted from the contract. An
    # agent reads the prose and writes where it says; the validators check the
    # contract's tree. When they disagree the work lands unowned and unchecked.
    for owned in data.get("owns") or []:
        if "/architecture/" in owned and owned not in text:
            errors.append(f"SKILL.md does not state the contract's owned write root: {owned}")
    discipline=data.get("engineering_discipline",{})
    for key in ("think_before_action","simplicity_first","surgical_scope","goal_driven_execution"):
        if not isinstance(discipline.get(key),dict) or not discipline[key]: errors.append(f"missing engineering discipline: {key}")
    discipline_text=(shared/"references/engineering-discipline.md").read_text(encoding="utf-8").lower()
    for phrase in ("think before acting","simplicity first","surgical scope","goal-driven execution"):
        if phrase not in discipline_text: errors.append(f"engineering discipline missing section: {phrase}")
    agent=yaml.safe_load((root/"agents/openai.yaml").read_text(encoding="utf-8"))
    if "model" in agent: errors.append("agents/openai.yaml must not pin a runtime model")
    for scenario_kind in ("golden", "adversarial"):
        scenario=yaml.safe_load((root/"evaluations"/f"{scenario_kind}.yml").read_text(encoding="utf-8"))
        if scenario.get("skill") != expected_skill: errors.append(f"{scenario_kind} scenario skill mismatch")
        if scenario.get("scenario_id") != f"{expected_skill}-{scenario_kind}": errors.append(f"{scenario_kind} scenario identity mismatch")
        oracle=scenario.get("oracle",{})
        if oracle.get("shell") is not False or not isinstance(oracle.get("argv"),list) or not oracle["argv"]: errors.append(f"{scenario_kind} oracle must use non-empty argv with shell=false")
        if scenario.get("kind") != scenario_kind: errors.append(f"{scenario_kind} scenario kind mismatch")
        if scenario.get("request",{}).get("expected_route") != expected_skill: errors.append(f"{scenario_kind} expected route mismatch")
        expected=scenario.get("expect",{})
        if expected.get("status") not in {"complete","blocked","resumable","rejected"}: errors.append(f"{scenario_kind} scenario has invalid expected status")
        if not isinstance(expected.get("required_artifacts"),list) or not isinstance(expected.get("forbidden_artifacts"),list): errors.append(f"{scenario_kind} artifact assertions must be lists")
        if not isinstance(expected.get("diagnostic_codes"),list): errors.append(f"{scenario_kind} diagnostics must be stable-code lists")
    return report(errors)
def report(errors):
    if errors:
        print("FAILED"); [print("- "+e) for e in errors]; return 1
    print("PASSED"); return 0
if __name__=="__main__": raise SystemExit(main())
