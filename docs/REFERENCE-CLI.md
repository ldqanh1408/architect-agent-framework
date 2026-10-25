---
document_role: reference
status: implementation-candidate
updated_at: 2026-10-15
derived_from: architect_framework/launcher.py
---

# Current CLI reference

Candidate: 2.0.0-alpha.1. Release status: NOT_QUALIFIED.
Use `--help` for exact options. Report any difference from this page as a defect.

## Setup and human review

Run setup in your own terminal. Use a new empty spec directory.

```bash
architect-runtime sdd host-init ./spec --workspace-id MY-SYSTEM --reviewer YOUR-NAME
architect-runtime console serve ./spec --enroll
architect-runtime console verify ./spec
```

Confirm a new key fingerprint in that terminal. A copied key file grants no trust.
Open `/runs` for task state and dispatch gates. Open `/` for document review and acceptance.
A dispatch approval authorizes one attempt. It does not accept or publish documents.
MCP exposes no human approval or acceptance tool.

## Task execution

```bash
architect-runtime start ./spec --tasks-file tasks.json
architect-runtime start ./spec --tasks-file next-tasks.json --base-change CHANGE-ID
architect-runtime status ./spec --json
architect-runtime claim ./spec --run RUN-ID --task TASK-ID
architect-runtime heartbeat ./spec --run RUN-ID --task TASK-ID --lease TOKEN
architect-runtime complete ./spec --run RUN-ID --task TASK-ID --lease TOKEN --operations-file operations.json
architect-runtime observe ./spec --after 0
architect-runtime control ./spec --run RUN-ID --action pause
```

| Command | Result |
|---|---|
| `plan`, `check` | Inspect current document readiness |
| `start` | Validate and store a bounded task plan |
| `status`, `scorecard` | Read current task state |
| `next`, `tick`, `recheck` | Refresh scheduling state; never create approval |
| `claim` | Obtain a private attempt lease for a ready task |
| `heartbeat` | Renew a current lease before its global deadline |
| `complete` | Submit scoped operations to an isolated candidate |
| `observe` | Read redacted events with a cursor |
| `control` | Pause, resume, cancel, or retry scheduling |

Keep the lease private. An expired lease or global deadline fences late results.
Cancel stops scheduling. The host worker can still run; its outcome remains unknown.
Task completion means checked candidate. Independent review and signed acceptance remain separate.

`start --base-change CHANGE-ID` freezes an existing checked candidate as the input.
Task claims return its exact snapshot and artifact revisions. Pending candidate grants
and policy changes do not authorize tasks. Changed source, baseline, or candidate
bindings block dispatch. MCP uses the `base_change` field on `architect_runs_start`.

## Document proposals and checks

```bash
architect-runtime sdd check ./spec
architect-runtime sdd changes propose ./spec --skill 01-system-architect --expect-snapshot SNAPSHOT --file operations.json
architect-runtime sdd regression ./spec --change CHANGE-ID
architect-runtime sdd review ./spec --change CHANGE-ID
architect-runtime sdd report ./spec --change CHANGE-ID
```

Read exact source revisions before authoring. The accepted skill grant controls writes.
Inspect the returned change ID. The original source stays unchanged until signed acceptance.
A deterministic PASS does not prove semantic review or human acceptance.

Configure a pinned review provider and a bounded budget before model calls.
A fixture response is transport evidence, not model qualification.
For frozen human labels, use `sdd eval --corpus corpus.json --stage-labels` through the launcher.
See [the task guide](GUIDE-CORE-RUNS.md) for label, model, and writing boundaries.

## Separate migration

```bash
architect-migrate ./old --workspace-id MY-SYSTEM --reviewer YOUR-NAME --owner 01-system-architect
architect-migrate ./old --destination ./new --workspace-id MY-SYSTEM --reviewer YOUR-NAME --owner 01-system-architect
```

Inspect the dry-run mapping and loss report before the second command.
Resolve unsupported input. Source edits and target edits stop the import.
Resume applies to an unused migration destination. Old approvals and keys grant no new authority.

## Catalog and gate maintenance

`architect-cli --help` lists catalog export, routing, validation, and maintainer tools.
Catalog tools do not accept a spec revision. Routing does not authorize writes.

```bash
architect-cli gate list
architect-cli gate run --id GATE-SDD-CHECK ./spec
architect-cli gate run --id GATE-SDD-REGRESSION ./spec
```

Read [the gate reference](REFERENCE-GATES.md) before selecting other registry entries.
Old predicate entries remain pending parity and deletion. A skipped entry is not PASS.
Do not use obsolete ledger, charter, tree-plan, or phase writers as a core workflow.
