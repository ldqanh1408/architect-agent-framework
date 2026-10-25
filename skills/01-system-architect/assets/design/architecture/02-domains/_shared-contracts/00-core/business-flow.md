---
primary_layer: content
---
# {{FLOW_NAME}}

[← Table of Contents]({{INDEX_PATH}}) · *Business Flow*

## Table of Contents

{{TOC_LINKS}}

{{FLOW_SUMMARY}}

## Primary Sequence

```mermaid
sequenceDiagram
    actor Actor as {{PRIMARY_ACTOR}}
    participant UI as {{CLIENT_OR_ENTRYPOINT}}
    participant API as {{API_OR_SERVICE}}
    participant Domain as {{DOMAIN_COMPONENT}}
    participant Store as {{DATA_STORE}}
    Actor->>UI: {{STEP_1_ACTION}}
    UI->>API: {{STEP_2_REQUEST}}
    API->>Domain: {{STEP_3_COMMAND}}
    Domain->>Store: {{STEP_4_DATA_OPERATION}}
    Store-->>Domain: {{STEP_5_DATA_RESULT}}
    Domain-->>API: {{STEP_6_DOMAIN_RESULT}}
    API-->>UI: {{STEP_7_RESPONSE}}
    UI-->>Actor: {{STEP_8_OUTCOME}}
```

## Flow Detail

| Step | Actor/System | Action | Input | Output | Failure Handling |
|---|---|---|---|---|---|
{{FLOW_STEP_ROWS}}

## Variants And Error Paths

| Case | Trigger | Behavior | User/System Outcome | Signal |
|---|---|---|---|---|
{{FLOW_VARIANT_ROWS}}

## Acceptance Check

{{FLOW_ACCEPTANCE_CHECK}}
## Assumptions and Open Questions

{{ASSUMPTIONS}}

## Self-Check

{{SELF_CHECK_NOTE}}

## Related Docs

{{RELATED_DOC_LINKS}}
