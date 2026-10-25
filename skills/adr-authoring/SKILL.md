---
name: adr-authoring
description: "Author formal ADR for significant architectural decisions. Use when an authoritative architectural decision scope, drivers/constraints, considered options/evidence, accountable decision authority, lifecycle status and repository conventions must be rendered as one Architecture Decision Record: context, decision, rationale, consequences, relations, provenance and implementation/validation follow-up. Preserves historical truth without inventing a decision. Do not use for portfolio-level decision governance, choosing technology, drafting an RFC/proposal/design specification, recording meeting notes/changelogs/runbooks, or documenting an unapproved recommendation."
license: MIT
compatibility: "Agent Skills clients; filesystem read/write access; accepted decision, authority, evidence, lifecycle and repository conventions when supplied"
allowed-tools: "read_file search_files write_file terminal"
version: 2.1.0
author: Architect Agent Framework
metadata:
  hermes:
    tags: [architecture-task, documentation, adr, decision-record, historical-traceability]
---

# Architecture Decision Record Authoring Contract

## Overview

`adr-authoring` renders one already-framed, authority-backed architectural decision into a durable record whose then-current context, options, rationale, consequences and lifecycle can be reconstructed. It does not make or approve the decision.

A complete template, merged ADR, accepted status, linked ticket or implemented change alone does not prove decision authority, option quality, implementation, effectiveness or current validity.

## Fast Path

Take this route first. Leave it the moment a step cannot be answered from supplied authority.

1. **Check an authorized decision already exists.** If the engineering team is still evaluating alternatives or lacks decision authority, route to `architecture-decision-architect` to frame and resolve the choice first.
2. **Bound the record identity and repository scope.** Confirm the target file path, stable decision ID, title, and decider identity. Proceeding without a stable identifier causes duplicate or orphan records in the decision history.
3. **Freeze the decision context and drivers.** Record the exact problem statement, business drivers, constraints, and assumptions at the time the decision was made. Retrofitting current context into historical records corrupts the decision chronology.
4. **Capture screened options and explicit non-selections.** Document the considered alternatives, including rejected or deferred options, with their trade-offs. Omitting rejected options leaves future maintainers unable to understand why plausible alternatives were passed over.
5. **Record decision outcome and authority evidence.** State the authorized choice, its applicability scope, and the exact decision maker or approval revision. Recording an unapproved recommendation as accepted creates false authority.
6. **Detail consequences and follow-up obligations.** List positive, negative, and neutral impacts along with required implementation tasks. Failing to record negative consequences hides operational risks until production failures occur.
7. **Write the record under the owned root**, classify every claim, and run postflight.

Leave the fast path for `## Workflow` when the decision amends or supersedes a prior ADR, sensitive context requires explicit redaction boundaries, conflicting historical decision records exist in the repository, or follow-up implementation tasks span multiple team ownerships.

## Worked Example

**Intake.** "We decided to replace our IPC message bus with lock-free shared memory ring buffers for the LMAX order book distribution, but we need an ADR committed before code review."

**What this skill produces** (excerpt from `architecture/01-global-strategy/05-governance/decisions/adr-markdown-document.md`):

```markdown
## Decision Record

ID: [ADR-42]
Title: Shared Memory Ring Buffers for Order Book Distribution
Status: Accepted
Deciders: Lead Market Data Architect, Head of Low-Latency Engineering

## Context and Drivers
The current IPC sockets incur 4.2 microseconds of p99 latency during peak volatility events.
The sub-microsecond SLA [C-1] requires order book snapshots to reach market makers within 500 nanoseconds.

## Decision Outcome
Adopt POSIX lock-free shared memory (`shm_open`) with atomic ring buffer offsets for market data delivery to internal trading engines.

| Option | p99 Latency | Memory Overhead | Complexity | Status |
|--------|-------------|-----------------|------------|--------|
| Lock-free Shared Memory | 180 ns | 256 MB fixed pool | High | Selected |
| IPC Sockets (Unix Domain) | 4.2 us | Dynamic | Low | Rejected |
| ZeroMQ IPC | 12.5 us | Dynamic | Medium | Rejected |

Rationale [R-1]: Lock-free shared memory meets the 500ns SLA without memory allocation during market spikes. IPC sockets were rejected because kernel context switches introduce unacceptably high latency variance.

## Consequences
- Positive: Order book broadcast latency drops from 4.2 us to 180 ns.
- Negative: Processes must manage shared memory layout drift manually across binary releases.
```

**What it does not produce.** The C++ ring buffer implementation, microbenchmark code, or deployment scripts. Those belong to the execution task — this skill documents the accepted decision and its rationale.

