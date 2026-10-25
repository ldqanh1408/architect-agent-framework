---
primary_layer: infrastructure
---
# Self Audit

[← Table of Contents]({{INDEX_PATH}})

## Table of Contents

{{TOC_LINKS}}

{{SELF_AUDIT_SUMMARY}}

## How to read the Status column

At Phase 1 there is no code, no test suite and no running system. "PASS" is
therefore not a claim this document is able to make — nothing exists yet that
could have passed. A row saying PASS is reporting on evidence it never looked at,
which is worse than an empty row because it reads like assurance.

So this table records **how a claim will be settled**, not a verdict on it. Use
exactly one of:

| Status | Means | Requires |
|---|---|---|
| `VERIFIED-BY-SCRIPT` | a command was run and exited 0 | the exact command in `Verification` |
| `VERIFIED-BY-QUOTE` | the claim is a literal quote from a source doc | file + line + quoted text |
| `UNVERIFIABLE-AT-PHASE-1` | real, but nothing at this phase can settle it | which phase settles it, and how |
| `DEFERRED-TO-PHASE-N` | deliberately out of scope until phase N | the reason |
| `GAP` | should be covered, is not | what is missing, and who fixes it |

`UNVERIFIABLE-AT-PHASE-1` is a good answer, not an admission. It converts into a
concrete task downstream — "benchmark checkout latency against REQ-012" is
something a later test-planning step can act on; "PASS" is not. Rows with no
verification path at all belong in `GAP`, where someone will see them.

## Core Coverage

| Core Area | Document | Status | Verification | Gap | Action |
|---|---|---|---|---|---|
{{CORE_COVERAGE_ROWS}}

## Traceability And Contract Coverage

| Check | Status | Verification | Evidence In Docs | Remaining Gap |
|---|---|---|---|---|
{{TRACEABILITY_CONTRACT_CHECK_ROWS}}

## Ambiguity And Safety Checks

| Check | Status | Verification | Rule | Note |
|---|---|---|---|---|
{{AMBIGUITY_SAFETY_ROWS}}

## Module Coverage

A module counts as `Activated` only when its directory exists on disk. List the
directory before writing the row: a row claiming a populated concern slot with no
folder behind it is the most common defect in this table, and it is invisible to
anyone reading the document instead of the tree.

| Module | Activated | Directory Exists | Reason | Generated Pages | Status |
|---|---|---|---|---|---|
{{MODULE_COVERAGE_ROWS}}

## Unverifiable At This Phase

Everything the audit could not settle, and what would settle it. This section
being non-empty is the normal, healthy state of a Phase 1 document.

| Claim | Why not verifiable now | Settled by | Owner phase |
|---|---|---|---|
{{UNVERIFIABLE_ROWS}}

## Final Result

{{SELF_AUDIT_RESULT}}

## Assumptions and Open Questions

{{ASSUMPTIONS}}

## Self-Check

{{SELF_CHECK_NOTE}}

## Related Docs

{{RELATED_DOC_LINKS}}
