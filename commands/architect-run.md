---
description: Plan and run (or continue) the gated multi-agent architecture run for a workspace
argument-hint: "[thư mục dự án (tùy chọn)]"
---

# `/architect-run` — Bounded Multi-Agent Run Scheduler & Wave Executor

Use the `architect-runtime` skill for **$ARGUMENTS**. Read the current marker, accepted grants, source obligations, and applicable skill methods before scheduling or claiming tasks.

## 1. Multi-Agent Wave Scheduling & Concurrency Protocol

1. **Preflight Model & Slot Verification:**
   Run the model probe and skill slot check before dispatching worker waves so rate limits (`429`) or unavailable models (`402`) never crash a multi-agent run:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap sdd probe-models
   python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap sdd plan-waves "${ARGUMENTS:-.}" --batch-size 4 --out .architect-build/waves-plan.json
   python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap skills status "${ARGUMENTS:-.}" --json
   ```
2. **Bounded Task Preparation & Lease Lifecycle (`max_concurrency <= 4`):**
   - Prepare bounded tasks with explicit dependencies, disjoint write scopes (`1–2` pages per micro-batch), required outputs, and human questions (`max_concurrency <= 4`).
   - Use `architect_runs_start`, `architect_runtime_next`, `architect_task_claim`, `architect_task_heartbeat`, and `architect_task_complete` (or CLI `start`, `next`, `claim`, `heartbeat`, `complete`).
   - For a direct isolated proposal, use `architect_sdd_propose` with the configured skill and exact origin. Read a base candidate with `architect_sdd_read` before extending it.
3. **Post-Wave Gate Verification & Review Handoff:**
   - Run `architect_sdd_prepare_check` (`sdd prepare-check <ws> --tighten --style-fix --stamp`), deterministic checks (`architect_sdd_check`), and historical regression (`sdd regression <ws> --full`).
   - Obtain independent semantic review (`architect_candidate_review`). Give the person `architect_console_url` for run gates and signed document acceptance.

## 2. Non-Negotiable Governance & Revision Rules

A completed task candidate is not an accepted document. Do not write registered files or human decisions directly.
A missing marker requires explicit initialization or migration. A malformed marker requires repair.
Report incomplete evidence and the concrete next action.

Use `00-requirement-clarifier` for requirement facts, `01-system-architect` for architecture and `02-spec-critic` for independent critique. Read each complete package method before its task. Use the configured accepted grant for each owner.
Bind `expected_snapshot` to the exact `origin_snapshot`; preserve expected artifact revisions. Pass `base_change` when extending an existing checked candidate and read that candidate before drafting the next operations.
Initialization is a human action. Never infer approval from a prior conversation or a task completion record.

## Next

Read the current result, then use `/architect-status` for the next scoped action.

## If it fails

- A missing or malformed workspace marker requires explicit setup, migration or repair; preserve existing documents.
- For other failures, report the stable error code, affected scope and next action; do not paste a traceback or claim completion.
