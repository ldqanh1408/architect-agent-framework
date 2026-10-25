# Requirement Supplement: {{PROJECT_NAME}} [{{DOC_ID}}]

[<- Table of Contents]({{INDEX_PATH}})

## Table of Contents

- [Summary](#summary)
- [Existing Baseline](#existing-baseline)
- [Delta Interview Log](#delta-interview-log)
- [Clarified Requirement Deltas](#clarified-requirement-deltas)
- [Affected Stable IDs](#affected-stable-ids)
- [Compatibility Constraints](#compatibility-constraints)
- [Change Control Handoff](#change-control-handoff)
- [Self-Check](#self-check)
- [Related Docs](#related-docs)

## Summary

{{TWO_TO_THREE_SENTENCE_SUMMARY_OF_THE_REQUIREMENT_DELTA}}

## Existing Baseline

| Baseline Artifact | Evidence Read | Notes |
|---|---|---|
| {{BASELINE_PATH}} | {{REQ_OR_API_OR_ADR_IDS_FOUND}} | {{NOTE}} |

## Delta Interview Log

| Round | Topic | Question | Answer | Resolved Delta IDs |
|---|---|---|---|---|
| {{ROUND}} | {{TOPIC}} | {{QUESTION}} | {{ANSWER}} | {{CLR_D_IDS}} |

## Clarified Requirement Deltas

| Delta ID | Classification | EARS Requirement / Decision | MoSCoW | Acceptance Signal |
|---|---|---|---|---|
| {{CLR_D_ID}} | {{NEW_OR_MODIFY_OR_REMOVE_OR_CLARIFICATION}} | {{EARS_REQUIREMENT_OR_DECISION}} | {{MOSCOW}} | {{TESTABLE_SIGNAL}} |

## Affected Stable IDs

| Existing ID | File | Impact |
|---|---|---|
| {{STABLE_ID_OR_NEW}} | {{SPEC_FILE_OR_NEW_FILE}} | {{ADD_MODIFY_REMOVE_CLARIFY}} |

## Compatibility Constraints

| Constraint | Source | Required Handling |
|---|---|---|
| {{CONSTRAINT}} | {{USER_OR_SPEC_ID}} | {{HANDLING}} |

## Change Control Handoff

```yaml
kind: requirement-delta
source: {{DOC_ID}}
recommended_cr: {{CR_ID_OR_NEXT}}
delta_ids:
  - {{CLR_D_ID}}
touched_ids:
  - {{STABLE_ID_OR_NEW}}
required_next_skill: 00-requirement-clarifier
system_architect_apply_mode: approved-cr-only
```

## Self-Check

| Check | Status | Note |
|---|---|---|
| Existing baseline was read before writing deltas | {{COMPLETE_OR_PARTIAL}} | {{NOTE}} |
| Every delta has CLR-D ID and classification | {{COMPLETE_OR_PARTIAL}} | {{NOTE}} |
| Every affected existing artifact has a stable ID or NEW marker | {{COMPLETE_OR_PARTIAL}} | {{NOTE}} |
| Handoff routes through an approved CR to system-architect, not direct SSoT edit | {{COMPLETE_OR_PARTIAL}} | {{NOTE}} |

## Related Docs

- [Requirements]({{REQUIREMENTS_PATH}})
- [Change Request]({{CHANGE_REQUEST_PATH}})
{{RELATED_DOC_LINKS}}
