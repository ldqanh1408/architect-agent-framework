---
primary_layer: content
---
# Stakeholder–Concern Matrix

[← Table of Contents]({{INDEX_PATH}}) · *System Views › Viewpoints › Stakeholders*

## Table of Contents

- [Summary](#summary)
- [Stakeholders](#stakeholders)
- [Concerns and the View That Answers Them](#concerns-and-the-view-that-answers-them)
- [Unanswered Concerns](#unanswered-concerns)
- [Assumptions and Open Questions](#assumptions-and-open-questions)
- [Self-Check](#self-check)
- [Related Docs](#related-docs)

## Summary

ISO/IEC/IEEE 42010 asks a question that "did we draw all five C4 levels" cannot
answer: **does every stakeholder concern have at least one view that addresses
it?** A diagram set can be complete by artifact type and still be silent on the
thing the warehouse manager needed to know.

This page is the register that makes the question answerable. Each diagram page
already declares its `viewpoint`, `stakeholders` and `concerns` in front-matter;
without this page those declarations are a field nobody joins on.

## Stakeholders

Name real roles, not departments. "Ops" is a department; "the person paged at
03:00 when the branch link drops" is a stakeholder with a concern.

| ID | Stakeholder | Who this actually is | What they decide or do with this documentation |
|---|---|---|---|
| STK-1 | {{ROLE}} | {{CONCRETE_DESCRIPTION}} | {{DECISION_THEY_MAKE}} |
| STK-2 | {{ROLE}} | {{CONCRETE_DESCRIPTION}} | {{DECISION_THEY_MAKE}} |

## Concerns and the View That Answers Them

A concern is a question the stakeholder needs answered, phrased as a question.
"Performance" is a topic; "will the checkout still respond in under two seconds
on the worst store's connection?" is a concern.

| Concern ID | Stakeholder | The question | Viewpoint | View that answers it |
|---|---|---|---|---|
| CON-1 | STK-1 | {{QUESTION}} | VP-x | [{{VIEW}}]({{VIEW_PATH}}) |
| CON-2 | STK-2 | {{QUESTION}} | VP-x | [{{VIEW}}]({{VIEW_PATH}}) |

## Unanswered Concerns

Leaving this section empty is almost always wrong at Phase 1 — a real elicitation
finds concerns the current view set does not cover. Recording them is what turns
a gap into planned work instead of a surprise at review.

| Concern ID | Why no view answers it yet | What would settle it | When |
|---|---|---|---|
| CON-n | {{REASON}} | {{THE_VIEW_OR_EVIDENCE_NEEDED}} | Phase {{N}} |

## Assumptions and Open Questions

- ASM-x: {{ASSUMED_STAKEHOLDER_OR_CONCERN}} — see `01-global-strategy/00-context/assumptions.md`.

## Self-Check

| Claim | How it will be settled |
|---|---|
| Every concern row names a view that exists | VERIFIED-BY-SCRIPT: `python 01-system-architect/scripts/check_output_docs.py <workspace>` (V-MAN-4) |
| Stakeholders were elicited, not invented | VERIFIED-BY-QUOTE: cite the brief or interview line for each STK row, or mark it ASM |
| The concern list is complete | UNVERIFIABLE-AT-PHASE-1: settled by stakeholder review; record the date when it happens |

## Related Docs

- [Viewpoint Catalog](viewpoint-catalog.md)
- [Correspondence Rules](correspondence-rules.md)
- [Quality Attributes](../../01-global-strategy/01-requirements/quality-attributes.md) — concerns with numbers attached
