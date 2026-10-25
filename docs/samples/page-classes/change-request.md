---
page_class: change_request
id: CR-012
---

# CR-012 — `InvoiceSent.channel` gains a `portal` value

## Semantic change

`channel` meant "how the client was told" with values `email` and `manual`. It now also admits `portal`,
meaning the client was not told at all and will find the invoice by logging in. Consumers that treated
`channel` as "a message was sent" become wrong.

## Touched ids

`InvoiceSent` (message), `API-invoice-send` (request body enum), `REQ-007` (delivery requirement), and the
`Invoice.delivery_channel` column.

## Impact graph

From `InvoiceSent`: `30-notifications` (would send nothing and must not treat that as a failure),
`50-analytics` (its "delivered" metric silently changes meaning). From `API-invoice-send`: the SPA's send
dialog. Computed from `source-map.yml` plus the `traces` frontmatter of each page, not by hand.

## Decision

Accepted, 2026-04-02, with the condition that `50-analytics` ships its metric rename in the same release —
otherwise a dashboard keeps a name that no longer describes what it counts.

## Migration

1. Add `portal` to the enum, published under the existing major subject (additive, per the evolution rule).
2. `30-notifications` skips `portal` and records `delivery_skipped`, not `delivery_failed`.
3. `50-analytics` renames `delivered_total` to `notified_total` and adds `portal_total`.
4. Only then does the SPA expose the new option.

## Verification

`pytest tests/contract/test_invoice_sent_schema.py -q` fails if any consumer still branches on two values, and
`architect-cli gate run GATE-TRACEABILITY-GRAPH <workspace>` fails if a touched id has no downstream page
updated.
