"""Framework-to-core boundary. Import the engine lazily; hooks need only mode."""
from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from .mode import workspace_mode

WORKSPACE_FILE = "sdd-workspace.yml"


def available():
    try:
        _core()
        return True
    except BridgeError:
        return False


def _classification_answer(workspace):
    from .mode import classify
    result = classify(workspace)
    return {"mode": result["state"], "applicable": False, "status": "INCOMPLETE", "exit_code": 3,
            "hint": result["next_action"], "result": result}


def _section_check(workspace, section, change=None):
    if workspace_mode(workspace) != "core":
        return _classification_answer(workspace)
    if not available():
        return {"mode": "core", "applicable": True, "status": "UNAVAILABLE", "exit_code": 3,
                "hint": "Install architect-agent-framework[sdd] in this interpreter", "result": None}
    try:
        report = inspect(workspace, change)[section]
        state = report["status"]
        return {"mode": "core", "applicable": True, "status": state,
                "exit_code": 0 if state == "PASS" else 1 if state == "FAIL" else 3, "hint": "", "result": report}
    except Exception as exc:
        error = exc.to_dict() if hasattr(exc, "to_dict") else {"status": "ERROR", "message": str(exc)}
        return {"mode": "core", "applicable": True, "status": error["status"], "exit_code": 3,
                "hint": str(exc), "result": error}


def check(workspace, change=None):
    return _section_check(workspace, "check", change)


def regression(workspace, change=None):
    return _section_check(workspace, "regression", change)


class BridgeError(ValueError, FileNotFoundError):
    def __init__(self, code, message, status="ERROR"):
        super().__init__(message)
        self.code, self.status = code, status

    def to_dict(self):
        return {"status": self.status, "code": self.code, "message": str(self)}


def require_core(workspace):
    from .mode import classify
    result = classify(workspace)
    if result["state"] != "current":
        raise BridgeError(result["code"], result["next_action"], "ERROR" if result["state"] == "invalid" else "INCOMPLETE")


def reject_legacy_write(workspace):
    require_core(workspace)
    raise BridgeError("SDD_CORE_WRITE_REQUIRED", "Use architect_sdd_propose with a skill grant and expected snapshot")


def _core():
    try:
        from sdd_core.engine import Engine
        return Engine
    except ImportError as exc:
        raise BridgeError("SDD_DEPENDENCY_MISSING", "Install architect-agent-framework[sdd] in the runtime environment", "INCOMPLETE") from exc


def inspect(workspace, change_id=None):
    """Read check/regression/freshness without reconciliation or state writes."""
    require_core(workspace)
    Engine = _core()
    from sdd_core.freshness import freshness
    from sdd_core.model import SddError, Status, digest
    from sdd_core.validation import check_snapshot
    from sdd_core.workspace import capture

    engine = engine_for(workspace)
    origin = capture(Path(workspace))
    baseline = engine.store.baseline()
    before = engine.store.load_snapshot(baseline["snapshot_digest"]) if baseline else None
    if change_id:
        change, snapshot, before = engine.context(change_id)
    else:
        snapshot = origin
        change = {"change_id": "preview-" + digest({"snapshot": snapshot.digest, "base": baseline})[:24],
                  "snapshot_digest": snapshot.digest, "origin_snapshot": snapshot.digest,
                  "base_acceptance": baseline["acceptance_id"] if baseline else None, "restored_ids": []}
    deterministic = check_snapshot(snapshot, before, engine.store.history(), compare_incremental=True)
    restored = set(change.get("restored_ids", []))
    deterministic.findings = [f for f in deterministic.findings if not (f.code == "RETIRED_ID_REUSE" and set(f.subjects) <= restored)]
    if not change_id and baseline and snapshot.digest == baseline["snapshot_digest"]:
        regression = engine.baseline_readiness()
    else:
        regression = engine._readiness(change, snapshot, before)
    source_findings, sources = freshness(engine.store, snapshot, before=before)
    if capture(Path(workspace)).digest != origin.digest or engine.store.baseline() != baseline:
        raise SddError("WORKSPACE_CHANGED", "Workspace or baseline changed during inspection; retry", Status.STALE)
    states = [deterministic.status, regression.status, *(f.status for f in source_findings if f.severity == "blocker")]
    status = next((s for s in (Status.ERROR, Status.STALE, Status.INCOMPLETE, Status.FAIL) if s in states), Status.PASS)
    return {"status": status.value, "mode": "core", "snapshot_digest": snapshot.digest,
            "origin_snapshot": origin.digest, "change_id": change_id, "baseline": baseline,
            "check": deterministic.to_dict(), "regression": regression.to_dict(), "freshness": sources,
            "next_action": "Resolve findings, obtain independent review, then open the console for signed acceptance."}


