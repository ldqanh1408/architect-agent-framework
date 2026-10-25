---
primary_layer: content
---
# Constraints

[← Table of Contents]({{INDEX_PATH}}) · *Global Strategy › Strategy › Constraints*

## Table of Contents

- [Summary](#summary)
- [Technical Constraints](#technical-constraints)
- [Organizational Constraints](#organizational-constraints)
- [Convention Constraints](#convention-constraints)
- [Assumptions and Open Questions](#assumptions-and-open-questions)
- [Self-Check](#self-check)
- [See Also](#see-also)
- [Related Docs](#related-docs)

## Summary

Constraints are the things the design does not get to choose. Recording them
separately from decisions keeps ADRs honest: an ADR that "chose" something a
constraint already forced is not a decision, and an option rejected on a
constraint should say which one.

## Technical Constraints

| ID | Constraint | Source | Consequence for the design |
|---|---|---|---|
| TC-1 | {{TECHNICAL_CONSTRAINT}} | {{SOURCE}} | {{CONSEQUENCE}} |

## Organizational Constraints

| ID | Constraint | Source | Consequence for the design |
|---|---|---|---|
| OC-1 | {{ORGANIZATIONAL_CONSTRAINT}} | {{SOURCE}} | {{CONSEQUENCE}} |

## Convention Constraints

| ID | Convention | Scope | Enforced by |
|---|---|---|---|
| CC-1 | {{CONVENTION}} | {{SCOPE}} | {{ENFORCEMENT}} |

## Assumptions and Open Questions

- ASSUMPTION: {{ASSUMPTION}}
- Open question: {{OPEN_QUESTION}}

## Self-Check

| Check | Status |
|---|---|
| Every constraint names its source, not just its content | {{CHECK_1}} |
| No constraint is really a decision in disguise | {{CHECK_2}} |

## See Also

- {{RELATED_ADR_IDS}}

## Related Docs

- [Solution Strategy](solution-strategy.md)
- [Quality Attributes](quality-attributes.md)
