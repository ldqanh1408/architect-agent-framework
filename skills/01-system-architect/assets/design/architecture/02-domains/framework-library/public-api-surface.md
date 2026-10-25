---
primary_layer: content
---
# Public API Surface

[← Table of Contents]({{INDEX_PATH}}) · *Framework-Library Module*

## Table of Contents

{{TOC_LINKS}}

{{PUBLIC_API_SUMMARY}}

## API Surface Map

```mermaid
classDiagram
    class {{ENTRY_TYPE}} {
        +{{ENTRY_METHOD_1}}()
        +{{ENTRY_METHOD_2}}()
    }
    class {{CONFIG_TYPE}} {
        +{{CONFIG_ATTR_1}}
    }
    class {{RESULT_TYPE}}
    {{ENTRY_TYPE}} --> {{CONFIG_TYPE}} : configured by
    {{ENTRY_TYPE}} --> {{RESULT_TYPE}} : returns
```

## Public Types

| Type / Function | Kind | Stability | Purpose | Since |
|---|---|---|---|---|
{{PUBLIC_TYPE_ROWS}}

Stability values: `stable`, `experimental`, `internal-do-not-use`, `deprecated`.

## Entry Points

| Entry point | How the consumer reaches it | Example |
|---|---|---|
{{ENTRY_POINT_ROWS}}

## What Is Deliberately NOT Public

| Hidden element | Why hidden | Enforcement |
|---|---|---|
{{HIDDEN_ELEMENT_ROWS}}

## Assumptions and Open Questions

{{ASSUMPTIONS}}

## Self-Check

{{SELF_CHECK_NOTE}}

## Related Docs

- [Framework / Library Overview](framework-library-overview.md)
- [Versioning & Compatibility](versioning-compatibility.md)
{{RELATED_DOC_LINKS}}
