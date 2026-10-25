# Architecture method and preservation contract

Read this guide before authoring or refactoring. Apply it to current core candidates and exact source revisions.

## Contents

- Intake and authority
- Preserve existing normative detail (R1–R6)
- Maximal coverage, rule precedence, and selective documents
- Topology and context boundaries (R7–R10)
- Mechanisms and technology decisions
- Delegation and request resolution
- Derived views and delivery
- Change, review and handoff

## Intake and authority

Read confirmed clauses, relevant accepted specifications and decisions. If intent is materially ambiguous, send the question to the clarifier. An unambiguous brief can go directly to architecture, and must undergo full source intake and obligation extraction.

Freeze the intake manifest and hash every in-scope source file before planning (`unread`, `partial`, `read`, `reconciled`). Extract all headings, normative clauses, identifiers, tables, diagrams/specs, appendices, GAP closure items, acceptance findings, and existing frontend/backend code or ADR documents, including normative sections that lack explicit IDs. Classify each extracted source item by authority: requirement, accepted decision, proposed decision, design intent, observed code, or measured acceptance evidence.

Trace each derived `REQ-*` or concern to `CLR-*`, a source span, or an approved change. Never use the generated pages or registered obligations alone as the denominator of completeness (`DT-01`). Every source item in the universe `U` must carry an explicit disposition:

- `covered`: assigned to a canonical owner artifact/clause with substantive body witnesses and passing depth checks.
- `gap`: applicable and required by source, but missing design, missing witness, or conflicting evidence.
- `deferred`: postponed by an authorized decision with explicit owner and review trigger (accounted, not covered).
- `not_applicable`: excluded with source-grounded rationale and applicability evidence.

Report six metrics separately: **accounting completeness**, **design coverage**, **critical coverage**, **depth completeness**, **exclusion/defer count**, and **source intake completeness**.

Every normative assertion follows one of three routes:

- **Quoted:** reproduce the authoritative identifier/value and cite source/revision.
- **Assumed:** mark `ASM-*`, owner and falsifiable reversal trigger, including at the point of use.
- **Decided:** cite the actual ADR and decision status. A proposed ADR is not approved authority.

A capacity number needs a population/workload model and its inputs. If the population is unknown, record the question instead of choosing a plausible round number. Preserve that status when a number is reused downstream.

## Preserve existing normative detail (R1–R6)

Before changing a document set, produce a preservation inventory that includes:

- endpoint paths, methods, headers and status/error codes;
- property/configuration keys, types, defaults, units, required/optional fields and null semantics;
- entity/table/index/storage names, schema fields and enum values;
- class/interface/method/SPI names and normative algorithms or code snippets;
- cron schedules, timeout/retention/rate limits, guards and state transitions;
- deployment zones, cross-zone contracts, operational procedures and delivery constraints.

For each fact identify the source, its revision and canonical target owner. Keep the exact spelling/value unless the change is explicitly authorized. A literal search confirms that an exact identifier survived; it does not prove its surrounding semantics survived. Review that the same conditions and guarantees still apply.

Keep one whole-system topology with deployment zones, components in each and cross-zone contracts by stable ID. If the inherited behavior needs a mechanism page, create one rather than hiding it in a summary table. Preserve normative snippets; “code is illustrative” is not a safe assumption.

Do not drop roadmaps, recovery procedures, frontend design/code contracts, acceptance findings, or ops material merely because another skill owns their final form or because a source file already exists. Preserve them in the appropriate owned artifact or return a handoff request with source/target/owner. Every inventory item ends as preserved, intentionally changed with authority, or an unresolved gap.

## Maximal coverage, rule precedence, and selective documents

Keep three orthogonal dimensions separate:

1. **Coverage and depth policy (`maximal` | `standard` | `minimal` | `seed`):** governs which concerns from the source inventory must be covered and to what design depth.
2. **Layout and catalog profile:** provides path conventions and reference families (`design/workspace-skeleton-maximal.md`) without dropping concerns that lack a pre-named slot.
3. **Execution budget:** governs task batching, turn limits, and review packet windows. Never shrink the target document tree to fit a single turn or review call.

Enforce this strict rule precedence:

1. Granted write scope and preservation of source truth and accepted decisions.
2. User intent for `maximal` coverage, scope, and implementation depth.
3. Workspace coverage/depth contract (`document_coverage` in `sdd-workspace.yml`) and source traceability.
4. Applicability evaluation, single canonical fact ownership, anti-duplication, and content-based split/merge rules.
5. KISS for clear prose, navigation, and removing true redundancy **after** coverage and depth are preserved.

Read `design/document-tree-primer.md`, `design/target-document-tree-planning.md`, and `design/workspace-skeleton-maximal.md` when planning document navigation. In core mode, `sdd-workspace.yml` is the single configuration authority; catalog documents provide structural and family checklists without creating a competing state ledger.

**Split/Merge rules:** Split a concern into its own dedicated page whenever:
- a mechanism or contract has an independent lifecycle, owner, version, or consumer set;
- a state machine or algorithm requires dedicated guards, error transitions, retry/idempotency, recovery, or invariants;
- a technology dependency requires specific integration, configuration, failure handling, and operational design;
- a frontend or end-to-end journey traverses UI -> API -> backend -> workflow -> evidence boundaries;
- merging would obscure body witnesses, exceed review packet bounds, or couple unrelated changes.

