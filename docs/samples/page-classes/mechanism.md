---
page_class: mechanism
---

# Invoice number allocation

## Trigger

A send confirmation for an invoice in `DRAFT`, arriving on the command path of `20-invoicing`.

## Preconditions

The tenant row exists and carries `next_invoice_seq`. The invoice has at least one line item. No number has
been allocated to this invoice before — enforced by a unique index on `(tenant_id, invoice_id)`.

## Algorithm

1. Open a transaction on the tenant row with `SELECT ... FOR UPDATE`.
2. Read `next_invoice_seq`; the allocated number is that value.
3. Write the number onto the invoice and set `body_frozen_at`.
4. Increment `next_invoice_seq` by one.
5. Commit. Only after the commit is the Stripe call made.

## Defaults

Lock wait timeout **3 s**. Sequence starts at **1** per tenant and never resets. Retry on lock timeout:
**2 attempts**, 150 ms apart, then surface the error.

## Failure modes

Lock timeout after retries returns `INVOICE_BUSY` and the invoice stays `DRAFT`. A crash between step 5 and
the Stripe call leaves a numbered invoice still in `DRAFT`: the number is spent, which is legal, because
REQ-002 forbids reuse, not gaps.

## Verification

`pytest tests/test_invoice_numbering.py -q` — includes a 10 000-way concurrent allocation asserting zero
duplicates, and a crash-injection case asserting the number is never handed out twice.
