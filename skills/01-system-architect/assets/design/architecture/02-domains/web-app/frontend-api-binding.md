---
primary_layer: content
---
# Frontend API Binding

[← Table of Contents]({{INDEX_PATH}}) · *Web App Module*

## Table of Contents

{{TOC_LINKS}}

{{FRONTEND_API_BINDING_SUMMARY}}

## API Binding Sequence

```mermaid
sequenceDiagram
    participant View as {{VIEW_NAME}}
    participant ApiClient as {{API_CLIENT}}
    participant API as {{API_SERVICE}}
    View->>ApiClient: {{REQUEST_TRIGGER}}
    ApiClient->>API: {{HTTP_METHOD}} {{API_PATH}}
    API-->>ApiClient: {{API_RESPONSE}}
    ApiClient-->>View: {{VIEW_MODEL}}
```

## Binding Matrix

| Screen | Trigger | API/Message | Params | Response Mapping | Cache Rule |
|---|---|---|---|---|---|
{{FRONTEND_API_BINDING_ROWS}}

## Error Mapping

| API Error | UI State | User Message | Retry Rule |
|---|---|---|---|
{{FRONTEND_API_ERROR_ROWS}}
## Assumptions and Open Questions

{{ASSUMPTIONS}}

## Self-Check

{{SELF_CHECK_NOTE}}

## Related Docs

{{RELATED_DOC_LINKS}}
