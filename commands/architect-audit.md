---
description: Audit brownfield codebases and acceptance test evidence against SRS/ADR specifications (UC-04)
argument-hint: "[thư mục dự án (tùy chọn — tự động quét code, test và SRS)]"
---

# `/architect-audit` — Brownfield Codebase & Acceptance Evidence Auditor (`UC-04`)

Perform an exhaustive architectural drift and acceptance gate audit across implementation repositories and test suites in **$ARGUMENTS** against upstream SRS/ADR authority.

## 1. Mandatory Reference Loading

Before auditing, read:
- `${CLAUDE_PLUGIN_ROOT}/skills/01-system-architect/SKILL.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/02-spec-critic/SKILL.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/01-system-architect/references/output-contract.md`

## 2. Step-by-Step Brownfield Audit Protocol

1. **Phase 1 — Exhaustive Evidence & Codebase Extraction (`audit: true`):**
   Compute SHA-256 digests, line counts, and structural inventories across all specified code directories (`frontend/`, `backend/`, `src/`), acceptance suites (`*-acceptance/`, test reports, playwright/pytest outputs), and authority specs (`SYSTEM_REQUIREMENTS.md`, ADRs) via MCP `architect_sdd_extract` or CLI:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap sdd extract-sources "${ARGUMENTS:-.}" --audit
   ```
2. **Phase 2 — Architectural Drift & Conflict Classification (`CNF-*` & `FND-*`):**
   Compare the normative specification against actual implementation evidence across 4 dimensions:
   - **`SPECIFIED_NOT_BUILT`:** Requirements, bounded contexts, routes/views, or security controls mandated by SRS/ADR that are missing or stubbed in code.
   - **`IMPLEMENTATION_DRIFT`:** Structural divergence (e.g., SRS mandates 2 isolated SPA applications `workspace-web` and `ops-admin-web`, but the repository ships a single combined app or mismatched route/state contracts).
   - **`ACCEPTANCE_GATE_FAIL` (`NO_GO`):** Failed acceptance tests, broken E2E journeys, or unverified SLO gates (`FND-001..N`).
   - **`AUTHORITY_CONFLICT` (`CNF-01..N`):** Contradictions between upstream documents or between code and spec.
3. **Phase 3 — Reconcile Ledgers & Remediation Register:**
   - Register every conflict in `architecture/00-plan/source-manifest.md` with `read_status: reconciled`, `authority_preserved: true`, and `resolution_status: recorded_conflict` (never silently overwrite normative SRS requirements with broken implementation behavior).
   - Document every finding and remediation work order in `architecture/00-plan/concern-inventory.md` and `architecture/04-delivery/04-audit/traceability-and-gap-audit.md` (`DELIV-AUDIT`).
4. **Phase 4 — Deterministic Gate Verification:**
   Run `architect_sdd_check` (`sdd check <ws> --full`) to verify `source_intake_completeness == 1.0`, `accounting_completeness == 1.0`, and zero unresolved `SOURCE_AUTHORITY_CONFLICT` or `DESIGN_GAP_OPEN` defects.

## Next

Read the current result, then use `/architect-check` or `/architect-status` for the next scoped action.

## If it fails

- A missing or malformed workspace marker requires explicit setup, migration or repair; preserve existing documents.
- For other failures, report the stable error code, affected scope and next action; do not paste a traceback or claim completion.
