# Design Review: {{PROJECT_NAME}} [{{DOC_ID}}]

[← Table of Contents]({{INDEX_PATH}})

## Table of Contents

- [Summary](#summary)
- [Review Scope](#review-scope)
- [Findings](#findings)
- [Pre-Mortem Notes](#pre-mortem-notes)
- [Verdict](#verdict)
- [Review Rounds](#review-rounds)
- [Assumptions & Open Questions](#assumptions--open-questions)
- [Self-Check](#self-check)
- [Related Docs](#related-docs)

## Summary

{{TWO_TO_THREE_SENTENCE_SUMMARY_OF_WHAT_WAS_REVIEWED_AND_OUTCOME}}

## Review Scope

| Spec File | Version / Last Modified | Lenses Applied |
|---|---|---|
| {{SPEC_FILE}} | {{SPEC_VERSION}} | {{LENSES}} |

## Findings

| ID | Severity | Location | Finding | Suggested Direction |
|---|---|---|---|---|
| {{RISK_ID}} | {{SEVERITY}} | {{SPEC_FILE_AND_SECTION}} | {{FINDING}} | {{SUGGESTED_DIRECTION}} |

## Pre-Mortem Notes

| Failure Scenario | Plausibility | Spec-Level Remedy | Converted To |
|---|---|---|---|
| {{FAILURE_SCENARIO}} | {{HIGH_MED_LOW}} | {{REMEDY_OR_NONE}} | {{RISK_ID_OR_DISMISSED}} |

## Verdict

{{APPROVED_OR_APPROVED_WITH_CONCERNS_OR_REJECTED}} — {{ONE_SENTENCE_JUSTIFICATION}}

## Review Rounds

One row per round, oldest first, never rewritten. Two REJECTED rounds in a row is the cap: a third
REJECTED escalates the blockers to the human reviewer in the review console (`architect_console_url`) instead of starting a fourth round.

| Round | Verdict | Reviewed |
|---|---|---|
| {{ROUND_NUMBER}} | {{APPROVED_OR_APPROVED_WITH_CONCERNS_OR_REJECTED}} | {{REVIEW_DATE}} |

## Assumptions & Open Questions

- ASSUMPTION: {{ASSUMPTION_OR_UNSPECIFIED}}
- OPEN QUESTION: {{OPEN_QUESTION_OR_NONE}}

## Self-Check

| Check | Status | Note |
|---|---|---|
| Every finding cites a spec file and section | {{COMPLETE_OR_PARTIAL}} | {{NOTE}} |
| Verdict follows deterministic severity rules | {{COMPLETE_OR_PARTIAL}} | {{NOTE}} |
| No spec file was edited by this review | {{COMPLETE_OR_PARTIAL}} | {{NOTE}} |

## Related Docs

- [Requirements]({{REQUIREMENTS_PATH}})
- [Architecture]({{ARCHITECTURE_PATH}})
{{RELATED_DOC_LINKS}}
