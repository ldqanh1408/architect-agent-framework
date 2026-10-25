# Metamodel — the prose face of `correspondence_rules.yaml`

**G-3 (CROSSTALK-E2E-WORKFLOW-PLAN).** This file is the **prose face** of the 16
correspondence rules in `architect_framework/data/correspondence_rules.yaml` — it is
**derived**, not a second list. Editing this file does nothing; edit the YAML, then
regenerate. A relation the site draws must resolve against one of these rules; a
relation that matches none is `EDGE-SOURCE-WEAK` at best and a defect at worst.

**16 rules, ISO 42010:2022 viewpoints.** Every rule maps one source
viewpoint to a target viewpoint and states what must hold between them.

| Rule | Source viewpoint | Target viewpoint | Type | What must hold |
|---|---|---|---|---|
| CR-001-DDD-CONTAINER-MAPPING | Bounded Context Viewpoint | C4 Container Viewpoint | MustExist | Every Bounded Context defined in Domain Viewpoint MUST be mapped to at least 1 C4 Container. |
| CR-002-AGGREGATE-REPOSITORY-MAPPING | Tactical DDD Viewpoint | Database Viewpoint | AttributeMatch | Every Aggregate Root MUST have a corresponding primary persistence table or document schema. |
| CR-003-API-SECURITY-AUTH | API Viewpoint | IAM Viewpoint | MustExist | Every public API endpoint MUST reference an explicit authentication/authorization scheme. |
| CR-004-CONTAINER-INFRA-RESOURCE | C4 Container Viewpoint | Infrastructure Viewpoint | MustExist | Every C4 Container MUST have defined CPU and Memory deployment resource limits. |
| CR-005-DOMAIN-EVENT-MESSAGE-CHANNEL | Event Viewpoint | Message Broker Viewpoint | MustExist | Every Domain Event MUST have a corresponding message channel (topic/queue) in the message broker configuration. |
| CR-006-INFRA-COST-ESTIMATE | Infrastructure Viewpoint | Cost Viewpoint | MustExist | Every infrastructure resource (VM, database, cache) MUST have a cost estimate in the FinOps model. |
| CR-007-SLO-OBSERVABILITY-ALERT | SLO Viewpoint | Observability Viewpoint | MustExist | Every Service Level Objective (SLO) MUST have at least one corresponding Prometheus alerting rule. |
| CR-008-SECURITY-THREAT-CONTROL | Threat Model Viewpoint | Security Control Viewpoint | MustExist | Every identified STRIDE threat MUST have a corresponding security control or mitigation strategy documented. |
| CR-009-API-ASYNCAPI-CONTRACT | API Viewpoint | AsyncAPI Viewpoint | AttributeMatch | Every asynchronous event published by a service MUST have a corresponding AsyncAPI specification entry. |
| CR-010-DEPLOYMENT-ROLLBACK | Deployment Viewpoint | Rollback Viewpoint | MustExist | Every deployment pipeline MUST define an explicit rollback strategy. |
| CR-011-CONTEXT-MAP-INTEGRATION-PATTERN | Context Map Viewpoint | Integration Pattern Viewpoint | MustExist | Every upstream/downstream context relationship MUST use an explicit integration pattern (ACL, Open Host, Published Language). |
| CR-012-AI-AGENT-GUARDRAIL | AI Agent Viewpoint | Guardrail Viewpoint | MustExist | Every AI agent in the system MUST have input and output guardrails defined to prevent harmful or out-of-scope outputs. |
| CR-013-DATA-RETENTION-COMPLIANCE | Data Schema Viewpoint | Compliance Viewpoint | AttributeMatch | Every PII or sensitive data field MUST have a documented retention policy and encryption standard. |
| CR-014-AGGREGATE-CDC-PIPELINE | Tactical DDD Viewpoint | Data Pipeline Viewpoint | MustExist | Every Aggregate Root with downstream read model consumers MUST have a CDC or event-driven sync mechanism. |
| CR-015-INFRA-NETWORK-POLICY | Infrastructure Viewpoint | Network Policy Viewpoint | MustExist | Every Kubernetes workload MUST have a NetworkPolicy defining allowed ingress and egress traffic. |
| CR-016-DISASTER-RECOVERY-RTO-RPO | SLO Viewpoint | Disaster Recovery Viewpoint | AttributeMatch | Every system component with an availability SLO > 99.9% MUST have a Disaster Recovery plan with defined RTO and RPO. |

## How a relation resolves

A typed edge in `source-map.yml` is valid when its `kind` maps to one of the 16 rules:
providesApi ↔ CR-001 (container mapping), consumesApi ↔ CR-009 (API contract),
publishesEvent ↔ CR-005 (domain event message channel), dependsOn ↔ the rule naming
the dependency the source viewpoint requires. `check_source_map_typed.py` enforces the
kind vocabulary; this file is the human-readable reason a kind exists at all.

## Traceability
| Claim | Classification | Source | Freshness |
|---|---|---|---|
| 16 rules, derived | observed | architect_framework/data/correspondence_rules.yaml | 2026-08-08 |

## Verification
| Gate | Command | Exit | Evidence time |
|---|---|---:|---|
| Rule count matches | `python -c "import yaml; print(len(yaml.safe_load(open('architect_framework/data/correspondence_rules.yaml',encoding='utf-8'))['rules']))"` | 0 | 2026-08-08 |
