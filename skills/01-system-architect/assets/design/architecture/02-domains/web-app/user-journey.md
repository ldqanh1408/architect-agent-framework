---
primary_layer: content
---
# {{JOURNEY_NAME}}

[← Table of Contents]({{INDEX_PATH}}) · *Web App Module*

## Table of Contents

{{TOC_LINKS}}

{{JOURNEY_SUMMARY}}

## Journey Sequence

```mermaid
sequenceDiagram
    actor User as {{USER_ROLE}}
    participant UI as Web UI
    participant API as {{API_SERVICE}}
    participant Store as {{DATA_STORE}}
    User->>UI: {{JOURNEY_STEP_1}}
    UI->>API: {{JOURNEY_STEP_2}}
    API->>Store: {{JOURNEY_STEP_3}}
    Store-->>API: {{JOURNEY_STEP_4}}
    API-->>UI: {{JOURNEY_STEP_5}}
    UI-->>User: {{JOURNEY_STEP_6}}
```

## Screen Steps

| Step | Screen | User Action | System Response | Error/Fallback |
|---|---|---|---|---|
{{JOURNEY_STEP_ROWS}}

## Linked Contracts

| Requirement | Flow | API/Message | Entity | Test |
|---|---|---|---|---|
{{JOURNEY_TRACE_ROWS}}
## Assumptions and Open Questions

{{ASSUMPTIONS}}

## Self-Check

{{SELF_CHECK_NOTE}}

## Related Docs

{{RELATED_DOC_LINKS}}
