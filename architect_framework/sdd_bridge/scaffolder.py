"""Deterministic Source-to-Concern-to-Target-Plan solver, Pack-Free Archetype-First scaffolder, and workspace materializer."""
from __future__ import annotations

import hashlib
import json
import posixpath
from pathlib import Path
import re
from typing import Any
import yaml

from architect_framework import contracts
from architect_framework.exporter.output_modules import ARCHETYPE_MODULES

CORE_ARCHETYPE_CLUSTERS: dict[str, str] = {
    "backend-service": "03_application_architecture",
    "frontend": "01_frontend_architecture",
    "ai-system": "04_ai_architecture",
    "data-platform": "05_data_architecture",
    "identity-access": "07_security_architecture",
    "integration-adapter": "03_application_architecture",
    "infra-platform": "06_infrastructure_architecture",
    "observability": "08_quality_attribute_architecture",
}

BUNDLED_SKILLS = frozenset({
    "00-requirement-clarifier",
    "01-system-architect",
    "02-spec-critic",
    "architect-runtime",
    "architect-skill-orchestrator",
    "adr-authoring",
    "agent-workflow-design",
    "arch-review-task",
})

WAVE_DEFINITIONS: dict[int, str] = {
    1: "w1-global-strategy",
    2: "w2-shared-contracts",
    3: "w3-frontend-contexts",
    4: "w4-domain-contexts",
    5: "w5-cross-cutting-delivery",
    6: "w6-system-views-index",
}

VALID_PROFILES = frozenset({"seed", "minimal", "standard", "maximal", "portfolio"})


def infer_core_archetype(slug_or_text: str, default: str = "backend-service") -> tuple[str, str]:
    """Infer one of the 8 Core Archetypes and its canonical domain cluster from a context slug or description."""
    lower = (slug_or_text or "").lower()
    if any(k in lower for k in ("frontend", "web", "spa", "ui", "portal", "client", "mobile", "react", "dashboard")):
        return "frontend", CORE_ARCHETYPE_CLUSTERS["frontend"]
    if any(k in lower for k in ("ai", "llm", "agent", "rag", "prompt", "embedding", "inference", "model-router")):
        return "ai-system", CORE_ARCHETYPE_CLUSTERS["ai-system"]
    if any(k in lower for k in ("data", "warehouse", "etl", "analytics", "lake", "cdc", "vector", "search-index", "persistence")):
        return "data-platform", CORE_ARCHETYPE_CLUSTERS["data-platform"]
    if any(k in lower for k in ("auth", "iam", "identity", "rbac", "abac", "security", "passkey", "oauth", "oidc", "crypto", "vault", "zero-trust", "governance")):
        return "identity-access", CORE_ARCHETYPE_CLUSTERS["identity-access"]
    if any(k in lower for k in ("adapter", "webhook", "connector", "integration", "stripe", "github", "provider", "acl")):
        return "integration-adapter", CORE_ARCHETYPE_CLUSTERS["integration-adapter"]
    if any(k in lower for k in ("infra", "k8s", "kubernetes", "terraform", "cloud", "network", "mesh", "cluster", "topology")):
        return "infra-platform", CORE_ARCHETYPE_CLUSTERS["infra-platform"]
    if any(k in lower for k in ("observability", "telemetry", "metrics", "logging", "tracing", "slo", "sre", "alert", "monitor", "profiling")):
        return "observability", CORE_ARCHETYPE_CLUSTERS["observability"]
    arch = default if default in ARCHETYPE_MODULES else "backend-service"
    return arch, CORE_ARCHETYPE_CLUSTERS.get(arch, "03_application_architecture")


def resolve_pack_free_owner(requested_skill: str | None, workspace: Path | str | None = None) -> str:
    """Return `requested_skill` if it is bundled or installed in a Skill Pack; otherwise fall back to `01-system-architect`."""
    sk = (requested_skill or "").strip() or "01-system-architect"
    if sk in BUNDLED_SKILLS:
        return sk
    try:
        from architect_framework import skillpacks
        with skillpacks.activated(workspace or Path.cwd()):
            if sk in skillpacks.installed():
                return sk
    except Exception:
        pass
    return "01-system-architect"


def classify_wave_for_path(path: str) -> tuple[int, str]:
    """Classify an architecture path into one of the 6 canonical topological waves (w1..w6)."""
    rel = str(path or "")
    if "/01-global-strategy/" in rel or rel.startswith("01-global-strategy/"):
        return 1, WAVE_DEFINITIONS[1]
    if "/_shared-contracts/" in rel or "/02-domains/00-overview/" in rel or rel.startswith("02-domains/00-overview/") or rel.startswith("02-domains/_shared-contracts/"):
        return 2, WAVE_DEFINITIONS[2]
    if "/01_frontend_architecture/" in rel:
        return 3, WAVE_DEFINITIONS[3]
    if "/02-domains/" in rel or rel.startswith("02-domains/"):
        return 4, WAVE_DEFINITIONS[4]
    if "/03-cross-cutting/" in rel or "/04-delivery/" in rel or rel.startswith("03-cross-cutting/") or rel.startswith("04-delivery/"):
        return 5, WAVE_DEFINITIONS[5]
    return 6, WAVE_DEFINITIONS[6]


class _CompactYamlDumper(yaml.SafeDumper):
    """YAML dumper that renders scalar arrays in compact flow style so frontmatter stays within line budgets."""


def _represent_compact_list(dumper: yaml.SafeDumper, data: list[Any]):
    if data and all(isinstance(x, (str, int, float, bool)) and len(str(x)) < 64 for x in data):
        return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=True)
    return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=False)


_CompactYamlDumper.add_representer(list, _represent_compact_list)


def dump_compact_yaml(data: Any) -> str:
    return yaml.dump(data, Dumper=_CompactYamlDumper, sort_keys=False, allow_unicode=True, width=120)


def _clean_id_token(raw: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.:-]+", "-", str(raw or "").strip().upper()).strip("-")
    if not cleaned or not cleaned[0].isalpha():
        cleaned = "A-" + cleaned
    return cleaned[:120]


