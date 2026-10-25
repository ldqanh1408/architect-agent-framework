# Spec Critic Rules (Design Review Specification)

Authoritative rules for how `spec-critic` reviews specification sets. SKILL.md and the agent prompt summarize these rules; this file is the detailed contract.

## 1. Review Lenses & Derivation Rules

| Lens | Input | Check | Output on failure |
|---|---|---|---|
| Consistency | any two specs referencing the same element | fields, components, and IDs agree across files | RISK-xxx (severity by Section 3) |
| Edge/failure | each FLOW/API spec | error branch specified for each main flow; timeout/retry/degradation for each external dependency | RISK-xxx |
| Pre-mortem | whole set + [premortem-checklist](../assets/premortem-checklist.md) | plausible failure causes with spec-level remedies | RISK-xxx |
| ADR challenge | tradeoffs-adr.md | each ADR records ≥1 rejected alternative with reason; rationale does not contradict an NFR | RISK-xxx |
| Testability | requirements.md | each REQ is verifiable as written (measurable outcome) | RISK-xxx |

## 2. Traceability Rules

- Every RISK-xxx cites the spec file and section it anchors to; a finding without a spec anchor is invalid and must be dropped.
- RISK numbering is stable: never renumber existing IDs; append only. Continue from the highest RISK-xxx already present in the spec set (`system-architect` also emits RISK ids in risk registers).
- Each finding includes a suggested direction, never a rewritten spec — the fix belongs to `system-architect`.

## 3. Severity Rules

| Severity | Criteria | Verdict effect |
|---|---|---|
| blocker | derivation would produce wrong artifacts: contradiction between specs, main flow without error behavior, REQ untestable as worded | REJECTED |
| major | gap likely to surface as rework during implementation: missing degradation behavior, unchallenged ADR contradicting an NFR | APPROVED-WITH-CONCERNS |
| minor | quality nit that does not change derived artifacts: naming drift, missing example | APPROVED (listed) |

Verdict is computed, not judged: any blocker → **REJECTED**; no blockers but ≥1 major → **APPROVED-WITH-CONCERNS**; else **APPROVED**.

## 4. Boundary Rules

- This skill NEVER edits spec files — it is read-only; findings route to `system-architect`.
- If specs are already the baselined SSoT (downstream artifacts exist), route findings to `system-architect` as change-request input (Approved CR Apply Mode) instead of direct spec edits.
- The critic reviews design content; delivery-package completeness (tickets, DoD, code coverage) is outside this distribution, but readiness findings (`GATE-xxx`) on the spec set are this skill's to raise.
- Review and authoring are separate lanes: never run spec-critic on specs authored in the same working session without flagging the shared-context risk in the report.

## 5. Output Quality Rules

- Follow the shared page structure in [template-standard.md](template-standard.md).
- No unresolved placeholders, no `TODO`; findings are complete sentences naming concrete elements.
- Validate generated documents with `architect-runtime sdd check <workspace> --full` before reporting completion.
