---
page_class: overview
---

# `20-invoicing` — overview

## Scope

Everything between a freelancer pressing **Send** and an `InvoiceSent` event reaching the outbox: number
allocation, body freezing, state transitions, and delivery bookkeeping.

## Responsibilities

Owns the invoice aggregate and its state machine (`DRAFT → SENT → PAID | VOID`). It is the only writer of
invoice numbers, and the only component allowed to move an invoice out of `DRAFT`.

## Boundaries

Payment sessions belong to `10-payments-adapter`; this module calls it and never talks to Stripe directly.
Email delivery belongs to `30-notifications`. Tax rates belong to `40-billing-rules`.

## Not doing

It does not compute tax, does not store payment credentials, and does not retry failed sends on a schedule —
a failed send leaves a `DRAFT` and a human decides. That keeps the gapless-sequence guarantee (REQ-002)
provable without a distributed lock.

## Read next

`01-invoicing/invoicing-design.md` for the mechanism, `UC-004` for the flow a user sees, and `source-map.yml`
for what this module provides and consumes.
