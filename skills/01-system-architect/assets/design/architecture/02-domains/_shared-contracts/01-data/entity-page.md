---
primary_layer: workflow
---
# {{ENTITY_NAME}}

[← Table of Contents]({{INDEX_PATH}}) · *Entity Detail*

## Table of Contents

{{TOC_LINKS}}

## Summary

{{ENTITY_SUMMARY}}

## Core Description & Mechanisms

{{PLACEHOLDER: Provide a deep technical explanation of this entity's role in the domain. Explain data ownership, partitioning strategy, lifecycle triggers, validation logic, and how concurrency or race conditions are handled. This must be a narrative paragraph, not a list.}}

## Entity Lifecycle

```mermaid
stateDiagram-v2
    [*] --> {{INITIAL_STATE}}
    {{INITIAL_STATE}} --> {{ACTIVE_STATE}}: {{ACTIVATE_TRIGGER}}
    {{ACTIVE_STATE}} --> {{TERMINAL_STATE}}: {{CLOSE_TRIGGER}}
    {{TERMINAL_STATE}} --> [*]
```

## Detailed Tables & Data Contracts

### Entity Contract

| Property | Type | Source | Mutation Rule | Visibility |
|---|---|---|---|---|
{{ENTITY_PROPERTY_ROWS}}

### Relationships

| Related Entity | Cardinality | Ownership | Delete Behavior |
|---|---|---|---|
{{ENTITY_RELATIONSHIP_ROWS}}

## Assumptions and Open Questions

{{ASSUMPTIONS}}

## Self-Check

{{SELF_CHECK_NOTE}}

## Related Docs

{{RELATED_DOC_LINKS}}
