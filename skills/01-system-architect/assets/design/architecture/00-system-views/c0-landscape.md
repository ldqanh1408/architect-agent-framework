---
primary_layer: content
viewpoint: system-landscape
stakeholders: [{{STK_IDS}}]
concerns: [{{CONCERN_IDS}}]
---
# C0 — System Landscape

[← Table of Contents]({{INDEX_PATH}}) · *System Views › Landscape*

## Table of Contents

- [Summary](#summary)
- [When This Page Exists](#when-this-page-exists)
- [Landscape](#landscape)
- [Systems](#systems)
- [Ownership](#ownership)
- [Self-Check](#self-check)
- [Related Docs](#related-docs)

## Summary

C4's System Landscape view: the map of *several* systems, with this workspace's
system-of-interest as one box among them. It answers "what else is in this
estate and who owns it", which the context diagram cannot answer without
ceasing to be a context diagram.

## When This Page Exists

Only at the `portfolio` level — more than one system-of-interest, or more than
one owning team. Below that it is noise, and generating it early is exactly the
kind of empty ceremony `P11` exists to prevent.

The failure it prevents is specific: without this slot, a growing estate gets
crammed into `c1-context.md` one system at a time, until that page shows four
systems, twelve externals, and no longer tells anyone what the boundary is.

## Landscape

```mermaid
flowchart LR
    subgraph Estate[{{ORGANISATION}}]
        SOI[{{SYSTEM_OF_INTEREST}}]:::soi
        S2[{{NEIGHBOUR_SYSTEM}}]
        S3[{{NEIGHBOUR_SYSTEM}}]
    end
    EXT[{{EXTERNAL_PARTY}}]
    SOI -->|{{CONTRACT_ID}}| S2
    S3 -->|{{CONTRACT_ID}}| SOI
    SOI -->|{{CONTRACT_ID}}| EXT
    classDef soi stroke-width:3px;
```

## Systems

| System | In scope here | Owning team | Relationship to the system-of-interest | Contract |
|---|---|---|---|---|
| {{SYSTEM}} | yes / no | {{TEAM}} | {{upstream / downstream / peer}} | {{API-x / MSG-x}} |

"In scope here" is the column that keeps this page from turning into an
enterprise inventory. Systems marked `no` appear because they touch us, not
because we document them.

## Ownership

| Segment | Systems | Owning team | Where its architecture lives |
|---|---|---|---|
| SEG-x | {{SYSTEMS}} | {{TEAM}} | {{path or external link}} |

Cross-reference `02-domains/00-overview/segments.md`; the two must agree on
segment ids.

## Self-Check

| Claim | How it will be settled |
|---|---|
| The workspace is at the `portfolio` level | VERIFIED-BY-QUOTE: `planning metadata: selected_profile` in `registered planning artifact` |
| Every edge cites a contract id | VERIFIED-BY-SCRIPT: `check_seam_coverage.py` |
| Segment ids match `segments.md` | VERIFIED-BY-SCRIPT: V-MAN-2 |
| The estate list is complete | UNVERIFIABLE-AT-PHASE-1: settled by portfolio review |

## Related Docs

- [C1 Context](c1-context.md)
- [Segments](../02-domains/00-overview/segments.md)
- [Viewpoint Catalog](00-viewpoints/viewpoint-catalog.md)
