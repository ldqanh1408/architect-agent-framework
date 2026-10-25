---
page_class: standard_entry
id: STD-014
---

# STD-014 — Money is stored as minor units in an integer

## Statement

Every monetary value persisted or transmitted is an integer count of the currency's minor unit, paired with an
ISO 4217 code. A float or a decimal string in a money field is a violation. Conformance is decidable by
reading the column type and the field name.

## Scope

All services, all tables, all message payloads. It binds new work from 2026-01-01 and any table touched by a
migration after that date.

## Lifecycle status

**Active** since 2026-01-01. It replaced STD-009, which allowed `NUMERIC(12,2)` and was retired after a
rounding defect in multi-currency totals.

## Enforcement

`GATE-SDD-SEMANTIC-RULES` flags any column matching `amount|price|total|fee` whose type is not an integer, and
any schema field of those names typed `number`. A violation fails the phase, not just the review.

## Exemptions

`legacy_ledger.amount_decimal` is exempt until its migration lands, approved by the platform lead on
2026-02-04. The exemption names an end date; one without an end date is not granted.
