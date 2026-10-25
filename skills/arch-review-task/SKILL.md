---
name: arch-review-task
description: "Conduct formal architecture review against ISO 42010 standards. Use when an authoritative architecture-review subject/scope/baseline, requirements/decisions/principles/policies/risks, submitter/owner, reviewer mandates, evidence and disposition authority must be examined in one bounded review: criteria, coverage, findings, responses, conditions, decision record and re-review/closure evidence. Produces review evidence without redesigning or self-approving architecture. Do not use for architecture design/advice, portfolio-level review governance, code/PR/security/operational-readiness review, compliance audit/certification, checklist execution or meeting facilitation."
license: MIT
compatibility: "Agent Skills clients; filesystem read/write access; accepted subject, criteria, reviewer, evidence and disposition authority when supplied"
allowed-tools: "read_file search_files write_file terminal"
version: 2.1.0
author: Architect Agent Framework
metadata:
  hermes:
    tags: [architecture-task, governance, architecture-review, findings, disposition]
---

# Architecture Review Execution Contract

## Overview

`arch-review-task` performs one evidence-bounded review of an exact architecture subject against authoritative concerns and criteria. It records coverage, findings, limitations, responses and governing disposition without choosing architecture or granting itself approval authority.

A meeting held, checklist passed, report produced, score calculated, PR approved or no findings recorded alone does not prove review completeness, architecture quality, compliance, implementation readiness or outcome.

## Fast Path

Take this route first. Leave it the moment a step cannot be answered from supplied authority.

1. **Check an architecture review is required.** If the request is for architecture design or advice, route to `arch-spec-authoring` or plain architectural guidance instead.
2. **Bound the review subject and mandate.** Identify the exact architecture revision, submitter, and reviewing authority. A review without a bounded subject and mandate lacks legal standing to issue findings.
3. **Freeze criteria and oracles.** Bind evaluation questions directly to authoritative requirements, ADR decisions, or enterprise policies. Inventing criteria during review invalidates the disposition.
4. **Evaluate evidence against criteria.** Inspect authoritative architecture models, design documents, and test results for coverage. Submitted claims without verifiable evidence are recorded as gaps, not pass states.
5. **Form findings and obtain responses.** Trace every nonconformity to an exact criterion and location, and capture the subject owner's formal response. A reviewer recommendation is not a governing decision.
6. **Write the overview under the owned root**, classify every claim, and run postflight.

Leave the fast path for `## Workflow` when criteria conflict across authoritative sources, subject owners dispute findings, waiver or exception requests require risk acceptance, or re-review is triggered by material subject revision.

## Worked Example

**Intake.** "We need formal sign-off on the core payment gateway redesign before going to production. Security says the auth token handling violates enterprise policy."

**What this skill produces** (excerpt from `architecture/01-global-strategy/05-governance/reviews/architecture-review-report.md`):

```markdown
## Review Findings and Disposition

Review Subject [RS-1]
  subject: Payment Gateway Service v2.4.0-rc1
  baseline: Architecture Specification [PAY-ARCH-2026-v2]
  decider: Enterprise Architecture Board (EAB)

Finding [FD-1]
  criterion: Enterprise Policy [POL-SEC-04] Section 3.2 (OAuth Token Storage)
  location: Payment Gateway / Token Store Manager (`auth_handler.go#L45`)
  condition: Auth tokens are cached unencrypted in redis-master-01 memory.
  impact: High -- exposes active user sessions to read-access database replicas.
  owner-response: Disputed by Team Lead (claims Redis cluster is network-isolated).
  status: Confirmed nonconformity -- network isolation does not satisfy encryption-at-rest clause.

Disposition [DP-1]
  outcome: Conditional Acceptance
  condition: Satisfy [FD-1] by enabling Redis TLS + memory encryption before traffic cutover.
