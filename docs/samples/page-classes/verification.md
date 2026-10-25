---
page_class: verification
---

# `20-invoicing` — fitness self-check

## Claims checked

That number allocation is unique per tenant under concurrency (REQ-002); that a `SENT` invoice always has a
number and a frozen body; and that no component outside `20-invoicing` writes the `invoices` table.

## Command

```bash
python -m pytest tests/test_invoice_numbering.py tests/test_invoice_invariants.py -q
```

The third claim is checked separately by `architect-cli gate run GATE-LEDGER-OWNER <workspace>`.

## Expected exit

`0` when all three hold. A duplicate number prints
`AssertionError: 2 duplicate numbers for tenant t-004` and exits `1`. A missing workspace makes the gate exit
`2`, which is a setup error, not a failure of the claim.

## Not checked

Nothing here proves behaviour against the real Stripe API — the payment adapter is stubbed. Cross-region
behaviour is not checked because the tenant table is single-region by ADR-0007; if that changes, this page
gains a claim rather than losing one.
