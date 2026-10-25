"""One versioned authority for engine configuration and review wire contracts."""
from jsonschema import Draft202012Validator

from .model import SddError


def obj(properties, required=(), **extra):
    return {"type": "object", "properties": properties, "required": list(required), "additionalProperties": False, **extra}


TEXT = {"type": "string", "minLength": 1}
ID = {"type": "string", "pattern": r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$"}
TEXTS = {"type": "array", "items": TEXT, "uniqueItems": True}
REF = obj({"artifact": ID, "pointer": {"type": "string"}}, ["artifact", "pointer"])
EDGE = obj({"target": ID, "relation": {"enum": ["references", "derived_from", "satisfies", "constrains", "implements_contract"]}}, ["target", "relation"])
CLAUSE = obj({"id": ID, "anchor": TEXT}, ["id", "anchor"])
ARTIFACT_KINDS = [
    "requirement", "api", "data", "flow", "adr", "nfr", "diagram", "document", "source",
    "source_manifest", "concern_inventory", "target_plan",
    "overview", "use_case", "decision", "api_contract", "data_entity", "event_message",
    "mechanism", "runtime_scenario", "verification", "artifact", "test_strategy",
    "standard_entry", "governance_record", "audit_report", "planning", "viewpoint",
    "repository_documentation", "blocking_finding", "change_request", "frontend",
]
ARTIFACT = obj({
    "path": TEXT, "kind": {"enum": ARTIFACT_KINDS},
    "owner": TEXT, "depends_on": {"type": "array", "items": EDGE},
    "clauses": {"type": "array", "items": CLAUSE}, "generated": {"type": "boolean"},
    "source_revisions": {"type": "object", "additionalProperties": TEXT},
    "output_digest": TEXT, "projection_input_digest": TEXT, "data_schema": {"type": "object"},
    "projection": {"enum": ["dependency-mermaid", "obligation-index"]},
    "supersedes": TEXTS, "status": {"enum": ["active", "deprecated"]},
    "concerns": TEXTS, "source_items": TEXTS, "depth_dimensions": TEXTS,
    "canonical_facts": TEXTS,
    "disposition": {"enum": ["covered", "gap", "deferred", "not_applicable"]},
}, ["path", "kind", "owner"])
CHECK = obj({
    "id": ID, "operator": {"enum": ["equal", "subset", "range", "contains", "transitions"]},
    "source": REF, "target": REF, "minimum": {"type": "number"}, "maximum": {"type": "number"},
    "source_unit": {"enum": ["ms", "s", "min", "h", "B", "KiB", "MiB"]},
    "target_unit": {"enum": ["ms", "s", "min", "h", "B", "KiB", "MiB"]},
}, ["id", "operator", "source", "target"])
OBLIGATION = obj({
    "id": ID, "source": ID, "consumers": TEXTS, "owner": TEXT,
    "criticality": {"enum": ["critical", "major", "minor"]},
    "checks": {"type": "array", "items": CHECK}, "rubric": TEXT,
    "external_sources": TEXTS, "active": {"type": "boolean"},
    "direct_scope_only": {"type": "boolean"},
}, ["id", "source", "consumers", "owner", "criticality"])
SOURCE = obj({
    "id": ID, "url": TEXT, "version": TEXT, "owner": TEXT,
    "max_age_seconds": {"type": "integer", "minimum": 1}, "expected_digest": TEXT,
    "json_pointer": {"type": "string"}, "max_bytes": {"type": "integer", "minimum": 1, "maximum": 10485760},
}, ["id", "url", "version", "owner", "max_age_seconds"])
POLICY = obj({
    "mode": {"enum": ["shadow", "advisory", "enforce"]}, "reviewers": TEXTS,
    "decision_authority": {"enum": ["local", "external"]},
    "require_human_acceptance": {"type": "boolean"}, "max_rejected_rounds": {"type": "integer", "minimum": 1},
    "allow_waivers": {"type": "boolean"}, "require_requirement_obligations": {"type": "boolean"},
    "require_system_review": {"type": "boolean"},
    "shard_system_review": {"type": "boolean"},
    "max_file_bytes": {"type": "integer", "minimum": 1},
    "max_packet_bytes": {"type": "integer", "minimum": 1000},
    "max_input_tokens": {"type": "integer", "minimum": 256},
    "max_workspace_documents": {"type": "integer", "minimum": 1, "maximum": 2000},
    "max_review_age_seconds": {"type": "integer", "minimum": 1},
    "fallback_owner": TEXT,
    "runtime": obj({
        "max_tasks": {"type": "integer", "minimum": 1, "maximum": 1000},
        "max_concurrency": {"type": "integer", "minimum": 1, "maximum": 16},
        "max_task_attempts": {"type": "integer", "minimum": 1, "maximum": 3},
        "max_total_attempts": {"type": "integer", "minimum": 1, "maximum": 3000},
        "deadline_seconds": {"type": "integer", "minimum": 1, "maximum": 604800},
        "lease_seconds": {"type": "integer", "minimum": 1, "maximum": 86400},
        "notify_seconds": {"type": "integer", "minimum": 0, "maximum": 86400},
        "first_run_gate": {"enum": ["auto", "notify", "approve"]},
    }),
}, ["mode", "reviewers"])
PROVIDER = obj({
    "type": {"enum": ["typesafe-jev", "openai-compatible", "cascade"]}, "endpoint": TEXT, "model": TEXT, "api_key_env": TEXT,
    "timeout_seconds": {"type": "number", "exclusiveMinimum": 0},
    "max_attempts": {"type": "integer", "minimum": 1, "maximum": 3},
    "max_output_tokens": {"type": "integer", "minimum": 1},
    "max_input_tokens": {"type": "integer", "minimum": 256},
    "max_cost_usd": {"type": "number", "minimum": 0},
    "input_per_million": {"type": "number", "minimum": 0}, "output_per_million": {"type": "number", "minimum": 0},
    "qualification_digest": TEXT, "qualification_scope": TEXT,
    "screening": obj({"type": {"const": "typesafe-jev"}, "endpoint": TEXT, "model": TEXT, "api_key_env": TEXT,
        "timeout_seconds": {"type": "number", "exclusiveMinimum": 0}, "max_output_tokens": {"type": "integer", "minimum": 1},
        "input_per_million": {"type": "number", "minimum": 0}, "output_per_million": {"type": "number", "minimum": 0}},
        ["type", "endpoint", "model", "api_key_env", "input_per_million", "output_per_million"]),
}, ["type", "endpoint", "model", "api_key_env", "max_cost_usd", "input_per_million", "output_per_million"])
DOCUMENT_COVERAGE = obj({
    "schema_version": {"const": 1},
    "mode": {"enum": ["portfolio", "maximal", "standard", "minimal", "seed"]},
    "requested_mode": {"enum": ["portfolio", "maximal", "standard", "minimal", "seed"]},
    "policy_version": TEXT,
    "source_manifest_artifact": ID,
    "concern_inventory_artifact": ID,
    "target_plan_artifact": ID,
    "basis_digest": TEXT,
    "required_families": TEXTS,
    "enforce_maximal_structure": {"type": "boolean"},
    "enforce_line_budget": {"type": "boolean"},
    "require_depth_witnesses": {"type": "boolean"},
}, ["schema_version", "mode", "policy_version"])
WORKSPACE = obj({
    "version": {"const": 1}, "workspace_id": ID, "workspace_profile_id": TEXT,
    "selected_profile": {"enum": ["seed", "minimal", "standard", "maximal", "portfolio"]},
    "document_coverage": DOCUMENT_COVERAGE,
    "artifacts": {"type": "object", "propertyNames": ID, "additionalProperties": ARTIFACT},
    "obligations": {"type": "array", "items": OBLIGATION},
    "policy": POLICY, "provider": PROVIDER,
    "language": obj({"profile_id": {"const": "aaf-ste80-v1"},
        "glossary": {"type": "object", "additionalProperties": obj({
            "definition": TEXT, "part_of_speech": {"enum": ["noun", "verb", "adjective", "adverb", "pronoun", "preposition", "conjunction", "determiner", "interjection"]},
            "canonical_spelling": TEXT, "source": TEXT, "approved_exception": TEXT}, ["part_of_speech", "source"])},
        "max_repair_rounds": {"type": "integer", "minimum": 1, "maximum": 2}}, ["profile_id", "glossary"]),
    "external_sources": {"type": "array", "items": SOURCE},
    "attachments": TEXTS,
    "control_directories": {"type": "array", "uniqueItems": True, "items": {"enum": [".architect", ".architect-runtime", ".architect-build"]}},
    "owners": TEXTS,
    "skills": {"type": "object", "additionalProperties": obj({"capabilities": TEXTS, "write_scope": TEXTS, "source": {"enum": ["package", "host"]}}, ["capabilities", "write_scope"])},
}, ["version", "workspace_id", "artifacts", "obligations", "policy"])
EVIDENCE = obj({"artifact_id": ID, "revision": TEXT, "start": {"type": "integer", "minimum": 0},
                "end": {"type": "integer", "minimum": 1}, "quote": TEXT}, ["artifact_id", "revision", "start", "end", "quote"])
COVERAGE = obj({"obligation_id": TEXT, "status": {"enum": ["pass", "fail", "unknown", "intentionally_changed"]},
                "rationale": TEXT, "evidence": {"type": "array", "items": EVIDENCE}}, ["obligation_id", "status", "rationale", "evidence"])
REVIEW_FINDING = obj({"obligation_id": TEXT, "kind": {"enum": ["contradiction", "missing", "regression", "risk"]},
    "severity": {"enum": ["blocker", "major", "minor"]}, "explanation": TEXT,
    "evidence": {"type": "array", "items": EVIDENCE}, "inspected_ids": TEXTS},
    ["obligation_id", "kind", "severity", "explanation", "evidence", "inspected_ids"])
REVIEW = obj({"packet_digest": TEXT, "completion": {"enum": ["complete", "incomplete"]},
    "coverage": {"type": "array", "items": COVERAGE}, "findings": {"type": "array", "items": REVIEW_FINDING}},
    ["packet_digest", "completion", "coverage", "findings"])


def validate(value, schema, code="SCHEMA_INVALID"):
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda x: str(list(x.absolute_path)))
    if errors:
        error = errors[0]
        raise SddError(code, f"{'/'.join(map(str, error.absolute_path)) or '/'}: {error.message}")
