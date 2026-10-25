---
generated: true
primary_layer: content
page_class: overview
skill: backend-service-architect
cluster: 03_application_architecture
module: {{MODULE_NAME}}
source_hashes: []
---
# {{MODULE_TITLE}} [{{STABLE_ID}}]

[← Table of Contents]({{INDEX_PATH}})

## Table of Contents

- [Summary](#summary)
- [Detailed Description](#detailed-description)
- [Contracts and Invariants](#contracts-and-invariants)
- [Ownership and Handoffs](#ownership-and-handoffs)
- [Traceability](#traceability)
- [Verification](#verification)
- [Open Decisions](#open-decisions)

## Summary

{{ONE_PARAGRAPH: what this module decides, its scope, and what it rules out.}}

> This paragraph is the **only** text the parent's blackbox band extracts. Write it
> so it reads correctly standing alone on the C1 page, because that is where it
> will appear.

## Detailed Description

{{FORCES_MECHANISM_AND_BOUNDARY}}

### Alternatives rejected

| Option | Why it was not taken | Under what evidence it would win |
|---|---|---|
| {{OPTION}} | {{REASON}} | {{REVERSAL_TRIGGER}} |

## Contracts and Invariants

State each as a numbered invariant the rest of the system can be checked against,
not as prose. An invariant nobody can test is a preference.

    {{INVARIANT_NAME}} [{{ID}}-1]
      {{WHAT_MUST_HOLD_AND_WHAT_BREAKS_IF_IT_DOES_NOT}}

## Ownership and Handoffs

Rows marked `external` are the ones the parent's blackbox band renders as the
interface table. Keep them true at the boundary, not at the implementation.

| Concern | Direction | Owner | Handoff payload | Blocked until |
|---|---|---|---|---|
| {{CONCERN}} | inbound \| outbound \| internal | {{OWNER}} | {{TYPED_REQUEST}} | {{CONDITION}} |

## Traceability

| Claim | Classification | Source | Freshness |
|---|---|---|---|
| {{CLAIM}} | provided / observed / derived / decided / assumed / unknown | {{PATH_OR_ID}} | {{HASH_OR_DATE}} |

Assumptions and open questions live here, classified `assumed` and `unknown`
respectively — not in a separate section a checker never learns about.

## Verification

| Gate | Command | Exit | Evidence time |
|---|---|---:|---|
| {{GATE}} | `{{ARGV}}` | {{EXIT}} | {{TIME}} |

Legal verdicts, and only these five: `VERIFIED-BY-SCRIPT` · `VERIFIED-BY-QUOTE` ·
`UNVERIFIABLE-AT-PHASE-1` · `DEFERRED-TO-PHASE-N` · `GAP`. At design time there is
no code, so `PASS` is not optimistic — it is not well-formed.

## Open Decisions

{{REQUEST_PAYLOADS_OR_NONE}}
