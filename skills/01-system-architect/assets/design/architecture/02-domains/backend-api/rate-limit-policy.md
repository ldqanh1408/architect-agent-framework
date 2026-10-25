---
primary_layer: content
---
# Rate Limit Policy

[← Table of Contents]({{INDEX_PATH}}) · *Backend API Module*

## Table of Contents

{{TOC_LINKS}}

{{RATE_LIMIT_SUMMARY}}

## Limit Matrix

| Consumer | Endpoint/Group | Limit | Window | Burst | Response |
|---|---|---|---|---|---|
{{RATE_LIMIT_ROWS}}

## Throttle Behavior

```mermaid
flowchart LR
    Request["Incoming request"] --> Check["Check quota"]
    Check -->|Allowed| Process["Process request"]
    Check -->|Limited| Reject["Return {{RATE_LIMIT_STATUS}}"]
```
## Assumptions and Open Questions

{{ASSUMPTIONS}}

## Self-Check

{{SELF_CHECK_NOTE}}

## Related Docs

{{RELATED_DOC_LINKS}}