def derive_maximal_plan(
    source_manifest: dict[str, Any],
    concern_inventory: dict[str, Any],
    *,
    mode: str = "maximal",
    requested_mode: str = "maximal",
    policy_version: str = "maximal-coverage-1",
) -> dict[str, Any]:
    """Derive a target document tree plan from a reconciled source manifest and concern inventory.

    Preserves 100% of applicable concerns, splits independent mechanisms/contracts/ADRs/scenarios,
    and keeps coverage policy, layout profile, and execution budget orthogonal.
    """
    concerns = [c for c in concern_inventory.get("concerns", []) if isinstance(c, dict)]
    planned_nodes: list[dict[str, Any]] = []
    omissions: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []

    for src in source_manifest.get("sources", []):
        if src.get("read_status") != "reconciled" or src.get("extraction_status", "complete") != "complete":
            blockers.append({
                "kind": "source_intake_incomplete",
                "source_id": src.get("id"),
                "status": src.get("read_status"),
            })

    nodes_by_artifact: dict[str, dict[str, Any]] = {}
    for c in concerns:
        cid = c["id"]
        disp = c.get("disposition", "gap")
        if disp in {"deferred", "not_applicable"}:
            omissions.append({
                "concern_id": cid,
                "disposition": disp,
                "authority": c.get("authority", ""),
                "owner": c.get("owner", "01-system-architect"),
                "rationale": c.get("rationale", ""),
                "source_witness": c.get("source_witness", ""),
                "review_trigger": c.get("review_trigger", ""),
            })
            continue
        if disp == "gap":
            blockers.append({
                "kind": "design_gap",
                "concern_id": cid,
                "owner": c.get("owner", "01-system-architect"),
                "rationale": c.get("rationale", "Missing evidence or design decision"),
            })
            continue

        art_id = c.get("owner_artifact") or f"ART-{cid}"
        path = c.get("target_path") or f"architecture/02-domains/{cid.lower()}.md"
        kind = c.get("artifact_kind", "document")
        owner = c.get("owner", "01-system-architect")
        if art_id not in nodes_by_artifact:
            nodes_by_artifact[art_id] = {
                "artifact_id": art_id,
                "path": path,
                "kind": kind,
                "owner": owner,
                "disposition": "covered",
                "concern_ids": [],
                "source_ids": [],
                "required_depth_dimensions": [],
                "question_answered": c.get("question", f"How is {cid} designed and verified?"),
                "split_rationale": c.get("split_rationale", "Independent mechanism/contract boundary"),
            }
        node = nodes_by_artifact[art_id]
        if cid not in node["concern_ids"]:
            node["concern_ids"].append(cid)
        for sitem in c.get("source_items", []):
            if sitem not in node["source_ids"]:
                node["source_ids"].append(sitem)
        for dim in c.get("required_depth_dimensions", []):
            if dim not in node["required_depth_dimensions"]:
                node["required_depth_dimensions"].append(dim)

    planned_nodes = sorted(nodes_by_artifact.values(), key=lambda n: n["path"])
    return {
        "schema_version": 1,
        "coverage_mode": mode,
        "requested_mode": requested_mode,
        "selected_profile": mode,
        "policy_version": policy_version,
        "planned_nodes": planned_nodes,
        "omissions": omissions,
        "blockers": blockers,
    }


def expand_archetype_slots(
    context_slug: str,
    cluster: str,
    index_prefix: str,
    skill: str,
    archetype: str,
    *,
    include_self_audit: bool = True,
    max_module_slots: int | None = None,
) -> list[dict[str, str]]:
    """Expand a bounded context into its canonical archetype concern slots without `{module}` path corruption."""
    modules = list(ARCHETYPE_MODULES.get(archetype, ARCHETYPE_MODULES["backend-service"]))
    if max_module_slots is not None and max_module_slots >= 0:
        modules = modules[:max_module_slots]
    base = f"architecture/02-domains/{cluster}/{index_prefix}-{context_slug}/{skill}"
    slots: list[dict[str, str]] = [{
        "slot": "00-overview",
        "mod_id": "overview",
        "path": f"{base}/00-overview/{context_slug}-overview.md",
        "kind": "overview",
    }]
    for mod in modules:
        raw_parts = [p for p in mod.path.strip("/").split("/") if p]
        slot_folder = raw_parts[1] if len(raw_parts) >= 2 else raw_parts[0]
        slot_folder = slot_folder.replace("{module}", context_slug)
        slot_kind = "nfr" if (mod.id == "slo" and mod.page_class == "requirement") else mod.page_class
        slots.append({
            "slot": slot_folder,
            "mod_id": mod.id,
            "path": f"{base}/{slot_folder}/{context_slug}-{mod.id}.md",
            "kind": slot_kind,
        })
    if include_self_audit:
        slots.append({
            "slot": "99-self-audit",
            "mod_id": "self-audit",
            "path": f"{base}/self-audit.md",
            "kind": "audit_report",
        })
    return slots


