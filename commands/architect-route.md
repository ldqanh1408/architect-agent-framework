---
description: Route an architecture request to the Domain and Task skill pair that owns the decision (UC-05)
argument-hint: "<bài toán kiến trúc cần định tuyến>"
---

# `/architect-route` — Deterministic 297-Slot Architecture Skill Router (`UC-05`)

Determine which specialized **Domain Skill × Task Skill** pair in the 297-slot AAF catalog owns the architectural decision for: **$ARGUMENTS**

## 1. Mandatory Reference Loading

Load `${CLAUDE_PLUGIN_ROOT}/skills/architect-skill-orchestrator/SKILL.md` to apply the routing precedence rules across the 110 Domain Skills (10 architecture clusters), 186 Task Skills (21 task families), and 1 Orchestrator (297 total skill slots).

## 2. Deterministic Routing Procedure

1. **Execute the Deterministic Skill Router:**
   Run the router via the self-contained CLI launcher:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap cli route-skills --query "$ARGUMENTS"
   ```
2. **Classify the Request Across 4 Axes:**
   - **Decision Authority:** Which bounded context or architectural plane owns the system-of-record invariant?
   - **Expected Deliverable:** ADR (`decision`), API contract (`api_contract`), data model (`data_entity`), state machine (`state_machine`), cross-cutting mechanism (`mechanism`), or full workspace tree?
   - **Domain Cluster (10 Catalog Clusters):** `01_business_architecture`, `02_domain_architecture`, `03_application_architecture` (includes frontend/mobile/edge), `04_ai_architecture`, `05_data_architecture`, `06_infrastructure_architecture`, `07_security_architecture`, `08_quality_attribute_architecture`, `09_delivery_architecture`, or `10_documentation_architecture`.
   - **Available Evidence:** Greenfield brief vs brownfield codebase vs live production incident/audit.
3. **Report the Routing Verdict (`selected`, `ambiguous`, `blocked`, or `no-route`):**
   - State the selected `domain_skill_id`, `task_skill_id`, target archetype, and required depth dimensions.
4. **Verify Skill Slot Availability & Pack Coverage:**
   Check whether the selected skill slot is populated (`licensed`, `third-party`, `core`, `base`, or `empty`):
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap skills offer <skill-id>
   ```
   If the user provides a skill pack archive to install, run:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap skills install <zip>
   ```

## Next

When the verdict is `selected`, run `/architect-execute` (for a single standalone artifact) or `/architect-design` (for a full workspace).

## If it fails

- `ambiguous`: show the candidates and the evidence that would separate them, and ask the user.
- Say in one sentence what failed and what fixes it; do not paste a traceback or a raw JSON error to the user.
