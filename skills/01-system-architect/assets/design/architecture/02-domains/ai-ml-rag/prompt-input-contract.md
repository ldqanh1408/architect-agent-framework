---
primary_layer: content
---
# Prompt Input Contract

[← Table of Contents]({{INDEX_PATH}}) · *AI ML RAG Module*

## Table of Contents

{{TOC_LINKS}}

{{PROMPT_INPUT_SUMMARY}}

## Prompt Flow

```mermaid
sequenceDiagram
    participant User
    participant App as {{APPLICATION}}
    participant Model as {{MODEL_PROVIDER}}
    User->>App: {{USER_INPUT}}
    App->>App: Validate and enrich prompt
    App->>Model: Send prompt contract
    Model-->>App: Structured output
    App-->>User: Render response
```

## Input Schema

```
{{PROMPT_INPUT_JSON}}
```

| Field | Type | Required | Validation | Purpose |
|---|---|---|---|---|
{{PROMPT_INPUT_FIELD_ROWS}}
## Assumptions and Open Questions

{{ASSUMPTIONS}}

## Self-Check

{{SELF_CHECK_NOTE}}

## Related Docs

{{RELATED_DOC_LINKS}}
