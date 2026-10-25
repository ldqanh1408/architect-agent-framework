---
page_class: runtime_scenario
id: SCN-002
---

# SCN-002 — Send under a slow payment provider

## Context

A freelancer sends an invoice while Stripe is responding at the edge of its timeout. This is the scenario that
decides whether the gapless-sequence guarantee survives a partial failure, which makes it architecturally
interesting rather than merely common.

## Steps

1. `web-app` → `api-gateway`: `POST /v1/invoices/{id}/send`, `Idempotency-Key` set.
2. `api-gateway` → `20-invoicing`: gRPC `SendInvoice`, deadline 5 s.
3. `20-invoicing`: tenant row lock, number allocated, body frozen, transaction committed. **~16 ms at p99.**
4. `20-invoicing` → `10-payments-adapter`: `CreateSession`, timeout 3 s.
5. `10-payments-adapter` → Stripe: responds at **2.8 s**.
6. `20-invoicing`: status `SENT`, `InvoiceSent` written to the outbox in one transaction.
7. `30-notifications` polls the outbox and emails the client, within 10 s of step 6.

## Failure branch

If step 5 exceeds 3 s, step 4 times out. The invoice stays `DRAFT`, the allocated number is spent, no event is
written, and `502 PAYMENT_PROVIDER_UNAVAILABLE` reaches the caller. A retry with the same `Idempotency-Key`
allocates a **new** number — gaps are legal, reuse is not.

## Observable measures

End-to-end p99 **under 5 s** with the provider at 2.8 s. Number allocation p99 **under 25 ms** (REQ-002).
Zero duplicate numbers under the 10 000-way concurrency test.

## Quality goal

Makes the REQ-002 correctness claim falsifiable under partial failure: if any run of this scenario produces a
reused number, the claim is false regardless of what the unit tests say.
