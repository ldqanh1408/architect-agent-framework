---
primary_layer: content
---
# Security Design

[← Table of Contents]({{INDEX_PATH}}) · *Security*

## Table of Contents

{{TOC_LINKS}}

{{SECURITY_SUMMARY}}

## Identity And Access Flow

```mermaid
sequenceDiagram
    actor User as {{USER_ACTOR}}
    participant IdP as {{IDENTITY_PROVIDER}}
    participant App as {{APPLICATION}}
    participant API as {{API_SERVICE}}
    User->>App: Sign in
    App->>IdP: Start auth flow
    IdP-->>App: Token or assertion
    App->>API: Request with credential
    API-->>App: Authorized response
```

## Controls

| Area | Control | Risk Reduced | Verification |
|---|---|---|---|
{{SECURITY_CONTROL_ROWS}}

## Threats And Mitigations

| Threat | Attack Path | Impact | Mitigation | Signal |
|---|---|---|---|---|
{{THREAT_ROWS}}
## Assumptions and Open Questions

{{ASSUMPTIONS}}

## Self-Check

{{SELF_CHECK_NOTE}}

## Related Docs

{{RELATED_DOC_LINKS}}