## When to Use

Use when one consequential architectural decision is ready to be recorded under accepted repository and lifecycle conventions.

Do not use for decision-system governance, technology selection, RFC/proposal/specification, meeting notes, changelog/runbook or unapproved recommendation. ADR vocabulary alone is insufficient routing evidence.

## Ownership and Write Boundary

This task writes only `<output_root>/architecture/01-global-strategy/05-governance/decisions/adr-markdown-document.md`. Source decisions, approvals, implementation artifacts and repository ADRs remain read-only unless the delegated output root resolves to the authoritative ADR location.

This task owns faithful record composition, local validation and typed handoffs. Decision authorities own scope/status/outcome. Domain owners own option semantics. Repository owners define path/template/metadata. Delivery owners implement follow-up.

## Required Distinctions

- **Decision question/problem** is what requires resolution; **scope** sets affected systems/people/horizon/exclusions.
- **Proposal/recommendation** advocates an option; **decision** is an authorized outcome; **ADR** records it.
- ADR is not automatically an RFC, design doc, specification, meeting note, changelog, runbook, issue or implementation plan.
- RFC/proposal supports deliberation before authority acts; design/specification defines implementation/behavior; ADR preserves why an outcome was authorized.


- Decision identity binds stable ID, title, scope, owner/authority, repository/document release and aliases.
- Sequential number, UUID, date ID or slug are repository choices; next-number discovery cannot invent identity policy.


- Context records then-current problem/state, affected parties/systems, horizon and why a decision was needed.
- **Driver** motivates evaluation; **constraint** limits viable choices; **assumption** is treated as true with uncertainty; **unknown** remains unresolved.
- Principle, requirement, risk, incident, benchmark, prototype, cost, policy and stakeholder evidence retain source/revision/freshness.


- **Option** is a candidate outcome; no-change/defer/experiment can be options when authoritative and viable.
- “Considered” distinguishes identified, screened, investigated, viable, rejected, deferred and not-selected states.

- Options retain owners, scope, assumptions, evidence, trade-offs, reversibility and reason for exclusion/non-selection.

- **Decision outcome** states what was authorized, boundaries, applicability and effective conditions.
- **Rationale** explains decisive drivers/evidence/values; it is not a complete copy of analysis or timeless truth.
- Facts, observations, inferences, assumptions, preferences, dissent and authority statements remain distinguishable.

- **Trade-off** exchanges valued outcomes; **consequence** is expected impact/obligation/risk resulting from the decision.
- Positive, negative, neutral, deferred, displaced and unknown consequences can be recorded under local convention.


- Risk acceptance cannot be implied by accepted ADR status unless the named authority explicitly accepted it.
- Status is lifecycle metadata with repository-defined semantics and transition authority.
- Draft/proposed, under-review, accepted, rejected, deferred, deprecated, superseded, amended and retired are not universal required states.
- Accepted records the decision outcome under authority; it does not mean implemented, verified, effective or successful.

- Deprecated can mean discouraged/still present; superseded means replacement scope exists; retired can mean no longer applicable. Follow repository semantics.
- Status date, decision date, effective date, publication date and review date are distinct when applicable.

- Historical decision/context/rationale should not be silently rewritten to match current understanding.
- Corrections annotate factual errors with provenance; material change in outcome/scope/rationale usually requires amendment or successor under repository policy.

- **Amendment** changes/clarifies allowed portions; **supersession** replaces all or a bounded portion with a successor decision.

- Relations include predecessor/successor, supersedes/superseded-by, amends/amended-by, depends-on, conflicts-with, relates-to and implements/refines where supported.


- Chronology records what was known/authorized then; later evidence appears as annotation/review/successor, not retroactive rationale.
- Implementation plan/tasks/code/config/schema/infrastructure/tests/releases are follow-up artifacts, not mandatory ADR body detail.



- Follow-ups include stable artifact/task IDs, owner, responsibility, dependency and evidence expectation when supplied.
- Open questions and evidence gaps remain explicit; `[INVESTIGATE]`, TODO or decision request formatting follows repository convention.
- A load-bearing unresolved fact can block accepted ADR publication; unknowns are not hidden behind plausible prose.
- Decision authority includes accountable decider/body, mandate/delegation revision and evidence of status transition.


- Sensitive security/commercial/personnel context may need redaction/access controls while retaining enough rationale for authorized readers.

- Sources can include ADR/RFC/design docs/issues/PRs/meeting records/research/tests/benchmarks/incidents; each carries provenance/freshness.




- Title/Status/Context/Decision/Consequences is not universally sufficient; options, authority, evidence, relations or unknowns may be load-bearing.



