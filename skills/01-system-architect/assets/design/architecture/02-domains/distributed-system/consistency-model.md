---
primary_layer: content
---
# Consistency Model

[← Table of Contents]({{INDEX_PATH}}) · *Distributed System Module*

## Table of Contents

{{TOC_LINKS}}

{{CONSISTENCY_MODEL_SUMMARY}}

## Consistency Decisions

| Data/Workflow | Consistency Level | Reason | Compensation | User Impact |
|---|---|---|---|---|
{{CONSISTENCY_ROWS}}

## State Convergence

```mermaid
stateDiagram-v2
    [*] --> Pending
    Pending --> Confirmed: {{CONFIRM_EVENT}}
    Pending --> Compensating: {{COMPENSATION_EVENT}}
    Compensating --> Resolved: {{RESOLUTION_EVENT}}
```
## Assumptions and Open Questions

{{ASSUMPTIONS}}

## Self-Check

{{SELF_CHECK_NOTE}}

## Related Docs

{{RELATED_DOC_LINKS}}
