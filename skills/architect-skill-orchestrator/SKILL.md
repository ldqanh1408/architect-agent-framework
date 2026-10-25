---
name: architect-skill-orchestrator
description: "Use when an unclassified architecture request must be routed through this library by requested decision/deliverable, authority, ownership, dependencies, and evidence to the smallest compatible domain and task leaves before their bodies are loaded. Produces a deterministic route verdict, candidate rationale, ambiguity/blocker record, typed leaf handoffs, dependency order, and progressive load plan; it owns metadata-only coordination, not architecture artifacts. Do not use when authoritative leaf IDs are already resolved, or merely to perform architecture, write a design/specification/diagram/ADR, plan a generic task, search a catalog, spawn agents, execute a workflow, choose tools, or route from titles/keywords."
license: MIT
compatibility: "Agent Skills clients; filesystem read access to compact skill metadata and selected SKILL.md leaves; optional deterministic router implementation when supplied"
allowed-tools: "terminal read_file"
version: 2.1.0
author: Architect Agent Framework
metadata:
  hermes:
    tags: [architecture-routing, metadata-only, ownership, typed-handoffs, progressive-disclosure]
---

# Architect Skill Orchestrator

## Overview

`architect-skill-orchestrator` is the metadata-only entry point for unclassified architecture requests. It resolves the requested decision and deliverable, accountable authority, artifact ownership, required dependencies, and evidence obligations; selects the smallest compatible leaves; and emits a progressive load and handoff plan. It does not perform architecture, author artifacts, execute tasks, spawn agents, or infer a route from names.

The selected domain and task leaves own intake, decisions, writes, execution, verification, blockers, and completion. A router verdict is coordination evidence only; it is not domain authority or proof that work happened.

## When to Use

Use when:

- the request is architectural but exact authoritative leaf IDs are not supplied;
- multiple plausible owners overlap and the requested decision/deliverable must discriminate them;
- a domain authority and a narrow task procedure must be paired without transferring ownership;
- prerequisite producer/consumer contracts and execution order must be identified before loading bodies;
- ambiguity, missing authority, incompatible ownership, unavailable packages, or stale metadata must block deterministically;
- context cost requires bounded metadata discovery and smallest-leaf progressive loading;
- a reroute must preserve the prior verdict, evidence, completed effects, and invalidated handoffs.

Do not use when authoritative leaf IDs and compatibility are already resolved. Do not use for generic planning, catalog browsing, skill recommendation, agent delegation, workflow execution, tool selection, or any architecture deliverable itself.

## Routing Authority and Boundaries

The orchestrator may read compact routing metadata and only the selected `SKILL.md` leaves after admission. It writes no architecture artifact and cannot approve, override, merge, or reconstruct leaf decisions.

It owns:

- request classification by decision, deliverable, authority, ownership, dependency, evidence, and lifecycle scope;
- candidate comparison, compatibility, ambiguity, blocker, and no-route semantics;
- minimum compatible leaf-set selection and progressive load planning;
- typed routing context, producer-consumer handoffs, execution dependency order, and reroute records;
- metadata identity, revision, provenance, freshness, and route reproducibility requirements.

It delegates:

- business intent, priorities, acceptance, and risk decisions to their authorities;
- domain models, architecture choices, contracts, and artifact roots to domain leaves;
- authoring, analysis, implementation, review, validation, migration, and operation to task leaves;
- task/agent scheduling, retries, budgets, concurrency, and execution state to workflow/execution owners;
- catalog maintenance, package installation, metadata publication, and compatibility declarations to library governance/tooling;
- final outcome verification to the selected leaves and accountable consumer.

## Required Distinctions

- **Title/keyword similarity** is discovery evidence, not routing authority.
- **Catalog membership** proves discoverability, not applicability, compatibility, availability, or quality.
- **Top score/rank** does not prove one owner; score semantics and discriminators must be explicit.
- **Selected route** does not prove leaf bodies were loaded, task executed, artifact written, or outcome achieved.
- **Compatible pair** does not prove required producer evidence exists or is fresh.
- **Loaded skill** does not grant write authority beyond its owned root or current request.
- **Domain leaf** owns enduring architecture decisions; **task leaf** owns the bounded procedure/deliverable action.
- **Dependency** differs from a co-owner; a producer contract does not transfer its decision authority to a consumer.
- **Ambiguous** means multiple materially different routes remain; **blocked** means required authority/evidence/package is absent; **no-route** means the admitted library has no suitable owner.
- **Successful prior combination** is historical evidence, not a default route for a changed request.

