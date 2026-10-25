> Historical page-class sample. It does not define current core execution.

---
page_class: blocking_finding
---

# Settlement flow has no runtime scenario

## Blocked item

`00-system-views/06-runtime/SCN-003-settle-invoice.md`, and with it the `PAID` branch of the invoice state
machine in `05-state-machines/invoice/`.

## Missing evidence

No `feature_cluster` token for settlement, because the charter describes settlement as "Stripe tells us" with
no actor, no failure mode, and no timing expectation. The slot admits on that token, so it cannot be created —
and writing it anyway would be inventing the flow, not documenting it.

## Owner

The requirement author. The specific gap is one sentence: what the system does when a settlement webhook
arrives for an invoice that is already `PAID`.

## Resume condition

The historical evidence extractor reported `feature_cluster` for settlement. That is observable, not a
judgement — the slot opens by itself once the token appears.

## Cost of delay

Slice 3 of the delivery plan cannot state an exit criterion, so it cannot be scheduled. Every week this stays
open, the webhook handler is built against an assumption nobody wrote down.
