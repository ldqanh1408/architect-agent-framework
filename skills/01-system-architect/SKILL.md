---
name: 01-system-architect
description: "SDD architecture: Author and refactor linked architecture, API, data and flow specifications from confirmed requirements. Use for document planning, technology tradeoffs, preservation of normative detail, delegated design and controlled CRUD of an accepted spec set."
---

# System Architect

## Required intake

Read [workflow-contract.yml](workflow-contract.yml) and [the domain method](references/architecture-method.md) **before every task**. The domain method is active guidance, not optional background. Read the complete authoritative brief and the relevant accepted baseline. Keep source facts, proposed assumptions and approved decisions distinct.

Use the current core lifecycle before writing:

- A `sdd-workspace.yml` marker selects [the core workflow](references/workflow-v2.md). A malformed marker is an error; never fall back to legacy.
- A workspace without that marker requires explicit initialization or migration. Do not run an old workflow.

Do not write `.sdd` records, approval records or engine/host ledgers yourself. Use the selected host service. Follow the granted ownership and scope; task completion is separate from review and human acceptance. Read required references even when only `SKILL.md` was loaded by the host.

## Work sequence

1. Freeze the source intake manifest, record source digests/revisions (`unread/partial/read/reconciled`), and extract an independent source obligation inventory before restructuring. Include headings, normative clauses, IDs, tables, diagrams/specs, appendices, GAP closures, acceptance findings, and existing frontend/backend code or ADR documents. Apply the preservation method R1–R6, including exact identifiers/defaults, normative snippets, topology and downstream material. Never use generated pages as the denominator of completeness.
2. Derive the concern graph and target document tree according to the requested coverage/depth policy (`maximal` whenever requested by the user or whenever the source spans >= 2 bounded contexts, >= 5 concerns in a context, >= 15 functional requirements, or >= 20 data entities). Keep **coverage/depth policy**, **layout/catalog profile**, and **execution budget** strictly separate: batching execution never reduces the target tree. Load [tree primer](references/design/document-tree-primer.md), [tree planning](references/design/target-document-tree-planning.md), and [maximal catalog guidance](references/design/workspace-skeleton-maximal.md). Split independent mechanisms, contracts, state machines, ADRs, runtime scenarios, exceptions, and frontend/backend bounded contexts into dedicated nodes; merge only after preserving full source coverage, canonical ownership, and implementation depth. KISS applies only to eliminate duplication after coverage and depth are preserved. The current registry and accepted grants govern artifact paths and ownership.
3. Establish canonical fact owners, bounded contexts, whole-system zones and contracts. Design mechanisms with exact guards, states, payloads, failure/recovery semantics, configuration defaults/units, and observable verification signals across all nine depth dimensions. Make technology scorecards and dedicated ADR files for real choices, preserving assumptions at their point of use.
4. Evaluate every shape below. Read [conditional architecture rules](references/design/conditional-rules.md) for matching shapes **before authoring**; state applicability and gaps. Treat remedies there as candidates whose relevance must be established, not permission to invent architecture.
5. When delegating, read [child delegation](references/design/child-skill-delegation.md), the routed skill and its actual contract. Confirm the slot is filled; pass source revisions, scope and expected outputs. Resolve requests for shared contracts/ADRs instead of allowing cross-owner writes. Host policy owns execution order.
6. Create a candidate through the selected lifecycle in bounded batches when needed. For CRUD inspect old and new consumers, preserve lineage, and update dependent witnesses. Do not silently weaken accepted guarantees.
7. Derive views after source specifications. Use [design templates](assets/design/) as applicable content shapes, not obligations to create empty files. Run deterministic, coverage/depth, and historical regression checks; obtain separate candidate review through `architect_candidate_review`. Route targeted language corrections through `architect_language_repair` and review the returned child candidate.
8. Present snapshot, diff, coverage/depth metrics (`covered`, `gap`, `deferred`, `not_applicable`), preservation misses and findings to the human. Accept only through the authorized host path, then report current/stale/due/unknown states honestly.

Synthetic padding is forbidden: one fact has one owner page, while multiple consumer views may reference that canonical clause. Before expanding a repeated tree, prototype repeated page roles and run `architect_runtime.py --bootstrap sdd check <workspace> --full` for the applicable registered artifact contracts; inspect findings before scaling. When dispatching parallel subagents across waves, cap concurrency at `max_parallel_workers <= 4` and assign micro-batches of 1-2 pages per turn after running `sdd probe-models`.

## Conditional reading router

| Rule | Read when |
|---|---|
| R11 | data is edited on both sides and must reconcile |
| R12 | one process handles user authentication and its own upstream credentials |
| R13 | an external system sends webhooks |
| R14 | an external agent/CLI can change user data |
| R15 | deployment configuration comes from files/environment |
| R16 | money, stock, points or another balance must reconcile |
| R17 | a client must operate while disconnected |
| R18 | an external API is critical to a user-visible flow |

## Workspace boundary

Use the active method and current output contract. Process old input only through the separate migration tool. Imported records grant no current approval.


Read [document-style.md](references/document-style.md) before writing or repairing English prose. Preserve protected facts and report incomplete style evidence.
