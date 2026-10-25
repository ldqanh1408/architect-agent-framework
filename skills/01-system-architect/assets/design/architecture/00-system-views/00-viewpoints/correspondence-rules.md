---
primary_layer: content
---
# Correspondence Rules

[← Table of Contents]({{INDEX_PATH}}) · *System Views › Viewpoints › Correspondences*

## Table of Contents

- [Summary](#summary)
- [Rules](#rules)
- [Known Divergences](#known-divergences)
- [Self-Check](#self-check)
- [Related Docs](#related-docs)

## Summary

Views drift. The container diagram gets a new service, the deployment diagram
does not, and six weeks later two documents describe two different systems and
both look authoritative.

ISO/IEC/IEEE 42010 handles this with **correspondence rules**: explicit
statements of what must agree across views, so drift becomes a check that fails
rather than a discrepancy someone eventually notices. `visual-source-map.md`
records where a diagram's source lives; this page records what two views owe
each other.

## Rules

| ID | Between | What must agree | Direction | Enforced by |
|---|---|---|---|---|
| COR-1 | `c2-container.md` ↔ `02-domains/*/` | every Container id maps to a `module_charter` row with a runtime footprint | container is derived from charter | `check_tier_skeleton.py` |
| COR-2 | `c2-container.md` ↔ `c4-deployment.md` | every container appears on exactly one node | deployment refines container | review |
| COR-3 | `06-runtime/SCN-*.md` ↔ `c2-container.md` | every participant in a scenario is a container or an external system in C1 | scenario refines container | `check_output_docs.py` |
| COR-4 | `06-runtime/SCN-*.md` ↔ `01-requirements/quality-attributes.md` | every scenario names the QS-xxx it exercises | scenario realises quality scenario | V-MAN-5 |
| COR-5 | `logical-l2-submodules.md` ↔ `02-domains/00-overview/context-map.md` | the same bounded contexts and the same edges | visual is derived from the map | review |
| COR-6 | `_shared-contracts/**` ↔ per-context pages | a contract id used in a context exists in the shared catalogue | contract is upstream | `check_seam_coverage.py` |
| COR-7 | `04-fitness-functions/FIT-*.md` ↔ `03-standards/standards-register.md` | a rule enforcing a standard cites its STD-xxx and that standard is not `retired` | rule enforces standard | V-MAN-5 |

Direction matters: it says which side is the source when the two disagree. A
correspondence with no direction turns every drift into an argument.

## Known Divergences

Where two views legitimately differ, say so here rather than letting a reader
discover it and assume one is stale.

| Rule | Divergence | Why it is intentional | Revisit when |
|---|---|---|---|
| COR-x | {{WHAT_DIFFERS}} | {{REASON}} | {{TRIGGER}} |

## Self-Check

| Claim | How it will be settled |
|---|---|
| Each rule names two real artifacts | VERIFIED-BY-SCRIPT: path existence check |
| Rules with an enforcing script actually fail on a violation | VERIFIED-BY-SCRIPT: the named checker has a bad fixture |
| Rules marked "review" have an owner and a cadence | UNVERIFIABLE-AT-PHASE-1: settled at the first review; record the date |

## Related Docs

- [Viewpoint Catalog](viewpoint-catalog.md)
- [Stakeholder–Concern Matrix](stakeholder-concern-matrix.md)
- [Visual Source Map](../visual-source-map.md)
