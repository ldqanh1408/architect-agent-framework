---
primary_layer: content
---
# Technical Debt

[← Table of Contents]({{INDEX_PATH}}) · *Global Strategy › Risks › Debt*

## Table of Contents

- [Summary](#summary)
- [Debt Register](#debt-register)
- [Debt Taken Deliberately](#debt-taken-deliberately)
- [Self-Check](#self-check)
- [Related Docs](#related-docs)

## Summary

arc42 §11 is "Risks **and** technical debt", and the second half is usually
dropped. A risk is something that might happen; debt is something already true
that you have decided to live with.

At Phase 1 debt is not hypothetical: adopting an existing system as-is, deferring
a context boundary you already know is wrong, or choosing the faster option
knowing it will be undone all create debt before any code exists.

## Debt Register

| ID | Debt | Where it lives | Why it was taken | Cost of carrying it | Trigger to repay |
|---|---|---|---|---|---|
| DEBT-1 | {{WHAT}} | {{path or context}} | {{REASON}} | {{ongoing cost}} | {{measurable trigger}} |

"Trigger to repay" is the column that separates managed debt from a wish. "When
we have time" is not a trigger; "when the second consumer of this contract
appears" is.

## Debt Taken Deliberately

| ID | Decision | ADR | What we chose not to build | Revisit when |
|---|---|---|---|---|
| DEBT-x | {{DECISION}} | ADR-000x | {{OMITTED_CAPABILITY}} | {{TRIGGER}} |

Deliberate debt should trace to an ADR. Debt with no decision behind it is
usually an assumption that was never written down — route it to
`00-context/assumptions.md` instead.

## Self-Check

| Claim | How it will be settled |
|---|---|
| Every deliberate-debt row cites an ADR that exists | VERIFIED-BY-SCRIPT: id existence check |
| Every trigger is observable | VERIFIED-BY-QUOTE: the trigger names a metric, an event, or a count |
| The register is complete | UNVERIFIABLE-AT-PHASE-1: debt accumulates during implementation; `01-system-architect` appends |

## Related Docs

- [Risk Register](risk-register.md)
- [Assumptions](../00-context/assumptions.md)
- [Decisions](../05-governance/decisions/)
