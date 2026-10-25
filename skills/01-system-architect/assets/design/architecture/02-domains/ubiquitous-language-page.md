---
primary_layer: content
---
# Ubiquitous Language — {{CONTEXT_NAME}}

[← Table of Contents]({{INDEX_PATH}}) · *Domains › {{CONTEXT_NAME}} › Overview › Language*

## Table of Contents

- [Summary](#summary)
- [Terms](#terms)
- [Terms That Mean Something Else Elsewhere](#terms-that-mean-something-else-elsewhere)
- [Self-Check](#self-check)
- [Related Docs](#related-docs)

## Summary

The system glossary in `01-global-strategy/00-context/glossary.md` pins down the
words the whole system shares. This page pins down the words *this context* uses,
which is not the same list and is sometimes not the same definitions.

That is the point rather than a problem. In DDD a term is only meaningful inside
a boundary, and finding that "order" means something different in fulfilment than
in billing is usually evidence that the boundary is in the right place — or, if
the two meanings turn out to be the same, that it is not.

## Terms

| Term | Meaning in this context | Appears in | Not to be confused with |
|---|---|---|---|
| {{TERM}} | {{DEFINITION_IN_DOMAIN_WORDS}} | {{aggregate / API / event}} | {{NEAREST_CONFUSABLE_TERM}} |

Define terms in the domain's language, not in implementation terms. "A row in the
orders table" is not a definition; "a customer's commitment to buy, which stops
being changeable once picking starts" is.

## Terms That Mean Something Else Elsewhere

| Term | Here it means | Elsewhere it means | Where | How the two are reconciled |
|---|---|---|---|---|
| {{TERM}} | {{LOCAL}} | {{FOREIGN}} | `02-domains/{{other}}/` | {{translation in the ACL / separate names / accepted}} |

A row here should usually correspond to a translation somewhere — an
anticorruption layer, an explicit mapping in a contract, or an accepted
`separate-ways` edge on the context map. A term collision with no reconciliation
is a defect waiting to become a production bug.

## Self-Check

| Claim | How it will be settled |
|---|---|
| Every term used in this context's contracts is defined | VERIFIED-BY-SCRIPT: `check_output_docs.py` term sweep |
| Every collision names its reconciliation | VERIFIED-BY-QUOTE: the last column cites a contract, ACL module, or context-map edge |
| Definitions match how the domain expert speaks | UNVERIFIABLE-AT-PHASE-1: settled by domain review; record the date |

## Related Docs

Link targets below are written for this page's **instantiated** location,
`02-domains/<cluster>/<NN-submodule>/<skill>/00-overview/ubiquitous-language.md` — four levels deeper
than this template file sits. Do not "correct" them against the template's own
path.

- [System Glossary](../../../../../01-global-strategy/00-context/glossary.md)
- [Context Map](../../../../00-overview/context-map.md)
