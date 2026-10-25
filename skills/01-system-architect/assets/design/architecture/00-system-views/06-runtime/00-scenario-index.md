---
primary_layer: content
---
# Runtime Scenario Index

[← Table of Contents]({{INDEX_PATH}}) · *System Views › Runtime*

## Table of Contents

- [Summary](#summary)
- [Scenarios](#scenarios)
- [Scenarios Deliberately Not Documented](#scenarios-deliberately-not-documented)
- [Self-Check](#self-check)
- [Related Docs](#related-docs)

## Summary

arc42 §6. This is where a quality goal stops being an adjective. "Checkout must
survive the branch link dropping" is unfalsifiable as a sentence in
`quality-attributes.md`; as a scenario that names the building blocks it
traverses and what each one does when the link is gone, it is something
a later test-planning step outside this distribution can turn into a test.

**Keep the count small.** arc42 is explicit: document only the scenarios that are
crucial to understanding the system or critical to a top quality goal. Dozens of
scenarios get *designed*; one to five get *documented*. A scenario per use case
is a transcript, and nobody reads transcripts.

## Scenarios

| ID | Scenario | Why it is architecturally relevant | Quality scenario | Contexts traversed |
|---|---|---|---|---|
| SCN-001 | {{NAME}} | {{WHAT_UNDERSTANDING_IT_UNLOCKS}} | QS-x | {{CTX_A}} → {{CTX_B}} |
| SCN-002 | {{NAME}} | {{...}} | QS-y | {{...}} |

Selection heuristics, in the order they usually apply:

1. The flow that carries the money, the stock, or the irreversible side effect.
2. The flow that crosses the most bounded contexts — that is where the contracts
   are actually exercised.
3. Start-up / shut-down / recovery, if the system has state that survives a
   restart.
4. The flow named by the top quality goal, if it is not already one of the above.

## Scenarios Deliberately Not Documented

| Flow | Why it is not here |
|---|---|
| {{FLOW}} | {{e.g. single-context CRUD; the component view already answers it}} |

This section is what keeps the list short *and* honest. Without it, "we only
documented three scenarios" is indistinguishable from "we forgot".

## Self-Check

| Claim | How it will be settled |
|---|---|
| At most five scenario pages exist | VERIFIED-BY-SCRIPT: V-MAN-7 |
| Every scenario cites a QS-xxx | VERIFIED-BY-SCRIPT: COR-4 |
| Every participant is a real container or external system | VERIFIED-BY-SCRIPT: COR-3 |
| The scenarios chosen are the right ones | UNVERIFIABLE-AT-PHASE-1: settled by review with STK-x |

## Related Docs

- [Quality Attributes](../../01-global-strategy/01-requirements/quality-attributes.md)
- [Container View](../c2-container.md)
- [Correspondence Rules](../00-viewpoints/correspondence-rules.md)