def propose(workspace, operations, skill, expected_snapshot, operation_id=None, base_change=None):
    require_core(workspace)
    _core()
    from sdd_core.changes import propose as core_propose
    from sdd_core.storage import Store
    if not isinstance(skill, str) or not skill.strip() or not expected_snapshot:
        raise BridgeError("SDD_PROPOSAL_BINDING_REQUIRED", "Supply a configured skill and the inspected origin_snapshot")
    if not isinstance(operations, list) or not operations or not all(isinstance(x, dict) for x in operations):
        raise BridgeError("SDD_OPERATIONS_INVALID", "Supply a nonempty list of change operations")
    change = core_propose(Store(Path(workspace)), Path(workspace), operations, operation_id, skill, expected_snapshot, base_change)
    return {"status": "DRAFT", "mode": "core", "change": change,
            "next_action": "Inspect this change_id. Review and signed acceptance are separate."}


def status(workspace, change_id=None):
    if workspace_mode(workspace) != "core":
        return _classification_answer(workspace)
    return inspect(workspace, change_id)


def status_probe(workspace: str | Path = ".") -> dict[str, Any]:
    """Interactive context-aware wizard probe for `/architect` (ISS-23 / WO-R3.3)."""
    root = Path(workspace).resolve()
    if not root.exists():
        return {
            "initialized": False,
            "workspace": str(root),
            "existing_sources": [],
            "code_dirs": [],
            "recommended_commands": ["/architect-clarify", "/architect-init", "/architect-quickstart"],
        }
    has_marker = (root / WORKSPACE_FILE).is_file()
    md_files = sorted(p.name for p in root.glob("*.md") if p.is_file())
    code_dirs = sorted(p.name for p in root.iterdir() if p.is_dir() and p.name in {"frontend", "backend", "src", "app", "services", "packages", "frontend-acceptance"})
    if not has_marker:
        recs = [
            {"command": "/architect-clarify", "use_case": "UC-01", "when": "Clarify raw ideas or incomplete briefs via Socratic interview"},
            {"command": "/architect-quickstart", "use_case": "UC-02", "when": "Generate a fast-track MVP architecture (12-25 pages) in 5-10 minutes"},
            {"command": "/architect-design --mode maximal", "use_case": "UC-03", "when": "Generate a full enterprise Maximal specification (Phase 0 -> Phase 5)"},
        ]
        if code_dirs:
            recs.append({"command": "/architect-audit", "use_case": "UC-04", "when": "Audit existing codebase/acceptance evidence against specifications"})
        return {
            "initialized": False,
            "workspace": str(root),
            "existing_sources": md_files,
            "code_dirs": code_dirs,
            "recommended_commands": recs,
            "next_action": "Choose a workflow: /architect-clarify, /architect-quickstart, /architect-design --mode maximal, or /architect-audit.",
        }
    rep = status(root)
    chk = rep.get("check") or {}
    cov = chk.get("details", {}).get("coverage_metrics") or {}
    counts = cov.get("counts") or {}
    from sdd_core.workspace import capture
    art_count = counts.get("registered_artifacts") or len(capture(root, allow_live_read=True).artifacts)
    return {
        "initialized": True,
        "workspace": str(root),
        "status": chk.get("status", rep.get("status", "INCOMPLETE")),
        "readiness_status": rep.get("status", "INCOMPLETE"),
        "snapshot_digest": rep.get("snapshot_digest"),
        "artifact_count": art_count,
        "coverage_metrics": cov,
        "finding_count": len(chk.get("findings", [])),
        "console_url": "http://localhost:8767/",
        "next_action": "sdd prepare-check <workspace> && /architect-check --full" if chk.get("status") != "PASS" else "/architect-review or /architect-console",
    }


