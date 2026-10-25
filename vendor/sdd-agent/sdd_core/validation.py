from __future__ import annotations

import math
import re

from .graph import affected, build_graph, full_impact_oracle
from .model import Finding, Result, Snapshot, SddError, Status, canonical, digest
from .parsing import pointer
from .workspace import diff

UNITS = {"ms": ("time", .001), "s": ("time", 1), "min": ("time", 60), "h": ("time", 3600),
         "B": ("size", 1), "KiB": ("size", 1024), "MiB": ("size", 1048576)}

_PLACEHOLDER_RE = re.compile(
    r"(?i)(\b(?:TODO(?!\s+(?:list|lists|item|items|state|states|status|task|tasks|app|board)\b)|TBD|FIXME|XXX)\b|lorem ipsum|authored content pending|to be completed|coming soon)"
)
_FENCE_BLOCK_RE = re.compile(r"(?ms)^[ \t]*(?:`{3,}|~{3,})[^\n]*\n.*?^[ \t]*(?:`{3,}|~{3,})[ \t]*$")
_THINK_BLOCK_RE = re.compile(r"(?is)\A\s*<think>.*?</think>\s*")
_TOC_LINK_RE = re.compile(r"^(?:[-*+]|\d+[.)])\s+\[[^\]]+\]\(#[^)]+\)\s*$")
_TABLE_SEP_RE = re.compile(r"^\s*\|?[\s:|-]+\|[\s:|-]*$")

DEPTH_DIMENSION_PATTERNS: dict[str, re.Pattern[str]] = {
    "contract": re.compile(r"(?i)\b(dto|payload|request|response|error|status|schema|field|contract|endpoint|header|version)\b"),
    "dto": re.compile(r"(?i)\b(dto|payload|request|response|error|status|schema|field|contract|endpoint|header|version)\b"),
    "errors": re.compile(r"(?i)\b(dto|payload|request|response|error|status|schema|field|contract|endpoint|header|version)\b"),
    "api_contract": re.compile(r"(?i)\b(dto|payload|request|response|error|status|schema|field|contract|endpoint|header|version)\b"),
    "fields": re.compile(r"(?i)\b(field|column|type|enum|invariant|constraint|primary|foreign|key|index|table)\b"),
    "enums": re.compile(r"(?i)\b(field|column|type|enum|invariant|constraint|primary|foreign|key|index|table)\b"),
    "invariants": re.compile(r"(?i)\b(field|column|type|enum|invariant|constraint|primary|foreign|key|index|table)\b"),
    "data_entity": re.compile(r"(?i)\b(field|column|type|enum|invariant|constraint|primary|foreign|key|index|table)\b"),
    "alternate_flows": re.compile(r"(?i)\b(alternate|exception|error|failure|retry|fallback|recover\w*|compensat\w*|timeout|rollback|degrad\w*|dlq)\b"),
    "error_recovery": re.compile(r"(?i)\b(alternate|exception|error|failure|retry|fallback|recover\w*|compensat\w*|timeout|rollback|degrad\w*|dlq)\b"),
    "recovery": re.compile(r"(?i)\b(alternate|exception|error|failure|retry|fallback|recover\w*|compensat\w*|timeout|rollback|degrad\w*|dlq)\b"),
    "guards": re.compile(r"(?i)\b(guard\w*|transition\w*|concurren\w*|lock\w*|lease\w*|fenc\w*|idempoten\w*|invariant\w*|optimistic|mutex|serializ\w*)\b"),
    "concurrency": re.compile(r"(?i)\b(guard\w*|transition\w*|concurren\w*|lock\w*|lease\w*|fenc\w*|idempoten\w*|invariant\w*|optimistic|mutex|serializ\w*)\b"),
    "state_machine": re.compile(r"(?i)\b(guard\w*|transition\w*|concurren\w*|lock\w*|lease\w*|fenc\w*|idempoten\w*|invariant\w*|optimistic|mutex|serializ\w*)\b"),
    "authority": re.compile(r"(?i)\b(authority|source|srs|adr|fr-\d+|nfr-\d+|br-\d+|owner|upstream|normative|mandate|govern\w*|accept\w*|status|baseline)\b"),
    "trigger": re.compile(r"(?i)\b(trigger\w*|event\w*|command\w*|request\w*|schedule\w*|webhook\w*|invok\w*|dispatch\w*|publish\w*|emit\w*|arrival|cron)\b"),
    "states": re.compile(r"(?i)\b(state\w*|status|phase|lifecycle|pending|active|completed|failed|transition\w*|terminal|initial)\b"),
    "configuration": re.compile(r"(?i)\b(config\w*|env|parameter\w*|setting\w*|timeout\w*|threshold\w*|limit\w*|ttl|default\w*|flag\w*|ceiling|quota\w*)\b"),
    "observability": re.compile(r"(?i)\b(metric\w*|trace\w*|span\w*|log\w*|alert\w*|slo|sli|telemetry|prometheus|otel|audit\w*|counter\w*|histogram\w*|signal\w*|observability|reconciliat\w*)\b"),
    "consumers": re.compile(r"(?i)\b(consumer\w*|downstream|client\w*|subscriber\w*|caller\w*|depend\w*|integrat\w*|module\w*|service\w*|view\w*|reader\w*)\b"),
}

_LEDGER_KINDS = frozenset({"source_manifest", "concern_inventory", "target_plan", "planning", "source"})


def _is_upstream_requirement(artifact) -> bool:
    """Distinguish upstream requirement artifacts from downstream bounded-context SLO pages (ISS-06)."""
    if artifact.kind != "requirement" or artifact.metadata.get("status") == "deprecated":
        return False
    path = str(artifact.path or "")
    if artifact.id.startswith("CTX-") or "/02-domains/" in path or path.startswith("02-domains/") or "/12-slo/" in path:
        return False
    return True


def subject_artifact(snapshot: Snapshot, subject: str):
    if subject in snapshot.artifacts:
        return snapshot.artifacts[subject]
    return next((a for a in snapshot.artifacts.values() if subject in a.clauses), None)


def subject_revision(snapshot: Snapshot, subject: str):
    artifact = subject_artifact(snapshot, subject)
    if artifact is None:
        return None
    return artifact.clauses[subject]["digest"] if subject in artifact.clauses else artifact.revision


def normative_obligation(obligation):
    return {k: v for k, v in obligation.items() if k != "owner"}


