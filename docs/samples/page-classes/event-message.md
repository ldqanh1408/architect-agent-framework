---
page_class: event_message
---

# `InvoiceSent`

## Business meaning

An invoice left `DRAFT`, carries a number, and a payment link now exists for the client. The event asserts a
fact that already happened; it does not ask anyone to do anything.

## Producer

`20-invoicing`, written to the outbox inside the same transaction that sets `status = SENT`. No other
component may emit it.

## Consumers

`30-notifications` sends the client email. `50-analytics` updates the revenue-pipeline projection.
`40-billing-rules` records the tax point. Each consumer is independent; none may assume ordering against
another consumer's work.

## Schema and evolution

`{ tenant_id, invoice_id, number, amount_minor, currency, sent_at, channel }`. Fields may be added. Removing
a field or narrowing `channel` requires a new major subject and a 90-day overlap during which both are
published.

## Ordering and duplication

Ordered per `invoice_id` by partition key; unordered across invoices. At-least-once delivery, so consumers
dedupe on `(invoice_id, sent_at)`. A duplicate must be a no-op, not a second email.

## Failure handling

After 5 failed deliveries the message moves to `InvoiceSent.dlq` with the original headers intact. The DLQ is
drained by hand; nothing auto-replays, because a replayed send can email a client twice.

## Spec reference

The channel, operation, and payload schema live in `asyncapi-3-0-specification.md` next to this page. This
page explains intent and does not restate the schema.
