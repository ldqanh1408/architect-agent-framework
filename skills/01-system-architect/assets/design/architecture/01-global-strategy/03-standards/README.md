---
primary_layer: content
---
# Standards

[← Table of Contents]({{INDEX_PATH}}) · *Global Strategy › Standards*

## Purpose

TOGAF's Standards Library for this workspace: the specifications new work must
conform to, with a status so that "adopted", "being trialled" and "on its way
out" stop being the same sentence.

## Structure

| File | Holds |
|---|---|
| `standards-register.md` | the register: one row per standard, with domain, status, scope, owner, source |
| `<topic>-standards.md` | the detail for a standard that needs more than a register row to be compliable — `api-standards.md`, `security-standards.md`, `data-standards.md` |

Create a topic page only when the register row is insufficient. Most standards
are compliable from one row plus a link to the external spec.

## Exists from

The `standard` level. Below that, a single project with one team does not have a
standards *library*; it has decisions, and those live in
`05-governance/decisions/`.

## Related Docs

- [Standards Register](standards-register.md)
- [Fitness Functions](../../03-cross-cutting/04-fitness-functions/00-overview.md)
- [Technology Selection](../02-strategy/technology-selection.md)