def historical_changes(before: Snapshot | None, after: Snapshot) -> dict[str, dict]:
    if before is None:
        return {}
    old = {o["id"]: o for o in before.config["obligations"] if o.get("active", True)}
    new = {o["id"]: o for o in after.config["obligations"] if o.get("active", True)}
    changes = {}
    for identifier, obligation in old.items():
        candidate = new.get(identifier)
        if candidate is None or normative_obligation(obligation) != normative_obligation(candidate):
            changes[identifier] = {"kind": "contract_change", "before": obligation, "after": candidate}
        elif (subject_revision(before, obligation["source"]) != subject_revision(after, obligation["source"])
              or (subject_artifact(before, obligation["source"]) and
                  subject_artifact(before, obligation["source"]).revision !=
                  getattr(subject_artifact(after, obligation["source"]), "revision", None))):
            facts = []
            for check in obligation.get("checks", []):
                reference = check["source"]
                if reference["artifact"] != obligation["source"]:
                    continue
                try:
                    old_fact = pointer(subject_artifact(before, obligation["source"]).data, reference["pointer"])
                    new_artifact = subject_artifact(after, obligation["source"])
                    new_fact = pointer(new_artifact.data, reference["pointer"]) if new_artifact else None
                    if canonical(old_fact) != canonical(new_fact):
                        facts.append({"pointer": reference["pointer"], "before": old_fact, "after": new_fact})
                except SddError:
                    facts.append({"pointer": reference["pointer"], "status": "INCOMPLETE"})
            changes[identifier] = {"kind": "source_change", "before": obligation, "after": candidate, "source_fact_changes": facts}
    if before.config["policy"] != after.config["policy"]:
        changes["@policy"] = {"kind": "policy_change", "before": before.config["policy"], "after": after.config["policy"]}
    return changes


def relation_check(snapshot, check):
    source = subject_artifact(snapshot, check["source"]["artifact"])
    target = subject_artifact(snapshot, check["target"]["artifact"])
    if source is None or target is None:
        raise SddError("RELATION_INPUT_MISSING", check["id"], Status.INCOMPLETE)
    left, right = pointer(source.data, check["source"]["pointer"]), pointer(target.data, check["target"]["pointer"])
    if "source_unit" in check or "target_unit" in check:
        if not all(k in check for k in ("source_unit", "target_unit")):
            raise SddError("UNIT_UNSPECIFIED", check["id"], Status.INCOMPLETE)
        su, sf = UNITS[check["source_unit"]]
        tu, tf = UNITS[check["target_unit"]]
        if su != tu or type(left) not in {int, float} or type(right) not in {int, float}:
            raise SddError("UNIT_TYPE_MISMATCH", check["id"])
        left, right = left * sf, right * tf
    operator = check["operator"]
    if operator == "equal":
        ok = canonical(left) == canonical(right)
        if "source_unit" in check:
            ok = math.isclose(left, right, rel_tol=1e-12, abs_tol=0)
    elif operator in {"subset", "transitions"}:
        if not isinstance(left, list) or not isinstance(right, list):
            raise SddError("RELATION_TYPE_MISMATCH", "subset/transitions require arrays")
        ok = {canonical(x) for x in right} <= {canonical(x) for x in left}
    elif operator == "contains":
        if not isinstance(left, list):
            raise SddError("RELATION_TYPE_MISMATCH", "contains requires an authoritative array")
        ok = canonical(right) in {canonical(x) for x in left}
    else:
        if type(right) not in {int, float} or not any(x in check for x in ("minimum", "maximum")):
            raise SddError("RELATION_TYPE_MISMATCH", "range requires a numeric target and bounds")
        ok = check.get("minimum", -math.inf) <= right <= check.get("maximum", math.inf)
    return ok, (source.id, target.id), ({"artifact_id": source.id, "revision": source.revision, "pointer": check["source"]["pointer"]},
                                         {"artifact_id": target.id, "revision": target.revision, "pointer": check["target"]["pointer"]})


def _strip_frontmatter_only(text: str) -> str:
    body = _THINK_BLOCK_RE.sub("", text or "")
    if body.startswith("---\n"):
        end = body.find("\n---\n", 4)
        if end != -1:
            body = body[end + 5:]
    elif body.startswith("---\r\n"):
        end = body.find("\r\n---\r\n", 5)
        if end != -1:
            body = body[end + 7:]
    return body


def _strip_frontmatter_and_chrome(text: str, *, strip_placeholders: bool = True) -> str:
    """Extract substantive body lines, stripping headings, TOC, blockquotes, and chrome (ISS-02, ISS-04)."""
    body = _strip_frontmatter_only(text)
    lines = []
    in_comment = False
    for line in body.splitlines():
        s = line.strip()
        if not s:
            continue
        if in_comment:
            if "-->" in s:
                in_comment = False
            continue
        if s.startswith("<!--"):
            if "-->" not in s:
                in_comment = True
            continue
        if re.match(r"^#{1,6}\s+", s):
            continue
        if s.startswith("[←") or s.startswith("[<-"):
            continue
        if s.startswith(">"):
            continue
        if _TOC_LINK_RE.match(s):
            continue
        if _TABLE_SEP_RE.match(s):
            continue
        if strip_placeholders and _PLACEHOLDER_RE.search(s):
            continue
        lines.append(s)
    return "\n".join(lines)


