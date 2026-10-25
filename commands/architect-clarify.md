---
description: Clarify raw ideas or incomplete briefs via Socratic interview into structured requirements (UC-01)
argument-hint: "[ý tưởng hoặc yêu cầu cần làm rõ]"
---

# `/architect-clarify` — Socratic Requirement Clarification Playbook (`UC-01`)

Transform raw ideas, stakeholder notes, or incomplete briefs in **$ARGUMENTS** into a complete, traceable requirement baseline (`clarified-requirements.md`) using the `00-requirement-clarifier` foundation skill.

## 1. Mandatory Skill & Reference Loading

Before formulating interview questions or drafting requirements, read these files from `${CLAUDE_PLUGIN_ROOT}`:
- `${CLAUDE_PLUGIN_ROOT}/skills/00-requirement-clarifier/SKILL.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/00-requirement-clarifier/workflow-contract.yml`
- `${CLAUDE_PLUGIN_ROOT}/skills/00-requirement-clarifier/references/clarification-method.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/00-requirement-clarifier/references/ambiguity-taxonomy.yml`
- `${CLAUDE_PLUGIN_ROOT}/skills/00-requirement-clarifier/references/output-contract.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/00-requirement-clarifier/assets/interview-question-bank.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/00-requirement-clarifier/assets/clarified-requirements-template.md`

## 2. Step-by-Step Execution Protocol

1. **Zero-Config Workspace Bootstrap:**
   If `sdd-workspace.yml` does not exist yet in the target directory, initialize it in `solo-author` mode via MCP `architect_sdd_init` or CLI:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap sdd host-init . --workspace-id clarified-spec --reviewer lead-architect --profile seed --preset solo-author --allow-existing-sources
   ```
2. **Ambiguity Taxonomy Scan (6 Orthogonal Dimensions):**
   Inspect the input across:
   - **Actors, Tenancy & Trust Boundaries** (roles, B2B/B2C tenancy isolation, auth model)
   - **Core Domain Workflows & State Lifecycles** (triggers, preconditions, happy path, failure/compensation path)
   - **Data Entities, Authority & Retention Invariants** (system-of-record ownership, PII/encryption, audit trails)
   - **Scale, Throughput & Latency SLOs** (P95/P99 latency budgets, RPO/RTO, peak concurrency)
   - **External System Integrations & Protocols** (webhooks, idempotency, rate limits, circuit breakers)
   - **Compliance, Deployment & Cost Constraints** (cloud topology, regulatory boundaries, release gates)
3. **Bounded Socratic Interview (Maximum 5 Questions with Recommended Defaults):**
   - If critical ambiguities block architectural decisions, ask **at most 5 high-leverage questions** in a single turn.
   - Every question MUST include **2–3 concrete Recommended Defaults** so the user can simply reply *"Use recommended defaults"* or override specific items.
4. **Author Normalized Deliverables:**
   - Author or update `brief.md` and `clarified-requirements.md` following `assets/clarified-requirements-template.md`.
   - Assign stable, unique IDs to every atomic requirement: Functional Requirements (`FR-001..N`), Non-Functional Requirements (`NFR-001..N`), Business Rules (`BR-001..N`), Core Entities (`ENT-001..N`), and Explicit Assumptions/Open Questions (`ASM-001..N`).
   - Record proposals via `architect_sdd_propose` (or CLI `sdd changes propose`) and verify with `architect_sdd_check`.

## Next

Read the current result, then use `/architect-quickstart` or `/architect-design` for the next scoped action.

## If it fails

- A missing or malformed workspace marker requires explicit setup, migration or repair; preserve existing documents.
- For other failures, report the stable error code, affected scope and next action; do not paste a traceback or claim completion.
