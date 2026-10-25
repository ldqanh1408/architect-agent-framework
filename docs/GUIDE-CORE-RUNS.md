# Run and review a core workspace

This guide describes the implementation candidate. It is not a release certificate.

Create a new empty workspace in your own terminal:

```bash
architect-runtime sdd host-init ./spec --workspace-id MY-SYSTEM --reviewer YOUR-NAME
architect-runtime console serve ./spec --enroll
```

Register a configured reviewer key in document review. Confirm its fingerprint in that terminal.
A copied key file does not establish trust.

Ask the host to prepare a bounded task plan. Declare each task's skill, objective, writes, outputs, dependencies, and human questions.
Read effective contracts. A routing result selects a skill. The accepted grant controls its writes.

```bash
architect-runtime plan ./spec --tasks-file tasks.json
architect-runtime start ./spec --tasks-file tasks.json
architect-runtime start ./spec --tasks-file next-tasks.json --base-change CHANGE-ID
architect-runtime status ./spec --json
architect-runtime observe ./spec --after 0
architect-runtime claim ./spec --run RUN-ID --task TASK-ID
architect-runtime heartbeat ./spec --run RUN-ID --task TASK-ID --lease TOKEN
architect-runtime complete ./spec --run RUN-ID --task TASK-ID --lease TOKEN --operations-file operations.json
```

Use `--base-change` to continue from a checked candidate. The plan freezes its
identity and snapshot. The first task reads that candidate without replaying its
operations. The candidate supplies no new grant, policy, or approval authority.
A changed origin or baseline requires a new plan. An invalid candidate must pass
deterministic checks before dispatch. Review and acceptance remain separate.
The MCP tool `architect_runs_start` accepts the same `base_change` field.

`plan` and `architect_runtime_plan` preview the same normalized task binding as
`start`, without creating run state. They accept tasks, optional skill selection
and a checked initial candidate. An objective is text; conflicting `objective`
and compatibility `reason` inputs are refused.

Skill content is frozen with package, contract and brief digests. Claims return
the bounded brief privately; observers and persisted task records contain its
hashes. A changed or missing package, reference or binding invalidates dispatch,
gate decisions, heartbeats and results. Prepare a new run after reviewing changes.
Known empty slots fail preflight. Host-provided owners still need accepted grants.
Package contracts cannot expand those grants.

Input limits are 1024 regular package files, 2 MiB per file, 16 MiB per package,
64 workflow references and 8 MiB per assembled brief. Package links are refused.
The run store uses schema 3. Older stores require explicit recovery or migration;
opening one does not silently rewrite its records.

Open **Runs and task gates**. Read task state, dependencies, write scope, and events.
A person signs a pending dispatch gate. They must answer every current question before approval.
Notification deadlines create no human approval record.

Claim a task only when its gate permits dispatch. Keep its attempt lease private.
Read its base candidate before further authoring. Use `architect_sdd_read` for exact candidate revisions.
Send a heartbeat before the lease expires. A late worker cannot submit through an expired or cancelled lease.
The global run deadline also stops new claims, gate decisions, heartbeats, and result commits.
The checked prefix remains available. Replaying an already completed result creates no new candidate.
A blocked deadline does not prove that the host worker stopped. Its outcome remains unknown.
A retry uses a fresh gate and attempt. A changed source or baseline needs a new plan.

A view pause stops screen updates. A scheduling pause stops new dispatch.
Running host workers can continue. Their late results remain fenced.
Host tool traces, usage, and cost are unavailable. Observation coverage is partial.

Task completion creates a checked candidate. Obtain independent semantic review before requesting document acceptance.
The person signs acceptance in document review. The engine verifies current authority before publication.
The person inspects conflicts before `sdd host-recover` after interrupted publication.

## Review model configuration

Configure the exact provider, model, credential environment variable, workload profile, prices, and budget.
Do not assume that a mutable model alias matches a qualified model.
The returned model must match the configured pin.

An optional Jev stage uses Choice screening. Structured review with source evidence remains required.
The cascade shares one deadline, attempt ceiling, and reservation account across its stages.
Cancellation, budget exhaustion, and model drift do not trigger another model call.
No cost saving is certified. A screening stage can add cost. Compare quality and cost on an independent corpus first.

Stage labels without calling a provider:

```bash
architect-runtime sdd eval ./spec --corpus corpus.json --stage-labels
```

Open **Settings** in the task workbench. Inspect each frozen case, its sources, and its proposed label.
Select the cases you reviewed, explain the review, and sign them.
Two verified independent human reviewers must review each held-out case.
Names in input JSON do not approve labels. Label signatures do not accept documents or qualify a model.

Live qualification needs distinct source cases, source groups, workload families, and current signed labels.
Wilson bounds and source-group bootstrap intervals constrain precision, critical recall, and false blockers.
The report binds source implementation, configuration, corpus, and declared profile. Missing evidence remains INCOMPLETE.

## Technical writing

Aim for short, clear technical English under the 80% STE-inspired profile.
Preserve IDs, values, units, links, code, normative words, negation, and UNKNOWN during repair.
Use separate writer, style, and meaning roles. Use at most two repair rounds.
Keep the last fact-safe draft if repair fails. Ask a human to review unresolved language and meaning.
The partial checker does not certify ASD-STE100 or 80% full-profile compliance.

## Old workspaces

Run migration as a separate offline tool. Use a separate destination and an explicit owner.

```bash
architect-migrate ./old --workspace-id MY-SYSTEM --reviewer YOUR-NAME --owner 01-system-architect
architect-migrate ./old --destination ./new --workspace-id MY-SYSTEM --reviewer YOUR-NAME --owner 01-system-architect
```

Inspect the mapping, loss report, unsupported files, and quarantined state before the second command.
The original source remains unchanged. Old approvals, keys, and pending graphs do not become authority.
Imported documents require new review. Resume refuses changed source or target bytes.
Use resume before the target is used by the core engine. Preserve a changed or used target for separate recovery.
