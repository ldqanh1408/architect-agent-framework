# Delegate architecture tasks

The system architect coordinates registered architecture artifacts. A router can
select a skill. The selected skill's accepted workspace grant controls its writes.
A catalog slot, tier label, or routing score does not establish ownership.

## Task preparation

Read the current source snapshot, accepted baseline, artifact registry, effective
grants, and selected skill instructions. Check that the required package exists.
An empty or unavailable skill slot cannot supply missing expertise. Record an
unresolved route, its evidence, and the next owner instead of inventing an output.

Keep each task focused on one bounded context or one shared contract. Declare:

- A stable task ID, skill ID, objective, and expected outputs.
- The exact source and base candidate revisions.
- Artifact IDs and paths permitted by the accepted grant.
- Upstream dependencies and shared contracts that the task reads.
- Human questions, remaining evidence gaps, and stop conditions.

The coordinator submits this plan through the current runtime. Its validated,
frozen form controls execution. Do not create another execution ledger. Agents
must not write engine state, lease records, or human decision records directly.

## Execution and observation

A person reads the proposed scope and answers the current questions in **Runs and
task gates**. They sign the required dispatch gate before the task can be claimed.
A notification timeout supplies no approval. A retry needs a fresh attempt and gate.

The runtime grants an attempt lease. Read the task's base candidate and exact input
revisions before authoring. Keep the lease private. Send heartbeats while working.
Submit operations through the task completion API. The runtime applies them to an
isolated candidate and checks the result. An agent's success summary does not
complete the task or accept its documents.

Observe tasks, dependencies, attempts, gates, write scope, and events in the
workbench. The current terminal interfaces are:

```bash
architect-runtime status WORKSPACE --json
architect-runtime observe WORKSPACE --after EVENT-CURSOR
```

Runtime limits and task dependencies control concurrency. Separate artifacts can
run concurrently when the plan and accepted grants permit it. Tasks that depend
on a shared contract wait for the checked upstream candidate. Serialize conflicting
writes with explicit dependencies. Do not invent a globally sequential child chain.

Cancellation, expired leases, a run deadline, or stale sources stop new commits.
The checked prefix remains readable. An unknown host-worker outcome remains UNKNOWN.
A screen pause stops updates; a scheduling pause stops new dispatch. Neither proves
that a running worker stopped. Host tool traces, nested usage, and cost remain
unavailable. Report this observation limit to the operator.

## Ownership and shared contracts

Each registered artifact has one owner. The architect owns only artifacts granted
to that skill. A child reads required upstream sources and works only on its granted
outputs. A required source outside the frozen read set needs a coordinator response.

Allocate stable API, message, entity, and flow IDs through registry proposals. Link
producers and consumers to those IDs. A child proposes a shared-contract change to
its registered owner. The owner authors an isolated proposal; the coordinator
updates downstream task dependencies and input revisions. A contract stub is a
visible gap until its required behavior and review evidence exist.

Common seams are design questions, not automatic routes:

| Producer and consumer | Contract to specify |
|---|---|
| User surface and backend | Endpoint behavior, input errors, auth, and user-visible states |
| Service and data pipeline | Message identity, schema, replay, ordering, and retention |
| Adapter and application | Vendor-neutral port, timeout outcomes, retries, and quotas |
| SDK and external consumer | Public API, compatibility, versioning, and deprecation |
| Observability and service | Signal schema, redaction, freshness, SLI, and alert owner |
| Extension and host | Permissions, inbox verification, deduplication, and lifecycle |

For an unlisted seam, identify both owners and the required contract. Missing
ownership or conflicting requirements blocks the affected task. Do not move another
owner's document or silently select a winning proposal.

## Resolve unclear boundaries

Use the primary consumer and lifecycle as evidence. Preserve the alternatives in
a registered decision artifact when the choice affects accepted scope.

- **Client SDK:** External consumers need a public API and compatibility contract.
  An internal vendor wrapper needs an integration port. A later public release needs
  a new reviewed ownership and versioning decision.
- **Design system:** Internal UI ownership covers tokens, accessibility, and component
  behavior. External consumers also need versioning and compatibility evidence.
  Keep one authoritative component contract and link each consuming surface.
- **ML inference:** Separate online endpoint behavior from training, model promotion,
  features, and drift controls. Link both through registered endpoint and model
  contracts. The routing catalog must support the actual workload.
- **RAG or LLM runtime:** Specify retrieval quality and freshness, provider invocation
  and cost controls, and the product endpoint's policy, isolation, and response states.
  Route each responsibility from its evidence, without assuming a tier covers all three.
- **Browser extension:** Specify the user experience together with host permissions
  and lifecycle. Use one owner for each artifact and shared contracts for the seams.
- **Service around a vendor SDK:** A deployed endpoint still needs service contracts.
  Vendor calls use the adapter port. A shared library needs its own consumer contract.

If evidence cannot resolve ownership, return a question with the alternatives,
impacts, and next owner. A person decides changes that require human authority.
Agents must not mark their own decision as human-approved.

## Child feedback

A child can request a decision, contract, handoff, requirement, concern definition,
or routing clarification. Return the request ID, requesting skill, source revision,
motivation, recommendation, alternatives, and affected artifact IDs. Keep unknowns
visible. The current task contract controls request and retry budgets; if none is
configured, request a bounded limit instead of assuming unlimited repair.

Send requirement changes to the requirement owner. Send shared-contract changes
to that artifact's owner. The coordinator can route a proposal; it cannot invent
acceptance or write beyond its own grant. An accepted response must identify its
exact evidence and current authority. Rejection records a reason and the permitted
next action. Repeated requests keep the same identity and refer to the prior response.

Conflicting shared-contract proposals need a reviewed decision with both alternatives
and their consumer impact. Resume downstream tasks from the resulting checked
candidate. A stale plan or signature needs replacement, not silent reuse.

## Select optional concerns

For each optional concern, record the evidence and a simple relevance score:

| Signal | Score |
|---|---|
| Brief explicitly requires the concern / related term / absent | 4 / 2 / 0 |
| Required upstream seam / weak implication / absent | 2 / 1 / 0 |
| Confirmed regulation requires it / may apply / absent | 2 / 1 / 0 |
| Confirmed scale requires it / suggests it / unknown | 2 / 1 / 0 |

A score of 6–10 supports a full page. A score of 3–5 supports a concise question
and gap record when relevant. A score of 0–2 supports omission with a reason.
Required source obligations and shared seams override this heuristic. Unverified
regulation or scale is an assumption, not confirmed evidence. Scores do not prove
coverage, permit empty placeholder pages, or qualify the candidate.

For an offline client with an explicit unreliable-network requirement and an
upstream idempotency seam, the score is at least 6: specify local durability,
replay, conflicts, and visible status. A stateless service with no migration
requirement can omit its own storage migration page and link the actual data owner.

## Derived views and final handoff

Select C4 or UML views from stakeholder questions. Register each derived artifact,
its owner, source IDs, and source revisions. A visual task reads those sources,
reports missing or stale evidence, and renders only its granted derived outputs.
It cannot invent architecture or change the source contract. Each view identifies
source specifications, covered elements, traceability, and unresolved gaps.

Run deterministic checks and historical regression on the candidate. Obtain
independent semantic review of the current source evidence. A task gate permits
execution. It does not accept documents. A person separately signs acceptance in
document review. The engine rechecks current authority before publication.

Return changed IDs, candidate ID, actual check and review results, affected
consumers, open questions, and next owners. Preserve INCOMPLETE, STALE, ERROR,
FAIL, and UNKNOWN. Passing checks alone never mean release readiness.
