---
page_class: data_entity
---

# `Invoice`

## Identity and grain

Key `(tenant_id, invoice_id)`. One row is one invoice for one client at one point in its lifecycle. Line items
are a child table; a row here is never a line.

## Lifecycle

Created as `DRAFT` when the freelancer starts one. Moves to `SENT` on UC-004. From `SENT` it reaches `PAID`
on a settled Stripe webhook, or `VOID` when the freelancer cancels. `PAID` and `VOID` are terminal.

## Invariants

`status = SENT` implies `number IS NOT NULL AND body_frozen_at IS NOT NULL`. `number` is unique per
`tenant_id`. A row in `PAID` never changes again except for `updated_at`.

## Writer

`20-invoicing` only. `10-payments-adapter` proposes a settlement by publishing an event; it does not write
this table.

## Retention and deletion

Kept **10 years** after `PAID` or `VOID` for tax audit. A deletion request anonymises the client name and
email in place and leaves the number, amount, and dates — the sequence must stay gapless.

## Privacy

`client_email` and `client_name` are personal data under GDPR. `amount` and `number` are business records and
are not erasable.

## Consistency

Readers outside `20-invoicing` see `SENT` only after the allocating transaction commits. A reader polling
during a send observes `DRAFT`, never a half-numbered row.
