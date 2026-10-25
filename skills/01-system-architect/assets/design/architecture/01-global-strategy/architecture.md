---
primary_layer: content
---
# Architecture

[← Table of Contents]({{INDEX_PATH}})

## Table of Contents

{{TOC_LINKS}}

{{ARCHITECTURE_SUMMARY}}

## High-Level Architecture

```mermaid
flowchart LR
    User["{{USER_ACTOR}}"] --> UI["{{CLIENT_LAYER}}"]
    UI --> API["{{API_LAYER}}"]
    API --> Domain["{{DOMAIN_LAYER}}"]
    Domain --> Data["{{DATA_LAYER}}"]
    Domain --> Integration["{{INTEGRATION_LAYER}}"]
    Ops["{{OBSERVABILITY_LAYER}}"] --> API
```

| Layer | Responsibility | Technology | Scaling Note |
|---|---|---|---|
{{ARCHITECTURE_LAYER_ROWS}}

## Boundaries

| Boundary | Inside | Outside | Contract |
|---|---|---|---|
{{BOUNDARY_ROWS}}

## Self Check

{{SELF_CHECK_NOTE}}
## Assumptions and Open Questions

{{ASSUMPTIONS}}

## Related Docs

{{RELATED_DOC_LINKS}}
