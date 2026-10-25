---
page_class: requirement
id: REQ-002
---

# REQ-002 — An invoice number is allocated exactly once

## Statement

Every invoice that reaches `SENT` carries exactly one sequential number, and no number is ever reused, even
across a failed send attempt.

## Trigger and response

The freelancer confirms a send. The system allocates the next number in the tenant's sequence and freezes the
invoice body before any external call is made.

## Rationale

Tax authorities in the launch markets require a gapless, non-reused invoice sequence. A reused number is an
accounting defect the customer cannot correct after the fact.

## Measurable threshold

Zero duplicate numbers per tenant across 10 000 concurrent sends; allocation adds no more than **25 ms** at the
99th percentile.

## Boundaries

This governs the number only. Invoice *content* immutability after `SENT` is REQ-009. Credit notes have a
separate sequence and are out of scope here.

## Unknowns

Whether one market requires a per-calendar-year reset is unconfirmed with counsel. If it does, the sequence
key gains a year component and the uniqueness test changes shape.
