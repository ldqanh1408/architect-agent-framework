---
primary_layer: content
---
# Authentication And Authorization Flow

[← Table of Contents]({{INDEX_PATH}}) · *Backend API Module*

## Table of Contents

{{TOC_LINKS}}

{{API_AUTH_FLOW_SUMMARY}}

## Auth Sequence

```mermaid
sequenceDiagram
    participant Client as {{CLIENT}}
    participant IdP as {{IDENTITY_PROVIDER}}
    participant API as {{API_SERVICE}}
    Client->>IdP: {{AUTH_REQUEST}}
    IdP-->>Client: {{AUTH_RESULT}}
    Client->>API: Request with credential
    API->>API: Validate auth and permission
    API-->>Client: {{AUTHORIZED_RESPONSE}}
```

## Permission Rules

| Role/Client | Scope/Permission | Allowed APIs | Denied Behavior |
|---|---|---|---|
{{API_PERMISSION_ROWS}}
## Assumptions and Open Questions

{{ASSUMPTIONS}}

## Self-Check

{{SELF_CHECK_NOTE}}

## Related Docs

{{RELATED_DOC_LINKS}}
