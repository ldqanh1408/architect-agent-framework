"""Which page class each required output of a skill contract declares (specification).

Plan section 6a states the routing rule in two tiers: **page class chooses the shape**
(which folder family an artifact belongs to), **`scope` chooses the tier**
(system-wide or per module). section 6a.1 then measured that only the second tier could
actually run — all 183 task contracts declared `scope`, and none of them declared
a page class. A rule whose first tier reads a field that does not exist is not a
rule; this module is that field.

Three things are deliberate here.

**The unit is the required output, not the skill.** Forty-three task skills emit
more than one artifact, and the extra one is often a different shape entirely:
`domain-modeling` emits an aggregate model (`data_entity`) *and* a context map
(`diagram`). A per-skill class would have had to pick one and be wrong about the
other, which is exactly the collapse section 19.2 caught in the multiplicity work.

**A family default plus named exceptions, not 218 rows.** The family a task
belongs to predicts its artifact's shape 153 times out of 218; the remaining 65
are listed one by one because each is a judgement someone can disagree with in
writing. A flat 218-row table would hide which of those rows carry an argument.
The split is measurable and the test asserts it: default plus overrides must
cover exactly the 218 outputs the registry declares, with no key left over.

**The orchestrator is excluded on purpose.** Its `required_outputs` are route
status and a candidate list — decisions handed back to the caller, not pages
written to a tree. Giving them a page class would claim a page exists where none
does. It keeps the plain list of strings, and that asymmetry is the honest one.

Every value here must name a class the vocabulary published by
:func:`architect_framework.contracts.page_classes` defines. This module does not
read that vocabulary — it stays a leaf with no contract access, the same shape as
`output_modules` — so the cross-check lives in `tests/test_artifact_page_class.py`
and in the H-2 closure ratchet, which reads contracts as a third surface next to
the skeleton and the 110 manifests.
"""

from __future__ import annotations

from pathlib import PurePosixPath

# --------------------------------------------------------------------------- #
# Domain skills — 110 skills x 3 outputs = 330 artifacts, the symmetric half of
# H-4 that section 6c had to restate because the plan kept counting only the 218.
# --------------------------------------------------------------------------- #

#: Matched on the tail of the output path. The overview file carries the skill id
#: in its name (`rest-api-design-overview.md`), so it is matched by suffix rather
#: than by an exact key.
DOMAIN_OUTPUT_PAGE_CLASS: tuple[tuple[str, str], ...] = (
    ("README.md", "repository_documentation"),
    ("-overview.md", "overview"),
    ("fitness-self-check.md", "verification"),
)


def domain_output_page_class(path: str) -> str:
    """The class of one of a domain skill's three required outputs.

    Raises rather than defaulting: a fourth output added to `_domain_package`
    without a decision about its shape should fail at generation, not ship as
    whatever the last branch happened to be.
    """
    tail = PurePosixPath(path).name
    for marker, page_class in DOMAIN_OUTPUT_PAGE_CLASS:
        if tail == marker or tail.endswith(marker):
            return page_class
    raise KeyError(
        f"domain output {path!r} has no declared page class; "
        "add one to DOMAIN_OUTPUT_PAGE_CLASS rather than letting it ship unclassified"
    )


# --------------------------------------------------------------------------- #
# Task skills — 183 skills, 218 artifacts.
# --------------------------------------------------------------------------- #

#: The shape a family's work has when nothing in the artifact's own name argues
#: otherwise. Chosen from what the family's destination slots already declare in
#: the skeleton, so an artifact and the slot it lands in agree by construction
#: wherever the default holds.
TASK_FAMILY_PAGE_CLASS: dict[str, str] = {
    # Destinations are `00-context/assumptions.md`, `01-requirements/**` and
    # `04-risks/risk-register.md` — all three declare `requirement` (section 4.2).
    "01_discovery": "requirement",
    # Lands in `02-domains/00-overview/` and the functional view.
    "02_business_analysis": "overview",
    # `{module}/02-domain-model/` and `_shared-contracts/01-data/{entity}/`.
    "03_domain_modeling": "data_entity",
    # A style assessment is the evidence table an ADR later cites, not the ADR.
    "04_arch_style_selection": "decision",
    "05_tech_selection": "decision",
    "06_tradeoff_analysis": "decision",
    # Five views in `00-system-views/`, detail copies in `{module}/04-diagrams/`.
    "07_system_modeling": "diagram",
    "08_api_design": "api_contract",
    "09_data_design": "data_entity",
    # section 7.3 settled this: authn/authz pages describe how the system *decides*, so
    # they are mechanisms, not contracts. The four security slots in
    # `03-cross-cutting/02-security/` already declare `mechanism`.
    "10_security_design": "mechanism",
    "11_performance_design": "mechanism",
    "12_reliability_design": "mechanism",
    # Infra deliverables are manifests other things consume — Terraform modules,
    # Helm charts, Kubernetes YAML. `artifact` asks exactly that: what is this,
    # and who breaks when it changes.
    "13_infra_design": "artifact",
    "14_observability_design": "mechanism",
    "15_deployment_design": "mechanism",
    "16_testing_strategy": "test_strategy",
    "17_documentation": "repository_documentation",
    "18_governance": "audit_report",
    "19_cost_operations": "decision",
    "20_ai_tasks": "mechanism",
    # specification. `planning` was one of the four `04-delivery/**` classes specification gave a
    # page class to for the first time, and until now no producer claimed it.
    "21_delivery_planning": "planning",
}

