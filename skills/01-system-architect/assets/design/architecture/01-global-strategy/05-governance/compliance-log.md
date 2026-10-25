---
primary_layer: content
---
# Compliance Log

[← Table of Contents]({{INDEX_PATH}}) · *Global Strategy › Governance › Compliance*

## Table of Contents

- [Summary](#summary)
- [Assessments](#assessments)
- [Findings and Actions](#findings-and-actions)
- [Standards Deviations](#standards-deviations)
- [Self-Check](#self-check)
- [Related Docs](#related-docs)

## Summary

TOGAF's Governance Repository is more than a decision log. The decisions are in
`decisions/`; this page holds the other half — what happened when someone
checked whether the decisions were actually followed.

Its value is the link it creates: an ADR that was later found violated, and the
action taken. Without it, a project can hold a complete ADR set and a complete
set of review findings and have no way to connect the two.

## Assessments

| ID | Date | Checkpoint | Scope assessed | Assessor | Outcome |
|---|---|---|---|---|---|
| ASM-C1 | {{DATE}} | {{e.g. pre-implementation gate}} | ADR-000x, STD-00y | {{ROLE}} | pass \| pass-with-findings \| fail |

## Findings and Actions

| Finding | Assessment | What was violated | Recommended action | Owner | Status |
|---|---|---|---|---|---|
| FND-1 | ASM-C1 | ADR-000x / STD-00y | {{ACTION}} | {{ROLE}} | open \| accepted \| remediated |

`accepted` is a legitimate outcome and needs to be distinguishable from
`remediated` — an accepted violation is a decision, and it should acquire an ADR
of its own rather than living only in this table.

## Standards Deviations

| Deviation | Standard | Context | Justification | Expires |
|---|---|---|---|---|
| DEV-1 | STD-00x | {{CONTEXT}} | {{WHY}} | {{DATE_OR_TRIGGER}} |

## Self-Check

| Claim | How it will be settled |
|---|---|
| Every finding names an ADR or STD that exists | VERIFIED-BY-SCRIPT: id existence check |
| Every `accepted` finding has a corresponding ADR | VERIFIED-BY-SCRIPT: cross-reference against `decisions/` |
| No assessment rows exist yet | UNVERIFIABLE-AT-PHASE-1: nothing has been built, so nothing can have been assessed — this page is a shell until something is built |

At Phase 1 this page is correctly almost empty. Populating it with invented
assessments would be the exact failure `Self-Audit Honesty` warns about: a
verdict for a check that never happened.

## Related Docs

- [Decisions](decisions/)
- [Standards Register](../03-standards/standards-register.md)
- [Acceptance Report](../../04-delivery/04-audit/)