## Routing Evidence Tuple

Bind every verdict to:

`{request/correlation ID, exact request revision, requested decision/deliverable/artifact/lifecycle scope, declared and unresolved authorities/owners, success/non-goal constraints, candidate leaf stable IDs/kinds/packages/metadata revisions, owned roots and read/write boundaries, positive/negative routing predicates, required/produced handoff types, compatibility relation and source revision, dependency graph, required evidence identities/freshness, candidate rationale/discriminators/rejections, selected/ambiguous/blocked/no-route status, load-plan order and body digests, execution consumer, prior verdict/supersession/invalidation, evaluator/tool/config/time}`.

Keep discovered, candidate, compatible, selected, loaded, handed-off, executing, verified, completed, blocked, ambiguous, superseded, and retired states separate.

## Blocking Conditions

Each condition sits in exactly one column. A **code** row is caught by `scripts/route.py` itself and pinned by a deterministic test in the framework's `tests/test_skill_router.py`. An **agent** row needs judgement the router does not have; its adversarial scenario stays `evidence_class: contract-only` until a live run executes it.

| # | Block when | Code catches (`scripts/route.py`) | Only the agent catches |
|---|---|---|---|
| 1 | the requested decision or deliverable is absent | `blocked`, exit 2 — `test_blocking_1_request_without_a_decision_blocks` | — |
| 2 | business/domain authority or artifact owner is unresolved | — | `evaluations/agent-only/authority-unresolved.yml` |
| 3 | candidates differ materially and discriminating evidence is missing | `ambiguous`, exit 2 — `test_blocking_3_tied_candidates_are_ambiguous` | — |
| 4 | a candidate routes only by title/tag/vendor/framework | — | `evaluations/agent-only/title-only-route.yml` |
| 5 | domain/task ownership overlaps without precedence | — | `evaluations/agent-only/ownership-overlap.yml` |
| 6 | compatibility or required handoff types are absent | `blocked`, exit 2 — `test_blocking_6_incompatible_pair_blocks` | — |
| 7 | selected package/body/revision is unavailable | `blocked`, exit 1 — `test_blocking_7_unknown_id_blocks` | — |
| 8 | metadata is stale or conflicts with leaf bodies | — | `evaluations/agent-only/stale-metadata.yml` |
| 9 | dependencies cycle | — | `evaluations/agent-only/dependency-cycle.yml` |
| 10 | a consumer would reconstruct missing producer decisions | — | `evaluations/agent-only/reconstructed-producer.yml` |
| 11 | a route would require loading the full library | — | `evaluations/agent-only/full-library-load.yml` |
| 12 | success is inferred from route score, catalog hit, skill load, agent launch, command success, artifact presence, or prior combination alone | — | `evaluations/agent-only/inferred-success.yml` |

Return a stable verdict with request ID, status, candidate IDs, exact discriminator or missing evidence, responsible owner, safe non-execution behavior, invalidated prior route, and resume condition.

## Module Ownership Policy

`route` picks an execution point — a (domain, task) pair. A module charter asks a narrower question: which domain skill **owns** a module. `python scripts/route.py owner --intent "<module intent>"` answers it with the router's `select_module_owner`, the same function `charter build` calls, so the pipeline and this skill cannot disagree on `status`, `selected_domain` or `resolved_by`. The first rule that applies decides:

| `resolved_by` | Applies when | Verdict |
|---|---|---|
| `domain-rank` | the domain ranking alone has a positive top score strictly above the second | `selected`, even where `route` says `ambiguous`; `route`'s status is kept as `router_status` |
| `domain-rank-tie` | two or more domains share the top positive score | `ambiguous`: the tie is named and no owner is chosen |
| `architect-tiebreak` | `--owner <id> --owner-reason "<why>"` names one of the domains tied under `domain-rank-tie` | `selected`, with `tied` and `owner_reason` recorded |

When no domain scores above 0 the router's own verdict stands, and it cannot be `selected`: `route` proposes a candidate only for a domain that scores above 0. The two rules that once covered that case, `router` and `domain-unanimity`, fired 0 times over the catalogue's 305 skill descriptions and were removed. An `--owner` outside the tie, without a reason, or against a clear `domain-rank` selection is refused: the verdict carries `refusal` and the command exits 2. Exit 0 means `selected` with no refusal.

## Minimum-Sufficient Routing Decision

