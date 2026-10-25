---
primary_layer: content
---
# Governance

[← Table of Contents]({{INDEX_PATH}}) · *Global Strategy › Governance*

## Purpose

TOGAF's Governance Repository. It is broader than a decision log, and splitting
it out from the old `02-decisions/` slot is what made room for the rest.

## Contents

| Path | Holds |
|---|---|
| `decisions/` | the ADR log — one file per architecturally significant decision, plus `0000-deferred-register.md` for candidates deliberately not designed |
| `compliance-log.md` | assessments, findings, and standards deviations: what happened when someone checked whether the decisions were followed |

## Why both

A project can hold a complete ADR set and a complete set of review findings and
still have no way to connect the two. The compliance log is the join: an ADR that
was later found violated, and the action taken.

At Phase 1 `compliance-log.md` is correctly almost empty — nothing has been built,
so nothing can have been assessed. Filling it with invented assessments is the
failure the Self-Audit Honesty rules exist to prevent.

## Related Docs

- [Standards Register](../03-standards/standards-register.md)
- [Fitness Functions](../../03-cross-cutting/04-fitness-functions/00-overview.md)