def _audit_prose_substance(art, mode: str, cov: dict) -> tuple[list[Finding], bool]:
    """Detect placeholder/stub text, empty sections, and line budget violations (ISS-03 / WO-R1.3)."""
    findings: list[Finding] = []
    is_substantive = True
    if art.metadata.get("generated") or art.metadata.get("status") == "deprecated":
        return findings, True
    if art.kind in _LEDGER_KINDS or str(art.path).endswith((".json", ".yml", ".yaml")):
        return findings, True

    raw_body = _strip_frontmatter_only(art.text)
    prose_no_fences = _FENCE_BLOCK_RE.sub("", raw_body)

    # 1. Placeholder / TODO stub detection
    if _PLACEHOLDER_RE.search(prose_no_fences):
        is_substantive = False
        findings.append(Finding(
            "PLACEHOLDER_CONTENT_DETECTED",
            f"Artifact {art.id} contains unresolved placeholder or stub content (e.g., TODO / authored content pending)",
            (art.id,),
            Status.INCOMPLETE,
        ))

    # 2. Empty section detection on structured multi-section pages
    masked_body = _FENCE_BLOCK_RE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), raw_body)
    numbered_sections = list(re.finditer(r"(?m)^##\s+(\d+\.\s+.+)$", masked_body))
    if len(numbered_sections) >= 4:
        empty_secs: list[str] = []
        for idx, match in enumerate(numbered_sections):
            sec_title = match.group(1).strip()
            start = match.end()
            end = numbered_sections[idx + 1].start() if idx + 1 < len(numbered_sections) else len(raw_body)
            sec_chunk = raw_body[start:end]
            sec_lines = []
            for ln in sec_chunk.splitlines():
                st = ln.strip()
                if not st or st.startswith("#") or st.startswith(">") or st.startswith("[←") or st.startswith("[<-"):
                    continue
                if _TOC_LINK_RE.match(st) or _TABLE_SEP_RE.match(st) or _PLACEHOLDER_RE.search(st):
                    continue
                sec_lines.append(st)
            sec_words = sum(len(x.split()) for x in sec_lines)
            if len(sec_lines) < 2 and sec_words < 20:
                empty_secs.append(sec_title)
        if empty_secs:
            is_substantive = False
            findings.append(Finding(
                "SECTION_BODY_EMPTY",
                f"Artifact {art.id} has {len(empty_secs)} empty or stub section(s): {', '.join(empty_secs[:3])}",
                (art.id,),
                Status.INCOMPLETE,
            ))

    # 3. Line budget verification (180-350 lines) for maximal structured pages
    adata = art.data if isinstance(art.data, dict) else {}
    enforce_budget = bool(cov.get("enforce_line_budget", False) or adata.get("enforce_line_budget", False) or (mode in {"maximal", "portfolio"} and len(numbered_sections) >= 8))
    if enforce_budget:
        total_lines = len((art.text or "").splitlines())
        body_lines = len(raw_body.strip().splitlines())
        too_short = total_lines < 180 and body_lines < 160
        too_long = body_lines > 350 and total_lines > 350
        if too_short or too_long:
            is_substantive = False
            findings.append(Finding(
                "PAGE_LINE_BUDGET_VIOLATION",
                f"Artifact {art.id} violates maximal page line budget (expected 180-350 lines; got total={total_lines}, body={body_lines})",
                (art.id,),
                Status.INCOMPLETE,
            ))

    return findings, is_substantive


def compute_coverage_basis_digest(snapshot: Snapshot) -> str:
    cov = snapshot.config.get("document_coverage") or {}
    manifest_id = cov.get("source_manifest_artifact")
    inv_id = cov.get("concern_inventory_artifact")
    plan_id = cov.get("target_plan_artifact")
    revs = {}
    for aid in (manifest_id, inv_id, plan_id):
        if aid and aid in snapshot.artifacts:
            revs[aid] = snapshot.artifacts[aid].revision
    for a in sorted(snapshot.artifacts.values(), key=lambda x: x.id):
        if a.kind == "source" or _is_upstream_requirement(a):
            revs[a.id] = a.revision
    payload = {
        "schema_version": cov.get("schema_version", 1),
        "mode": cov.get("mode", snapshot.config.get("selected_profile", "standard")),
        "requested_mode": cov.get("requested_mode", cov.get("mode", "standard")),
        "policy_version": cov.get("policy_version", "maximal-coverage-1"),
        "revisions": revs,
        "skills": snapshot.config.get("skills", {}),
    }
    return digest(payload)