- Duplicate ID/title/scope and conflicting active decisions require reconciliation rather than creating another record blindly.
- Search existing records for predecessors, overlapping scope, conflicts and established conventions before drafting.

- Evidence states include framed, drafted, proposed, reviewed, accepted/rejected/deferred, published, implemented, verified, effective, amended, superseded, deprecated and retired.
- Draft generation, schema validation, review approval, decision acceptance, implementation and outcome verification are separate states.
- Verification checks required local schema/metadata/links plus fidelity to authoritative decision/evidence, not style alone.
- **Completion** means ADR-authoring contract passed—not decision good, implementation complete or outcome successful.

## ADR Evidence Tuple

Bind claims to stable ADR/decision/question/scope/system/stakeholder/authority/driver/constraint/assumption/unknown/option/evidence/outcome/rationale/dissent/consequence/risk/relation/implementation/validation/review/source IDs; exact decision/repository/template/schema/evidence/authority revisions; framed/drafted/proposed/reviewed/accepted/rejected/deferred/published/implemented/verified/effective/amended/superseded/deprecated/retired states; dates/horizons, provenance, freshness, sensitivity and invalidation trigger.

Keep source decision, record draft, publication, lifecycle transition, implementation and realized outcome separate.

## Required Intake

Require decision stable ID/question/scope; accountable authority and status evidence; context/drivers/constraints/assumptions/unknowns; considered options/evidence and selected outcome/rationale; consequences/risks/dissent; dates/effective horizon; predecessors/relations/supersession; implementation/validation/follow-up references; repository path/title/number/template/metadata/index/link conventions; classification/access and freshness criteria.

Block rather than infer Nygard/MADR/Y-statement, Markdown/frontmatter, `docs/adr`, sequential zero-padded numbers, current date, proposed initial status, positive/negative/neutral sections, three options, immutable files, proposed→accepted→deprecated→superseded lifecycle, decision-makers, two reviewers, consensus, diagrams or index updates.

## Blocking Conditions

Block when no authorized decision exists; question/scope is ambiguous; authority/status/date is unsupported; context/drivers/constraints are fabricated; option set/evidence is asymmetric or missing; rationale/consequences are retrofitted; existing ADR conflicts/duplicates; repository conventions are unknown; supersession scope is unresolved; sensitive evidence cannot be handled; or completion relies on scaffold/template/PR/ticket/link alone.

Return stable IDs, blocked record/fields/relations, missing authority/evidence, safe draft-with-explicit-gaps/no-publication strategy, owner and exact resume condition.

## Minimum-Sufficient Record

Compare no record, lightweight decision note, ADR, RFC/proposal, design specification, meeting decision entry, amendment, annotation or successor ADR through consequence radius, longevity, reversibility and repository authority. Do not default to ADR for every technical change, MADR/Nygard, one file/decision, sequential numbering, Markdown/frontmatter, prescribed statuses/sections, immutable text or permanent retention.

## Workflow