def execute_standalone(
    domain_skill: str = "",
    task_skill: str = "",
    query: str = "",
    *,
    out_path: str | Path | None = None,
    workspace: str | Path | None = None,
) -> dict[str, Any]:
    """UC-05 (WO-R3.5): Execute a single Domain x Task skill pair in standalone mode without requiring sdd-workspace.yml."""
    from architect_framework.document_style import evaluate as evaluate_style
    from architect_framework.sdd_bridge.scaffolder import _render_authored_page, _clean_id_token

    _STANDALONE_SKILL_ALIASES = {
        "data-persistence-architect": "database-architect",
        "frontend-system-architect": "frontend-architect",
        "api-contract-design": "rest-api-design",
    }
    q_lower = (query or "").lower()
    if not domain_skill:
        if any(k in q_lower for k in ("db", "postgres", "sql", "storage", "data", "persistence")):
            domain_skill = "database-architect"
        elif any(k in q_lower for k in ("auth", "security", "oauth", "passkey", "zero-trust", "jwt")):
            domain_skill = "security-architect"
        elif any(k in q_lower for k in ("ai", "llm", "rag", "agent", "embedding")):
            domain_skill = "ai-system-architect"
        elif any(k in q_lower for k in ("ui", "frontend", "react", "spa", "web")):
            domain_skill = "frontend-architect"
        else:
            domain_skill = "backend-service-architect"
    if not task_skill:
        if any(k in q_lower for k in ("adr", "decision", "choose", "compare", "vs", "chọn", "so sánh")):
            task_skill = "adr-authoring"
        elif any(k in q_lower for k in ("api", "rest", "grpc", "graphql", "webhook", "endpoint")):
            task_skill = "rest-api-design"
        elif any(k in q_lower for k in ("agent", "workflow", "subagent")):
            task_skill = "agent-workflow-design"
        else:
            task_skill = "adr-authoring"

    aid = _clean_id_token(f"{domain_skill}-{task_skill}")[:64]
    kind = "adr" if "adr" in task_skill.lower() or "decision" in task_skill.lower() else ("api_contract" if "api" in task_skill.lower() else "mechanism")
    rel_out = str(out_path or f"{task_skill}-spec.md")
    node = {
        "artifact_id": aid,
        "path": rel_out,
        "kind": kind,
        "owner": domain_skill or "01-system-architect",
        "concern_ids": [f"CNC-{aid}"],
        "source_ids": ["SRC-STANDALONE-REQUEST"],
        "required_depth_dimensions": ["authority", "contract", "guards", "alternate_flows", "observability", "consumers"],
    }
    markdown = _render_authored_page(node, generate_substantive=True)
    if query:
        markdown += f"\n### Targeted Problem Context\n- **Request Scope**: {query.strip()}\n- **Selected Domain Skill**: `{domain_skill}`\n- **Selected Task Skill**: `{task_skill}`\n"
    resolved_skills = {}
    try:
        from architect_framework import skillpacks
        with skillpacks.activated(workspace or Path.cwd()):
            for sk_id in (domain_skill, task_skill):
                if not sk_id:
                    continue
                canonical_id = _STANDALONE_SKILL_ALIASES.get(sk_id, sk_id)
                try:
                    sl = skillpacks.slot(canonical_id)
                    resolved_skills[sk_id] = {
                        "canonical_id": canonical_id,
                        "state": sl.state,
                        "content_path": str(sl.content) if sl.content else None,
                    }
                except Exception:
                    continue
    except Exception:
        pass
    style_report = evaluate_style(markdown)
    written_to = None
    if out_path is not None:
        target = Path(out_path)
        ws_root = Path(workspace).resolve() if workspace else Path.cwd().resolve()
        if not target.is_absolute():
            target = ws_root / target
        # Protect active SDD workspaces from UNREGISTERED_ARTIFACT errors when running standalone outputs
        if (ws_root / "sdd-workspace.yml").is_file():
            try:
                rel_to_ws = target.resolve().relative_to(ws_root)
                if not rel_to_ws.parts[0].startswith("."):
                    target = ws_root / ".architect-build" / "standalone" / rel_to_ws
            except ValueError:
                pass
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(markdown, encoding="utf-8", newline="\n")
        written_to = str(target.resolve())
    return {
        "status": "COMPLETED",
        "mode": "standalone",
        "domain_skill": domain_skill,
        "task_skill": task_skill,
        "resolved_skills": resolved_skills,
        "artifact_id": aid,
        "output_path": written_to,
        "style_check": {
            "status": style_report["status"],
            "finding_count": len(style_report["findings"]),
        },
        "content": markdown if written_to is None else f"Wrote {len(markdown.splitlines())} lines to {written_to}",
        "next_action": "Run `/architect-init` if you want to promote this folder into a full versioned SDD workspace.",
    }


def engine_for(workspace):
    """Only this adapter supplies the host's independent decision verifier."""
    return _core()(workspace, decision_verifier=decision_verifier(workspace))


def decision_verifier(workspace):
    def verify(record):
        from architect_framework.console import attest
        return attest.verify(record, attest.load_reviewers(Path(workspace)),
                             decided_by_field="actor", when_field="created_at")
    return verify


