---
primary_layer: content
---
# Viewpoint Catalog

[← Table of Contents]({{INDEX_PATH}}) · *System Views › Viewpoints › Catalog*

## Table of Contents

- [Summary](#summary)
- [Viewpoints In Use](#viewpoints-in-use)
- [Viewpoint Definitions](#viewpoint-definitions)
- [Viewpoints Considered and Not Used](#viewpoints-considered-and-not-used)
- [Self-Check](#self-check)
- [Related Docs](#related-docs)

## Summary

A viewpoint is the *convention* for building a kind of view: which concerns it
frames, what model kinds it uses, what notation, and what it deliberately leaves
out. A view is one application of a viewpoint to this system.

Keeping the conventions in one place is what stops the fifth diagram from
inventing its own notation, and it is also this workspace's local Viewpoint
Library in TOGAF's Reference Library sense.

## Viewpoints In Use

| ID | Viewpoint | Concerns framed | Model kind / notation | Views realising it |
|---|---|---|---|---|
| VP-1 | Context | scope, external dependencies, who uses this | C4 L1 | [c1-context.md](../c1-context.md) |
| VP-2 | Container | what is deployed and what it runs on | C4 L2 | [c2-container.md](../c2-container.md) |
| VP-3 | Runtime | how a critical flow actually executes, including failure | C4 Dynamic / UML sequence | [06-runtime/](../06-runtime/) |
| VP-4 | Deployment | where things run, sizing, recovery | C4 Deployment | [c4-deployment.md](../c4-deployment.md) |
| VP-5 | Logical decomposition | ownership boundaries, bounded contexts | DDD context map | [logical-l2-submodules.md](../logical-l2-submodules.md) |

Add rows only for viewpoints this system actually uses. A catalogue listing
viewpoints with no views is the documentation equivalent of an empty folder.

## Viewpoint Definitions

### VP-{{N}} — {{NAME}}

- **Concerns framed:** CON-x, CON-y (from [stakeholder-concern-matrix.md](stakeholder-concern-matrix.md))
- **Typical stakeholders:** STK-x, STK-y
- **Model kinds:** {{e.g. C4 container diagram plus a container responsibility table}}
- **Notation:** {{PlantUML C4 / Mermaid / table}}
- **Deliberately out of scope:** {{what this viewpoint refuses to show, and which viewpoint shows it instead}}
- **Consistency obligations:** see [correspondence-rules.md](correspondence-rules.md)

The "deliberately out of scope" line does more work than it looks like. Most
unreadable architecture diagrams are one viewpoint quietly answering four
concerns at once.

## Viewpoints Considered and Not Used

| Viewpoint | Why not used here |
|---|---|
| {{e.g. C4 Code (L4)}} | {{generated from source once code exists; drawing it now would be fiction}} |

## Self-Check

| Claim | How it will be settled |
|---|---|
| Every viewpoint row has at least one realising view | VERIFIED-BY-SCRIPT: `check_output_docs.py` |
| Every concern in the matrix is framed by a viewpoint here | VERIFIED-BY-SCRIPT: V-MAN-4 |
| The notation choices are followed by the actual pages | VERIFIED-BY-QUOTE: spot-check each realising view's front-matter |

## Related Docs

- [Stakeholder–Concern Matrix](stakeholder-concern-matrix.md)
- [Correspondence Rules](correspondence-rules.md)
- [Visual Source Map](../visual-source-map.md)
