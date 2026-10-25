---
primary_layer: content
---
# Infrastructure As Code Design

[← Table of Contents]({{INDEX_PATH}}) · *DevOps Infrastructure Module*

## Table of Contents

{{TOC_LINKS}}

{{IAC_DESIGN_SUMMARY}}

## IaC Module Map

```mermaid
flowchart TB
    Root["{{IAC_ROOT}}"] --> Network["{{NETWORK_MODULE}}"]
    Root --> Runtime["{{RUNTIME_MODULE}}"]
    Root --> Data["{{DATA_MODULE}}"]
    Root --> Observability["{{OBS_MODULE}}"]
```

## Variable And Output Contract

| Name | Type | Direction | Purpose | Sensitive |
|---|---|---|---|---|
{{IAC_VARIABLE_OUTPUT_ROWS}}
## Assumptions and Open Questions

{{ASSUMPTIONS}}

## Self-Check

{{SELF_CHECK_NOTE}}

## Related Docs

{{RELATED_DOC_LINKS}}