Merge pages only when all source obligations, canonical ownership, stable anchors, and required depth dimensions are preserved. Never collapse multiple bounded contexts, 19 ADRs, 51 entities, 8 runtime scenarios, or 27 exception codes into flat summary tables merely to reduce file count. Conversely, never create empty optional pages or clone identical facts across files as synthetic padding.

## Topology and context boundaries (R7–R10)

Respect the selected workspace path contract. In the framework's D-1 layout, delegated ownership is `architecture/02-domains/<cluster>/<submodule>/<skill>/`; do not create a second root per context that contradicts it. Preserve independent responsibilities and contracts across contexts even if they share a folder or deployable.

When the source includes frontend applications or design specifications (routes, views, components, state stores, definition forms, user journeys, stream/API bindings, and acceptance findings), model each frontend application as an explicit architectural scope and map the full chain:
`actor/action -> route/view/state -> capability -> API/message contract -> backend mechanism -> success/error/unknown outcome -> evidence/test`.

Distinguish logical boundaries from runtime units. A C4 container must run, listen or store; an overview page, navigation folder or shared-contract directory is not a deployed container. Include external systems and trust/network zones.

Choose depth from actual mechanisms and risks. Rich configuration, extension points and algorithms need their details documented even in a one-context system. A broad system does not justify shallow duplicate pages.

## Mechanisms and technology decisions

For each applicable mechanism specify all nine depth witness dimensions (or state why a dimension is not applicable):

1. requirement/decision authority, purpose, boundary, and canonical owner;
2. trigger, actor, inputs, preconditions, and permission/tenant scope;
3. exact contract: API/message/schema/command/result and versioning;
4. algorithm or normative sequence, states, guards, invariants, and transitions;
5. side effects, consistency/transaction boundary, ordering, and concurrency;
6. failure and unknown outcomes, cancellation, retry/idempotency, and recovery;
7. configuration keys, defaults, units, limits, and source or `UNKNOWN` status;
8. observable evidence, audit trail, and verification scenarios;
9. consumers and dependent artifacts that must update on change.

Do not add retry, queues, circuit breakers or compensating operations by rote. Choose the behavior justified by the system and explain the tradeoff. A non-idempotent operation cannot acquire safe retry by a sentence saying “exponential backoff”.

For technology selection, compare credible alternatives against requirement-derived criteria, constraints, cost/licensing, operability, team capability and ecosystem. State the weighting rationale and uncertainty. Produce a scorecard when useful, without inventing benchmark numbers. An ADR records context, considered alternatives, chosen option, consequences, rejected tradeoffs and reversal triggers. Keep accepted, proposed, and deferred decisions distinct; technologies explicitly deferred or excluded by source (such as Kafka or external billing in MVP) remain deferred constraints rather than mandatory subsystems.

## Delegation and request resolution

Before delegation read `design/child-skill-delegation.md` for the legacy host, and the selected child's actual skill and contract. Use the router verdict and installed slot state. An empty skill slot or ambiguous route produces a gap; it is not permission to invent a specialist's expertise.

Pass one scoped task: module, chosen owner, source IDs and revisions, permitted paths, required context, expected output and validation evidence. Shared strategy/contracts and cross-context decisions remain with their canonical owner. A child must return a request instead of writing another owner's files.

Resolve requests for ADR, contract, handoff, requirement, taxonomy or classification. Deduplicate by kind, motivation and blocked stable IDs. Record request identity, status, decision/owner, touched artifacts and the route to resume work. Reuse an existing decision only if its scope and revision still apply.

Host orchestration chooses sequencing/parallelism from ownership and dependencies. Do not encode a second scheduler or status ledger in the skill.

## Derived views and delivery

Write source specifications before diagrams. Diagram requests carry source paths/revisions, stakeholder concern, viewpoint, element traceability and ownership. Request C4/UML skills only when installed and applicable; a missing optional visual is a visible gap, not an invented rendering.

Derived views cite `Source Specifications`, `Upstream Coverage` and element mappings. Regenerate them from registered sources after changes. A generated diagram cannot serve as authority for rewriting its input.

Keep delivery slices aligned to value and dependency order. Connect requirements to designs, API/data contracts, GAP closures, acceptance findings, and intended verification in traceability. Mark code/runtime performance as unverified until real execution evidence exists. Complete navigation last.

## Change, review and handoff

For an existing baseline, read the authorized change and preserve existing stable IDs. Inspect old and new consumers before delete, rename, split or merge; record lineage and replacement obligations. A coordinated rewrite that weakens an accepted guarantee still requires a human change decision.

Submit scoped edits using the selected lifecycle. Keep author task completion separate from review, risk acceptance and baseline acceptance. Report an executed check only with its actual command/result and the proposition it settles. Structural validation does not prove a latency SLO or deployment safety.

Hand off the exact snapshot/change, coverage and depth metrics, preservation misses, findings, unresolved assumptions, stale/deferred work and ownership. The critic owns review findings. The human owns approval and residual risk. Do not write acceptance claims into self-audit material.

## Repeated pages and canonical ownership

Synthetic padding is forbidden. Keep one fact on one authoritative owner page;
other pages link to that owner and explain their own role. Before expanding a
repeated layout, prototype repeated page roles with representative source facts.
Run `architect_runtime.py --bootstrap sdd check <workspace> --full` for registered page contracts,
then inspect semantic duplication and missing role content. Identical headings
are permitted; copied domain facts without a real distinct role are not. In core
mode enforce registered identities, obligations, depth witnesses, and graph review rather than
using a legacy page-shape gate as semantic approval.
