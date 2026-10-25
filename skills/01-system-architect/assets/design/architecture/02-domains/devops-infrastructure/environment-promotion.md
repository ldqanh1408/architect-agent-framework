---
primary_layer: content
---
# Environment Promotion

[← Table of Contents]({{INDEX_PATH}}) · *DevOps Infrastructure Module*

## Table of Contents

{{TOC_LINKS}}

{{ENV_PROMOTION_SUMMARY}}

## Promotion Path

```mermaid
flowchart LR
    Dev["Development"] --> Test["Test"]
    Test --> Staging["Staging"]
    Staging --> Production["Production"]
```

## Promotion Gates

| From | To | Gate | Approver | Rollback Point |
|---|---|---|---|---|
{{ENV_PROMOTION_ROWS}}
## Assumptions and Open Questions

{{ASSUMPTIONS}}

## Self-Check

{{SELF_CHECK_NOTE}}

## Related Docs

{{RELATED_DOC_LINKS}}