#: Keyed by the artifact's file name, which is unique across all 218 (asserted in
#: `tests/test_artifact_page_class.py`, because keying a routing table on a name
#: that could collide is how one artifact silently takes another's class).
#:
#: Each entry is here because the family default is wrong about this particular
#: page, and the comment says which question the page actually answers.
TASK_OUTPUT_PAGE_CLASS: dict[str, str] = {
    # -- 18_governance: the phase-6 producer (2026-09-24). A change request is
    # not an audit report; its class is the one whose impact graph is derived.
    "CR-{NNN}-{slug}.md": "change_request",
    # -- 01_discovery: six pages that are not requirements ------------------- #
    "dependency-map.md": "diagram",  # a picture of edges, for an audience
    "operational-context-profile.md": "overview",  # what the system runs inside
    "risk-mitigation-plan.md": "planning",  # what is done first, in what order
    "stakeholder-concerns-map.md": "viewpoint",  # section 6a.3 folds it into 00-viewpoints/
    "stakeholder-influence-matrix.md": "viewpoint",  # same fold
    "system-scope-specification.md": "overview",  # owns what, refuses what
    # -- 02_business_analysis ------------------------------------------------ #
    "bpmn-2-0-process-diagram.md": "diagram",
    "stakeholder-matrix.md": "viewpoint",  # section 6a.3, third of the three that fold
    # -- 03_domain_modeling: seven that are not entities --------------------- #
    "compensation-flow-diagram.md": "diagram",
    "context-map-diagram.md": "diagram",
    "domain-event-schema.md": "event_message",
    "domain-state-machine-spec.md": "mechanism",  # transitions and guards
    "repository-interface-spec.md": "api_contract",  # a callable surface
    "saga-orchestration-spec.md": "mechanism",
    "saga-step-sequence-diagram.md": "diagram",
    # -- 04_arch_style_selection --------------------------------------------- #
    "inter-service-communication-plan.md": "mechanism",  # how calls are made
    "service-boundary-map.md": "overview",  # what each side owns and refuses
    # -- 06_tradeoff_analysis ------------------------------------------------ #
    "iso-25010-maintainability-spec.md": "requirement",  # a threshold to meet
    "risk-mitigation-report.md": "planning",
    "scalability-limits-report.md": "requirement",  # the number the system owes
    # -- 07_system_modeling: three that are not pictures --------------------- #
    "entity-attribute-spec.md": "data_entity",
    "index-candidate-list.md": "data_entity",
    "system-boundary-specification.md": "overview",
    # -- 08_api_design ------------------------------------------------------- #
    "api-security-middleware-spec.md": "mechanism",
    "asyncapi-3-0-specification.md": "event_message",  # section 4.3's two messages
    "event-message-schema-registry.md": "event_message",
    # -- 09_data_design: seven that describe behaviour, not state ------------ #
    "db-backup-plan.md": "mechanism",
    "db-replication-spec.md": "mechanism",
    "data-encryption-spec.md": "mechanism",
    "data-retention-policy.md": "standard_entry",  # scope, lifecycle, exceptions
    "normalization-rationale-spec.md": "decision",  # why this shape won
    "schema-migration-plan.md": "planning",
    "sharding-architecture-spec.md": "mechanism",
    # -- 10_security_design -------------------------------------------------- #
    "dfd-diagram.md": "diagram",
    # -- 12_reliability_design ----------------------------------------------- #
    "chaos-experiment-plan.md": "test_strategy",
    "outbox-table-schema.md": "data_entity",
    # -- 13_infra_design: three that are behaviour, not deliverable ---------- #
    "cluster-autoscaler-spec.md": "mechanism",
    "ingress-controller-spec.md": "mechanism",
    "service-mesh-configuration.md": "mechanism",
    # -- 14_observability_design: six that are not mechanisms ---------------- #
    "customer-sla-document.md": "requirement",
    # specification corrected this from `artifact`: an error budget is a number the system
    # owes, and the page states the threshold and what happens when it is spent.
    # `artifact` matched no destination the observability family has, which is the
    # routing rule reporting a class that was wrong rather than a tree that was.
    "error-budget-report-template.md": "requirement",
    "grafana-dashboard-json-spec.md": "artifact",
    "health-check-spec.md": "verification",  # what it checks, by which command
    "otel-instrumentation-guide.md": "repository_documentation",
    "slo-sla-contract-spec.md": "requirement",
    # -- 15_deployment_design ------------------------------------------------ #
    "argo-rollouts-yaml.md": "artifact",
    # -- 16_testing_strategy: four that are not strategies ------------------- #
    "bottleneck-analysis-report.md": "audit_report",
    "can-i-deploy-pipeline-integration.md": "verification",
    "pact-broker-setup-guide.md": "repository_documentation",
    "k6-test-script.md": "artifact",
    # -- 17_documentation ---------------------------------------------------- #
    "adr-index-log.md": "overview",  # an index is a view over ADRs (section 7.4)
    "adr-markdown-document.md": "adr",
    "full-architecture-spec-document.md": "overview",
    "technical-rfc-document.md": "adr",  # a proposal that names what it trades
    # -- 18_governance ------------------------------------------------------- #
    "enterprise-architecture-policy.md": "standard_entry",
    "quality-gate-rule-config.md": "standard_entry",
    "standards-enforcement-manifest.md": "standard_entry",
    # -- 19_cost_operations: five of seven are not decision tables ----------- #
    "engineering-resource-plan.md": "planning",
    "finops-optimization-action-plan.md": "planning",
    "infrastructure-capacity-model.md": "artifact",
    "license-audit-report.md": "audit_report",
    "monthly-cloud-cost-estimate.md": "artifact",
    # -- 20_ai_tasks --------------------------------------------------------- #
    "ai-eval-metric-suite-spec.md": "verification",  # metric, command, threshold
    # section 10.1 named this one: it is the tenth AI artifact, and it is system-level
    # rather than a module concern, so it lands in `00-system-views/06-runtime/`
    # — whose slot declares `runtime_scenario`.
    "multi-agent-workflow-blueprint.md": "runtime_scenario",
    "system-prompt-template-spec.md": "artifact",
}


