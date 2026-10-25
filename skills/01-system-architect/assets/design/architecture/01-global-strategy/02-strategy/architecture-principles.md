---
primary_layer: content
---
# Architectural Principles

[← Table of Contents]({{INDEX_PATH}}) · *Global Strategy › Strategy › Principles*

## Table of Contents

- [Summary](#summary)
- [Binding Principles](#binding-principles)
- [How a Principle Is Enforced](#how-a-principle-is-enforced)
- [Assumptions and Open Questions](#assumptions-and-open-questions)
- [Self-Check](#self-check)
- [See Also](#see-also)
- [Related Docs](#related-docs)

## Summary

A principle is a rule that survives individual decisions: it constrains every
future ADR rather than being one. Principles are distinct from the *strategy*
that applies them, which is why they live in their own page — a strategy can be
revised without relitigating what the team believes.

## Binding Principles

| ID | Principle | Why it binds | What violating it looks like |
|---|---|---|---|
| PR-1 | {{PRINCIPLE}} | {{RATIONALE}} | {{VIOLATION_SHAPE}} |

## How a Principle Is Enforced

A principle with no enforcement is a preference. Each row names the mechanism
that would actually catch a violation.

| Principle | Enforcement mechanism | FIT rule |
|---|---|---|
| PR-1 | {{MECHANISM}} | {{FIT_ID}} |

## Assumptions and Open Questions

- ASSUMPTION: {{ASSUMPTION}}
- Open question: {{OPEN_QUESTION}}

## Self-Check

| Check | Status |
|---|---|
| Every principle states what violating it looks like | {{CHECK_1}} |
| Every enforceable principle resolves to a live FIT rule | {{CHECK_2}} |

## See Also

- {{RELATED_FIT_IDS}}

## Related Docs

- [Solution Strategy](solution-strategy.md)
- [Constraints](constraints.md)