def evaluate_document_coverage(snapshot: Snapshot, before: Snapshot | None, graph, result: Result) -> None:
    cov = snapshot.config.get("document_coverage")
    selected_profile = snapshot.config.get("selected_profile")
    if cov is None and selected_profile is None:
        result.details["coverage_status"] = "coverage not evaluated"
        return

    cov = cov or {}
    mode = cov.get("mode") or selected_profile or "standard"
    requested_mode = cov.get("requested_mode") or mode
    manifest_id = cov.get("source_manifest_artifact")
    inv_id = cov.get("concern_inventory_artifact")
    plan_id = cov.get("target_plan_artifact")
    manifest_art = snapshot.artifacts.get(manifest_id) if manifest_id else None
    inv_art = snapshot.artifacts.get(inv_id) if inv_id else None
    plan_art = snapshot.artifacts.get(plan_id) if plan_id else None

    # DTG-04: Intent preservation (no silent downgrade from maximal to seed/minimal, no budget tree shrink)
    plan_data = (plan_art.data if plan_art and isinstance(plan_art.data, dict) else {})
    plan_profile = plan_data.get("selected_profile") or plan_data.get("coverage_mode")
    if requested_mode in {"maximal", "portfolio"} and (mode in {"seed", "minimal"} or selected_profile in {"seed", "minimal"} or plan_profile in {"seed", "minimal"}):
        result.findings.append(Finding(
            "INTENT_DOWNGRADE_FORBIDDEN",
            "Maximal coverage intent cannot be downgraded to seed or minimal",
            (plan_id or "@coverage",),
            Status.FAIL,
        ))
    if plan_data.get("shrunk_for_budget") is True or (
        isinstance(plan_data.get("required_applicable_node_count"), int)
        and len(plan_data.get("planned_nodes", [])) < plan_data["required_applicable_node_count"]
    ):
        result.findings.append(Finding(
            "BUDGET_TREE_SHRINK_FORBIDDEN",
            "Execution or token budget must batch tasks, never reduce the target document tree",
            (plan_id or "@coverage",),
            Status.FAIL,
        ))

    # DTG-01: Source intake & extraction reconciliation
    total_sources = 0
    reconciled_sources = 0
    manifest_items: dict[str, dict] = {}
    if manifest_id and manifest_art is None:
        result.findings.append(Finding(
            "SOURCE_INTAKE_INCOMPLETE",
            f"Declared source_manifest_artifact {manifest_id} is missing",
            (manifest_id,),
            Status.INCOMPLETE,
        ))
    elif manifest_art is not None:
        mdata = manifest_art.data if isinstance(manifest_art.data, dict) else {}
        sources = mdata.get("sources", [])
        total_sources = len(sources)
        for src in sources:
            if not isinstance(src, dict):
                continue
            sid = str(src.get("id", "unknown-source"))
            rstatus = src.get("read_status", "unread")
            ext_status = src.get("extraction_status", "complete")
            if rstatus != "reconciled" or ext_status in {"partial", "truncated", "failed", "unread"}:
                result.findings.append(Finding(
                    "SOURCE_INTAKE_INCOMPLETE",
                    f"Source {sid} intake is incomplete (read_status={rstatus}, extraction_status={ext_status})",
                    (sid,),
                    Status.INCOMPLETE,
                ))
            else:
                reconciled_sources += 1

            items = src.get("items", [])
            extracted_sections = set()
            defs = []
            for item in items:
                if isinstance(item, dict) and item.get("id"):
                    manifest_items[item["id"]] = {**item, "source_id": sid}
                    if item.get("section"):
                        extracted_sections.add(item["section"])
                    if item.get("occurrence_kind", "definition") == "definition":
                        defs.append(item)

            exclusions = {
                (ex["section"] if isinstance(ex, dict) else str(ex)): (ex.get("rationale") if isinstance(ex, dict) else "excluded")
                for ex in src.get("exclusions", [])
            }
            for sec in src.get("sections", []):
                sec_id = sec.get("id") if isinstance(sec, dict) else str(sec)
                sec_status = sec.get("status", "extracted") if isinstance(sec, dict) else ("extracted" if sec_id in extracted_sections else ("excluded" if sec_id in exclusions else "missing"))
                sec_rat = sec.get("rationale") if isinstance(sec, dict) else exclusions.get(sec_id)
                if sec_status == "missing" or (sec_status == "excluded" and not sec_rat) or (sec_status == "extracted" and items and sec_id not in extracted_sections and not (isinstance(sec, dict) and sec.get("reconciled"))):
                    result.findings.append(Finding(
                        "SOURCE_SECTION_UNRECONCILED",
                        f"Section {sec_id} in source {sid} is neither extracted nor excluded with rationale",
                        (sid,),
                        Status.INCOMPLETE,
                    ))

            if "expected_definition_count" in src and (
                len(defs) != src["expected_definition_count"] or src.get("merged_definitions_and_references") is True
            ):
                result.findings.append(Finding(
                    "SOURCE_COUNT_MISMATCH",
                    f"Source {sid} definition count ({len(defs)}) does not match expected ({src['expected_definition_count']}) or conflates references",
                    (sid,),
                    Status.INCOMPLETE,
                ))

        for conflict in mdata.get("conflicts", []):
            if isinstance(conflict, dict) and (
                conflict.get("authority_preserved") is False
                or conflict.get("resolution_status") not in {"recorded_conflict", "resolved_by_decision"}
            ):
                result.findings.append(Finding(
                    "SOURCE_AUTHORITY_CONFLICT",
                    f"Source conflict {conflict.get('id', 'conflict')} overwrote source authority without recording conflict disposition",
                    (manifest_id,),
                    Status.FAIL,
                ))

        for unreg in mdata.get("unregistered_source_items", []):
            uid = unreg.get("id", str(unreg)) if isinstance(unreg, dict) else str(unreg)
            result.findings.append(Finding(
                "SOURCE_ITEM_UNACCOUNTED",
                f"External source requirement {uid} is not registered or accounted for",
                (uid,),
                Status.INCOMPLETE,
            ))

    # DTG-02: Source accounting & Concern Inventory dispositions
    concerns: list[dict] = []
    covered_source_items: set[str] = set()
    covered_owner_artifacts: set[str] = set()
    if inv_id and inv_art is None:
        result.findings.append(Finding(
            "SOURCE_ACCOUNTING_INCOMPLETE",
            f"Declared concern_inventory_artifact {inv_id} is missing",
            (inv_id,),
            Status.INCOMPLETE,
        ))
    elif inv_art is not None:
        idata = inv_art.data if isinstance(inv_art.data, dict) else {}
        concerns = [c for c in idata.get("concerns", []) if isinstance(c, dict)]
        for c in concerns:
            if c.get("owner_artifact"):
                covered_owner_artifacts.add(str(c["owner_artifact"]))
            for sitem in c.get("source_items", []):
                covered_source_items.add(sitem)

        for item_id in sorted(set(manifest_items) - covered_source_items):
            result.findings.append(Finding(
                "SOURCE_ITEM_UNACCOUNTED",
                f"Source item {item_id} from {manifest_id} is not accounted for in {inv_id}",
                (item_id,),
                Status.INCOMPLETE,
            ))

        # Also check that every registered upstream requirement artifact/clause is accounted for when inventory is active
        if manifest_items or concerns:
            all_accounted_refs = covered_source_items | set(manifest_items) | covered_owner_artifacts
            for req_art in snapshot.artifacts.values():
                if _is_upstream_requirement(req_art):
                    subjects = list(req_art.clauses) if req_art.clauses else [req_art.id]
                    if req_art.id not in all_accounted_refs and any(s not in all_accounted_refs for s in subjects):
                        declared_obl_sources = {o["source"] for o in snapshot.config["obligations"] if o.get("active", True)}
                        for s in subjects:
                            if s not in all_accounted_refs and s not in declared_obl_sources:
                                result.findings.append(Finding(
                                    "SOURCE_ITEM_UNACCOUNTED",
                                    f"Requirement subject {s} is missing from independent concern accounting",
                                    (s,),
                                    Status.INCOMPLETE,
                                ))

    # Audit prose substance across all registered artifacts (WO-R1.3)
    substance_ok_by_artifact: dict[str, bool] = {}
    for art in sorted(snapshot.artifacts.values(), key=lambda x: x.id):
        sub_findings, sub_ok = _audit_prose_substance(art, mode, cov)
        result.findings.extend(sub_findings)
        substance_ok_by_artifact[art.id] = sub_ok

    # DTG-03: Plan coverage & anti-collapse checks
    planned_nodes = [n for n in plan_data.get("planned_nodes", []) if isinstance(n, dict)]
    planned_by_concern: dict[str, list[dict]] = {}
    for node in planned_nodes:
        nid = node.get("artifact_id", "unknown-node")
        n_concerns = node.get("concern_ids", [])
        n_sources = node.get("source_ids", [])
        n_kind = node.get("kind", "document")
        if not n_concerns and not n_sources and n_kind not in {"navigation", "overview", "target_plan", "source_manifest", "concern_inventory"}:
            result.findings.append(Finding(
                "UNJUSTIFIED_PLAN_PADDING",
                f"Planned node {nid} has no source_ids or concern_ids",
                (nid,),
                Status.FAIL,
            ))
        for cid in n_concerns:
            planned_by_concern.setdefault(cid, []).append(node)

    if plan_id and plan_art is None:
        result.findings.append(Finding(
            "PLAN_COVERAGE_INCOMPLETE",
            f"Declared target_plan_artifact {plan_id} is missing",
            (plan_id,),
            Status.INCOMPLETE,
        ))

    for req_family in cov.get("required_families", []):
        has_family = any(
            req_family in a.path or req_family == a.kind or req_family in (a.data.get("family", "") if isinstance(a.data, dict) else "")
            for a in snapshot.artifacts.values()
        ) or any(req_family in str(n.get("path", "")) or req_family == n.get("family") for n in planned_nodes)
        if not has_family:
            result.findings.append(Finding(
                "PLAN_COVERAGE_INCOMPLETE",
                f"Required architectural family '{req_family}' has no planned or authored node",
                (req_family,),
                Status.INCOMPLETE,
            ))

    if mode in {"maximal", "portfolio"} and cov.get("enforce_maximal_structure", False):
        flat_domains = [
            a.id for a in snapshot.artifacts.values()
            if re.match(r"^(?:architecture/)?02-domains/[^/_][^/]*\.md$", a.path)
        ]
        if flat_domains:
            result.findings.append(Finding(
                "FLAT_DOMAINS_DEFECT",
                "Maximal mode forbids collapsing bounded contexts into single flat files directly under 02-domains/",
                tuple(sorted(flat_domains)),
                Status.FAIL,
            ))
        adr_items = [it for it in manifest_items.values() if it.get("kind") == "adr"]
        adr_artifacts = [a for a in snapshot.artifacts.values() if a.kind in {"adr", "decision"} or "/decisions/" in a.path]
        if len(adr_items) >= 3 and len(adr_artifacts) <= 1:
            result.findings.append(Finding(
                "INLINE_ADR_DEFECT",
                f"Source contains {len(adr_items)} ADRs but workspace collapses them into {len(adr_artifacts)} decision file(s)",
                ("@coverage",),
                Status.FAIL,
            ))
        scn_items = [it for it in manifest_items.values() if it.get("kind") in {"runtime_scenario", "flow"}]
        scn_artifacts = [a for a in snapshot.artifacts.values() if a.kind in {"runtime_scenario", "flow"} or "SCN-" in a.path]
        if len(scn_items) >= 3 and len(scn_artifacts) <= 1:
            result.findings.append(Finding(
                "SINGLETON_SCENARIO_DEFECT",
                f"Source contains {len(scn_items)} runtime scenarios but workspace collapses them into {len(scn_artifacts)} file(s)",
                ("@coverage",),
                Status.FAIL,
            ))
        fe_items = [it for it in manifest_items.values() if it.get("kind") == "frontend"]
        fe_artifacts = [a for a in snapshot.artifacts.values() if a.kind == "frontend" or "01_frontend_architecture" in a.path]
        if fe_items and not fe_artifacts:
            result.findings.append(Finding(
                "FRONTEND_COLLAPSE_DEFECT",
                "Source contains frontend design/code items but workspace has no frontend bounded context or frontend artifacts",
                ("@coverage",),
                Status.FAIL,
            ))

    # Evaluate each concern for DTG-02, DTG-03, DTG-05, DTG-06
    valid_dispositions = {"covered", "gap", "deferred", "not_applicable"}
    accounted_concerns = 0
    applicable_concerns = []
    covered_applicable = []
    critical_applicable = []
    covered_critical = []
    depth_passed_applicable = []
    deferred_concerns = []
    na_concerns = []
    gap_concerns = []

    for c in concerns:
        cid = str(c.get("id", "unknown-concern"))
        disp = c.get("disposition")
        is_crit = bool(c.get("critical", False) or c.get("criticality") == "critical")
        if disp not in valid_dispositions:
            result.findings.append(Finding(
                "INVALID_CONCERN_DISPOSITION",
                f"Concern {cid} has invalid disposition {disp!r}",
                (cid,),
                Status.INCOMPLETE,
            ))
            continue
        accounted_concerns += 1

        if disp == "not_applicable":
            na_concerns.append(cid)
            if not (c.get("rationale") and c.get("source_witness")):
                result.findings.append(Finding(
                    "EXCLUSION_WITHOUT_RATIONALE",
                    f"Concern {cid} is marked not_applicable without rationale and source_witness",
                    (cid,),
                    Status.INCOMPLETE,
                ))
            continue

        # Applicable concerns include covered, gap, and deferred
        applicable_concerns.append(cid)
        if is_crit:
            critical_applicable.append(cid)

        # Check scope constraint violations (REG-DT-11: deferred/excluded technology turned into active subsystem)
        scope_con = c.get("scope_constraint") or next(
            (manifest_items[s].get("scope_constraint") for s in c.get("source_items", []) if s in manifest_items and manifest_items[s].get("scope_constraint")),
            None,
        )
        if scope_con in {"deferred", "excluded_in_mvp"} and disp == "covered" and c.get("materialized_as_active_subsystem", True):
            result.findings.append(Finding(
                "APPLICABILITY_SCOPE_VIOLATION",
                f"Concern {cid} materializes deferred/excluded item ({scope_con}) as a required active subsystem",
                (cid,),
                Status.FAIL,
            ))

        # Check paid specialist skill slot boundary (REG-DT-27)
        if c.get("requires_paid_skill") and not c.get("skill_installed", False):
            if disp == "covered" and c.get("fabricated_specialist_content", False):
                result.findings.append(Finding(
                    "PAID_SKILL_CONTENT_FABRICATED",
                    f"Concern {cid} fabricated paid specialist content instead of recording a visible skill gap/handoff",
                    (cid,),
                    Status.FAIL,
                ))
            elif disp != "gap" and not c.get("handoff_recorded", False):
                result.findings.append(Finding(
                    "PAID_SKILL_GAP_UNRECORDED",
                    f"Concern {cid} requires an uninstalled specialist skill; record a visible skill gap or handoff",
                    (cid,),
                    Status.INCOMPLETE,
                ))

        if disp == "deferred":
            deferred_concerns.append(cid)
            if not (c.get("authority") and c.get("owner") and c.get("review_trigger")):
                result.findings.append(Finding(
                    "DEFERRED_WITHOUT_AUTHORITY",
                    f"Concern {cid} is deferred without authority, owner, and review_trigger",
                    (cid,),
                    Status.INCOMPLETE,
                ))
            continue

        if disp == "gap":
            gap_concerns.append(cid)
            result.findings.append(Finding(
                "DESIGN_GAP_OPEN",
                f"Applicable concern {cid} remains an open gap: {c.get('rationale', 'missing design or evidence')}",
                (cid,),
                Status.INCOMPLETE,
            ))
            continue

        # disp == "covered"
        owner_art_id = c.get("owner_artifact") or (planned_by_concern.get(cid, [{}])[0].get("artifact_id") if cid in planned_by_concern else None)
        if plan_art is not None and cid not in planned_by_concern and not c.get("owner_artifact"):
            result.findings.append(Finding(
                "PLAN_COVERAGE_INCOMPLETE",
                f"Concern {cid} is marked covered but has no planned node in {plan_id}",
                (cid,),
                Status.INCOMPLETE,
            ))
            continue

        art = subject_artifact(snapshot, owner_art_id) if owner_art_id else None
        if art is None:
            result.findings.append(Finding(
                "PLAN_COVERAGE_INCOMPLETE",
                f"Covered concern {cid} references missing owner artifact {owner_art_id}",
                (cid,),
                Status.INCOMPLETE,
            ))
            continue

        # DTG-06: Cross-boundary seam consistency (REG-DT-10)
        seam_ok = True
        for seam in c.get("required_seams", []):
            if not isinstance(seam, dict):
                continue
            target_id = seam.get("target_artifact") or seam.get("backend_owner")
            if not target_id or subject_artifact(snapshot, target_id) is None:
                seam_ok = False
                result.findings.append(Finding(
                    "CROSS_BOUNDARY_SEAM_UNRESOLVED",
                    f"Concern {cid} seam '{seam.get('id', 'seam')}' has no registered backend/contract owner ({target_id})",
                    (cid, art.id),
                    Status.INCOMPLETE,
                ))

        # DTG-05: Depth witness validation (ISS-01, ISS-02, ISS-05 / WO-R1.1, WO-R1.2)
        body_text = _strip_frontmatter_and_chrome(art.text)
        raw_body = _strip_frontmatter_only(art.text)
        adata = art.data if isinstance(art.data, dict) else {}
        req_dims = c.get("required_depth_dimensions", [])
        art_dims = set(adata.get("depth_dimensions", []) or art.metadata.get("depth_dimensions", []))
        has_witness_key = "depth_witnesses" in adata or "depth_witnesses" in art.metadata
        witness_map = adata.get("depth_witnesses") if isinstance(adata.get("depth_witnesses"), dict) else (
            art.metadata.get("depth_witnesses") if isinstance(art.metadata.get("depth_witnesses"), dict) else {}
        )
        numbered_sec_count = len(re.findall(r"(?m)^##\s+\d+\.", raw_body))
        require_witness_map = bool(
            has_witness_key
            or cov.get("require_depth_witnesses", False)
            or (mode in {"maximal", "portfolio", "standard"} and numbered_sec_count >= 6)
        )
        depth_ok = substance_ok_by_artifact.get(art.id, True)

        if not depth_ok or adata.get("overview_only") is True or adata.get("rtm_only") is True or len(body_text) < 60:
            depth_ok = False
            result.findings.append(Finding(
                "DEPTH_WITNESS_MISSING",
                f"Artifact {art.id} only provides frontmatter/RTM, placeholder stubs, or a shallow overview for concern {cid}",
                (art.id, cid),
                Status.INCOMPLETE,
            ))

        for dim in req_dims:
            has_dim = (not art_dims or dim in art_dims)
            if require_witness_map:
                w_quote = str(witness_map.get(dim, "")).strip() if isinstance(witness_map, dict) else ""
                if (
                    len(w_quote) < 15
                    or _PLACEHOLDER_RE.search(w_quote)
                    or (w_quote not in body_text and w_quote not in raw_body)
                ):
                    has_dim = False
            elif witness_map:
                w_quote = str(witness_map.get(dim, "")).strip()
                if not w_quote or _PLACEHOLDER_RE.search(w_quote) or w_quote not in body_text:
                    has_dim = False

            if dim in {"contract", "dto", "errors", "api_contract"} and adata.get("catalog_only") is True:
                has_dim = False
            elif dim in {"fields", "enums", "invariants", "data_entity"} and adata.get("entity_names_only") is True:
                has_dim = False
            elif dim in {"alternate_flows", "error_recovery", "recovery"} and adata.get("happy_path_only") is True:
                has_dim = False
            elif dim in {"guards", "concurrency", "state_machine"} and adata.get("states_only") is True:
                has_dim = False

            dim_pattern = DEPTH_DIMENSION_PATTERNS.get(dim)
            if dim_pattern is not None and not dim_pattern.search(body_text):
                has_dim = False

            if not has_dim:
                depth_ok = False
                result.findings.append(Finding(
                    "DEPTH_WITNESS_MISSING",
                    f"Artifact {art.id} lacks substantive body witness for required depth dimension '{dim}' on concern {cid}",
                    (art.id, cid),
                    Status.INCOMPLETE,
                ))

        if depth_ok and seam_ok:
            covered_applicable.append(cid)
            depth_passed_applicable.append(cid)
            if is_crit:
                covered_critical.append(cid)

    # DTG-07: Canonical ownership & CRUD lineage / guard preservation (REG-DT-13, REG-DT-14, REG-DT-29)
    fact_owners: dict[str, str] = {}
    for art in sorted(snapshot.artifacts.values(), key=lambda x: x.id):
        if art.metadata.get("status") == "deprecated":
            continue
        adata = art.data if isinstance(art.data, dict) else {}
        facts = list(art.metadata.get("canonical_facts") or adata.get("canonical_facts") or [])
        for fid in facts:
            if fid in fact_owners and fact_owners[fid] != art.id:
                result.findings.append(Finding(
                    "CANONICAL_OWNER_CONFLICT",
                    f"Canonical fact {fid} has multiple owners: {fact_owners[fid]} and {art.id}",
                    (fact_owners[fid], art.id),
                    Status.FAIL,
                ))
            else:
                fact_owners[fid] = art.id

    if before is not None:
        superseded_targets: dict[str, list[str]] = {}
        for art in snapshot.artifacts.values():
            for old_id in art.metadata.get("supersedes", []) or (art.data.get("supersedes", []) if isinstance(art.data, dict) else []):
                superseded_targets.setdefault(old_id, []).append(art.id)
        for old_id, old_art in before.artifacts.items():
            if old_art.metadata.get("status") == "deprecated":
                continue
            old_data = old_art.data if isinstance(old_art.data, dict) else {}
            old_dims = set(old_art.metadata.get("depth_dimensions") or old_data.get("depth_dimensions") or [])
            old_guards = set(old_data.get("guards") or [])
            if old_id not in snapshot.artifacts:
                replacements = [snapshot.artifacts[rid] for rid in superseded_targets.get(old_id, []) if rid in snapshot.artifacts]
                if not replacements:
                    result.findings.append(Finding(
                        "LINEAGE_OR_DEPTH_REGRESSION",
                        f"Removed or merged artifact {old_id} has no superseding owner preserving its lineage",
                        (old_id,),
                        Status.FAIL,
                    ))
                else:
                    new_dims = set().union(*(
                        set(r.metadata.get("depth_dimensions") or (r.data.get("depth_dimensions") if isinstance(r.data, dict) else []) or [])
                        for r in replacements
                    ))
                    if old_dims - new_dims:
                        result.findings.append(Finding(
                            "LINEAGE_OR_DEPTH_REGRESSION",
                            f"Merged/split replacement for {old_id} lost depth dimensions: {sorted(old_dims - new_dims)}",
                            (old_id, *[r.id for r in replacements]),
                            Status.FAIL,
                        ))
            else:
                cur_art = snapshot.artifacts[old_id]
                cur_data = cur_art.data if isinstance(cur_art.data, dict) else {}
                cur_dims = set(cur_art.metadata.get("depth_dimensions") or cur_data.get("depth_dimensions") or [])
                if old_dims - cur_dims:
                    result.findings.append(Finding(
                        "LINEAGE_OR_DEPTH_REGRESSION",
                        f"Artifact {old_id} lost required depth dimensions: {sorted(old_dims - cur_dims)}",
                        (old_id,),
                        Status.FAIL,
                    ))
                cur_guards = set(cur_data.get("guards") or [])
                if old_guards - cur_guards:
                    result.findings.append(Finding(
                        "GUARD_PRESERVATION_REGRESSION",
                        f"Artifact {old_id} dropped normative guards/negative constraints: {sorted(old_guards - cur_guards)}",
                        (old_id,),
                        Status.FAIL,
                    ))

    # DTG-08: Semantic economy / anti-padding (REG-DT-15, REG-DT-16, ISS-04 / WO-R1.4)
    seen_bodies: dict[str, str] = {}
    seen_shingles: list[tuple[str, str, set[str]]] = []
    seen_fact_sets: dict[tuple[str, ...], str] = {}
    for art in sorted(snapshot.artifacts.values(), key=lambda x: x.id):
        if art.metadata.get("generated") or art.metadata.get("status") == "deprecated":
            continue
        if art.kind in _LEDGER_KINDS:
            continue
        raw_chrome_stripped = _strip_frontmatter_and_chrome(art.text, strip_placeholders=False)
        norm_body = re.sub(r"\s+", " ", raw_chrome_stripped).strip().lower()
        if len(norm_body) >= 40:
            if norm_body in seen_bodies:
                other_id = seen_bodies[norm_body]
                result.findings.append(Finding(
                    "SEMANTIC_PADDING_DETECTED",
                    f"Artifacts {other_id} and {art.id} contain cloned/duplicate body prose",
                    (other_id, art.id),
                    Status.FAIL,
                ))
            else:
                seen_bodies[norm_body] = art.id
                words = re.findall(r"[a-z0-9_]+", norm_body)
                if len(words) >= 30:
                    shingles = {" ".join(words[i:i + 5]) for i in range(len(words) - 4)}
                    for other_id, other_kind, other_shingles in seen_shingles:
                        if other_kind == art.kind and other_shingles and shingles:
                            inter = len(shingles & other_shingles)
                            union = len(shingles | other_shingles)
                            if union and (inter / union) >= 0.85:
                                result.findings.append(Finding(
                                    "SEMANTIC_PADDING_DETECTED",
                                    f"Artifacts {other_id} and {art.id} exceed 85% 5-gram similarity ({inter}/{union})",
                                    (other_id, art.id),
                                    Status.FAIL,
                                ))
                                break
                    seen_shingles.append((art.id, art.kind, shingles))
        adata = art.data if isinstance(art.data, dict) else {}
        fact_sig = tuple(sorted(adata.get("FactSignature") or adata.get("duplicate_fact_signature") or []))
        if fact_sig:
            if fact_sig in seen_fact_sets and not adata.get("distinct_consumer_role"):
                other_id = seen_fact_sets[fact_sig]
                result.findings.append(Finding(
                    "SEMANTIC_PADDING_DETECTED",
                    f"Artifacts {other_id} and {art.id} duplicate the same facts without a distinct role",
                    (other_id, art.id),
                    Status.FAIL,
                ))
            else:
                seen_fact_sets[fact_sig] = art.id

    # DTG-09: Freshness & basis digest binding (REG-DT-17, REG-DT-24)
    expected_basis = compute_coverage_basis_digest(snapshot)
    if cov.get("basis_digest") and cov["basis_digest"] != expected_basis:
        result.findings.append(Finding(
            "COVERAGE_BASIS_STALE",
            "Coverage basis_digest is stale relative to current source, inventory, plan, or policy revisions",
            ("@coverage",),
            Status.STALE,
        ))
    if plan_art is not None:
        bound_revs = plan_data.get("source_revisions") or plan_art.metadata.get("source_revisions") or {}
        for src_id, expected_rev in bound_revs.items():
            actual_rev = subject_revision(snapshot, src_id)
            if actual_rev is not None and actual_rev != expected_rev:
                result.findings.append(Finding(
                    "COVERAGE_BASIS_STALE",
                    f"Target plan {plan_art.id} binds stale revision for {src_id} ({expected_rev} != {actual_rev})",
                    (plan_art.id, src_id),
                    Status.STALE,
                ))

    total_u = max(len(manifest_items), len(concerns))
    unaccounted_items = len(set(manifest_items) - covered_source_items) if concerns else len(manifest_items)
    accounted_u = max(0, total_u - unaccounted_items - (len(concerns) - accounted_concerns))
    metrics = {
        "mode": mode,
        "requested_mode": requested_mode,
        "basis_digest": expected_basis,
        "source_intake_completeness": (reconciled_sources / total_sources) if total_sources else 1.0,
        "accounting_completeness": (accounted_u / total_u) if total_u else 0.0,
        "design_coverage": (len(covered_applicable) / len(applicable_concerns)) if applicable_concerns else 0.0,
        "critical_coverage": (len(covered_critical) / len(critical_applicable)) if critical_applicable else 1.0,
        "depth_completeness": (len(depth_passed_applicable) / len(applicable_concerns)) if applicable_concerns else 0.0,
        "exclusion_defer_count": {
            "deferred": len(deferred_concerns),
            "not_applicable": len(na_concerns),
            "gap": len(gap_concerns),
        },
        "counts": {
            "total_sources": total_sources,
            "reconciled_sources": reconciled_sources,
            "universe_u": total_u,
            "applicable_concerns": len(applicable_concerns),
            "covered_concerns": len(covered_applicable),
            "critical_concerns": len(critical_applicable),
            "covered_critical_concerns": len(covered_critical),
            "stub_or_placeholder_artifacts": sum(1 for ok in substance_ok_by_artifact.values() if not ok),
        },
    }
    result.details["coverage_metrics"] = metrics
    result.details["coverage_status"] = "evaluated"