def task_output_page_class(family_id: str, path: str) -> str:
    """The class of one required output of one task contract.

    `path` may be a bare file name or a full output path; only the tail is used,
    because P6 fixes the file name and lets the prefix move (specification moves every
    one of these out of `tasks/{run-id}/` and the class must survive that).
    """
    tail = PurePosixPath(path).name
    override = TASK_OUTPUT_PAGE_CLASS.get(tail)
    if override is not None:
        return override
    try:
        return TASK_FAMILY_PAGE_CLASS[family_id]
    except KeyError:
        raise KeyError(
            f"task family {family_id!r} declares no default page class; "
            "add it to TASK_FAMILY_PAGE_CLASS"
        ) from None


TASK_OUTPUT_PATHS: dict[str, dict[str, str]] = {
    "3-year-tco-analysis-report.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/04-risks/3-year-tco-analysis-report.md"
    },
    "CR-{NNN}-{slug}.md": {
        "page_class": "change_request",
        "path": "architecture/01-global-strategy/05-governance/change-requests/CR-{NNN}-{slug}.md"
    },
    "TKT-{NNN}-{slug}.md": {
        "page_class": "planning",
        "path": "architecture/04-delivery/00-planning/tickets/TKT-{NNN}-{slug}.md"
    },
    "abac-policy-specification.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/02-security/abac-policy-specification.md"
    },
    "actor-model-assessment.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/actor-model-assessment.md"
    },
    "adr-index-log.md": {
        "page_class": "overview",
        "path": "architecture/01-global-strategy/05-governance/decisions/adr-index-log.md"
    },
    "adr-markdown-document.md": {
        "page_class": "adr",
        "path": "architecture/01-global-strategy/05-governance/decisions/adr-markdown-document.md"
    },
    "agent-memory-architecture-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/agent-memory-architecture-spec.md"
    },
    "aggregate-boundary-spec.md": {
        "page_class": "data_entity",
        "path": "architecture/02-domains/_shared-contracts/aggregate-boundary-spec.md"
    },
    "ai-eval-metric-suite-spec.md": {
        "page_class": "verification",
        "path": "architecture/03-cross-cutting/01-mechanisms/ai-eval-metric-suite-spec.md"
    },
    "alerting-policy-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/alerting-policy-spec.md"
    },
    "api-endpoint-catalog.md": {
        "page_class": "api_contract",
        "path": "architecture/02-domains/_shared-contracts/02-apis/api-endpoint-catalog.md"
    },
    "api-filtering-spec.md": {
        "page_class": "api_contract",
        "path": "architecture/02-domains/_shared-contracts/02-apis/api-filtering-spec.md"
    },
    "api-security-middleware-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/02-security/api-security-middleware-spec.md"
    },
    "api-versioning-policy.md": {
        "page_class": "api_contract",
        "path": "architecture/02-domains/_shared-contracts/02-apis/api-versioning-policy.md"
    },
    "architectural-risk-log.md": {
        "page_class": "requirement",
        "path": "architecture/01-global-strategy/04-risks/architectural-risk-log.md"
    },
    "architectural-roi-financial-report.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/04-risks/architectural-roi-financial-report.md"
    },
    "architecture-comparison-matrix.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/architecture-comparison-matrix.md"
    },
    "architecture-review-report.md": {
        "page_class": "audit_report",
        "path": "architecture/01-global-strategy/05-governance/reviews/architecture-review-report.md"
    },
    "architecture-smell-report.md": {
        "page_class": "audit_report",
        "path": "architecture/01-global-strategy/05-governance/reviews/architecture-smell-report.md"
    },
    "argo-rollouts-yaml.md": {
        "page_class": "artifact",
        "path": "architecture/04-delivery/02-release/argo-rollouts-yaml.md"
    },
    "argocd-spec.md": {
        "page_class": "artifact",
        "path": "architecture/03-cross-cutting/03-infrastructure/argocd-spec.md"
    },
    "assumption-log.md": {
        "page_class": "requirement",
        "path": "architecture/01-global-strategy/00-context/assumption-log.md"
    },
    "async-worker-architecture-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/async-worker-architecture-spec.md"
    },
    "asyncapi-3-0-specification.md": {
        "page_class": "event_message",
        "path": "architecture/02-domains/_shared-contracts/03-messages/asyncapi-3-0-specification.md"
    },
    "audit-logging-specification.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/02-security/audit-logging-specification.md"
    },
    "automated-rollback-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/04-delivery/02-release/automated-rollback-spec.md"
    },
    "autoscaling-configuration-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/autoscaling-configuration-spec.md"
    },
    "batch-processing-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/batch-processing-spec.md"
    },
    "blue-green-architecture-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/04-delivery/02-release/blue-green-architecture-spec.md"
    },
    "bottleneck-analysis-report.md": {
        "page_class": "audit_report",
        "path": "architecture/04-delivery/01-quality/bottleneck-analysis-report.md"
    },
    "bpmn-2-0-process-diagram.md": {
        "page_class": "diagram",
        "path": "architecture/00-system-views/02-functional/processes/{process}/bpmn-2-0-process-diagram.md"
    },
    "bpmn-2-0-spec.md": {
        "page_class": "diagram",
        "path": "architecture/00-system-views/02-functional/processes/{process}/bpmn-2-0-spec.md"
    },
    "bulkhead-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/bulkhead-spec.md"
    },
    "burn-rate-alert-rules.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/burn-rate-alert-rules.md"
    },
    "business-capability-map.md": {
        "page_class": "overview",
        "path": "architecture/02-domains/00-overview/business-capability-map.md"
    },
    "business-goal-alignment-matrix.md": {
        "page_class": "requirement",
        "path": "architecture/01-global-strategy/00-context/business-goal-alignment-matrix.md"
    },
    "c4-code-diagram-mermaid-plantuml.md": {
        "page_class": "diagram",
        "path": "architecture/00-system-views/generated/c4-code-diagram-mermaid-plantuml.md"
    },
    "c4-component-diagram-mermaid-plantuml.md": {
        "page_class": "diagram",
        "path": "architecture/00-system-views/03-structure/components/{container}/c4-component-diagram-mermaid-plantuml.md"
    },
    "c4-container-diagram-mermaid-plantuml.md": {
        "page_class": "diagram",
        "path": "architecture/00-system-views/03-structure/c4-container-diagram-mermaid-plantuml.md"
    },
    "c4-context-diagram-mermaid-plantuml.md": {
        "page_class": "diagram",
        "path": "architecture/00-system-views/01-context/c4-context-diagram-mermaid-plantuml.md"
    },
    "cache-key-design-document.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/cache-key-design-document.md"
    },
    "cache-selection-matrix.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/cache-selection-matrix.md"
    },
    "caching-strategy-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/caching-strategy-spec.md"
    },
    "can-i-deploy-pipeline-integration.md": {
        "page_class": "verification",
        "path": "architecture/04-delivery/01-quality/can-i-deploy-pipeline-integration.md"
    },
    "canary-deployment-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/04-delivery/02-release/canary-deployment-spec.md"
    },
    "cell-based-architecture-spec.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/cell-based-architecture-spec.md"
    },
    "chaos-experiment-plan.md": {
        "page_class": "test_strategy",
        "path": "architecture/04-delivery/01-quality/chaos-experiment-plan.md"
    },
    "chaos-game-day-plan.md": {
        "page_class": "test_strategy",
        "path": "architecture/04-delivery/01-quality/chaos-game-day-plan.md"
    },
    "circuit-breaker-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/05-exceptions/circuit-breaker-spec.md"
    },
    "clean-architecture-assessment.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/clean-architecture-assessment.md"
    },
    "cloud-selection-matrix.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/cloud-selection-matrix.md"
    },
    "cluster-autoscaler-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/03-infrastructure/cluster-autoscaler-spec.md"
    },
    "compensation-flow-diagram.md": {
        "page_class": "diagram",
        "path": "architecture/00-system-views/06-runtime/sequences/{saga}/compensation-flow-diagram.md"
    },
    "complexity-rating-spec.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/complexity-rating-spec.md"
    },
    "compression-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/compression-spec.md"
    },
    "concurrency-control-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/concurrency-control-spec.md"
    },
    "constraint-matrix.md": {
        "page_class": "requirement",
        "path": "architecture/01-global-strategy/01-requirements/constraint-matrix.md"
    },
    "constraint-specification.md": {
        "page_class": "data_entity",
        "path": "architecture/02-domains/_shared-contracts/01-data/constraint-specification.md"
    },
    "container-runtime-spec.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/container-runtime-spec.md"
    },
    "context-map-diagram.md": {
        "page_class": "diagram",
        "path": "architecture/02-domains/00-overview/context-map-diagram.md"
    },
    "context-optimization-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/context-optimization-spec.md"
    },
    "contract-test-plan.md": {
        "page_class": "test_strategy",
        "path": "architecture/04-delivery/01-quality/contract-test-plan.md"
    },
    "cqrs-architectural-assessment.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/cqrs-architectural-assessment.md"
    },
    "customer-sla-document.md": {
        "page_class": "requirement",
        "path": "architecture/01-global-strategy/01-requirements/customer-sla-document.md"
    },
    "data-encryption-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/02-security/data-encryption-spec.md"
    },
    "data-mesh-assessment.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/data-mesh-assessment.md"
    },
    "data-retention-policy.md": {
        "page_class": "standard_entry",
        "path": "architecture/01-global-strategy/03-standards/data-retention-policy.md"
    },
    "database-indexing-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/database-indexing-spec.md"
    },
    "database-selection-report.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/database-selection-report.md"
    },
    "db-backup-plan.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/db-backup-plan.md"
    },
    "db-replication-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/db-replication-spec.md"
    },
    "ddd-aggregate-model.md": {
        "page_class": "data_entity",
        "path": "architecture/02-domains/_shared-contracts/ddd-aggregate-model.md"
    },
    "dependency-map.md": {
        "page_class": "diagram",
        "path": "architecture/00-system-views/01-context/dependency-map.md"
    },
    "devsecops-test-strategy.md": {
        "page_class": "test_strategy",
        "path": "architecture/04-delivery/01-quality/devsecops-test-strategy.md"
    },
    "dfd-diagram.md": {
        "page_class": "diagram",
        "path": "architecture/00-system-views/05-information/dfd-diagram.md"
    },
    "distributed-tracing-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/distributed-tracing-spec.md"
    },
    "dlq-management-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/05-exceptions/dlq-management-spec.md"
    },
    "domain-entity-specification.md": {
        "page_class": "data_entity",
        "path": "architecture/02-domains/_shared-contracts/domain-entity-specification.md"
    },
    "domain-event-schema.md": {
        "page_class": "event_message",
        "path": "architecture/02-domains/_shared-contracts/domain-event-schema.md"
    },
    "domain-state-machine-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/02-domains/_shared-contracts/domain-state-machine-spec.md"
    },
    "dr-playbook-document.md": {
        "page_class": "repository_documentation",
        "path": "architecture/04-delivery/03-ops/dr-playbook-document.md"
    },
    "e2e-test-plan.md": {
        "page_class": "test_strategy",
        "path": "architecture/04-delivery/01-quality/e2e-test-plan.md"
    },
    "eda-assessment-report.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/eda-assessment-report.md"
    },
    "engineering-resource-plan.md": {
        "page_class": "planning",
        "path": "architecture/01-global-strategy/04-risks/engineering-resource-plan.md"
    },
    "enterprise-architecture-policy.md": {
        "page_class": "standard_entry",
        "path": "architecture/01-global-strategy/05-governance/reviews/enterprise-architecture-policy.md"
    },
    "entity-attribute-spec.md": {
        "page_class": "data_entity",
        "path": "architecture/00-system-views/05-information/entity-attribute-spec.md"
    },
    "erd-diagram-mermaid-plantuml.md": {
        "page_class": "diagram",
        "path": "architecture/00-system-views/05-information/erd-diagram-mermaid-plantuml.md"
    },
    "error-budget-report-template.md": {
        "page_class": "requirement",
        "path": "architecture/01-global-strategy/01-requirements/error-budget-report-template.md"
    },
    "error-code-registry.md": {
        "page_class": "api_contract",
        "path": "architecture/02-domains/_shared-contracts/02-apis/error-code-registry.md"
    },
    "event-message-schema-registry.md": {
        "page_class": "event_message",
        "path": "architecture/02-domains/_shared-contracts/03-messages/event-message-schema-registry.md"
    },
    "eviction-policy-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/eviction-policy-spec.md"
    },
    "fallback-strategy-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/05-exceptions/fallback-strategy-spec.md"
    },
    "feature-flag-architecture-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/04-delivery/02-release/feature-flag-architecture-spec.md"
    },
    "finops-optimization-action-plan.md": {
        "page_class": "planning",
        "path": "architecture/01-global-strategy/04-risks/finops-optimization-action-plan.md"
    },
    "framework-evaluation-matrix.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/framework-evaluation-matrix.md"
    },
    "full-architecture-spec-document.md": {
        "page_class": "overview",
        "path": "architecture/01-global-strategy/full-architecture-spec-document.md"
    },
    "grafana-dashboard-json-spec.md": {
        "page_class": "artifact",
        "path": "architecture/03-cross-cutting/03-infrastructure/grafana-dashboard-json-spec.md"
    },
    "graphql-schema-definition.md": {
        "page_class": "api_contract",
        "path": "architecture/02-domains/_shared-contracts/02-apis/{api}/graphql-schema-definition.md"
    },
    "hallucination-mitigation-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/hallucination-mitigation-spec.md"
    },
    "health-check-spec.md": {
        "page_class": "verification",
        "path": "architecture/03-cross-cutting/04-fitness-functions/health-check-spec.md"
    },
    "helm-chart-package-spec.md": {
        "page_class": "artifact",
        "path": "architecture/03-cross-cutting/03-infrastructure/helm-chart-package-spec.md"
    },
    "hexagonal-style-assessment.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/hexagonal-style-assessment.md"
    },
    "idempotency-spec.md": {
        "page_class": "api_contract",
        "path": "architecture/02-domains/_shared-contracts/02-apis/idempotency-spec.md"
    },
    "idp-selection-matrix.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/idp-selection-matrix.md"
    },
    "index-candidate-list.md": {
        "page_class": "data_entity",
        "path": "architecture/00-system-views/05-information/index-candidate-list.md"
    },
    "index-design-document.md": {
        "page_class": "data_entity",
        "path": "architecture/02-domains/_shared-contracts/01-data/index-design-document.md"
    },
    "infrastructure-capacity-model.md": {
        "page_class": "artifact",
        "path": "architecture/01-global-strategy/04-risks/infrastructure-capacity-model.md"
    },
    "ingress-controller-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/03-infrastructure/ingress-controller-spec.md"
    },
    "integration-test-spec.md": {
        "page_class": "test_strategy",
        "path": "architecture/04-delivery/01-quality/integration-test-spec.md"
    },
    "inter-service-communication-plan.md": {
        "page_class": "mechanism",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/inter-service-communication-plan.md"
    },
    "invariant-rules-documentation.md": {
        "page_class": "data_entity",
        "path": "architecture/02-domains/_shared-contracts/invariant-rules-documentation.md"
    },
    "iso-25010-maintainability-spec.md": {
        "page_class": "requirement",
        "path": "architecture/01-global-strategy/04-risks/iso-25010-maintainability-spec.md"
    },
    "iso-25010-nfr-specification.md": {
        "page_class": "requirement",
        "path": "architecture/01-global-strategy/01-requirements/iso-25010-nfr-specification.md"
    },
    "jwt-security-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/02-security/jwt-security-spec.md"
    },
    "k6-test-script.md": {
        "page_class": "artifact",
        "path": "architecture/04-delivery/01-quality/k6-test-script.md"
    },
    "kubernetes-yaml-specs.md": {
        "page_class": "artifact",
        "path": "architecture/03-cross-cutting/03-infrastructure/kubernetes-yaml-specs.md"
    },
    "language-evaluation-matrix.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/language-evaluation-matrix.md"
    },
    "layered-style-assessment.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/layered-style-assessment.md"
    },
    "license-audit-report.md": {
        "page_class": "audit_report",
        "path": "architecture/01-global-strategy/04-risks/license-audit-report.md"
    },
    "llm-benchmark-selection-matrix.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/llm-benchmark-selection-matrix.md"
    },
    "llm-guardrail-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/llm-guardrail-spec.md"
    },
    "load-balancing-architecture-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/load-balancing-architecture-spec.md"
    },
    "load-test-scenario-spec.md": {
        "page_class": "test_strategy",
        "path": "architecture/04-delivery/01-quality/load-test-scenario-spec.md"
    },
    "microservices-tradeoff-assessment.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/microservices-tradeoff-assessment.md"
    },
    "migration-guide-document.md": {
        "page_class": "repository_documentation",
        "path": "architecture/04-delivery/03-ops/migration-guide-document.md"
    },
    "model-routing-architecture-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/model-routing-architecture-spec.md"
    },
    "modular-monolith-assessment.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/modular-monolith-assessment.md"
    },
    "monthly-cloud-cost-estimate.md": {
        "page_class": "artifact",
        "path": "architecture/01-global-strategy/04-risks/monthly-cloud-cost-estimate.md"
    },
    "mtls-security-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/02-security/mtls-security-spec.md"
    },
    "multi-agent-workflow-blueprint.md": {
        "page_class": "runtime_scenario",
        "path": "architecture/00-system-views/06-runtime/multi-agent-workflow-blueprint.md"
    },
    "mutation-testing-spec.md": {
        "page_class": "test_strategy",
        "path": "architecture/04-delivery/01-quality/mutation-testing-spec.md"
    },
    "network-architecture-diagram.md": {
        "page_class": "diagram",
        "path": "architecture/00-system-views/04-deployment/environments/{env}/network-architecture-diagram.md"
    },
    "nfr-traceability-map.md": {
        "page_class": "requirement",
        "path": "architecture/01-global-strategy/01-requirements/nfr-traceability-map.md"
    },
    "normalization-rationale-spec.md": {
        "page_class": "decision",
        "path": "architecture/02-domains/_shared-contracts/01-data/normalization-rationale-spec.md"
    },
    "oauth2-architecture-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/02-security/oauth2-architecture-spec.md"
    },
    "observability-stack-matrix.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/observability-stack-matrix.md"
    },
    "oidc-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/02-security/oidc-spec.md"
    },
    "openapi-3-1-specification.md": {
        "page_class": "api_contract",
        "path": "architecture/02-domains/_shared-contracts/02-apis/{api}/openapi-3-1-specification.md"
    },
    "operational-context-profile.md": {
        "page_class": "overview",
        "path": "architecture/00-system-views/01-context/operational-context-profile.md"
    },
    "operational-runbook-document.md": {
        "page_class": "repository_documentation",
        "path": "architecture/04-delivery/03-ops/operational-runbook-document.md"
    },
    "otel-instrumentation-guide.md": {
        "page_class": "repository_documentation",
        "path": "architecture/04-delivery/03-ops/otel-instrumentation-guide.md"
    },
    "outbox-table-schema.md": {
        "page_class": "data_entity",
        "path": "architecture/02-domains/_shared-contracts/01-data/outbox-table-schema.md"
    },
    "pact-broker-setup-guide.md": {
        "page_class": "repository_documentation",
        "path": "architecture/04-delivery/01-quality/pact-broker-setup-guide.md"
    },
    "pagination-standard-spec.md": {
        "page_class": "api_contract",
        "path": "architecture/02-domains/_shared-contracts/02-apis/pagination-standard-spec.md"
    },
    "partitioning-plan.md": {
        "page_class": "data_entity",
        "path": "architecture/02-domains/_shared-contracts/01-data/partitioning-plan.md"
    },
    "pipeline-style-assessment.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/pipeline-style-assessment.md"
    },
    "pki-architecture-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/02-security/pki-architecture-spec.md"
    },
    "plugin-style-assessment.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/plugin-style-assessment.md"
    },
    "production-dockerfile-spec.md": {
        "page_class": "artifact",
        "path": "architecture/03-cross-cutting/03-infrastructure/production-dockerfile-spec.md"
    },
    "prometheus-metrics-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/prometheus-metrics-spec.md"
    },
    "pros-cons-breakdown.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/pros-cons-breakdown.md"
    },
    "protocol-buffer-spec-proto.md": {
        "page_class": "api_contract",
        "path": "architecture/02-domains/_shared-contracts/02-apis/{api}/protocol-buffer-spec-proto.md"
    },
    "pugh-weighted-decision-matrix.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/pugh-weighted-decision-matrix.md"
    },
    "quality-gate-pass-fail-audit.md": {
        "page_class": "audit_report",
        "path": "architecture/01-global-strategy/05-governance/reviews/quality-gate-pass-fail-audit.md"
    },
    "quality-gate-rule-config.md": {
        "page_class": "standard_entry",
        "path": "architecture/01-global-strategy/05-governance/reviews/quality-gate-rule-config.md"
    },
    "queue-performance-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/queue-performance-spec.md"
    },
    "queue-selection-report.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/queue-selection-report.md"
    },
    "rag-architecture-specification.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/rag-architecture-specification.md"
    },
    "rbac-permission-matrix.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/02-security/rbac-permission-matrix.md"
    },
    "read-write-model-separation-spec.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/read-write-model-separation-spec.md"
    },
    "readme-md-document.md": {
        "page_class": "repository_documentation",
        "path": "architecture/04-delivery/03-ops/readme-md-document.md"
    },
    "regulatory-compliance-audit-report.md": {
        "page_class": "audit_report",
        "path": "architecture/01-global-strategy/05-governance/reviews/regulatory-compliance-audit-report.md"
    },
    "relay-process-design.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/relay-process-design.md"
    },
    "repository-interface-spec.md": {
        "page_class": "api_contract",
        "path": "architecture/02-domains/_shared-contracts/repository-interface-spec.md"
    },
    "requirement-specification-matrix.md": {
        "page_class": "requirement",
        "path": "architecture/01-global-strategy/01-requirements/requirement-specification-matrix.md"
    },
    "retry-strategy-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/05-exceptions/retry-strategy-spec.md"
    },
    "rfc-7807-error-spec.md": {
        "page_class": "api_contract",
        "path": "architecture/02-domains/_shared-contracts/02-apis/rfc-7807-error-spec.md"
    },
    "risk-mitigation-plan.md": {
        "page_class": "planning",
        "path": "architecture/01-global-strategy/04-risks/risk-mitigation-plan.md"
    },
    "risk-mitigation-report.md": {
        "page_class": "planning",
        "path": "architecture/01-global-strategy/04-risks/risk-mitigation-report.md"
    },
    "roadmap.md": {
        "page_class": "planning",
        "path": "architecture/04-delivery/00-planning/roadmap.md"
    },
    "rollback-trigger-conditions-doc.md": {
        "page_class": "mechanism",
        "path": "architecture/04-delivery/02-release/rollback-trigger-conditions-doc.md"
    },
    "rolling-deployment-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/04-delivery/02-release/rolling-deployment-spec.md"
    },
    "saga-orchestration-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/02-domains/_shared-contracts/saga-orchestration-spec.md"
    },
    "saga-step-sequence-diagram.md": {
        "page_class": "diagram",
        "path": "architecture/00-system-views/06-runtime/sequences/{saga}/saga-step-sequence-diagram.md"
    },
    "sampling-strategy-doc.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/sampling-strategy-doc.md"
    },
    "scalability-limits-report.md": {
        "page_class": "requirement",
        "path": "architecture/01-global-strategy/04-risks/scalability-limits-report.md"
    },
    "schema-migration-plan.md": {
        "page_class": "planning",
        "path": "architecture/04-delivery/00-planning/schema-migration-plan.md"
    },
    "sdk-audit-matrix.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/sdk-audit-matrix.md"
    },
    "search-engine-matrix.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/search-engine-matrix.md"
    },
    "secrets-management-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/02-security/secrets-management-spec.md"
    },
    "serverless-feasibility-assessment.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/serverless-feasibility-assessment.md"
    },
    "service-boundary-map.md": {
        "page_class": "overview",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/service-boundary-map.md"
    },
    "service-mesh-configuration.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/03-infrastructure/service-mesh-configuration.md"
    },
    "shadow-deployment-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/04-delivery/02-release/shadow-deployment-spec.md"
    },
    "sharding-architecture-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/sharding-architecture-spec.md"
    },
    "slo-sla-contract-spec.md": {
        "page_class": "requirement",
        "path": "architecture/01-global-strategy/01-requirements/slo-sla-contract-spec.md"
    },
    "slo-sli-definition-document.md": {
        "page_class": "requirement",
        "path": "architecture/01-global-strategy/01-requirements/slo-sli-definition-document.md"
    },
    "soa-evaluation-spec.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/soa-evaluation-spec.md"
    },
    "sql-ddl-nosql-schema-spec.md": {
        "page_class": "data_entity",
        "path": "architecture/02-domains/_shared-contracts/01-data/sql-ddl-nosql-schema-spec.md"
    },
    "stakeholder-concerns-map.md": {
        "page_class": "viewpoint",
        "path": "architecture/00-system-views/00-viewpoints/stakeholder-concerns-map.md"
    },
    "stakeholder-influence-matrix.md": {
        "page_class": "viewpoint",
        "path": "architecture/00-system-views/00-viewpoints/stakeholder-influence-matrix.md"
    },
    "stakeholder-matrix.md": {
        "page_class": "viewpoint",
        "path": "architecture/00-system-views/00-viewpoints/stakeholder-matrix.md"
    },
    "standards-enforcement-manifest.md": {
        "page_class": "standard_entry",
        "path": "architecture/01-global-strategy/05-governance/reviews/standards-enforcement-manifest.md"
    },
    "storage-selection-spec.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/storage-selection-spec.md"
    },
    "stress-test-spec.md": {
        "page_class": "test_strategy",
        "path": "architecture/04-delivery/01-quality/stress-test-spec.md"
    },
    "stride-threat-model-report.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/02-security/stride-threat-model-report.md"
    },
    "structured-logging-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/structured-logging-spec.md"
    },
    "system-boundary-specification.md": {
        "page_class": "overview",
        "path": "architecture/00-system-views/01-context/system-boundary-specification.md"
    },
    "system-prompt-template-spec.md": {
        "page_class": "artifact",
        "path": "architecture/03-cross-cutting/01-mechanisms/system-prompt-template-spec.md"
    },
    "system-scope-specification.md": {
        "page_class": "overview",
        "path": "architecture/01-global-strategy/00-context/system-scope-specification.md"
    },
    "tco-cost-model.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/tco-cost-model.md"
    },
    "team-topology-map.md": {
        "page_class": "overview",
        "path": "architecture/02-domains/00-overview/team-topology-map.md"
    },
    "tech-benchmark-matrix.md": {
        "page_class": "decision",
        "path": "architecture/01-global-strategy/02-strategy/style-assessments/tech-benchmark-matrix.md"
    },
    "technical-rfc-document.md": {
        "page_class": "adr",
        "path": "architecture/01-global-strategy/05-governance/decisions/technical-rfc-document.md"
    },
    "terraform-module-manifests.md": {
        "page_class": "artifact",
        "path": "architecture/03-cross-cutting/03-infrastructure/terraform-module-manifests.md"
    },
    "threat-to-control-mapping-matrix.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/02-security/threat-to-control-mapping-matrix.md"
    },
    "timeout-matrix.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/05-exceptions/timeout-matrix.md"
    },
    "tool-routing-specification.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/tool-routing-specification.md"
    },
    "transactional-inbox-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/transactional-inbox-spec.md"
    },
    "transactional-outbox-spec.md": {
        "page_class": "mechanism",
        "path": "architecture/03-cross-cutting/01-mechanisms/transactional-outbox-spec.md"
    },
    "uml-activity-diagram.md": {
        "page_class": "diagram",
        "path": "architecture/00-system-views/02-functional/activities/{use-case}/uml-activity-diagram.md"
    },
    "uml-class-diagram.md": {
        "page_class": "diagram",
        "path": "architecture/00-system-views/03-structure/classes/{context}/uml-class-diagram.md"
    },
    "uml-deployment-diagram.md": {
        "page_class": "diagram",
        "path": "architecture/00-system-views/04-deployment/environments/{env}/uml-deployment-diagram.md"
    },
    "uml-sequence-diagram.md": {
        "page_class": "diagram",
        "path": "architecture/00-system-views/06-runtime/sequences/{scenario}/uml-sequence-diagram.md"
    },
    "uml-state-diagram.md": {
        "page_class": "diagram",
        "path": "architecture/02-domains/_shared-contracts/05-state-machines/{aggregate}/uml-state-diagram.md"
    },
    "unit-test-standard-spec.md": {
        "page_class": "test_strategy",
        "path": "architecture/04-delivery/01-quality/unit-test-standard-spec.md"
    },
    "value-object-definitions.md": {
        "page_class": "data_entity",
        "path": "architecture/02-domains/_shared-contracts/value-object-definitions.md"
    },
    "value-stream-specification.md": {
        "page_class": "overview",
        "path": "architecture/00-system-views/02-functional/value-stream-specification.md"
    },
    "wbs.md": {
        "page_class": "planning",
        "path": "architecture/04-delivery/00-planning/wbs.md"
    },
    "webhook-architecture-spec.md": {
        "page_class": "api_contract",
        "path": "architecture/02-domains/_shared-contracts/02-apis/webhook-architecture-spec.md"
    },
    "well-architected-audit-scorecard.md": {
        "page_class": "audit_report",
        "path": "architecture/01-global-strategy/05-governance/reviews/well-architected-audit-scorecard.md"
    }
}