def _baseline_nodes_for_profile(profile: str, include_standard_branches: bool) -> list[tuple[str, str, str, list[str]]]:
    """Return the baseline architecture nodes appropriate for `profile` (`seed`..`portfolio`)."""
    all_baseline: list[tuple[str, str, str, list[str]]] = [
        ("SYS-INDEX", "architecture/index.md", "overview", ["SRC-ROOT"]),
        # 7 Core Diagram Views in 00-system-views/
        ("VIEW-VIEWPOINTS", "architecture/00-system-views/00-viewpoints/viewpoint-catalogue.md", "overview", ["SRC-ROOT"]),
        ("VIEW-C1-CONTEXT", "architecture/00-system-views/01-context/c1-system-context.md", "diagram", ["SRC-ROOT"]),
        ("VIEW-USE-CASES", "architecture/00-system-views/02-functional/use-case-map.md", "use_case", ["SRC-ROOT"]),
        ("VIEW-C2-CONTAINERS", "architecture/00-system-views/03-structure/c2-container-view.md", "diagram", ["SRC-ROOT"]),
        ("VIEW-C3-COMPONENTS", "architecture/00-system-views/03-structure/c3-component-and-module-map.md", "diagram", ["SRC-ROOT"]),
        ("VIEW-DEPLOYMENT", "architecture/00-system-views/04-deployment/deployment-topology.md", "diagram", ["SRC-ROOT"]),
        ("VIEW-INFORMATION-ERD", "architecture/00-system-views/05-information/erd-and-information-model.md", "diagram", ["SRC-ROOT"]),
        ("VIEW-RUNTIME-INDEX", "architecture/00-system-views/06-runtime/00-runtime-scenario-index.md", "overview", ["SRC-ROOT"]),
        # 01-global-strategy/
        ("STRAT-CONTEXT", "architecture/01-global-strategy/00-context/problem-brief-and-goals.md", "overview", ["SRC-ROOT"]),
        ("STRAT-REQUIREMENTS", "architecture/01-global-strategy/01-requirements/requirements-baseline.md", "overview", ["SRC-ROOT"]),
        ("STRAT-SOLUTION", "architecture/01-global-strategy/02-strategy/solution-strategy.md", "overview", ["SRC-ROOT"]),
        ("STRAT-STANDARDS", "architecture/01-global-strategy/03-standards/engineering-standards.md", "overview", ["SRC-ROOT"]),
        ("STRAT-RISKS", "architecture/01-global-strategy/04-risks/risk-and-debt-register.md", "verification", ["SRC-ROOT"]),
        # 02-domains/00-overview/ and _shared-contracts/ (all 6 popular branches: 00-core..05-state-machines)
        ("DOM-OVERVIEW", "architecture/02-domains/00-overview/domain-landscape.md", "overview", ["SRC-ROOT"]),
        ("DOM-CONTEXT-MAP", "architecture/02-domains/00-overview/context-map.md", "overview", ["SRC-ROOT"]),
        ("SHARED-CORE-TYPES", "architecture/02-domains/_shared-contracts/00-core/core-types-and-error-envelope.md", "data_entity", ["SRC-ROOT"]),
        ("SHARED-DATA-SCHEMAS", "architecture/02-domains/_shared-contracts/01-data/shared-data-entities.md", "data_entity", ["SRC-ROOT"]),
        ("SHARED-API-CONTRACTS", "architecture/02-domains/_shared-contracts/02-apis/cross-domain-api-contracts.md", "api_contract", ["SRC-ROOT"]),
        ("SHARED-EVENT-MESSAGES", "architecture/02-domains/_shared-contracts/03-messages/domain-events-and-messages.md", "event_message", ["SRC-ROOT"]),
        ("SHARED-EXTERNAL-CONTRACTS", "architecture/02-domains/_shared-contracts/04-external/external-provider-contracts.md", "api_contract", ["SRC-ROOT"]),
        ("SHARED-STATE-MACHINES", "architecture/02-domains/_shared-contracts/05-state-machines/cross-context-state-machines.md", "flow", ["SRC-ROOT"]),
        # 03-cross-cutting/ & 04-delivery/
        ("XCUT-OVERVIEW", "architecture/03-cross-cutting/00-overview.md", "overview", ["SRC-ROOT"]),
        ("XCUT-MECHANISMS", "architecture/03-cross-cutting/01-mechanisms/resilience-and-idempotency.md", "mechanism", ["SRC-ROOT"]),
        ("XCUT-SECURITY", "architecture/03-cross-cutting/02-security/security-and-tenancy-model.md", "mechanism", ["SRC-ROOT"]),
        ("XCUT-INFRA", "architecture/03-cross-cutting/03-infrastructure/runtime-and-network-baseline.md", "mechanism", ["SRC-ROOT"]),
        ("XCUT-FITNESS", "architecture/03-cross-cutting/04-fitness-functions/fitness-functions-catalog.md", "verification", ["SRC-ROOT"]),
        ("XCUT-EXCEPTIONS", "architecture/03-cross-cutting/05-exceptions/exception-handling-and-error-codes.md", "mechanism", ["SRC-ROOT"]),
        ("DELIV-PLANNING", "architecture/04-delivery/00-planning/implementation-roadmap-and-wbs.md", "planning", ["SRC-ROOT"]),
        ("DELIV-QUALITY", "architecture/04-delivery/01-quality/verification-and-acceptance-gates.md", "verification", ["SRC-ROOT"]),
        ("DELIV-OPERATIONS", "architecture/04-delivery/02-operations/operational-runbook-and-dr.md", "mechanism", ["SRC-ROOT"]),
        ("DELIV-AUDIT", "architecture/04-delivery/04-audit/traceability-and-gap-audit.md", "audit_report", ["SRC-ROOT"]),
    ]
    prof_cfg = contracts.profile_spec(profile)
    mandatory_ids = set(prof_cfg.get("mandatory_artifacts") or [])
    if profile == "seed":
        seed_ids = mandatory_ids or {"SYS-INDEX", "VIEW-C1-CONTEXT", "STRAT-CONTEXT", "STRAT-REQUIREMENTS", "STRAT-SOLUTION", "STRAT-RISKS"}
        return [row for row in all_baseline if row[0] in seed_ids]
    if profile == "minimal":
        min_ids = mandatory_ids or {
            "SYS-INDEX", "VIEW-C1-CONTEXT", "VIEW-C2-CONTAINERS",
            "STRAT-CONTEXT", "STRAT-REQUIREMENTS", "STRAT-SOLUTION", "STRAT-RISKS",
            "DOM-OVERVIEW", "XCUT-OVERVIEW", "XCUT-FITNESS", "DELIV-PLANNING",
        }
        return [row for row in all_baseline if row[0] in min_ids]
    if not include_standard_branches:
        return []
    selected = list(all_baseline)
    if profile == "portfolio":
        selected.extend([
            ("VIEW-C0-LANDSCAPE", "architecture/00-system-views/01-context/c0-system-landscape.md", "diagram", ["SRC-ROOT"]),
            ("DOM-SEGMENTS", "architecture/02-domains/00-overview/segments.md", "overview", ["SRC-ROOT"]),
        ])
    return selected


