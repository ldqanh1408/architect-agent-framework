---
page_class: adr
id: ADR-0007
---

# ADR-0007 — Allocate invoice numbers under a tenant row lock

## Status

Accepted, 2026-03-11. Supersedes ADR-0004.

## Context

REQ-002 requires a gapless, never-reused invoice sequence per tenant. Sends are concurrent, and the allocation
happens immediately before an external call that can fail.

## Options

1. Row lock on the tenant record (`SELECT ... FOR UPDATE`).
2. A database sequence per tenant.
3. A distributed counter in Redis with a Lua allocation script.

## Evidence

`invoice-sequence-assessment.md` — the `decision`-class page next to this ADR — scores the three on
correctness under partition, latency at p99, and operational surface. Option 3 was fastest by 8 ms and the
only one that can silently lose the counter on a failover.

## Decision

Allocate under a tenant row lock, in the same transaction that freezes the invoice body.

## Consequences

Sends against a single tenant serialise. At the measured ceiling — 40 sends/second per tenant — that is
comfortable, but a tenant above ~200/second would need re-deciding. Cross-region active-active is ruled out
for this table.

## Enforcement

`GATE-CONTENT-DEPTH` on `01-invoicing/invoicing-design.md`, plus the concurrency test named in
[`mechanism.md`](mechanism.md), which fails if allocation moves outside the transaction.

## Reversal conditions

A tenant sustaining more than 200 sends/second, or a requirement for active-active writes on the tenant
table. Either observation opens a new ADR that supersedes this one.
