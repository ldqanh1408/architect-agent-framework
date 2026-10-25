---
primary_layer: content
---
# Cross-Cutting Concepts — Index

[← Table of Contents]({{INDEX_PATH}}) · *Cross-Cutting › Overview*

## Table of Contents

- [Summary](#summary)
- [Concepts by Category](#concepts-by-category)
- [Concepts Considered and Not Needed](#concepts-considered-and-not-needed)
- [Self-Check](#self-check)
- [Related Docs](#related-docs)

## Summary

arc42 §8 is the section that becomes a melting pot: anything that did not fit
elsewhere ends up here, and after a while nobody can find anything. arc42's own
FAQ names the failure and the answer — group the concepts by category and keep an
index.

A concept belongs here when it spans two or more bounded contexts. A behaviour
that lives in one context belongs in that context's slots, not in this shared
subtree; putting it here is how a single service's retry policy becomes something
every other team believes applies to them.

## Concepts by Category

### Domain and business

| Concept | Page | Contexts it binds |
|---|---|---|
| {{CONCEPT}} | [{{page}}](01-mechanisms/{{page}}) | {{SLUGS}} |

### Architecture and design patterns

| Concept | Page | Contexts it binds |
|---|---|---|
| {{CONCEPT}} | [{{page}}](01-mechanisms/{{page}}) | {{SLUGS}} |

### Safety and security

| Concept | Page | Contexts it binds |
|---|---|---|
| {{CONCEPT}} | [{{page}}](02-security/{{page}}) | {{SLUGS}} |

### Operations

| Concept | Page | Contexts it binds |
|---|---|---|
| {{CONCEPT}} | [{{page}}](03-infrastructure/{{page}}) | {{SLUGS}} |

### User experience

| Concept | Page | Contexts it binds |
|---|---|---|
| {{CONCEPT}} | [{{page}}](01-mechanisms/{{page}}) | {{SLUGS}} |

Drop a category heading entirely when the system has nothing in it. An empty
category is the same defect as an empty folder.

## Concepts Considered and Not Needed

| Concept | Why not | Where it lives instead |
|---|---|---|
| {{CONCEPT}} | {{single-context concern}} | `02-domains/{{slug}}/{{slot}}/` |

## Self-Check

| Claim | How it will be settled |
|---|---|
| Every page under `03-cross-cutting/` is listed here | VERIFIED-BY-SCRIPT: directory listing vs index |
| Every listed concept binds two or more contexts | VERIFIED-BY-QUOTE: the "contexts it binds" column has two or more slugs |
| Nothing single-context has leaked in | VERIFIED-BY-SCRIPT: `check_submodule_sequence.py` |

## Related Docs

- [Fitness Functions](04-fitness-functions/00-overview.md)
- [Quality Attributes](../01-global-strategy/01-requirements/quality-attributes.md)