def check_snapshot(snapshot: Snapshot, before: Snapshot | None = None, history: list[dict] | None = None,
                   compare_incremental=False) -> Result:
    graph = build_graph(snapshot)
    result = Result(snapshot.digest, list(snapshot.findings) + graph.findings,
                    expected=len(snapshot.config["artifacts"]), scanned=len(snapshot.artifacts))
    delta = diff(before, snapshot)
    impacted = affected(before, snapshot, set(delta["changed"]))
    if compare_incremental and impacted != full_impact_oracle(before, snapshot, set(delta["changed"])):
        result.findings.append(Finding("IMPACT_PARITY", "Incremental selection differs from independent traversal"))
    declared_sources, check_ids = set(), set()
    relation_results = {}
    active = [o for o in snapshot.config["obligations"] if o.get("active", True)]
    source_ids = {s["id"] for s in snapshot.config.get("external_sources", [])}
    for obligation in active:
        identifier = obligation["id"]
        declared_sources.add(obligation["source"])
        relation_results[identifier] = []
        if not obligation["consumers"]:
            result.findings.append(Finding("MISSING_CONSUMER", "Active obligation has no witness", (), Status.INCOMPLETE, obligation_id=identifier))
        if not obligation.get("checks") and not obligation.get("rubric"):
            result.findings.append(Finding("OBLIGATION_UNVERIFIABLE", "Declare a predicate or semantic rubric", (), Status.INCOMPLETE, obligation_id=identifier))
        for external in obligation.get("external_sources", []):
            if external not in source_ids:
                result.findings.append(Finding("EXTERNAL_SOURCE_MISSING", external, (), Status.INCOMPLETE, obligation_id=identifier))
        for check in obligation.get("checks", []):
            if check["id"] in check_ids:
                result.findings.append(Finding("DUPLICATE_CHECK_ID", check["id"], obligation_id=identifier))
            check_ids.add(check["id"])
            allowed = {obligation["source"], *obligation["consumers"]}
            if any(check[side]["artifact"] not in allowed for side in ("source", "target")):
                result.findings.append(Finding("PREDICATE_SCOPE", check["id"], obligation_id=identifier))
                continue
            try:
                ok, subjects, evidence = relation_check(snapshot, check)
                relation_results[identifier].append({"check_id": check["id"], "status": "PASS" if ok else "FAIL"})
                if not ok:
                    result.findings.append(Finding("CONTRACT_DRIFT", check["id"], subjects, obligation_id=identifier, evidence=evidence))
            except SddError as exc:
                relation_results[identifier].append({"check_id": check["id"], "status": exc.status.value})
                result.findings.append(Finding(exc.code, str(exc), (), exc.status, obligation_id=identifier))
    if snapshot.config["policy"].get("require_requirement_obligations", True):
        for artifact in snapshot.artifacts.values():
            if not _is_upstream_requirement(artifact):
                continue
            for subject in artifact.clauses or {artifact.id: {}}:
                if subject not in declared_sources:
                    result.findings.append(Finding("REQUIREMENT_UNCOVERED", f"{subject} has no declared obligation", (subject,), Status.INCOMPLETE))
    for artifact in snapshot.artifacts.values():
        if artifact.metadata.get("data_schema"):
            from jsonschema import Draft202012Validator, SchemaError
            from referencing.exceptions import Unresolvable
            try:
                def remote_reference(value):
                    if isinstance(value, dict):
                        return any(k in {"$ref", "$dynamicRef"} and isinstance(v, str) and not v.startswith("#") or remote_reference(v) for k, v in value.items())
                    if isinstance(value, list):
                        return any(remote_reference(v) for v in value)
                    return False
                if remote_reference(artifact.metadata["data_schema"]):
                    raise SddError("ARTIFACT_SCHEMA_REMOTE_REF", "Only bundled/local-fragment schema references are supported", Status.INCOMPLETE)
                Draft202012Validator.check_schema(artifact.metadata["data_schema"])
                errors = list(Draft202012Validator(artifact.metadata["data_schema"]).iter_errors(artifact.data))
                if errors:
                    result.findings.append(Finding("ARTIFACT_SCHEMA_INVALID", errors[0].message, (artifact.id,)))
            except SchemaError as exc:
                result.findings.append(Finding("ARTIFACT_SCHEMA_UNSUPPORTED", exc.message, (artifact.id,), Status.INCOMPLETE))
            except (Unresolvable, RecursionError) as exc:
                result.findings.append(Finding("ARTIFACT_SCHEMA_UNRESOLVED", str(exc), (artifact.id,), Status.INCOMPLETE))
            except SddError as exc:
                result.findings.append(Finding(exc.code, str(exc), (artifact.id,), exc.status))
        if artifact.metadata.get("generated"):
            from .projections import projection_input_digest
            edges = [e for e in graph.edges if e[0] == artifact.id and e[2] == "derived_from"]
            bound = artifact.metadata.get("source_revisions", {})
            if not edges:
                result.findings.append(Finding("PROJECTION_SOURCE_MISSING", artifact.id, (artifact.id,), Status.INCOMPLETE))
            if artifact.metadata.get("output_digest") != artifact.revision:
                result.findings.append(Finding("PROJECTION_MODIFIED", "Generated bytes differ from the recorded output; rebuild from source", (artifact.id,), Status.STALE))
            if artifact.metadata.get("projection_input_digest") != projection_input_digest(snapshot, artifact.id):
                result.findings.append(Finding("PROJECTION_INPUT_STALE", "Graph, contract or upstream recipe inputs changed; rebuild from source", (artifact.id,), Status.STALE))
            for _, source, _ in edges:
                if bound.get(source) != subject_revision(snapshot, source):
                    result.findings.append(Finding("PROJECTION_STALE", f"{artifact.id} was not derived from current {source}", (artifact.id, source), Status.STALE))
    old_ids = (set(before.artifacts) | {c for a in before.artifacts.values() for c in a.clauses}) if before else set()
    current_ids = set(snapshot.artifacts) | {c for a in snapshot.artifacts.values() for c in a.clauses}
    tombstones = set().union(*(set(c.get("tombstones", [])) for c in history or [])) if history else set()
    for identifier in current_ids - old_ids:
        if identifier in tombstones and identifier not in result.details.get("restored_ids", []):
            result.findings.append(Finding("RETIRED_ID_REUSE", f"Use an explicit restore operation for {identifier}", (identifier,)))
    for identifier, owner in ([(a.id, a.owner) for a in snapshot.artifacts.values()] +
                              [(o["id"], o["owner"]) for o in active] +
                              [(s["id"], s["owner"]) for s in snapshot.config.get("external_sources", [])]):
        if owner.lower() in {"unassigned", "unknown", "tbd"} or ("owners" in snapshot.config and owner not in snapshot.config["owners"]):
            fallback = snapshot.config["policy"].get("fallback_owner", ",".join(snapshot.config["policy"]["reviewers"]))
            result.findings.append(Finding("OWNER_UNRESOLVED", f"Assign an active owner; escalate to {fallback or 'workspace administrator'}", (identifier,), Status.INCOMPLETE))
    evaluate_document_coverage(snapshot, before, graph, result)
    result.details.update({"diff": delta, "impacted": sorted(impacted), "relations": relation_results,
                           "historical_changes": historical_changes(before, snapshot),
                           "graph": [list(e) for e in sorted(graph.edges)], "scope": "spec-only"})
    return result
