---
primary_layer: content
---
# Offline Sync Strategy

[← Table of Contents]({{INDEX_PATH}}) · *Mobile Module*

## Table of Contents

{{TOC_LINKS}}

{{OFFLINE_SYNC_SUMMARY}}

## Sync Lifecycle

```mermaid
stateDiagram-v2
    Online --> Offline: {{NETWORK_LOSS}}
    Offline --> Queued: {{LOCAL_CHANGE}}
    Queued --> Syncing: {{NETWORK_RETURN}}
    Syncing --> Synced: {{SYNC_SUCCESS}}
    Syncing --> Conflict: {{SYNC_CONFLICT}}
```

## Sync Rules

| Data | Offline Behavior | Conflict Rule | Retry | User Feedback |
|---|---|---|---|---|
{{OFFLINE_SYNC_ROWS}}
## Assumptions and Open Questions

{{ASSUMPTIONS}}

## Self-Check

{{SELF_CHECK_NOTE}}

## Related Docs

{{RELATED_DOC_LINKS}}
