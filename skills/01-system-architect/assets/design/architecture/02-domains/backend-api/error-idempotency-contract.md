---
primary_layer: content
---
# Error And Idempotency Contract

[← Table of Contents]({{INDEX_PATH}}) · *Backend API Module*

## Table of Contents

{{TOC_LINKS}}

{{ERROR_IDEMPOTENCY_SUMMARY}}

## Error Format

```
{{ERROR_FORMAT_JSON}}
```

| Status | Error Code | Meaning | Client Action |
|---|---|---|---|
{{ERROR_STATUS_ROWS}}

## Idempotency Rules

| Operation | Key Source | Dedup Window | Replay Response | Storage |
|---|---|---|---|---|
{{IDEMPOTENCY_ROWS}}
## Assumptions and Open Questions

{{ASSUMPTIONS}}

## Self-Check

{{SELF_CHECK_NOTE}}

## Related Docs

{{RELATED_DOC_LINKS}}