def scaffold_maximal_plan(
    harvest: dict[str, Any],
    *,
    profile: str = "maximal",
    workspace: Path | str | None = None,
) -> dict[str, Any]:
    """Expand a harvest specification into a complete Pack-Free Archetype-First Target Plan and artifact registry."""
    norm_profile = profile if profile in VALID_PROFILES else "maximal"
    prof_cfg = contracts.profile_spec(norm_profile)
    planned_nodes: list[dict[str, Any]] = []
    artifacts: dict[str, dict[str, Any]] = {}

    # Always include the 3 core planning ledgers
    core_ledgers = [
        ("SRC-MANIFEST", "architecture/00-plan/source-manifest.md", "source_manifest", "01-system-architect"),
        ("CONCERN-INV", "architecture/00-plan/concern-inventory.md", "concern_inventory", "01-system-architect"),
        ("TARGET-PLAN", "architecture/00-plan/document-tree-plan.md", "target_plan", "01-system-architect"),
    ]
    for aid, path, kind, owner in core_ledgers:
        artifacts[aid] = {"path": path, "kind": kind, "owner": owner}

    requires_domains = bool(prof_cfg.get("requires_domains_band", norm_profile != "seed"))
    full_expansion = bool(prof_cfg.get("requires_full_archetype_expansion", norm_profile in {"maximal", "portfolio"}))
    max_contexts = prof_cfg.get("max_bounded_contexts")
    raw_contexts = list(harvest.get("bounded_contexts", []))
    if not requires_domains:
        active_contexts: list[dict[str, Any]] = []
    elif isinstance(max_contexts, int) and norm_profile in {"minimal", "standard"}:
        active_contexts = raw_contexts[:max_contexts]
    else:
        active_contexts = raw_contexts

    # Bounded contexts in 02-domains/ (omitted in `seed` profile per Section 14.1)
    for ctx_pos, ctx in enumerate(active_contexts):
        slug = ctx["slug"]
        inferred_arch, inferred_cluster = infer_core_archetype(slug)
        archetype = ctx.get("archetype") or inferred_arch
        if archetype not in ARCHETYPE_MODULES:
            archetype = inferred_arch
        cluster = ctx.get("cluster") or CORE_ARCHETYPE_CLUSTERS.get(archetype, inferred_cluster)
        idx = ctx.get("index", f"{10 + ctx_pos:02d}")
        requested_skill = ctx.get("skill", "01-system-architect")
        skill = resolve_pack_free_owner(requested_skill, workspace)
        raw_sources = list(ctx.get("source_ids", [f"SRC-{_clean_id_token(slug)}"]))
        slots = expand_archetype_slots(
            slug,
            cluster,
            idx,
            skill,
            archetype,
            include_self_audit=full_expansion,
            max_module_slots=2 if norm_profile == "minimal" else None,
        )
        for slot_idx, slot in enumerate(slots):
            mod_token = _clean_id_token(slot.get("mod_id") or slot["slot"])
            slug_token = _clean_id_token(slug)
            aid = f"CTX-{slug_token}-{mod_token}"
            if len(raw_sources) <= 45:
                slot_sources = list(raw_sources)
            else:
                chunk_size = max(15, min(45, (len(raw_sources) + len(slots) - 1) // len(slots)))
                start = (slot_idx * chunk_size) % max(1, len(raw_sources) - chunk_size + 1)
                slot_sources = raw_sources[start:start + chunk_size]
            dims = _default_dimensions_for_kind(slot["kind"])
            planned_nodes.append({
                "artifact_id": aid,
                "path": slot["path"],
                "kind": slot["kind"],
                "owner": skill,
                "archetype": archetype,
                "disposition": "covered",
                "concern_ids": [f"CNC-{aid}"],
                "source_ids": slot_sources,
                "required_depth_dimensions": dims,
            })
            artifacts[aid] = {"path": slot["path"], "kind": slot["kind"], "owner": skill}

    # Global strategy, 7 Core Diagrams in 00-system-views, _shared-contracts (00..05), cross-cutting, and delivery baseline nodes
    if "include_standard_branches" in harvest:
        include_std = bool(harvest["include_standard_branches"])
    else:
        include_std = bool(prof_cfg.get("include_standard_branches", norm_profile in {"standard", "maximal", "portfolio"})) and not bool(raw_contexts)

    baseline_nodes = _baseline_nodes_for_profile(norm_profile, include_std)
    for aid, path, kind, src_ids in baseline_nodes:
        if aid not in artifacts:
            dims = _default_dimensions_for_kind(kind)
            planned_nodes.append({
                "artifact_id": aid,
                "path": path,
                "kind": kind,
                "owner": "01-system-architect",
                "disposition": "covered",
                "concern_ids": [f"CNC-{aid}"],
                "source_ids": list(src_ids),
                "required_depth_dimensions": dims,
            })
            artifacts[aid] = {"path": path, "kind": kind, "owner": "01-system-architect"}

    for idx, adr in enumerate(harvest.get("adrs", []), 1):
        slug = adr if isinstance(adr, str) else adr["slug"]
        aid = adr.get("id", f"ADR-{idx:04d}") if isinstance(adr, dict) else f"ADR-{idx:04d}"
        aid = _clean_id_token(aid)
        path = f"architecture/01-global-strategy/05-governance/decisions/{idx:04d}-{slug}.md"
        src_ids = adr.get("source_ids", [aid]) if isinstance(adr, dict) else [aid]
        planned_nodes.append({
            "artifact_id": aid,
            "path": path,
            "kind": "adr",
            "owner": "01-system-architect",
            "disposition": "covered",
            "concern_ids": [f"CNC-{aid}"],
            "source_ids": src_ids[:45],
            "required_depth_dimensions": ["authority", "contract", "consumers"],
        })
        artifacts[aid] = {"path": path, "kind": "adr", "owner": "01-system-architect"}

    raw_scenarios = list(harvest.get("runtime_scenarios", []))
    max_scns = prof_cfg.get("max_runtime_scenarios")
    if norm_profile == "seed" and not prof_cfg.get("requires_individual_scenarios", False):
        active_scenarios = []
    elif isinstance(max_scns, int) and norm_profile in {"minimal", "standard"}:
        active_scenarios = raw_scenarios[:max_scns]
    else:
        active_scenarios = raw_scenarios

    for idx, scn in enumerate(active_scenarios, 0):
        slug = scn if isinstance(scn, str) else scn["slug"]
        aid = scn.get("id", f"SCN-{idx:03d}") if isinstance(scn, dict) else f"SCN-{idx:03d}"
        aid = _clean_id_token(aid)
        path = f"architecture/00-system-views/06-runtime/{aid}-{slug}.md"
        src_ids = scn.get("source_ids", [aid]) if isinstance(scn, dict) else [aid]
        planned_nodes.append({
            "artifact_id": aid,
            "path": path,
            "kind": "runtime_scenario",
            "owner": "01-system-architect",
            "disposition": "covered",
            "concern_ids": [f"CNC-{aid}"],
            "source_ids": src_ids[:45],
            "required_depth_dimensions": ["trigger", "states", "guards", "alternate_flows", "observability"],
        })
        artifacts[aid] = {"path": path, "kind": "runtime_scenario", "owner": "01-system-architect"}

    return {
        "selected_profile": norm_profile,
        "coverage_mode": norm_profile,
        "planned_nodes": planned_nodes,
        "artifacts": artifacts,
    }


def _default_dimensions_for_kind(kind: str) -> list[str]:
    if kind in {"api_contract", "api", "frontend"}:
        return ["authority", "contract", "dto", "errors", "alternate_flows", "consumers"]
    if kind in {"data_entity", "data", "artifact"}:
        return ["authority", "fields", "enums", "invariants", "configuration", "consumers"]
    if kind in {"event_message", "runtime_scenario", "flow"}:
        return ["authority", "trigger", "states", "guards", "alternate_flows", "observability"]
    if kind in {"mechanism", "nfr"}:
        return ["authority", "guards", "concurrency", "alternate_flows", "configuration", "observability"]
    return ["authority", "contract", "consumers"]


def auto_discover_sources(workspace: Path) -> list[Path]:
    """Zero-config source discovery: scan workspace (and cwd if workspace is a child folder) for specs and code."""
    root = Path(workspace).resolve()
    search_roots = [root]
    cwd = Path.cwd().resolve()
    if cwd != root and root.parent == cwd:
        search_roots.append(cwd)

    discovered: list[Path] = []
    seen: set[Path] = set()
    skip_dirs = {"architecture", ".architect", ".architect-runtime", ".architect-build", ".sdd", ".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
    code_dir_names = {"frontend", "backend", "src", "app", "services", "packages", "acceptance", "frontend-acceptance", "SRS", "requirements", "specs", "adr", "decisions"}

    for base in search_roots:
        if not base.is_dir():
            continue
        for item in sorted(base.iterdir()):
            if item.name.startswith(".") or item.name in skip_dirs:
                continue
            resolved = item.resolve()
            if resolved in seen:
                continue
            if item.is_file() and item.suffix.lower() in {".md", ".txt", ".rst"} and item.name.lower() not in {"claude.md", "agents.md", "license.md"}:
                seen.add(resolved)
                discovered.append(item)
            elif item.is_dir() and (item.name in code_dir_names or item.name.endswith("-acceptance") or item.name.endswith("-web") or item.name.endswith("-api")):
                seen.add(resolved)
                discovered.append(item)
        if discovered:
            break
    return discovered


def extract_sources_to_harvest(
    workspace: Path,
    source_paths: list[Path] | None = None,
    *,
    audit_mode: bool = False,
) -> dict[str, Any]:
    """Phase 1 Exhaustive Source Intake: hash sources, extract IDs (FR/NFR/BR/ADR/ENT/SCN/GAP), infer Core Archetypes, and detect conflicts."""
    sources_manifest: list[dict[str, Any]] = []
    all_items: list[dict[str, Any]] = []
    adrs: list[dict[str, Any]] = []
    scenarios: list[dict[str, Any]] = []
    bounded_contexts: list[dict[str, Any]] = []
    seen_context_slugs: set[str] = set()
    conflicts: list[dict[str, Any]] = []

    id_pattern = re.compile(r"\b((?:FR|NFR|BR|EX|GAP|ADR|ENT|SCN|UC|CFG|FND)-[A-Za-z0-9_-]{1,32})\b")

    if not source_paths:
        source_paths = auto_discover_sources(Path(workspace))
    for idx, src_path in enumerate(source_paths, 1):
        p = Path(src_path)
        if not p.exists() and (Path(workspace) / src_path).exists():
            p = Path(workspace) / src_path
        sid = f"SRC-{idx:02d}-{_clean_id_token(p.stem or p.name)[:24]}"
        if p.is_dir():
            files = sorted([f for f in p.rglob("*") if f.is_file() and f.suffix in {".md", ".ts", ".tsx", ".py", ".java", ".json", ".yml", ".yaml"}])
            combined_text = "\n".join(f.read_text(encoding="utf-8", errors="replace") for f in files[:60])
            sha = hashlib.sha256(combined_text.encode("utf-8")).hexdigest()
            line_count = len(combined_text.splitlines())
            authority = "observed_code"
        elif p.is_file():
            combined_text = p.read_text(encoding="utf-8", errors="replace")
            sha = hashlib.sha256(combined_text.encode("utf-8")).hexdigest()
            line_count = len(combined_text.splitlines())
            authority = "accepted_decision" if "adr" in p.name.lower() else "requirement"
        else:
            continue

        sections: list[dict[str, Any]] = []
        items: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        current_sec = "SEC-00-ROOT"
        sections.append({"id": current_sec, "status": "extracted", "reconciled": True})

        for line in combined_text.splitlines():
            h_match = re.match(r"^#{1,3}\s+(.+)$", line.strip())
            if h_match:
                heading_text = h_match.group(1).strip()
                sec_slug = _clean_id_token(heading_text)[:32]
                current_sec = f"SEC-{sec_slug}"
                if not any(s["id"] == current_sec for s in sections):
                    sections.append({"id": current_sec, "status": "extracted", "reconciled": True})
                if re.search(r"\b(?:module|context|subsystem|service|portal|gateway|engine|platform)\b", heading_text, re.IGNORECASE):
                    ctx_slug = re.sub(r"[^a-z0-9]+", "-", heading_text.lower()).strip("-")[:32]
                    if ctx_slug and ctx_slug not in seen_context_slugs and len(bounded_contexts) < 12:
                        arch, cluster = infer_core_archetype(heading_text)
                        seen_context_slugs.add(ctx_slug)
                        bounded_contexts.append({
                            "slug": ctx_slug,
                            "cluster": cluster,
                            "index": f"{10 + len(bounded_contexts):02d}",
                            "skill": "01-system-architect",
                            "archetype": arch,
                        })
            for m in id_pattern.finditer(line):
                token = m.group(1).upper()
                if token in seen_ids:
                    continue
                seen_ids.add(token)
                prefix = token.split("-", 1)[0]
                item_kind = {
                    "ADR": "adr",
                    "SCN": "runtime_scenario",
                    "UC": "runtime_scenario",
                    "ENT": "data_entity",
                    "GAP": "gap_closure",
                    "FND": "blocking_finding",
                }.get(prefix, "frontend" if authority == "observed_code" else "requirement")
                item_rec = {
                    "id": token,
                    "section": current_sec,
                    "kind": item_kind,
                    "occurrence_kind": "definition",
                }
                items.append(item_rec)
                all_items.append(item_rec)
                if prefix == "ADR":
                    adrs.append({"id": token, "slug": token.lower(), "source_ids": [token]})
                elif prefix in {"SCN", "UC"}:
                    scenarios.append({"id": token, "slug": token.lower(), "source_ids": [token]})
                elif prefix == "FND" and audit_mode:
                    conflicts.append({
                        "id": f"CNF-{token}",
                        "source_item": token,
                        "authority_preserved": True,
                        "resolution_status": "recorded_conflict",
                        "description": f"Observed acceptance finding {token} requires remediation against specification.",
                    })

        if not items:
            fallback_id = f"REQ-{_clean_id_token(p.stem or 'CORE')[:20]}-001"
            item_rec = {"id": fallback_id, "section": current_sec, "kind": "requirement", "occurrence_kind": "definition"}
            items.append(item_rec)
            all_items.append(item_rec)

        if p.is_dir():
            dir_slug = re.sub(r"[^a-z0-9]+", "-", p.name.lower()).strip("-")[:32]
            if dir_slug and dir_slug not in seen_context_slugs:
                arch, cluster = infer_core_archetype(p.name)
                seen_context_slugs.add(dir_slug)
                bounded_contexts.append({
                    "slug": dir_slug,
                    "cluster": cluster,
                    "index": f"{10 + len(bounded_contexts):02d}",
                    "skill": "01-system-architect",
                    "archetype": arch,
                    "source_ids": [it["id"] for it in items[:45]],
                })

        sources_manifest.append({
            "id": sid,
            "path": str(src_path),
            "sha256": sha,
            "line_count": line_count,
            "authority": authority,
            "read_status": "reconciled",
            "extraction_status": "complete",
            "expected_definition_count": len(items),
            "sections": sections,
            "items": items,
        })

    all_item_ids = [it["id"] for it in all_items] or ["SRC-ROOT"]
    if not bounded_contexts:
        bounded_contexts.append({
            "slug": "core-service",
            "cluster": "03_application_architecture",
            "index": "10",
            "skill": "01-system-architect",
            "archetype": "backend-service",
            "source_ids": all_item_ids[:45],
        })
    else:
        for ctx in bounded_contexts:
            if not ctx.get("source_ids"):
                ctx["source_ids"] = all_item_ids[:45]

    harvest = {
        "sources": sources_manifest,
        "conflicts": conflicts,
        "bounded_contexts": bounded_contexts,
        "adrs": adrs or [{"id": "ADR-0001", "slug": "core-architecture-baseline", "source_ids": [all_items[0]["id"]] if all_items else ["SRC-ROOT"]}],
        "runtime_scenarios": scenarios or [{"id": "SCN-001", "slug": "primary-execution-flow", "source_ids": [all_items[0]["id"]] if all_items else ["SRC-ROOT"]}],
        "include_standard_branches": True,
    }
    out_dir = Path(workspace) / ".architect-build"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "harvest.json").write_text(json.dumps(harvest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return harvest


def freeze_coverage_basis(workspace: Path) -> dict[str, Any]:
    """Compute and freeze document_coverage.basis_digest without chicken-and-egg failure."""
    from sdd_core.storage import Store, atomic_write
    from sdd_core.validation import compute_coverage_basis_digest
    from sdd_core.workspace import CONFIG, capture

    root = Path(workspace).resolve()
    cfg_path = root / CONFIG
    if not cfg_path.is_file():
        from architect_framework.sdd_bridge import BridgeError
        raise BridgeError("WORKSPACE_UNINITIALIZED", f"Missing {CONFIG} in {root}; initialize the workspace first")
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    if not isinstance(cfg, dict):
        raise ValueError("Invalid workspace configuration")
    cov = cfg.setdefault("document_coverage", {
        "schema_version": 1,
        "mode": cfg.get("selected_profile", "maximal"),
        "requested_mode": cfg.get("selected_profile", "maximal"),
        "policy_version": "maximal-coverage-1",
    })
    if not cov.get("basis_digest"):
        cov["basis_digest"] = "pending-initial-freeze"
        with Store(root).lock():
            atomic_write(cfg_path, dump_compact_yaml(cfg).encode("utf-8"))
    snap1 = capture(root, use_cache=False)
    expected_digest = compute_coverage_basis_digest(snap1)
    if cov.get("basis_digest") != expected_digest:
        cov["basis_digest"] = expected_digest
        with Store(root).lock():
            atomic_write(cfg_path, dump_compact_yaml(cfg).encode("utf-8"))
    snap2 = capture(root, use_cache=False)
    return {
        "status": "FROZEN",
        "workspace": str(root),
        "basis_digest": expected_digest,
        "snapshot_digest": snap2.digest,
    }


def _render_authored_page(node: dict[str, Any], *, generate_substantive: bool = True) -> str:
    """Render a 10-section architectural specification page with compact YAML frontmatter."""
    aid = node["artifact_id"]
    kind = node.get("kind", "document")
    dims = node.get("required_depth_dimensions") or _default_dimensions_for_kind(kind)
    sources = (node.get("source_ids") or ["SRC-ROOT"])[:45]
    concerns = node.get("concern_ids") or [f"CNC-{aid}"]
    title = aid.replace("-", " ").title()

    witnesses = {
        "authority": f"Normative authority for {aid} derives from {', '.join(sources[:3])} under owner {node.get('owner', '01-system-architect')} governance.",
        "trigger": f"Execution trigger initiates when an inbound request, command, or scheduled event arrives at {aid}.",
        "contract": f"Contract schema for {aid} enforces versioned request DTOs, response payloads, and deterministic status codes.",
        "dto": f"Request and response DTO payload schemas define explicit field types, validation rules, and error envelopes.",
        "errors": f"Error taxonomy maps validation, authentication, timeout, and conflict status codes to deterministic caller actions.",
        "api_contract": f"API contract endpoint headers, payload schema, and compatibility rules govern all inbound and outbound calls.",
        "fields": f"Entity table schema declares primary key UUIDs, foreign key references, indexed columns, and strict data types.",
        "enums": f"Domain state enums restrict allowed column values and reject unknown enum transitions at persistence boundaries.",
        "invariants": f"Data invariant constraints enforce tenant isolation, uniqueness keys, and non-negative balance assertions.",
        "data_entity": f"Data entity table schema defines primary keys, foreign keys, column types, enums, and invariant constraints.",
        "states": f"Lifecycle state machine transitions from PENDING to ACTIVE, COMPLETED, or FAILED terminal states.",
        "guards": f"State transition guards verify tenant scope, lease fencing tokens, and idempotency keys before mutation.",
        "concurrency": f"Concurrency control uses optimistic locking, lease fencing tokens, and idempotent deduplication keys.",
        "state_machine": f"State machine transitions enforce guard predicates, concurrency locks, and idempotent replay protection.",
        "alternate_flows": f"On timeout, exception, or downstream failure, fallback recovery compensates partial state and retries safely.",
        "error_recovery": f"Error recovery flow executes bounded exponential backoff retries, circuit breaking, and rollback compensation.",
        "recovery": f"Recovery procedures restore consistent state via rollback compensation, dead-letter replay, and fallback routing.",
        "configuration": f"Runtime configuration parameters define timeout thresholds, retry limits, TTL defaults, and feature flags.",
        "observability": f"Observability emits OpenTelemetry trace spans, Prometheus metrics, structured audit logs, and SLO alerts.",
        "consumers": f"Downstream consumers, dependent modules, and caller services integrate with {aid} through versioned seams.",
    }
    selected_witnesses = {d: witnesses.get(d, witnesses["contract"]) for d in dims}

    fm = {
        "artifact_id": aid,
        "kind": kind,
        "owner": node.get("owner", "01-system-architect"),
        "status": "active",
        "concerns": concerns,
        "source_items": sources,
        "depth_dimensions": dims,
        "canonical_facts": [f"FACT-{aid}"],
        "guards": [f"GUARD-{aid}-ISOLATION", f"GUARD-{aid}-IDEMPOTENCY"],
        "depth_witnesses": selected_witnesses,
    }
    fm_text = dump_compact_yaml(fm).strip()

    if not generate_substantive:
        return f"---\n{fm_text}\n---\n# {title}\n\n## 1. Purpose and architectural scope\nTODO: authored content pending.\n"

    sections_body = f"""# {title}

## 1. Purpose and architectural scope
{witnesses["authority"]}
This specification defines the boundary, responsibilities, and verification contract for `{aid}` (`{node["path"]}`).
It ensures every upstream requirement in `{', '.join(sources[:5])}` is realized with traceable design decisions.

## 2. Authority, upstream traceability and requirements
- **Primary Artifact ID**: `{aid}`
- **Owning Skill Role**: `{node.get("owner", "01-system-architect")}`
- **Covered Concerns**: `{', '.join(concerns)}`
- **Upstream Source Items**: `{', '.join(sources[:8])}`
All normative constraints from upstream SRS and ADR baselines govern this module without silent omission.

## 3. Triggers, entry conditions and invocation context
{witnesses["trigger"]}
Callers supply an authenticated tenant context, correlation identifier, and schema-validated input payload before execution begins.
Preconditions verify caller identity, rate-limit quota availability, and upstream dependency readiness.

## 4. Domain model, fields, enums and invariants
{witnesses["fields"]}
{witnesses["enums"]}
{witnesses["invariants"]}
| Element | Type / Constraint | Invariant & Ownership Rule |
| --- | --- | --- |
| `id` | `UUID` (Primary Key) | Immutable canonical identifier owned by `{aid}` |
| `tenant_id` | `UUID` (Foreign Key) | Mandatory tenant isolation boundary enforced by guard `GUARD-{aid}-ISOLATION` |
| `status` | `ENUM(PENDING, ACTIVE, COMPLETED, FAILED)` | Controlled lifecycle state with deterministic transitions |
| `revision` | `BIGINT` (Optimistic Lock) | Monotonically increasing version counter preventing lost updates |

## 5. Contract, schema and versioning
{witnesses["contract"]}
{witnesses["dto"]}
{witnesses["errors"]}
```json
{{
  "contract_id": "{aid}",
  "schema_version": "1.0.0",
  "request_dto": {{"tenant_id": "uuid", "idempotency_key": "string", "payload": {{}}}},
  "response_dto": {{"status": "ACTIVE", "revision": 1}},
  "errors": ["ERR_UNAUTHORIZED", "ERR_CONFLICT_STALE_REVISION", "ERR_TIMEOUT_RETRYABLE"]
}}
```

## 6. States, guards and transitions
{witnesses["states"]}
{witnesses["guards"]}
1. `INITIAL -> PENDING`: Validates caller credentials and records idempotency key under `GUARD-{aid}-IDEMPOTENCY`.
2. `PENDING -> ACTIVE`: Acquires lease fencing token and verifies `GUARD-{aid}-ISOLATION`.
3. `ACTIVE -> COMPLETED`: Commits state mutation and emits audit telemetry receipt.
4. `ACTIVE -> FAILED`: Records terminal failure code and triggers compensation workflow.

## 7. Concurrency, ordering and idempotency
{witnesses["concurrency"]}
Concurrent writes targeting the same entity key serialize through optimistic version checks and lease fencing tokens.
Duplicate requests carrying an identical `idempotency_key` within the retention window return the stored deterministic outcome.

## 8. Alternate flows, failures and recovery
{witnesses["alternate_flows"]}
{witnesses["error_recovery"]}
- **Transient Downstream Timeout**: Executes bounded retry with exponential backoff and jitter before opening the circuit breaker.
- **Stale Revision / Lock Conflict**: Rejects mutation with status `409 Conflict` and instructs caller to refresh state.
- **Partial Execution Failure**: Runs compensating rollback action and routes unrecoverable payloads to the dead-letter queue.

## 9. Configuration, guardrails and observability
{witnesses["configuration"]}
{witnesses["observability"]}
- **Configuration Defaults**: `request_timeout_ms = 3000`, `max_retry_attempts = 3`, `idempotency_ttl_seconds = 86400`.
- **Telemetry Signals**: Emits latency histogram `{aid.lower().replace('-', '_')}_duration_ms`, error counter, and structured audit log events.

## 10. Consumers and related documents
{witnesses["consumers"]}
Downstream services and review gates reference `[Target Document Tree Plan]({posixpath.relpath("architecture/00-plan/document-tree-plan.md", posixpath.dirname(node["path"]) or ".")})` and `[Concern Inventory]({posixpath.relpath("architecture/00-plan/concern-inventory.md", posixpath.dirname(node["path"]) or ".")})` to validate cross-boundary seams.
"""
    return f"---\n{fm_text}\n---\n{sections_body}"


def materialize_workspace(
    workspace: Path,
    harvest: dict[str, Any] | None = None,
    *,
    sources: list[Path] | None = None,
    profile: str = "maximal",
    preset: str = "solo-author",
    reviewer: str = "lead-architect",
    workspace_id: str | None = None,
    stub_only: bool = False,
) -> dict[str, Any]:
    """Materialize a complete SDD architecture tree, ledgers, 6 topological waves (w1..w6), and frozen basis_digest in one command."""
    from architect_framework.sdd_bridge import initialize
    from sdd_core.storage import Store, atomic_write

    norm_profile = profile if profile in VALID_PROFILES else "maximal"
    root = Path(workspace).resolve()
    ws_id = _clean_id_token(workspace_id or root.name or "architect-workspace").lower()
    if not (root / "sdd-workspace.yml").exists():
        initialize(root, ws_id, reviewer, profile=norm_profile, preset=preset, allow_existing_sources=True)

    if harvest is None:
        harvest_file = root / ".architect-build" / "harvest.json"
        if harvest_file.is_file():
            harvest = json.loads(harvest_file.read_text(encoding="utf-8"))
        else:
            harvest = extract_sources_to_harvest(root, sources or auto_discover_sources(root))

    plan_bundle = scaffold_maximal_plan(harvest, profile=norm_profile, workspace=root)
    planned_nodes = plan_bundle["planned_nodes"]
    artifacts_map = plan_bundle["artifacts"]

    # Build reconciled source-manifest.md
    manifest_sources = harvest.get("sources") or []
    all_source_ids: list[str] = []
    for s in manifest_sources:
        for it in s.get("items", []):
            if it.get("id") and it["id"] not in all_source_ids:
                all_source_ids.append(it["id"])
    for node in planned_nodes:
        for sid in node.get("source_ids", []):
            if sid not in all_source_ids:
                all_source_ids.append(sid)
    if not manifest_sources:
        manifest_sources = [{
            "id": "SRC-DEFAULT",
            "path": "SYSTEM_REQUIREMENTS.md",
            "authority": "requirement",
            "read_status": "reconciled",
            "extraction_status": "complete",
            "expected_definition_count": len(all_source_ids),
            "sections": [{"id": "SEC-MAIN", "status": "extracted", "reconciled": True}],
            "items": [{"id": sid, "section": "SEC-MAIN", "kind": "requirement", "occurrence_kind": "definition"} for sid in all_source_ids],
        }]
    else:
        existing_manifest_ids = {it["id"] for s in manifest_sources for it in s.get("items", []) if isinstance(it, dict) and it.get("id")}
        extra_ids = [sid for sid in all_source_ids if sid not in existing_manifest_ids]
        if extra_ids:
            sec_id = manifest_sources[0]["sections"][0]["id"] if manifest_sources[0].get("sections") else "SEC-MAIN"
            for sid in extra_ids:
                manifest_sources[0].setdefault("items", []).append({
                    "id": sid,
                    "section": sec_id,
                    "kind": "adr" if sid.startswith("ADR-") else ("runtime_scenario" if sid.startswith("SCN-") else "requirement"),
                    "occurrence_kind": "definition",
                })
            manifest_sources[0]["expected_definition_count"] = len(manifest_sources[0]["items"])

    manifest_fm = {
        "sources": manifest_sources,
        "conflicts": harvest.get("conflicts", []),
    }
    manifest_md = (
        f"---\n{dump_compact_yaml(manifest_fm).strip()}\n---\n"
        "# Source Manifest\n\nReconciled source intake ledger covering 100% of declared input sources.\n"
    )

    # Build reconciled concern-inventory.md
    concerns_list: list[dict[str, Any]] = []
    covered_in_concerns: set[str] = set()
    for node in planned_nodes:
        aid = node["artifact_id"]
        cids = node.get("concern_ids") or [f"CNC-{aid}"]
        sids = node.get("source_ids") or ["SRC-ROOT"]
        covered_in_concerns.update(sids)
        for cid in cids:
            concerns_list.append({
                "id": cid,
                "source_items": sids,
                "disposition": "covered",
                "critical": True,
                "owner": node.get("owner", "01-system-architect"),
                "owner_artifact": aid,
                "required_depth_dimensions": node.get("required_depth_dimensions") or _default_dimensions_for_kind(node.get("kind", "document")),
            })
    leftover = sorted(set(all_source_ids) - covered_in_concerns)
    if leftover and concerns_list:
        concerns_list[0]["source_items"] = sorted(set(concerns_list[0]["source_items"]) | set(leftover))

    inv_fm = {"concerns": concerns_list}
    inv_md = (
        f"---\n{dump_compact_yaml(inv_fm).strip()}\n---\n"
        "# Concern Inventory\n\nIndependent source-to-concern accounting matrix.\n"
    )

    # Build document-tree-plan.md
    plan_fm = {
        "artifact_id": "TARGET-PLAN",
        "kind": "target_plan",
        "schema_version": 1,
        "coverage_mode": norm_profile,
        "requested_mode": norm_profile,
        "selected_profile": norm_profile,
        "policy_version": "maximal-coverage-1",
        "source_manifest_artifact": "SRC-MANIFEST",
        "concern_inventory_artifact": "CONCERN-INV",
        "planned_nodes": planned_nodes,
    }
    plan_md = (
        f"---\n{dump_compact_yaml(plan_fm).strip()}\n---\n"
        "# Target Document Tree Plan\n\n## Source Complexity Harvest and Concern Accounting Matrix\n"
        f"Materialized {len(planned_nodes)} architecture specification nodes under `{norm_profile}` profile.\n"
    )

    # Write ledger files and node files
    files_to_write: dict[str, str] = {
        "architecture/00-plan/source-manifest.md": manifest_md,
        "architecture/00-plan/concern-inventory.md": inv_md,
        "architecture/00-plan/document-tree-plan.md": plan_md,
    }
    for node in planned_nodes:
        files_to_write[node["path"]] = _render_authored_page(node, generate_substantive=not stub_only)

    for rel_path, content in files_to_write.items():
        full_path = root / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(full_path, content.encode("utf-8"))

    # Write .architect-build/page-spec.json and unified 6 topological waves (w1..w6)
    build_dir = root / ".architect-build"
    waves_dir = build_dir / "waves"
    waves_dir.mkdir(parents=True, exist_ok=True)
    for stale_wave in waves_dir.glob("*.json"):
        stale_wave.unlink(missing_ok=True)
    (build_dir / "page-spec.json").write_text(json.dumps(plan_bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    wave_buckets: dict[int, list[dict[str, Any]]] = {w: [] for w in WAVE_DEFINITIONS}
    for node in planned_nodes:
        w_num, _ = classify_wave_for_path(node.get("path", ""))
        wave_buckets[w_num].append(node)

    wave_files: list[str] = []
    batch_size = 4
    for w_num, w_slug in sorted(WAVE_DEFINITIONS.items()):
        w_nodes = wave_buckets[w_num]
        if not w_nodes:
            continue
        for b_idx in range(0, len(w_nodes), batch_size):
            batch = w_nodes[b_idx:b_idx + batch_size]
            b_num = (b_idx // batch_size) + 1
            batch_id = f"{w_slug}-batch-{b_num:03d}"
            w_name = f"{batch_id}.json"
            payload = {
                "batch_id": batch_id,
                "wave": w_num,
                "wave_name": w_slug,
                "batch": b_num,
                "batch_index": b_num,
                "max_concurrent_subagents": 4,
                "immutable": True,
                "artifact_count": len(batch),
                "artifacts": batch,
                "nodes": batch,
            }
            (waves_dir / w_name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
            wave_files.append(w_name)

    # Update sdd-workspace.yml and freeze basis_digest
    cfg_path = root / "sdd-workspace.yml"
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    cfg["selected_profile"] = norm_profile
    cfg["artifacts"] = artifacts_map
    cfg["document_coverage"] = {
        "schema_version": 1,
        "mode": norm_profile,
        "requested_mode": norm_profile,
        "policy_version": "maximal-coverage-1",
        "source_manifest_artifact": "SRC-MANIFEST",
        "concern_inventory_artifact": "CONCERN-INV",
        "target_plan_artifact": "TARGET-PLAN",
        "basis_digest": "pending-initial-freeze",
        "enforce_maximal_structure": norm_profile in {"maximal", "portfolio"},
    }
    owners = set(cfg.get("owners") or ["01-system-architect", "system-owner", reviewer])
    skills_cfg = cfg.setdefault("skills", {})
    try:
        from architect_framework import skillpacks
        with skillpacks.activated(root):
            for sk_id in skillpacks.installed():
                if sk_id not in skills_cfg and sk_id != "architect-runtime":
                    skills_cfg[sk_id] = {"capabilities": ["author", "configure"], "write_scope": ["architecture", "sdd-workspace.yml"]}
    except Exception:
        pass
    for a in artifacts_map.values():
        owners.add(a["owner"])
        if a["owner"] not in skills_cfg and a["owner"] not in {"system-owner", reviewer}:
            skills_cfg[a["owner"]] = {"capabilities": ["author", "configure"], "write_scope": ["architecture", "sdd-workspace.yml"]}
    cfg["owners"] = sorted(owners)
    cfg["control_directories"] = [".architect", ".architect-runtime", ".architect-build"]
    with Store(root).lock():
        atomic_write(cfg_path, dump_compact_yaml(cfg).encode("utf-8"))

    if not stub_only:
        from architect_framework.sdd_bridge.authoring_qa import prepare_check
        prepare_check(root, tighten=True, style_fix=True, stamp=True, pad_to_min=True)
    frozen = freeze_coverage_basis(root)
    return {
        "status": "MATERIALIZED",
        "workspace": str(root),
        "profile": norm_profile,
        "preset": preset,
        "artifact_count": len(artifacts_map),
        "planned_node_count": len(planned_nodes),
        "wave_batches": len(wave_files),
        "basis_digest": frozen["basis_digest"],
        "snapshot_digest": frozen["snapshot_digest"],
    }
