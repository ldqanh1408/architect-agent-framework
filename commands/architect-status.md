---
description: Show the current architecture run — agent states, coverage scorecard, and pending human gates
argument-hint: "[thư mục dự án (tùy chọn)]"
---

# `/architect-status` — Read-Only 4-Layer Workspace & Run Scorecard

Read the current workspace **$ARGUMENTS** without mutating any state. Call `architect_runtime_status` and `architect_sdd_check` via MCP, or run via the self-contained CLI launcher:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap status "${ARGUMENTS:-.}" --json
python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap sdd status-probe "${ARGUMENTS:-.}"
```

Use `architect_runs_observe` (or `observe <ws> --after <seq>`) to read durable task events.

## 1. Four Independent State Layers to Report

Always present the workspace status in a clean table or structured summary separating all 4 governance layers:
1. **Layer 1 — Task Execution State:**
   Active run ID, completed tasks, running workers (with active lease status), failed/retried tasks, and tasks paused at `waiting-for-human` dispatch gates.
2. **Layer 2 — Deterministic & Coverage Scorecard (`DTG-01`..`DTG-10`):**
   - Overall check verdict (`PASS`, `INCOMPLETE`, or `FAIL`) and current snapshot digest.
   - Total registered artifacts, substantive authored prose pages (`180–350` lines), vs remaining placeholder stubs (`TODO: authored content pending.`).
   - All 5 coverage metrics: `source_intake_completeness`, `accounting_completeness`, `design_coverage`, `critical_coverage`, and `depth_completeness`.
3. **Layer 3 — Independent Semantic & Language Review State:**
   Checked candidate ID, sharded `@system` / `OBL-SEAM-*` obligation verdicts, and `aaf-ste80-v1` technical language compliance score.
4. **Layer 4 — Human Acceptance & Workbench State:**
   Signed acceptance records (`acceptances/`), configured reviewer passkey state, and the `architect_console_url` (`http://localhost:8767/`) when a task gate or document acceptance is pending.

## 2. Strict Read-Only Invariant

Reading status starts no task and creates no candidate. A missing marker requires initialization or migration. A malformed marker requires repair.
Keep this command read-only: do not author, approve, accept or publish changes.

## Next

Read the current result, then use `/architect-check` for the next scoped action.

## If it fails

- A missing or malformed workspace marker requires explicit setup, migration or repair; preserve existing documents.
- For other failures, report the stable error code, affected scope and next action; do not paste a traceback or claim completion.
