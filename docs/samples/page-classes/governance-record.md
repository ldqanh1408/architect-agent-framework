---
page_class: governance_record
---

# Ownership of `20-invoicing`

## Event

Module ownership assigned at the phase-1 routing checkpoint, when `20-invoicing` was created from the charter.

## Decider

The routing policy in `skill_router`, arbitrated by the platform lead where the policy returned `ambiguous`.
`backend-service-architect` won on domain rank; `domain-capability-architect` was the runner-up.

## Basis

Charter clause C-11 ("invoicing is a transactional service, not a reporting surface") plus the
domain-unanimity rule. Both are machine-read; neither is a judgement call recorded after the fact.

## Affected scope

Everything under `02-domains/03_application_architecture/20-invoicing/**`, including who may accept a change
request against the invoice aggregate.

## Timestamp

2026-03-04, run 7. Superseded only by a later governance record against the same scope.
