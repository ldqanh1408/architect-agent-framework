---
description: Inspect current core checks, coverage/depth gates, anti-stub verification, and freshness (UC-06)
argument-hint: "[thư mục dự án (tùy chọn)]"
---

# `/architect-check` — Deterministic Gate, Coverage & Anti-Stub Inspector (`UC-06`)

Call the host-discovered `architect_sdd_check` tool (and `architect_style_check` when inspecting prose style), or run via the self-contained CLI launcher:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap sdd check "${ARGUMENTS:-.}" --full --out .architect-build/check.json
```

Supply a named candidate (`--change <id>`) when requested. Otherwise inspect the live workspace.

## 1. What `/architect-check` Verifies (Read-Only Gate Audit)

Read and report each verification dimension separately:
1. **Five Document Coverage Ratios (`document_coverage`):**
   - `source_intake_completeness` (all input sources registered & reconciled in `source-manifest.md`)
   - `accounting_completeness` (100% of universe $U$ accounted for in `concern-inventory.md` & `concern_ledger`)
   - `design_coverage` (every planned concern mapped to authored target artifacts)
   - `critical_coverage` (100% of critical requirements, ADRs, state machines, and scenarios covered)
   - `depth_completeness` (every required depth dimension backed by a verbatim `>= 40`-char preferred / `>= 20`-char minimum `depth_witness` quote in substantive body prose)
2. **Anti-Hollow & Structural Invariants (`DTG-01`..`DTG-10`):**
   - Stub & placeholder detection (`PLACEHOLDER_CONTENT_DETECTED` for `TODO`, `TBD`, `FIXME`, `authored content pending`)
   - Section completeness & line budget (`SECTION_BODY_EMPTY`, `PAGE_LINE_BUDGET_VIOLATION` outside 180–350 body lines for maximal prose pages)
   - Anti-duplication (`SEMANTIC_PADDING_DETECTED` across normalized body prose and 5-gram Jaccard similarity)
   - Anti-collapse (`FLAT_DOMAINS_DEFECT`, `INLINE_ADR_DEFECT`, `SINGLETON_SCENARIO_DEFECT`, `FRONTEND_COLLAPSE_DEFECT`)
3. **Lineage, Freshness & Semantic Obligations:**
   - Historical regression (`LINEAGE_OR_DEPTH_REGRESSION`, `GUARD_PRESERVATION_REGRESSION`), link integrity, source/consumer revision freshness, and semantic coverage. Cite exact source and consumer revisions. Name the affected obligation and owner.

## 2. Strict Read-Only Governance Rules

A resolving link does not prove consistent behavior. Missing evidence remains INCOMPLETE. A missing marker requires setup or migration. A malformed marker requires repair.
This command reads state. It creates no proposal, starts no task, invokes no provider, and changes no baseline.
Keep this command read-only: do not author, approve, accept or publish changes.

## Next

Read the current result, then use `/architect-status` or `/architect-review` for the next scoped action.

## If it fails

- A missing or malformed workspace marker requires explicit setup, migration or repair; preserve existing documents.
- For other failures, report the stable error code, affected scope and next action; do not paste a traceback or claim completion.