```

**What it does not produce.** Redesign of the token storage mechanism or implementation of Redis encryption. Those belong to `policy-definition` or application engineering handoffs.

## When to Use

Use when an exact architecture proposal/specification/baseline/change needs review for an identified decision under a supplied mandate.

Do not use for architecture design/advice, review-system governance, code/security/readiness review, audit/certification, checklist execution or meeting facilitation. Review vocabulary alone is insufficient routing evidence.

## Ownership and Write Boundary

This task writes only `<output_root>/architecture/01-global-strategy/05-governance/reviews/architecture-review-report.md`. Architecture artifacts, requirements, decisions, evidence, findings systems, implementation and production state remain read-only.

This task owns scoped examination, evidence/coverage/finding records, limitations and typed handoffs. Subject owners respond/remediate. Specialist reviewers own analysis. Named governance/risk authorities decide disposition/waiver.

## Required Distinctions

- **Review subject** is the exact artifact/system/change/release and revision examined; **review instance** is this bounded evaluation.
- Scope defines architecture layers, lifecycle stage, concerns, environments, dependencies, exclusions and decision use.
- Baseline/current, proposed/target, transition, implemented, deployed and observed runtime states remain distinct.

- Submitter supplies the subject; subject owner owns semantics; sponsor requests review; reviewer evaluates; decider issues governing disposition.
- Stakeholder/affected party contributes concerns/evidence; observer/attendee does not gain review or decision authority.
- Reviewer mandate identifies scope, expertise, authority, independence/conflicts, access and limitations.


- Architecture review evaluates an existing subject; architecture design creates/changes the subject; advice suggests without formal disposition.
- Approval/sign-off is a governance decision; review produces evidence/findings and may recommend or condition only within mandate.
- Audit evaluates against audit criteria under audit independence/method; conformance assessment evaluates a target against normative clauses.
- Code/PR review evaluates implementation changes; security review and operational-readiness review have specialist criteria and owners.

- Requirement, decision, principle, standard, policy, contract, constraint and risk are distinct criterion sources.


- Criteria bind stable ID, authority, applicability, exact revision and evaluation question/oracle.
- Review question asks what evidence is needed; check is a method/action; result is bounded evidence.

- Evidence binds source/artifact/query/test/benchmark/model/interview/inspection, subject revision, method, population/sample, environment, coverage and freshness.
- Submitted evidence differs from independently evaluated, applicable and sufficient evidence.
- Missing, inaccessible, stale, contradictory or low-integrity evidence yields gaps/unknowns, not plausible conclusions.
- Coverage identifies reviewed criteria/concerns/elements/scenarios/interfaces/environments and explicit exclusions/gaps.

- **Observation** records what was seen; **question** requests clarification; **finding** asserts a scoped condition against criterion/evidence.
- **Gap** identifies absent evidence/contract; **defect** is an evidenced nonconformity; **risk** is uncertain adverse exposure.
- Recommendation proposes an option; condition constrains disposition; blocker prevents a permitted decision/path under authority.

- Finding identity binds statement, subject location/scope, criterion, evidence, affected parties, uncertainty, status and owner.
- Finding status—raised, clarified, disputed, confirmed, rejected, accepted, remediated, verified, closed—differs from review disposition.
- Impact describes consequence for authoritative outcomes/obligations; likelihood/exposure/confidence are distinct and sourced.
- Severity and priority are not interchangeable: severity characterizes impact under policy; priority sequences action under owner authority.
- Critical/high/medium/low, must/should/consider, numeric scores and traffic-light ratings are not universal.



- Subject-owner response can agree, dispute, clarify, correct evidence or propose remediation/mitigation.

- Remediation changes subject/implementation; mitigation reduces exposure; waiver/exception permits bounded deviation; risk acceptance belongs to authority.

- Decision outcomes can include accept, reject, defer, conditional acceptance, request revision, escalate or unknown only under local mandate.
- Compliant/conformant, acceptable, approved, ready and low-risk are different claims with different authorities/oracles.
- Conditional acceptance specifies exact conditions, evidence, scope, owner, authority and invalidation/expiry when supplied.
- Deferred preserves unresolved evidence/decision trigger; unknown means evidence/authority cannot support disposition.


- Conflict between criteria/authorities requires precedence/escalation, not reviewer preference.
- Exception/waiver differs from finding rejection; it retains clause/scope/impact/mitigation/authority/review/expiry evidence.

- Review report/minutes/transcript/decision record are distinct artifacts; meeting notes do not create findings or approval.
- Report summarizes subject/scope/criteria/evidence/coverage/findings/limitations/responses/disposition with provenance.
- Re-review examines changed subject and unresolved scope; prior approval does not cover material revision automatically.
- Closure requires finding-specific verification or authority-backed disposition; a closed ticket/comment is insufficient.
- Verification binds exact changed subject, method, evidence, coverage, result and freshness.
- Review effective, finding remediated, condition satisfied, decision implemented and field outcome improved remain separate states.
- Follow-up/re-review trigger can come from subject/requirement/decision/risk/policy/evidence/incident/outcome/condition changes.

- Subject/evidence/criterion/authority changes invalidate affected findings/dispositions explicitly.
- Sensitive architecture/security/commercial/personnel evidence may require classification, redaction and restricted records.
- Publication/access/retention cannot leak protected evidence or erase dissent/history.
- Review methods can include document/model/code inspection, walkthrough, scenario, prototype, test, benchmark, interview or simulation.

- Architecture diagrams, C4, ADRs, threat models, NFR lists and checklists are not universal required inputs.
- Review depth follows consequence/uncertainty/reversibility/obligation and mandate, not fixed phase or document count.
- Evidence states include requested, admitted, scoped, assigned, in-review, observed, raised, disputed, confirmed, rejected, accepted, conditionally accepted, deferred, waived, remediated, verified, closed, appealed, reopened and stale.
- Review performed, finding recorded, disposition issued, action closed and outcome achieved remain separate.
- **Completion** means architecture-review execution contract passed—not architecture approval, compliance or production readiness.

## Architecture-Review Evidence Tuple

Bind claims to stable review/subject/system/change/release/document/owner/submitter/sponsor/reviewer/decider/stakeholder/criterion/requirement/decision/principle/policy/risk/evidence/coverage/observation/finding/response/recommendation/condition/disposition/exception/action/verification/source IDs; exact subject/criterion/evidence/authority revisions; requested/scoped/in-review/raised/disputed/confirmed/rejected/accepted/conditional/deferred/waived/remediated/verified/closed/stale states; provenance, applicability, freshness, sensitivity and invalidation trigger.

Keep subject truth, submitted/evaluated evidence, review findings, governing disposition, remediation and realized outcome separate.

## Required Intake

Require review subject/version/state/scope/exclusions/decision use; submitter/subject owner/sponsor/reviewers/specialists/decider/affected parties and mandates/conflicts; requirements/decisions/principles/standards/policies/risks/constraints/assumptions; criteria/questions/methods; architecture artifacts/evidence/freshness/coverage; disposition/exception/closure authority; repository/report/access conventions.

Block rather than infer ISO 42010 applicability, C4/ADR inputs, NFR checklist, patterns, reviewers/panel/quorum, independence, severity/score, Approved/Conditional/Rejected verdicts, remediation, owner/due date, waiver, review cadence or closure.

## Blocking Conditions

Block when subject/scope/version/decision use is absent; mandate/decider is unresolved; criteria are invented; reviewer competence/conflicts are undisclosed; evidence is stale/insufficient; finding cannot trace to criterion/evidence; recommendation is treated as decision; disposition/waiver lacks authority; re-review scope is unknown; or success relies on attendance/checklist/score/report/signature/no-findings alone.

Return stable IDs, blocked criteria/findings/dispositions, missing authority/evidence, safe observations/questions/no-disposition strategy, owner and exact resume condition.

## Minimum-Sufficient Review

Compare no formal review, async peer review, specialist review, bounded multi-owner review, independent assurance, defer/request-evidence, conditional decision or re-review through decision consequence and evidence maturity. Do not default to ARB/meeting, ISO/C4/ADR checklist, fixed panel, scores, severities, sign-off, remediation plan or review for every change.

## Workflow

1. **Frame review request.** Record subject/version/state/scope/decision use/owner, objective, exclusions and output boundary. Done when one review—not review-system design—is required.
2. **Resolve authorities.** Identify subject/domain/specialist, reviewer, decider/risk, remediation, evidence and records owners. Done when no criterion or approval is invented.
3. **Freeze subject/sources.** Inventory exact architecture/requirements/decisions/contracts/policies/risks/evidence revisions. Done when all reviewers examine one baseline.
4. **Resolve mandate/roles.** Record sponsor/submitter/owner/reviewer/specialist/decider/affected party rights, expertise/conflicts/access. Done when attendance cannot equal authority.
5. **Define review scope/coverage.** Map concerns/elements/interfaces/scenarios/environments/lifecycle states/exclusions to decision use. Done when comprehensive cannot be vague.
6. **Resolve criteria.** Bind questions/oracles to authoritative requirements/decisions/principles/contracts/policies/risks. Done when heuristics cannot self-author force.
7. **Define evidence plan.** Map criteria to source/method/version/population/sample/environment/freshness/integrity and missing behavior. Done when submitted cannot equal sufficient.
8. **Establish current evidence.** Inspect authoritative artifacts/results and record provenance/limitations/contradictions. Done when facts/inferences/unknowns differ.
9. **Examine scope systematically.** Apply scoped methods to criteria and record covered/not-covered/blocked dimensions. Done when checklist completion cannot hide gaps.
10. **Record observations/questions.** Capture exact subject location/state/evidence and clarification needs without premature severity. Done when comments cannot masquerade as findings.
11. **Form findings.** Bind condition/criterion/evidence/impact/uncertainty/affected scope/status/owner to stable IDs. Done when vague concerns cannot block.
12. **Assess impact/confidence.** Apply only sourced scales/policy and record limitations. Done when severity/score cannot self-decide disposition.
13. **Capture recommendations.** Record reviewer-proposed alternatives/trade-offs and canonical owner handoff without self-design/assignment. Done when recommendation remains advisory.
14. **Obtain subject responses.** Record agree/dispute/clarify/evidence correction/remediation proposal/residual gap with provenance. Done when disagreement cannot erase finding.
15. **Resolve finding status.** Confirm/reject/accept/dispute findings through evidence and authorized process. Done when false-positive classification is evidenced.
16. **Resolve conflicts/dissent.** Preserve reviewer/owner/criterion conflicts, recusal and escalation. Done when consensus cannot be fabricated.
17. **Prepare disposition.** Summarize scope/coverage/findings/conditions/unknowns/exceptions and permitted outcomes for decider. Done when recommendation cannot become approval.
18. **Record governing decision.** Capture authority/outcome/scope/conditions/dissent/waivers/evidence/date without implying implementation. Done when approval remains bounded.
19. **Define actions/follow-up.** Route remediation/mitigation/evidence/exception work to owners with acceptance oracles and dates only if authoritative. Done when reviewer cannot self-assign.
20. **Verify remediation/conditions.** Reinspect exact changed subject and evidence/coverage for relevant findings. Done when ticket closure is insufficient.
21. **Handle re-review/freshness.** Compare subject/criterion/evidence/authority revisions and trigger scoped reopening. Done when old disposition cannot cover material change.
22. **Adversarially verify.** Test wrong baseline, hidden conflict, absent specialist, stale evidence, vague finding, score-as-verdict, suppressed dissent and closed-unverified action. Done when each yields evidence, gap or blocker.
23. **Issue typed handoffs.** Route subject/criterion, evidence/finding and disposition/follow-up gaps with resume conditions. Done when review cannot design/remediate/approve itself.
24. **Publish owned artifact.** Write only resolved run-root report/records and preserve digest/provenance/access. Done when output is minimum sufficient.
25. **Close or resume safely.** Validate scope/mandate/criteria/evidence/coverage/findings/responses/disposition/follow-up/freshness. Done when completion means review passed—not architecture.

## Typed Outputs and Handoffs

- `architecture_review_scope`: review/subject/version/state/scope/decision-use/owner/mandate/source IDs and exclusions.
- `architecture_review_evidence_coverage`: criterion/question/method/source/revision/population/environment/coverage/freshness/gap evidence.
- `architecture_review_finding`: observation/condition/criterion/evidence/impact/confidence/status/response/recommendation/owner record.
- `architecture_review_disposition`: findings/coverage/conditions/unknowns/dissent/exception/decider/outcome/scope/date evidence.
- `architecture_review_subject_criterion_handoff`: missing baseline/scope/requirement/decision/principle/policy/risk/criterion authority.
- `architecture_review_evidence_finding_handoff`: missing artifact/test/benchmark/runtime evidence, reviewer expertise or finding clarification.
- `architecture_review_disposition_followup_handoff`: missing decider/risk acceptance/exception/remediation/verification/re-review/closure authority.

Every payload includes stable ID, producer, consumer/owner, review/subject/criterion/evidence/authority/source revisions, assumptions, unknowns, stale behavior, sensitivity and acceptance oracle.

## Resume Semantics

A blocker records review/subject/criterion/evidence/finding/response/disposition/action/repository/output IDs, conflicts, missing authorities, requests, owners and resume point. On resume compare subject/criterion/evidence/authority revisions; preserve history/dissent, invalidate stale findings/decisions and never convert recommendation into approval.

## Open-Source Research Basis

Recorded in `references/research-basis.md`: the repositories inspected for this skill, the concepts adapted from each, and the ones deliberately rejected. Load it when auditing provenance or revising the skill's boundaries; it is not required to execute the skill.

## Verification Checklist

- [ ] Trigger requests one bounded authority-backed architecture review
- [ ] Subject/reviewer/decider/specialist/remediation/evidence owners resolve
- [ ] Subject/evidence/finding/disposition/remediation/outcome states remain distinct
- [ ] Scope/mandate/criteria/evidence/coverage/finding semantics are explicit
- [ ] Responses/dissent/exceptions/disposition/re-review/freshness evidence is bounded
- [ ] ISO/checklists/reviewers/scores/severities/verdicts remain sourced
- [ ] Typed subject/criterion, evidence/finding and disposition/follow-up handoffs resolve gaps
- [ ] Completion means review execution passed—not architecture approval
- [ ] Resume invalidates stale evidence/decisions and preserves dissent
- [ ] Only artifacts under the resolved arch-review-task run root are writable
