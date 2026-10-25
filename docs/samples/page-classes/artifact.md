---
page_class: artifact
---

# `outbox` table

## Identity

`invoicing.outbox`, referenced across the workspace as artifact id `ART-outbox`.

## Description

One row per event awaiting publication: `(id, aggregate_id, type, payload_json, created_at, published_at)`.
`published_at IS NULL` means unpublished. Rows are written inside the same transaction as the state change
they describe, which is what makes "invoice is `SENT`" and "`InvoiceSent` exists" a single fact.

## Constraints

`payload_json` must validate against the schema registered for `type`. Rows are retained **7 days** after
`published_at`, then deleted by a nightly job. The table carries a partial index on `published_at IS NULL`,
without which the poller does a sequential scan at ~200 k rows.

## Consumers

The `30-notifications` poller reads and marks rows published. `50-analytics` reads the same rows
independently. Support reads it by hand when a client reports a missing email.

## Blast radius

Renaming `type` or changing `payload_json` shape breaks both pollers silently — they filter on `type` and
would simply stop matching. Any change here requires a `change_request` page listing both consumers, because
neither fails loudly.
