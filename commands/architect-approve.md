---
description: How a person approves a gate or signs document acceptance with a passkey (the agent cannot do it)
disable-model-invocation: true
---

# `/architect-approve` — Human WebAuthn Passkey Enrollment & Cryptographic Sign-Off (`UC-08`)

Explain the human-only cryptographic approval workflow clearly. An AI agent cannot enroll reviewer keys, approve dispatch gates, or sign document acceptance on behalf of a human reviewer.

## 1. Opening the Review Workbench (Standard Approval Mode)

To review pending task gates or sign document acceptance with an already-enrolled WebAuthn passkey, open the workbench in your own terminal (Windows PowerShell, macOS, or Linux):

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap console serve .
```

- **Approve a Task Dispatch Gate (`/runs`):** Open **Runs and task gates** to inspect a dispatch gate. Read its exact scope, answer its questions, write a reason, and sign with your passkey.
- **Accept a Specification Candidate (`/`):** Use document review to inspect the combined candidate, checks, sources, and review evidence. Sign document acceptance separately.

## 2. First-Time Reviewer Passkey Enrollment (`--enroll`)

For your first key, run this in your own terminal:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/architect_runtime.py" --bootstrap console serve . --enroll
```

1. Open the localhost URL shown in your terminal and register a passkey (Windows Hello, Touch ID, or hardware security key) for a configured reviewer ID in `sdd-workspace.yml`.
2. Confirm its SHA-256 fingerprint interactively in that terminal so `.architect/reviewers.yml` is updated safely.
3. Note on Governance Modes: Workspaces initialized with `--preset solo-author` (`policy.mode: advisory`, `first_run_gate: auto`) allow autonomous drafting without blocking at step 0 on a passkey, whereas `--preset governed-team` (`policy.mode: enforce`, `first_run_gate: approve`) enforces hardware passkey signatures on every dispatch gate and baseline acceptance.

## 3. Non-Negotiable Cryptographic Invariants

An agent cannot do these human actions. A copied key file has no authority.
If the packet is stale, review the current revision before signing. If no key is available, the gate remains pending.
Name-only terminal approvals are retired. After signing, ask the agent to continue `/architect-run`.

A malformed marker requires repair before signing.

## Next

Read the current result, then use `/architect-run` for the next scoped action.

## If it fails

- A missing or malformed workspace marker requires explicit setup, migration or repair; preserve existing documents.
- For other failures, report the stable error code, affected scope and next action; do not paste a traceback or claim completion.
