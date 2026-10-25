---
description: Manage living specification change requests and dependency impact radius without regression (UC-07)
argument-hint: "<nội dung thay đổi yêu cầu>"
---

# `/architect-change` — Living Specification Change Request & Impact Manager (`UC-07`)

Apply an incremental specification change for **$ARGUMENTS** across an existing SDD workspace while computing exact dependency impact and enforcing non-regression invariants (`DTG-07`).

## 1. Mandatory Reference Loading

Read `${CLAUDE_PLUGIN_ROOT}/skills/01-system-architect/SKILL.md` and `${CLAUDE_PLUGIN_ROOT}/skills/01-system-architect/references/output-contract.md` before modifying any workspace artifact.

## 2. Step-by-Step Living Spec Change Protocol

1. **Step 1 — Baseline Inspection & Dependency Impact Radius (`graph.affected`):**
   - Call `architect_sdd_check` (or run `python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap sdd check <ws> --full`) to inspect the current baseline snapshot (`origin_snapshot`) and dependency graph.
   - Trace all upstream authorities (`FR-*`, `NFR-*`, `ADR-*`) and downstream consumers (`CTX-*`, `SC-*`, `SCN-*`) affected by the change request so only the true impact radius is modified.
2. **Step 2 — Update Ledgers & Author Scoped Candidate Proposals:**
   - If the change introduces new requirements or concerns, update `clarified-requirements.md`, `architecture/00-plan/source-manifest.md`, `architecture/00-plan/concern-inventory.md`, and `architecture/00-plan/document-tree-plan.md`, then re-freeze `basis_digest` via `sdd freeze-digest <ws>`.
   - Update only the impacted specification pages via `architect_sdd_propose` (binding `expected_snapshot` to `origin_snapshot` and passing `base_change` when extending an active candidate).
   - Maintain the 180–350 body-line budget, all 10 canonical sections, `## 3. Executable Boilerplate`, and `## 4. Guardrails & Defaults`.
3. **Step 3 — Historical Non-Regression & Guard Preservation Gate (`DTG-07`):**
   - Run post-processing and historical regression verification:
     ```bash
     python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap sdd prepare-check <ws> --tighten --style-fix --stamp
     python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap sdd regression <ws> --full
     python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap sdd check <ws> --full
     ```
   - Confirm zero `LINEAGE_OR_DEPTH_REGRESSION` and zero `GUARD_PRESERVATION_REGRESSION` findings (every prior `canonical_fact`, `guard`, and `depth_dimension` must be preserved or explicitly superseded by a new ADR).

## Next

Read the current result, then use `/architect-check` for the next scoped action.

## If it fails

- A missing or malformed workspace marker requires explicit setup, migration or repair; preserve existing documents.
- For other failures, report the stable error code, affected scope and next action; do not paste a traceback or claim completion.
