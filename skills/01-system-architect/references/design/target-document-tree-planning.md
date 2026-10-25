# Plan architecture documents

Read the current marker, registered sources, accepted baseline, and effective grant.
Derive the target document tree from an independent, reconciled source inventory and the
requested coverage/depth policy (`maximal` | `standard` | `minimal` | `seed`).
The artifact registry in `sdd-workspace.yml` controls paths and owners. A template or
catalog is structural guidance, never a substitute for source-grounded derivation.

## Target tree derivation algorithm

Execute these steps in order before authoring specification pages:

1. **Freeze intake basis:** Identify all source roots and exclusions, compute SHA-256 digests and revisions, and record read/extraction status (`unread`, `partial`, `read`, `reconciled`) alongside user intent (`maximal` coverage/depth) and the accepted baseline.
2. **Extract and reconcile all source items:** Harvest every section, heading, normative clause, identifier, table, state machine, E2E flow, exception code, configuration parameter, appendix/GAP closure item, frontend design/code artifact, ADR decision, and acceptance finding. Reconcile extraction counts against the source files; any unread or truncated section is an explicit gap.
3. **Derive the concern graph:** Map each source item (`source_id`, revision, section/span, authority kind) to one or more architectural concerns across modules, shared contracts, frontend boundaries, cross-cutting mechanisms, platform integrations, system views, and delivery/verification.
4. **Evaluate applicability:** For each concern and catalog family (`workspace-skeleton-maximal.md`), record whether it is applicable (`covered` or `gap`), explicitly `deferred` with authority and review trigger, or `not_applicable` with source rationale. Preserve negative constraints (such as technologies deferred from MVP) as constraints rather than inventing subsystems.
5. **Assign canonical ownership and depth contract:** Assign one canonical fact owner and specify the required design depth dimensions (authority, trigger/scope, exact contract, algorithm/state/guards, consistency/concurrency, failure/recovery, config/defaults/units, observability/verification, and consumers).
6. **Split independent mechanisms and contracts:** Give each independent bounded context, module concern (`api`, `events`, `clients`, `data`, `mechanisms`, `security`, `observability`, `resilience`), ADR decision, runtime scenario, state machine, fitness function, and exception domain its own planned node when merging would blur witnesses or couple distinct lifecycles.
7. **Merge only when coverage and depth are preserved:** Consolidate nodes only after verifying that every source obligation, canonical owner, anchor, and depth witness remains intact and within review packet budgets.
8. **Validate source accounting and plan completeness:** Ensure 100% of extracted source items map to concerns and every applicable concern maps to a planned node with a depth contract.
9. **Render the plan and coverage matrix:** Record the target tree, source-to-concern-to-node coverage matrix, split/merge rationale, omissions/deferrals, missing grants, and blockers.
10. **Author in bounded candidates:** Execute authoring in waves or task batches according to execution budget without shrinking the planned target tree.

## Harvest dimensions by source type

| Source Type | Required Harvest Dimensions |
|---|---|
| SRS / Requirements | FR, NFR, BR, roles/permissions, entities/schemas, state machines/guards, exceptions (`EX-*`), E2E flows, dynamic config/defaults/units, deployment modes, RTM, roadmap, appendix/GAP closures |
| Frontend Design & Code | Information architecture, routes/views, components, state stores, definition forms/actions, user journeys, capabilities, `service`/`stream` API adapters, optimistic/offline/reconnect behavior, accessibility, performance budgets |
| Tech Stack & ADRs | Accepted/proposed/deferred decisions (`ADR-*`), module boundaries, runtime planes, version policies, per-technology integration contracts, configuration, operational consequences, rollout/rollback |
| Acceptance & Evidence | Gate verdicts, findings (`FND-*`), backend dependencies (`BE-*`), accepted exceptions, evidence revisions, and re-test plans |

When the input already contains an ADR document or a frontend/backend codebase, decompose those decisions and application modules into their canonical architectural nodes (`05-governance/decisions/NNNN-*.md`, `02-domains/...`, `_shared-contracts/...`). Never skip them under the excuse of "avoiding source duplication".

## Registry proposals and invalidation

Propose registry updates through the core configuration capability. Registration must identify each artifact's kind, path, and owner. If the current grant does not cover a required subtree, keep the planned nodes visible in the plan and report the missing grant as a blocker rather than dropping the concern.

A new or changed source, scope, grant, or coverage policy invalidates the affected plan basis (`basis_digest`). Inspect the delta, mark affected plan nodes and reviews stale, and update through an isolated proposal. A passing structural check is not human approval of a document plan.