1. **Frame authoring request.** Record decision/scope/audience/owner, objective, current/target state, non-goals and output boundary. Done when one authorized record—not decision making—is requested.
2. **Resolve authorities.** Identify decision/domain/risk, evidence, repository/documentation, implementation and validation owners. Done when no decider/status is invented.
3. **Freeze sources.** Inventory exact decision/repository/template/schema/evidence/authority revisions and freshness. Done when prose is reproducible.
4. **Discover conventions/history.** Inspect existing ADR IDs/paths/templates/statuses/metadata/index/relations and overlapping decisions. Done when identity/format is sourced.
5. **Define record identity.** Resolve stable ID/title/path/aliases/repository scope and collisions. Done when numbering cannot race or fabricate policy.
6. **Define question/scope.** State problem, affected systems/parties/horizon/exclusions/dependencies and owner. Done when independent choices are not hidden.
7. **Resolve status/chronology.** Record lifecycle status, authority evidence, decision/effective/publication/review dates as applicable. Done when draft/accepted/implemented differ.
8. **Compose context.** Record then-current state, drivers/constraints/principles/requirements/risks and why action was needed. Done when context is attributable.
9. **Record assumptions/unknowns.** Separate sourced assumptions, gaps, sensitivity and decision impact. Done when missing evidence stays visible.
10. **Record options.** Preserve identified/screened/viable/deferred/not-selected choices, no-change/experiment where authoritative, and owners. Done when no strawman is invented.
11. **Record option evidence.** Bind criteria/evidence/trade-offs/reversibility/uncertainty and exclusion reasons. Done when options are represented fairly.
12. **State decision outcome.** Record authorized choice, applicability/boundaries/effective conditions and authority. Done when recommendation cannot impersonate decision.
13. **State rationale/dissent.** Explain decisive evidence/values, rejected options, disagreement and uncertainty. Done when fact/inference/preference remain distinct.
14. **Record consequences/risks.** Capture expected benefits/harms/neutral/deferred/displaced/unknown effects, obligations and accepted risks only when sourced. Done when predictions cannot become outcomes.
15. **Record relations.** Link predecessor/successor/supersession/amendment/dependency/conflict/related records with direction/scope. Done when chronology stays navigable.
16. **Record follow-ups.** Link implementation/validation/rollback/review tasks/artifacts, owners and evidence expectations without inventing schedules. Done when ADR cannot equal implementation plan.
17. **Handle sensitivity.** Apply classification/redaction/access conventions while preserving provenance and unavailable-evidence markers. Done when rationale is safe and reconstructable.
18. **Render local schema.** Apply the accepted template/frontmatter/sections/filename/index/link style with explicit optional omissions. Done when format serves semantics.
19. **Validate semantic fidelity.** Compare every normative claim/status/reason/consequence against sources and mark unsupported gaps. Done when fluent prose cannot hallucinate history.
20. **Validate repository integrity.** Check schema/metadata/ID/path/title/date/status/links/duplicates/index only as required locally. Done when scaffold success is insufficient.
21. **Adversarially verify.** Test no authority, current-date substitution, favored-option bias, hidden unknown/dissent, status conflation, conflicting ADR and orphan supersession. Done when each yields evidence, gap or blocker.
22. **Review historical safety.** Ensure accepted history is not silently rewritten and corrections/amendments/successors follow policy. Done when chronology remains faithful.
23. **Issue typed handoffs.** Route decision/evidence, repository/lifecycle and implementation/validation gaps with exact resume conditions. Done when authoring cannot decide or implement.
24. **Publish owned artifact.** Write only resolved run-root record/index metadata, preserve digest/provenance and avoid unrelated docs. Done when output is minimum sufficient.
25. **Close or resume safely.** Validate identity/scope/authority/context/options/outcome/rationale/consequences/relations/follow-up evidence, blockers and freshness. Done when completion means ADR contract passed—not decision outcome.

## Typed Outputs and Handoffs

- `adr_authoring_scope`: ADR/decision/question/scope/audience/owner/repository/source IDs and exclusions.
- `adr_context_option_record`: drivers/constraints/assumptions/unknowns/options/evidence/viability/trade-off record.
- `adr_decision_consequence_record`: outcome/authority/rationale/dissent/consequence/risk/status/date evidence.
- `adr_relation_followup_record`: predecessor/successor/supersession/amendment/dependency/implementation/validation/review links.
- `adr_decision_evidence_handoff`: missing decision/scope/authority/status/options/evidence/rationale/consequence authority.
- `adr_repository_lifecycle_handoff`: missing ID/path/template/schema/metadata/date/status/relation/index/correction/sensitivity convention.
- `adr_implementation_validation_handoff`: missing implementation/fitness/test/review/rollback/follow-up artifact and owner.

Every payload includes stable ID, producer, consumer/owner, decision/repository/template/schema/evidence/authority/source revisions, assumptions, unknowns, stale behavior, sensitivity and acceptance oracle.

## Resume Semantics

A blocker records ADR/decision/question/status/authority/source/option/relation/repository/output/validation/evidence IDs, conflicts, missing fields, requests, owners and resume point. On resume compare all source/convention revisions; preserve stable identity, invalidate stale prose and never allocate duplicate IDs or silently overwrite accepted history.

## Open-Source Research Basis

Recorded in `references/research-basis.md`: the repositories inspected for this skill, the concepts adapted from each, and the ones deliberately rejected. Load it when auditing provenance or revising the skill's boundaries; it is not required to execute the skill.

## Verification Checklist

- [ ] Trigger requests one authority-backed ADR, not decision making
- [ ] Decision/domain/risk/evidence/repository/implementation owners resolve
- [ ] Decision/draft/publication/status/implementation/outcome states remain distinct
- [ ] Identity/context/options/evidence/rationale/consequence/relations semantics are explicit
- [ ] Historical safety/sensitivity/follow-up/validation evidence is bounded
- [ ] Templates, numbering, paths, dates, statuses and sections remain sourced
- [ ] Typed decision/evidence, repository/lifecycle and implementation/validation handoffs resolve gaps
- [ ] Completion means ADR contract passed—not decision/implementation outcome
- [ ] Resume invalidates stale prose and avoids duplicate identity/history writes
- [ ] Only artifacts under the resolved adr-authoring run root are writable
