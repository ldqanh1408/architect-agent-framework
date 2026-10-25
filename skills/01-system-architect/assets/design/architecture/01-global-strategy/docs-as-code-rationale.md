---
primary_layer: workflow
---
# Documentation Model — Three Layers and the Docs-as-Code Choice

[← Table of Contents]({{INDEX_PATH}}) · *Global Strategy › Documentation Model*

## Table of Contents

- [Summary](#summary)
- [The Three Layers](#the-three-layers)
- [Why Docs-as-Code](#why-docs-as-code)
- [Alternatives and Their Transition Triggers](#alternatives-and-their-transition-triggers)
- [The Hybrid Path](#the-hybrid-path)
- [Localization and no-loc](#localization-and-no-loc)
- [Assumptions and Open Questions](#assumptions-and-open-questions)
- [Self-Check](#self-check)
- [See Also](#see-also)
- [Related Docs](#related-docs)

## Summary

This workspace is authored as **Docs-as-Code**: Markdown in Git, reviewed through
pull requests, validated by the same CI that validates source. That is a choice,
not a default, so the reasons and the conditions that would reverse it are
recorded here rather than left implicit.

## The Three Layers

Every artifact declares exactly one `primary_layer` in its front-matter. The
layer says who owns the artifact and which failure mode it guards against.

| Layer | What it covers | Owner | Typical artifacts |
|---|---|---|---|
| **content** | Information architecture: metadata model, taxonomy, Markdown sources, glossary, interlinking, deadwood removal | architects and domain owners | requirements, domain models, ADRs, contracts, glossary |
| **workflow** | Docs-as-Code machinery: plain-text authoring, automated checks and linting, PR review and approval, diagrams-as-code | the skill/tooling owners | page contracts, templates, validators, review rules |
| **infrastructure** | Data and delivery: version control, CI/CD, static distribution, security and access control | platform / ops | CI workflows, deployment topology, access control, publishing |

`secondary_layers` records genuine overlap. It never replaces the single primary:
an artifact with two primaries has no owner.

## Why Docs-as-Code

| Force | How Docs-as-Code answers it |
|---|---|
| Docs drift from code | Both live in one repo and move in one pull request. |
| Review is informal | Documentation review is code review, with the same approvals. |
| Diagrams rot | Diagrams are source (C4-PlantUML / PlantUML), diffed like code. |
| Agents need the spec | Markdown is the format LLMs read most reliably, and chunks cleanly on headers. |

## Alternatives and Their Transition Triggers

Neither alternative is wrong; each becomes right under a stated condition.

| Model | What it buys | Transition trigger — adopt when |
|---|---|---|
| **Headless CMS** | A WYSIWYG surface for non-technical editors, publishing workflows, scheduled releases | Non-engineer authors become the majority of contributors **and** Git is the blocker (measured by rejected contributions, not by preference). |
| **DITA / CCMS** | Topic-based reuse at scale, conditional profiling, translation pipelines with formal review | The same content must ship in several product variants **or** regulated translation with per-topic sign-off is contractually required. |

Until a trigger fires, adopting either one costs a toolchain and buys nothing this
workspace needs.

## The Hybrid Path

The intermediate step, if editors need a friendlier surface before a trigger
fires: keep Markdown-in-Git as the single source of truth and put a Git-backed
editing surface in front of it. The SSoT does not move; only the editing
experience changes, so it is reversible.

## Localization and no-loc

Terms that must survive machine translation — brand names, API identifiers,
class and path names — are declared in front-matter as `no_loc_terms: [..]` and
written as inline code spans in prose. The workspace output language is declared
once in `registered planning artifact`; identifiers stay ASCII regardless of it.

## Assumptions and Open Questions

- ASSUMPTION: {{ASSUMPTION}}
- Open question: {{OPEN_QUESTION}}

## Self-Check

| Check | Status |
|---|---|
| Every page declares exactly one `primary_layer` | {{CHECK_1}} |
| Each alternative model carries a testable transition trigger | {{CHECK_2}} |
| `no_loc_terms` is present on pages that name brands or API identifiers | {{CHECK_3}} |

## See Also

- {{RELATED_ADR_IDS}}

## Related Docs

- [Architecture](architecture.md)
- [Solution Strategy](02-strategy/solution-strategy.md)