Compare direct execution of already-authoritative IDs, one domain leaf, one task leaf, one domain-plus-task pair, a bounded prerequisite chain, clarification, blocked, or no-route. Select the smallest set that covers one coherent requested decision/deliverable while preserving every authority boundary. Do not default to exactly one domain plus one task, four files, a matrix, top-1 ranking, confidence thresholds, interview questions, broad categories, past combinations, multi-agent execution, parallelism, memory, fallback skills, or vendor tooling.

## Workflow

1. **Admit the routing request.** Capture exact request, architecture intent, decision/deliverable, consumer, lifecycle point, success, and non-goals. Done when routing—not execution or generic recommendation—is the requested output.
2. **Resolve declared authority.** Identify business, domain, artifact, task, evidence, and acceptance owners already supplied. Done when the router cannot silently assign authority.
3. **Classify the deliverable.** Distinguish architecture decision/system contract from analysis, authoring, implementation, review, migration, operation, or other task action. Done when domain and task roles cannot be conflated.
4. **Bound the subject.** Record product/system/component/artifact, current/target state, lifecycle, affected owners, and exclusions. Done when adjacent scopes cannot trigger unrelated leaves.
5. **Load bounded metadata.** Read only the smallest relevant metadata shard with stable IDs, kinds, descriptions, boundaries, handoffs, compatibility, revision, and provenance. Done when no leaf body or unrelated catalog shard is loaded.
6. **Check metadata freshness.** Verify registry revision, package identity, leaf existence, ownership root, and compatibility source. Done when stale or missing metadata blocks rather than falls back.
7. **Generate candidates.** Use decision/deliverable, authority, ownership, scope, anti-triggers, and typed handoffs. Done when every candidate has positive evidence beyond title/keywords.
8. **Apply anti-routing.** Reject leaves whose owned decision, artifact, lifecycle, scale, or task boundary does not match. Done when each plausible false positive has an explicit reason.
9. **Resolve domain authority.** Select the leaf owning the enduring architecture decision or return ambiguity/blocker. Done when no task leaf becomes domain owner.
10. **Resolve task procedure.** Select only the leaf owning the requested bounded action when needed. Done when no domain leaf absorbs execution procedure.
11. **Check ownership collisions.** Compare write roots, decision rights, artifact identities, and precedence. Done when selected leaves have one writer per artifact and no hidden co-ownership.
12. **Check typed compatibility.** Match producer outputs, consumer inputs, versions, required evidence, failure/stale behavior, and acceptance oracles. Done when name-level pairing is insufficient.
13. **Build dependency graph.** Order prerequisite authority and evidence producers before consumers; detect cycles and optional branches. Done when order follows contracts rather than a generic workflow.
14. **Minimize the leaf set.** Remove redundant, overlapping, speculative, advisory, or downstream leaves. Done when every retained leaf is necessary for the admitted deliverable.
15. **Resolve ambiguity.** Compare materially different candidates using request-traceable discriminators; do not break ties by score or popularity. Done when one route is justified or status is `ambiguous`.
16. **Resolve blockers and no-route.** Separate missing evidence/authority/package from absence of any suitable library owner. Done when status and resume owner are precise.
17. **Emit route verdict.** Record full tuple, selected/rejected candidates, rationale, authority, compatibility, and limitations. Done when another evaluator can reproduce the decision.
18. **Emit progressive load plan.** Order selected leaf bodies first and only branch-specific material they explicitly require later. Done when no unselected body/reference enters context.
19. **Load and reconcile selected bodies.** Confirm metadata against exact selected `SKILL.md` revisions; leaf body wins for its current contract. Done when mismatch blocks and invalidates the route.
20. **Emit typed handoffs.** Pass request scope, authority, producer evidence, dependencies, write boundaries, unknowns, and oracles without reconstructing leaf decisions. Done when each consumer can fail closed.
21. **Transfer execution ownership.** Hand control to selected leaves or an execution owner; the orchestrator performs no leaf action. Done when writes and verification remain with canonical owners.
22. **Observe route outcomes.** Receive leaf status/evidence references, not self-attested summaries, and distinguish routing quality from task success. Done when selection can be evaluated without claiming the outcome.
23. **Handle reroute and resume.** Compare request, metadata, leaf, authority, evidence, and completion changes; invalidate affected handoffs and preserve completed effects. Done when retries do not duplicate work or erase provenance.
24. **Maintain routing quality.** Analyze ambiguities, false routes, no-routes, overrides, context cost, stale metadata, and downstream failures with attribution limits. Done when popularity or success rate alone cannot rewrite policy.
25. **Retire routing metadata.** Reconcile removed/renamed leaves, aliases, compatibility edges, active plans, cached verdicts, and links. Done when obsolete metadata cannot route silently.

