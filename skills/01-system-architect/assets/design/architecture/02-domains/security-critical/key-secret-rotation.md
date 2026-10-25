---
primary_layer: content
---
# Key And Secret Rotation

[← Table of Contents]({{INDEX_PATH}}) · *Security Critical Module*

## Table of Contents

{{TOC_LINKS}}

{{KEY_SECRET_ROTATION_SUMMARY}}

## Rotation Lifecycle

```mermaid
stateDiagram-v2
    Active --> PendingRotation: {{ROTATION_TRIGGER}}
    PendingRotation --> Rotated: {{NEW_SECRET_READY}}
    Rotated --> Verified: {{VERIFICATION_DONE}}
    Verified --> Retired: {{OLD_SECRET_RETIRED}}
```

## Rotation Matrix

| Secret/Key Name | Storage | Rotation Frequency | Owner | Rollback |
|---|---|---|---|---|
{{KEY_SECRET_ROTATION_ROWS}}
## Assumptions and Open Questions

{{ASSUMPTIONS}}

## Self-Check

{{SELF_CHECK_NOTE}}

## Related Docs

{{RELATED_DOC_LINKS}}
