---
page_class: api_contract
---

# `API-invoice-send` — send an invoice

## Operations

`POST /v1/invoices/{id}/send` moves a `DRAFT` invoice to `SENT`, allocating its number and creating a payment
session. It is the only write path out of `DRAFT`.

## Parameters and representation

Path: `id` (UUID). Body: `{ "channel": "email" | "manual" }`. Response `200`:
`{ "number": "2026-00418", "status": "SENT", "payment_url": "https://...", "expires_at": "..." }`.
All timestamps are RFC 3339 in UTC.

## Errors

`409 INVOICE_NOT_DRAFT` — the invoice already left `DRAFT`. `409 INVOICE_BUSY` — number allocation could not
take the tenant lock. `422 INVOICE_EMPTY` — no line items. `502 PAYMENT_PROVIDER_UNAVAILABLE` — Stripe refused;
the invoice stays `DRAFT`.

## Idempotency

The caller supplies `Idempotency-Key`. A repeat with the same key returns the first response unchanged for
**24 hours**, including the original `number`. A repeat without the key on an already-`SENT` invoice returns
`409 INVOICE_NOT_DRAFT`.

## Versioning and compatibility

`/v1` is supported until at least 2027-06-30. Adding a response field is not a break; removing one or
narrowing an enum is, and carries **90 days** notice on the changelog feed.

## Security

Bearer token scoped to the owning tenant. A token for another tenant returns `404`, never `403`, so the API
does not confirm that an invoice id exists.

## Verification

`pytest tests/contract/test_invoice_send.py -q` runs the published examples against the running service and
fails if any documented error code is unreachable.

## Spec reference

The machine-readable surface is `openapi-3-1-specification.md`, a sibling in this API's directory. This page
explains the intent and does not restate the schema.
