---
primary_layer: content
---
# Segments

[← Table of Contents]({{INDEX_PATH}}) · *Domains › Overview › Segments*

## Table of Contents

- [Summary](#summary)
- [Why This Is a Manifest and Not a Folder Level](#why-this-is-a-manifest-and-not-a-folder-level)
- [Segment Register](#segment-register)
- [Segment-Scoped Decisions](#segment-scoped-decisions)
- [Self-Check](#self-check)
- [Related Docs](#related-docs)

## Summary

TOGAF partitions the Architecture Landscape into Strategic, Segment and
Capability levels because volume forces it. This workspace already has the first
and the third: `00-system-views/` is strategic, each
`02-domains/<cluster>/<NN-submodule>/<skill>/` is a capability. This page is the middle one.

It only exists at the `portfolio` level. At four contexts, `domains-index.md` is
enough. At eighteen, a flat list of eighteen sibling folders with one index is
not navigation, and nothing can be reviewed or owned at an intermediate
granularity.

## Why This Is a Manifest and Not a Folder Level

The obvious implementation — `02-domains/<segment>/<cluster>/<NN-submodule>/<skill>/` — is the wrong
one. It pushes every context down one level, which breaks stable numbering (P2),
invalidates every `source-map.yml`, breaks the tier-range logic in
`check_tier_skeleton.py`, and forces a `git mv` of spec pages on promotion, which
P10 says is a design bug rather than a migration task.

The tier ranges (`00-`–`09-` frontend, `10-`–`19-` backend, …) already partition
the landscape. What was missing was only that the partition had no artifact. So
the segment layer is this table plus a `segment` field on each `module_charter`
row. Zero files move, and a workspace that never reaches `portfolio` pays
nothing.

## Segment Register

| ID | Segment | Tier range | Owning team | Contexts | Quality goals it owns |
|---|---|---|---|---|---|
| SEG-1 | {{NAME}} | `10-`–`19-` | {{TEAM}} | {{SLUGS}} | QS-x, QS-y |
| SEG-2 | {{NAME}} | `60-`–`69-` | {{TEAM}} | {{SLUGS}} | QS-z |

Every `module_charter` row must carry a `segment` value that appears here; an
unlisted segment is a finding, not a free-text label.

## Segment-Scoped Decisions

Some ADRs bind one segment rather than the whole system. Recording the scope is
what lets a segment evolve without renegotiating the entire estate.

| ADR | Segment | What it binds |
|---|---|---|
| ADR-000x | SEG-1 | {{SCOPE}} |

## Self-Check

| Claim | How it will be settled |
|---|---|
| Every `module_charter.segment` value appears in this register | VERIFIED-BY-SCRIPT: V-MAN-2 |
| Every segment has an owning team | VERIFIED-BY-QUOTE: non-empty column, traced to the brief or an ASM row |
| Segment ids match `c0-landscape.md` | VERIFIED-BY-SCRIPT: cross-reference |
| The segmentation is the right one | UNVERIFIABLE-AT-PHASE-1: settled by the first portfolio review |

## Related Docs

- [Domains Index](domains-index.md)
- [Context Map](context-map.md)
- [System Landscape](../../00-system-views/c0-landscape.md)
