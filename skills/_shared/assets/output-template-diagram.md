---
generated: true
primary_layer: content
skill: {{SKILL_ID}}
source_hashes: []
---
# {{TITLE}} [{{STABLE_ID}}]

## Summary

{{THE_VIEW_ITS_SCOPE_AND_WHAT_IT_SHOWS}}

## Detailed Description

{{THE_VIEW_CONTENT_AND_ITS_BOUNDARY}}

### Diagram

Diagram source is the sibling `.puml` with the same stem.

```plantuml
{{PLANTUML_BODY}}
```

{{DIAGRAM_EXPLANATION}}

## Contracts and Invariants

State each as a numbered invariant the rest of the system can be checked against,
not as prose. An invariant nobody can test is a preference.

    {{INVARIANT_NAME}} [{{ID}}-1]
      {{WHAT_MUST_HOLD_AND_WHAT_BREAKS_IF_IT_DOES_NOT}}

## Ownership and Handoffs

| Concern | Owner | Handoff payload | Blocked until |
|---|---|---|---|
| {{CONCERN}} | {{OWNER}} | {{TYPED_REQUEST}} | {{CONDITION}} |

## Traceability

| Claim | Classification | Source | Freshness |
|---|---|---|---|
| {{CLAIM}} | observed / provided / derived / decided / assumed / unknown | {{PATH_OR_ID}} | {{HASH_OR_DATE}} |

## Verification

| Gate | Command | Exit | Evidence time |
|---|---|---:|---|
| {{GATE}} | `{{ARGV}}` | {{EXIT}} | {{TIME}} |

## Open Decisions

{{REQUEST_PAYLOADS_OR_NONE}}
