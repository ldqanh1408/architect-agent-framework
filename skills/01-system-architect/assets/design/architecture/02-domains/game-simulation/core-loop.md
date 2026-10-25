---
primary_layer: content
---
# Core Loop

[← Table of Contents]({{INDEX_PATH}}) · *Game Simulation Module*

## Table of Contents

{{TOC_LINKS}}

{{CORE_LOOP_SUMMARY}}

## Loop Diagram

```mermaid
flowchart LR
    Observe["Observe"] --> Decide["Decide"]
    Decide --> Act["Act"]
    Act --> Feedback["Feedback"]
    Feedback --> Observe
```

## Loop Steps

| Step | Input | System Response | Feedback | Risk |
|---|---|---|---|---|
{{CORE_LOOP_ROWS}}
## Assumptions and Open Questions

{{ASSUMPTIONS}}

## Self-Check

{{SELF_CHECK_NOTE}}

## Related Docs

{{RELATED_DOC_LINKS}}
