---
primary_layer: content
---
# Risk Register

[← Table of Contents]({{INDEX_PATH}}) · *Global Strategy › Risks*

## Table of Contents

- [Summary](#summary)
- [Risk Matrix](#risk-matrix)
- [Technical Debt](#technical-debt)
- [Assumptions and Open Questions](#assumptions-and-open-questions)
- [Self-Check](#self-check)
- [See Also](#see-also)
- [Related Docs](#related-docs)

## Summary

Risks recorded with an owner and a trigger are managed; risks recorded as prose
are decoration. Each row states what would make the risk real, not only that it
exists.

## Risk Matrix

| ID | Risk | Impact | Likelihood | Exposure | Trigger | Mitigation | Owner |
|---|---|---|---|---|---|---|---|
| R-1 | {{RISK}} | high \| medium \| low | high \| medium \| low | {{IMPACT_X_LIKELIHOOD}} | {{TRIGGER}} | {{MITIGATION}} | {{OWNER}} |

## Technical Debt

| ID | Debt | Incurred by | Interest (what it costs to keep) | Repayment trigger |
|---|---|---|---|---|
| TD-1 | {{DEBT}} | {{DECISION_OR_ADR}} | {{ONGOING_COST}} | {{TRIGGER}} |

## Assumptions and Open Questions

- ASSUMPTION: {{ASSUMPTION}}
- Open question: {{OPEN_QUESTION}}

## Self-Check

| Check | Status |
|---|---|
| Every risk names an owner and a trigger | {{CHECK_1}} |
| Every accepted debt item states what it costs to keep | {{CHECK_2}} |

## See Also

- {{RELATED_ADR_IDS}}

## Related Docs

- [Problem Brief](../00-context/problem-brief.md)
- [Quality Attributes](../01-requirements/quality-attributes.md)
