---
primary_layer: content
---
# Push Notification Flow

[← Table of Contents]({{INDEX_PATH}}) · *Mobile Module*

## Table of Contents

{{TOC_LINKS}}

{{PUSH_NOTIFICATION_SUMMARY}}

## Push Sequence

```mermaid
sequenceDiagram
    participant App as Mobile App
    participant Backend as {{BACKEND_SERVICE}}
    participant Push as {{PUSH_PROVIDER}}
    App->>Backend: Register device token
    Backend->>Push: Send notification
    Push-->>App: Deliver notification
    App->>Backend: Open or action callback
```

## Notification Catalog

| Notification | Trigger | Payload | Permission | Fallback |
|---|---|---|---|---|
{{PUSH_NOTIFICATION_ROWS}}
## Assumptions and Open Questions

{{ASSUMPTIONS}}

## Self-Check

{{SELF_CHECK_NOTE}}

## Related Docs

{{RELATED_DOC_LINKS}}
