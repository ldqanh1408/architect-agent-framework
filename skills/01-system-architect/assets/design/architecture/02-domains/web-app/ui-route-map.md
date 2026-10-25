---
primary_layer: content
---
# UI Route Map

[← Table of Contents]({{INDEX_PATH}}) · *Web App Module*

## Table of Contents

{{TOC_LINKS}}

{{ROUTE_MAP_SUMMARY}}

## Route Diagram

```mermaid
flowchart LR
    Login["{{LOGIN_ROUTE}}"] --> Home["{{HOME_ROUTE}}"]
    Home --> List["{{LIST_ROUTE}}"]
    List --> Detail["{{DETAIL_ROUTE}}"]
    Home --> Settings["{{SETTINGS_ROUTE}}"]
```

## Route Catalog

| ID | Route | Purpose | Access | Data/API | State |
|---|---|---|---|---|---|
{{ROUTE_ROWS}}

## Route Guard Rules

| Route | Guard | Redirect | Failure State |
|---|---|---|---|
{{ROUTE_GUARD_ROWS}}
## Assumptions and Open Questions

{{ASSUMPTIONS}}

## Self-Check

{{SELF_CHECK_NOTE}}

## Related Docs

{{RELATED_DOC_LINKS}}
