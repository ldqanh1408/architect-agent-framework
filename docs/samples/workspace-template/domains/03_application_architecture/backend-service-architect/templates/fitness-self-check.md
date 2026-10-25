---
generated: true
primary_layer: content
page_class: verification
skill: backend-service-architect
---
# Fitness Self-Check: {{MODULE_TITLE}} [{{STABLE_ID}}-FIT]

[← Table of Contents]({{INDEX_PATH}})

## Summary

Records this module's fitness functions and the verdict each currently carries.
A self-check is **supporting evidence only**; where an executable gate exists, the
gate is authoritative and this page cites its argv and exit code.

## Detailed Description

Every rule below is prefixed `BSA-FIT` — **this skill's own `fitness_prefix` from
`skill-contract.yml`**, not a tier child's placeholder. A page that writes `BE-FIT`
is citing a skill that has no package and cannot be resolved.

> Known catalog defect (G-C): 20 of the 110 exported skills share a
> `fitness_prefix` with a sibling — only 54 distinct values exist. Until the ID is
> cluster-qualified, write `03_application_architecture:BSA-FIT-01` where the plain
> form would be ambiguous.

| Rule | What it asserts | Four-axis type |
|---|---|---|
| `BSA-FIT-01` | {{ASSERTION}} | atomic \| holistic · triggered \| continuous · static \| dynamic · automated \| MANUAL |

## Traceability

| Claim | Classification | Source | Freshness |
|---|---|---|---|
| `BSA-FIT-01` cites `QA-{{NNN}}` | derived | `architecture/01-global-strategy/01-requirements/quality-scenarios/QA-{{NNN}}.md` | {{HASH}} |

## Verification

| Rule | Verdict | Command / quote | Exit | Evidence time |
|---|---|---|---:|---|
| `BSA-FIT-01` | `UNVERIFIABLE-AT-PHASE-1` | settles when {{CONDITION}}, by {{DATE}} | — | {{TIME}} |
| `BSA-FIT-02` | `VERIFIED-BY-QUOTE` | `{{FILE}}:{{LINE}}` — "{{QUOTED_TEXT}}" | — | {{TIME}} |
| `BSA-FIT-03` | `VERIFIED-BY-SCRIPT` | `{{ARGV}}` | 0 | {{TIME}} |
| `BSA-FIT-04` | `GAP` | {{WHAT_IS_MISSING_AND_WHO_OWNS_IT}} | — | {{TIME}} |

**`UNVERIFIABLE-AT-PHASE-1` should be the majority.** A positive-verdict share above
about one third means the claims were narrowed until they fit a checker. A unanimous
table is a signal to look again, not a clean bill of health (V-11).

## Open Decisions

{{OQ_ROWS_OR_NONE}}