## Typed Outputs and Handoffs

- `architecture_route_request`: request/subject IDs, decision/deliverable, lifecycle, authorities, constraints, success/non-goals, evidence and unknowns.
- `architecture_route_verdict`: status, candidates, selected leaves, rationale/discriminators, ownership, compatibility, metadata revisions and limitations.
- `architecture_load_plan`: exact leaf IDs/paths/digests, order, load condition, context budget and stop rules.
- `architecture_dependency_plan`: producer/consumer leaf IDs, handoff types/versions, required evidence, order, optionality and cycle result.
- `architecture_leaf_handoff`: consumer, owned decision/action, scope, authority, inputs/evidence, writable root, blockers and acceptance oracle.
- `architecture_reroute_record`: prior/new tuples, trigger, preserved effects, invalidated handoffs, supersession and resume point.
- `architecture_route_verification`: reproduced verdict, metadata/body reconciliation, context loaded, route outcome evidence and limitations.

Every payload includes stable ID, producer, consumer/owner, request/leaf/metadata/evidence revisions, assumptions, unknowns, stale/failure behavior, and acceptance oracle.

## Resume Semantics

A blocker records the request revision, candidate and selected leaf IDs, missing authority/evidence/package, last accepted metadata/body/compatibility revisions, dependency/load/handoff state, already completed leaf effects and evidence IDs, safe non-execution state, invalidated route, and resume condition. On resume, rediscover current metadata and exact leaf bodies, compare the full tuple, preserve valid completed effects, invalidate stale handoffs, recompute only affected candidates/dependencies, and never relaunch or rewrite work merely because routing restarted.

## Common Pitfalls

1. Routing from names, descriptions, tags, vendors, frameworks, or incidental keywords alone.
2. Loading all leaf bodies before selection and causing context rot.
3. Treating catalog rank, confidence score, or prior popularity as authority.
4. Forcing exactly one domain/task pair when a direct leaf, dependency chain, ambiguity, or no-route is correct.
5. Letting the orchestrator perform architecture, write artifacts, execute workflows, or spawn agents.
6. Assigning authority from a compatible handoff or transferring producer decisions to consumers.
7. Recommending overlapping leaves without one owner, precedence, or typed boundaries.
8. Using fallback skills to hide unavailable packages, missing authority, or absent evidence.
9. Calling a loaded route executed, verified, completed, or effective.
10. Persisting “successful combinations” as future defaults without request/evidence comparison.
11. Measuring quality only by route acceptance, task success, token reduction, or lack of complaints.
12. Retiring leaves without aliases, active-plan invalidation, compatibility cleanup, and cached-verdict reconciliation.

## Open-Source Research Basis

Recorded in `references/research-basis.md`: the repositories inspected for this skill, the concepts adapted from each, and the ones deliberately rejected. Load it when auditing provenance or revising the skill's boundaries; it is not required to execute the skill.

## Verification Checklist

- [ ] Trigger is an unclassified architecture routing decision; known authoritative IDs and non-routing tasks bypass this skill
- [ ] Request decision/deliverable, subject/lifecycle, authorities, success/non-goals, evidence, and unknowns resolve
- [ ] Candidates are justified by ownership, anti-routing, compatibility, and handoffs—not titles, keywords, scores, or history
- [ ] Domain decision authority, task procedure, dependencies, and execution ownership remain distinct
- [ ] Exact request/candidate/metadata/compatibility/evidence/load-plan tuple identifies the verdict
- [ ] Selected, loaded, executing, verified, completed, ambiguous, blocked, no-route and superseded states remain separate
- [ ] Minimum leaf set, one writer per artifact, typed producer-consumer compatibility, and acyclic dependency order are explicit
- [ ] No architecture artifact, generic plan, agent delegation, workflow execution, or leaf verification is owned here
- [ ] Progressive load excludes unselected bodies and selected-body mismatch invalidates metadata routing
- [ ] Reroute preserves effects/provenance; retirement reconciles aliases, compatibility, active plans and cached verdicts
- [ ] No owner, route, compatibility, score, threshold, fallback, execution, success, or completion was invented
