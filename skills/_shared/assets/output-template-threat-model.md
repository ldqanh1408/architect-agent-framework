---
generated: true
primary_layer: content
skill: {{SKILL_ID}}
source_hashes: []
---
# {{TITLE}} [{{STABLE_ID}}]

## Summary

{{THE_THREAT_MODEL_ITS_SCOPE_AND_TRUST_BOUNDARY}}

## Detailed Description

| Asset | Threat | STRIDE class | Likelihood | Impact | Control | Owner |
|---|---|---|---|---|---|---|
| {{ASSET}} | {{THREAT}} | {{STRIDE}} | {{LIKELIHOOD}} | {{IMPACT}} | {{CONTROL}} | {{OWNER}} |

### Trust boundary

{{WHAT_CROSSES_THE_TRUST_BOUNDARY_AND_HOW_IT_IS_VERIFIED}}

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