def initialize(
    workspace,
    workspace_id: str | None = None,
    reviewer: str = "lead-architect",
    *,
    profile: str | None = None,
    preset: str | None = None,
    allow_existing_sources: bool = False,
):
    """Explicit workspace bootstrap with support for solo-author/governed-team presets and existing source files (WO-R3.1, WO-R3.2)."""
    _core()
    import yaml
    from sdd_core.bootstrap import initial_config
    from sdd_core.parsing import relative_path
    from sdd_core.storage import Store, atomic_write
    from sdd_core.schema import WORKSPACE, validate
    from sdd_core.workspace import _IGNORED_DIRS, _IGNORED_FILES
    root = Path(workspace).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if (root / WORKSPACE_FILE).exists():
        raise BridgeError("WORKSPACE_NOT_EMPTY", "Initialize a new empty directory; migrate existing documents explicitly")
    if any(root.iterdir()) and not allow_existing_sources:
        raise BridgeError("WORKSPACE_NOT_EMPTY", "Initialize a new empty directory; migrate existing documents explicitly")
    if not workspace_id:
        cleaned = re.sub(r"[^A-Za-z0-9_.:-]+", "-", root.name or "workspace").strip("-")
        workspace_id = cleaned if cleaned and cleaned[0].isalpha() else f"ws-{cleaned or 'default'}"
    config = initial_config(workspace_id, reviewer or "lead-architect", profile=profile, preset=preset)
    config["policy"]["decision_authority"] = "external"
    config["control_directories"] = [".architect", ".architect-runtime", ".architect-build"]
    if allow_existing_sources:
        attachments = []
        for item in sorted(root.iterdir()):
            if item.name in _IGNORED_DIRS or item.name in _IGNORED_FILES or item.name == WORKSPACE_FILE:
                continue
            if item.is_file():
                attachments.append(relative_path(item.name))
        if attachments:
            config["attachments"] = attachments
    config["skills"] = {
        "00-requirement-clarifier": {"capabilities": ["author", "configure"], "write_scope": ["requirements", "sdd-workspace.yml"]},
        "01-system-architect": {"capabilities": ["author", "configure"], "write_scope": ["architecture", "sdd-workspace.yml"]},
        "02-spec-critic": {"capabilities": ["review", "author"], "write_scope": ["reviews", "architecture/01-global-strategy/05-governance/reviews", "architecture/04-delivery/04-audit", "architecture"]},
        "adr-authoring": {"capabilities": ["author", "configure"], "write_scope": ["architecture/decisions", "architecture", "sdd-workspace.yml"]},
        "agent-workflow-design": {"capabilities": ["author", "configure"], "write_scope": ["architecture", "design", "sdd-workspace.yml"]},
        "arch-review-task": {"capabilities": ["review", "author"], "write_scope": ["reviews", "architecture/01-global-strategy/05-governance/reviews", "architecture/04-delivery/04-audit", "architecture"]},
    }
    try:
        from architect_framework import skillpacks
        with skillpacks.activated(root):
            for sk_id, pkg in sorted(skillpacks.installed().items()):
                if sk_id not in config["skills"] and sk_id != "architect-runtime":
                    config["skills"][sk_id] = {"capabilities": ["author", "configure"], "write_scope": ["architecture", "sdd-workspace.yml"]}
    except Exception:
        pass
    validate(config, WORKSPACE)
    with Store(root).lock():
        atomic_write(root / WORKSPACE_FILE, yaml.safe_dump(config, sort_keys=False, allow_unicode=True).encode("utf-8"))
        atomic_write(root / ".sdd" / ".gitignore", b"*.lock\n")
    return {"status": "INITIALIZED", "mode": "core", "workspace": str(root),
            "workspace_id": workspace_id, "profile": profile or "standard", "preset": preset or "governed-team",
            "next_action": "Author registered documents and obligations through proposals; enroll the reviewer in the console."}


def read_artifact(workspace, artifact_id, change_id=None, offset=0, limit=20000, *, max_limit=50000):
    """Read a bounded Unicode slice from a registered live or candidate artifact (fast path via SnapshotCache — WO-R5.1)."""
    require_core(workspace)
    from sdd_core.workspace import capture
    from sdd_core.model import SddError, Status
    if not isinstance(artifact_id, str) or type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= max_limit:
        raise BridgeError("READ_PACKET_INVALID", f"Use an artifact ID, nonnegative offset and limit 1..{max_limit}")
    engine = engine_for(workspace)
    origin = capture(Path(workspace)); baseline = engine.store.baseline()
    snapshot = engine.context(change_id)[1] if change_id else origin
    artifact = snapshot.artifacts.get(artifact_id)
    if artifact is None: raise BridgeError("ARTIFACT_UNKNOWN", "Select a registered artifact")
    if capture(Path(workspace)).digest != origin.digest or engine.store.baseline() != baseline:
        raise SddError("WORKSPACE_CHANGED", "Workspace changed during reading; retry", Status.STALE)
    return {"status": "READ", "artifact_id": artifact_id, "path": artifact.path, "revision": artifact.revision,
            "snapshot_digest": snapshot.digest, "origin_snapshot": origin.digest, "change_id": change_id,
            "offset": offset, "total_characters": len(artifact.text), "text": artifact.text[offset:offset + limit],
            "has_more": offset + limit < len(artifact.text)}
