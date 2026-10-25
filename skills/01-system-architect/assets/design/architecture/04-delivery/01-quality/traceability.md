---
primary_layer: infrastructure
---
# Requirement To Design To Test

[← Table of Contents]({{INDEX_PATH}}) · *Traceability*

## Table of Contents

{{TOC_LINKS}}

{{TRACEABILITY_SUMMARY}}

## Coverage Flow

```mermaid
flowchart LR
    REQ[{{REQUIREMENT_ID}} {{REQUIREMENT_NAME}}] --> FLOW[{{FLOW_ID}} {{FLOW_NAME}}]
    FLOW --> API[{{API_ID}} {{API_NAME}}]
    API --> ENTITY[{{ENTITY_ID}} {{ENTITY_NAME}}]
    API --> TEST[{{TEST_ID}} {{TEST_NAME}}]
```

## Traceability Matrix

| Requirement | Design Element | Flow | API / Message | Entity | Test / Acceptance | Status |
|---|---|---|---|---|---|---|
{{TRACEABILITY_ROWS}}

Every requirement must map to at least one design element and one test or acceptance check. List any uncovered requirement as an open question.

## Self Check

| Check | Status | Note |
|---|---|---|
{{SELF_CHECK_ROWS}}
## Assumptions and Open Questions

{{ASSUMPTIONS}}

## Related Docs

{{RELATED_DOC_LINKS}}
