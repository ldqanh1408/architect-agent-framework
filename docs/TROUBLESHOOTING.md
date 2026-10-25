---
document_role: reference
status: implementation-candidate
updated_at: 2026-10-14
---

# Troubleshoot the current core

Preserve source, candidates, and signed records before recovery. Inspect the exact error code.
Run `architect-runtime status ./spec --json` for tasks and `architect-runtime sdd report ./spec`
for documents. A successful read does not repair state or accept a document.

| Error or state | Next action |
|---|---|
| WORKSPACE_UNINITIALIZED | Initialize a new empty directory in your terminal |
| WORKSPACE_MIGRATION_REQUIRED | Inspect an explicit migration dry run; use a separate destination |
| WORKSPACE_VERSION_UNSUPPORTED | Use a compatible runtime or an explicit migration |
| Invalid marker | Repair the reported configuration error; do not delete the marker to select another engine |
| RUN_INPUT_STALE | Preserve the run and prepare a new plan from current source and baseline |
| waiting-for-human | Read the exact dispatch scope and answer each question in Gate inbox |
| TASK_DISPATCH_DENIED | Inspect dependency state, current gate, pause state, and attempt limits |
| RUN_DEADLINE | Preserve checked candidates; prepare a new bounded run; do not renew the old attempt |
| TASK_LEASE_STALE | Preserve late worker output separately; retry with a new attempt and gate |
| RUN_STORE_INVALID | Preserve the damaged store; use explicit recovery; task and gate state are unknown |
| RUN_SCHEMA_UNSUPPORTED | Preserve old state; do not let a new writer convert it implicitly |
| SEMANTIC_REVIEW_REQUIRED | Obtain independent review with exact source evidence |
| No trusted reviewer | Start the console with enrollment in your terminal and confirm the key fingerprint |
| Signature refused | Reopen the current scope; check the configured reviewer, host trust, expiry, and source binding |
| LABEL_MANIFEST_CORRUPT | Preserve the manifest; restage original source; no model is qualified by this state |
| MIGRATION_SOURCE_CHANGED | Preserve the partial target; inspect changes; prepare a new mapping into a new destination |
| MIGRATION_TARGET_CHANGED | Preserve target edits; recover separately; do not overwrite them with resume |

A view pause stops screen updates. A scheduling pause stops new dispatch.
Neither operation proves that a host worker stopped. Cancel fences late results.

A document can pass deterministic checks while review is incomplete. Task completion can
produce a checked candidate while acceptance is absent. These states require different actions.

Model drift, cancellation, and exhausted budgets stop the review cascade. Missing or ungrounded
evidence cannot become PASS. Keep the last fact-safe draft when writing repair fails and request
human review of unresolved meaning.

This candidate still has legacy parity and deletion blockers. See the current status record in
the source repository. Do not treat a historical report or a passing subset as a release certificate.
