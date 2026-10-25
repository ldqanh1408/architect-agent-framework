---
primary_layer: content
---
# Context Map

[← Table of Contents]({{INDEX_PATH}}) · *Domains › Overview › Context Map*

## Table of Contents

- [Summary](#summary)
- [Map](#map)
- [Relationships](#relationships)
- [What Each Pattern Obliges](#what-each-pattern-obliges)
- [Self-Check](#self-check)
- [Related Docs](#related-docs)

## Summary

DDD's strategic artifact. The boxes are the easy part; the value is in the
**type on each edge**, because the type is what generates work downstream.

A conformist edge means no adapter and accepted coupling. An anticorruption-layer
edge means a `60-`-tier integration module is *required*, not optional. Leaving
edges untyped is why the same system decomposes differently on two runs — the
inference gets made by whoever is delegating that day, and nothing records it.

## Map

```mermaid
flowchart LR
    A[{{CONTEXT_A}}]
    B[{{CONTEXT_B}}]
    X[{{EXTERNAL_SYSTEM}}]
    A -->|Customer/Supplier| B
    A -->|ACL| X
```

## Relationships

| Upstream | Downstream | Pattern | Contract | Module the pattern requires |
|---|---|---|---|---|
| {{CTX_A}} | {{CTX_B}} | customer-supplier | API-x | — |
| {{EXTERNAL}} | {{CTX_A}} | anticorruption-layer | API-y | `02-domains/6N-{{vendor}}-adapter/` |

Allowed patterns: `shared-kernel`, `customer-supplier`, `conformist`,
`anticorruption-layer`, `open-host-service`, `published-language`, `partnership`,
`separate-ways`.

## What Each Pattern Obliges

| Pattern | What it commits you to | What it forbids |
|---|---|---|
| `shared-kernel` | joint ownership, coordinated release, an ADR authorising it | unilateral change |
| `customer-supplier` | upstream accepts downstream requirements into its backlog | silent breaking change |
| `conformist` | downstream adopts upstream's model as-is | complaining about the model later |
| `anticorruption-layer` | a translation module downstream owns and pays for | leaking the foreign model inward |
| `open-host-service` | a published, versioned interface for many consumers | per-consumer special cases |
| `published-language` | a shared schema with an evolution policy | breaking consumers without a version |
| `partnership` | joint planning; both fail or both succeed | independent roadmaps |
| `separate-ways` | duplication, accepted deliberately | later surprise at the divergence |

Choosing a pattern is a decision with consequences, which is why several of these
rows deserve an ADR rather than a table cell.

## Self-Check

| Claim | How it will be settled |
|---|---|
| Every edge carries a pattern from the enumerated set | VERIFIED-BY-SCRIPT: V-MAN-6 |
| Every `anticorruption-layer` edge has a module in `module_charter` | VERIFIED-BY-SCRIPT: `check_tier_skeleton.py` |
| Every `shared-kernel` edge cites an authorising ADR | VERIFIED-BY-SCRIPT: id existence check |
| The map matches `logical-l2-submodules.md` | VERIFIED-BY-SCRIPT: COR-5 |

## Related Docs

- [Domains Index](domains-index.md)
- [Logical L2 Submodules](../../00-system-views/logical-l2-submodules.md)
- [Shared Contracts](../_shared-contracts/00-core/contract-design.md)
