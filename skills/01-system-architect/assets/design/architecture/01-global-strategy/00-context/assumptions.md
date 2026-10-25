---
primary_layer: workflow
---
# Assumptions & Open Questions

[← Table of Contents]({{INDEX_PATH}})

## Table of Contents

{{TOC_LINKS}}

## Summary

Every brief leaves gaps. Closing them is the architect's job — this page is where
the closures are recorded so a later reader can tell a customer constraint from a
choice that is still open to change.

The distinction matters at exactly the moment it is most expensive to recover:
six months in, when someone asks "can we drop Kubernetes?" and nobody knows
whether the customer asked for it or the architect assumed it. Without this page
the answer requires archaeology; with it, the answer is one row.

## The three exits for any identifier

Every technology name, protocol, threshold, default value and enumerated rule in
this specification set takes exactly one of these routes. There is no fourth.

| Route | When | Where it lives |
|---|---|---|
| **Quoted** | the brief states it | cite the source doc verbatim in the page that uses it |
| **Assumed** | you inferred it and it could reasonably be otherwise | an `ASM-xxx` row below |
| **Decided** | you weighed options and picked one | an ADR under `05-governance/decisions/` |

`architect-runtime sdd check <workspace> --full` enforces this: an identifier with no route
is reported. The fix is never to delete the technology — it is to write the row
or the ADR, which is a minute of work and the artifact someone will actually need.

Choosing between **Assumed** and **Decided**: if you would struggle to name a
second option and its consequences, it is an assumption. If you can, it deserves
an ADR. Assumptions are cheap and revisable; ADRs carry weight.

## Assumption Register

`Confidence` is about how likely the assumption is to survive contact with the
customer, not about how much you like it:

- `HIGH` — industry default, would surprise nobody, cheap to change if wrong
- `MEDIUM` — reasonable reading of an ambiguous brief; worth one confirming question
- `LOW` — no signal in the brief at all; **ask before building on it**

`Blast radius` is the honest part. If an assumption turns out wrong, what has to
be rewritten? An assumption with LOW confidence and a wide blast radius is the
highest-value question you can ask the customer this week.

| ID | Assumption | Why it was needed | Evidence in brief | Confidence | Blast radius if wrong | Owner / how to confirm |
|---|---|---|---|---|---|---|
{{ASSUMPTION_ROWS}}

## Open Questions

Things you could not resolve and did not assume past. Leaving a question here is
better than inventing an answer — an unanswered question blocks one decision, an
invented answer silently corrupts every page downstream of it.

| ID | Question | Blocks | Asked of | Status |
|---|---|---|---|---|
{{OPEN_QUESTION_ROWS}}

## Retired Assumptions

Assumptions that have since been confirmed or refuted. Keep them: the record of
what was once uncertain explains why the architecture has the shape it has.

| ID | Original assumption | Outcome | Resolved by | Date |
|---|---|---|---|---|
{{RETIRED_ASSUMPTION_ROWS}}

## Self-Check

{{SELF_CHECK_NOTE}}

## Related Docs

{{RELATED_DOC_LINKS}}
