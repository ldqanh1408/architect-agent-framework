---
primary_layer: content
---
# Glossary

[← Table of Contents]({{INDEX_PATH}}) · *Global Strategy › Context*

## Table of Contents

- [Summary](#summary)
- [Domain Terms](#domain-terms)
- [Term to Identifier Mapping](#term-to-identifier-mapping)
- [Deliberately Distinguished Terms](#deliberately-distinguished-terms)
- [Assumptions and Open Questions](#assumptions-and-open-questions)
- [Self-Check](#self-check)
- [Related Docs](#related-docs)

## Summary

Two words that mean the same thing, or one word that means two things, cost more
in a specification than anywhere else — because downstream skills read these
pages literally and turn the ambiguity into schema.

The failure is quiet. A brief says "kho" for both *warehouse* and *branch*; the
ERD ends up with `branch_id`, an ADR discusses "Kho A → Kho B", and nobody
notices they might be different concepts until a query returns the wrong rows.

This page fixes each term to one meaning and one identifier.

## Domain Terms

Write the definition as the business would state it, not as the database models
it. If the two differ, that difference belongs in the Notes column and is usually
worth an ASM row.

| Term | Language | Definition | Canonical identifier | Notes |
|---|---|---|---|---|
{{GLOSSARY_ROWS}}

## Term to Identifier Mapping

For bilingual or mixed-language projects, the mapping is the deliverable. Every
business term the brief uses gets exactly one code-side spelling, and every
code-side identifier traces back to exactly one business term.

| Business term (source language) | English term | Code identifier | Appears in |
|---|---|---|---|
{{TERM_MAPPING_ROWS}}

## Deliberately Distinguished Terms

Pairs that sound interchangeable and are not. This section exists because these
are the ones that get merged by accident, and merging them is expensive to undo
once schema and tests have been generated from it.

| Term A | Term B | How they differ | Why the distinction matters here |
|---|---|---|---|
{{DISTINGUISHED_TERM_ROWS}}

## Assumptions and Open Questions

Terms the brief used ambiguously and the reading chosen. Each of these is an
`ASM-xxx` candidate — a wrong guess here propagates into every page downstream.

{{GLOSSARY_ASSUMPTIONS}}

## Self-Check

| Check | Status |
|---|---|
| Every term used in an entity or API contract appears here | {{CHECK_1}} |
| No term maps to two identifiers, and no identifier to two terms | {{CHECK_2}} |
| Ambiguous source-language terms are recorded as ASM rows | {{CHECK_3}} |

## Related Docs

- [Problem Brief](problem-brief.md)
- [Assumptions & Open Questions](assumptions.md)
- [Requirements](../01-requirements/requirements.md)
