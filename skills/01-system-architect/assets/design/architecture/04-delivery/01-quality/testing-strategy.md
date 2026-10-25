---
primary_layer: infrastructure
---
# Testing Strategy

[← Table of Contents]({{INDEX_PATH}})

## Table of Contents

{{TOC_LINKS}}

{{TESTING_SUMMARY}}

## Test Pyramid

```mermaid
flowchart TB
    E2E["E2E / User Acceptance"] --> Contract["Contract / API / Message"]
    Contract --> Integration["Integration"]
    Integration --> Unit["Unit"]
```

| Layer | Scope | Tooling | Entry Criteria | Exit Criteria |
|---|---|---|---|---|
{{TEST_LAYER_ROWS}}

## Acceptance Checks

| Requirement | Scenario | Expected Result | Test Type |
|---|---|---|---|
{{ACCEPTANCE_CHECK_ROWS}}
## Assumptions and Open Questions

{{ASSUMPTIONS}}

## Self-Check

{{SELF_CHECK_NOTE}}

## Related Docs

{{RELATED_DOC_LINKS}}
