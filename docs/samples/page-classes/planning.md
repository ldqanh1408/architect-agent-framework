---
page_class: planning
---

# Invoicing — delivery plan

## Slices

1. **Draft and edit** — create, edit, delete a `DRAFT`. Ships alone; no external dependency.
2. **Send** — number allocation, body freeze, Stripe session, `SENT`. Needs slice 1.
3. **Settle** — Stripe webhook moves `SENT` to `PAID`. Needs slice 2 and a public webhook endpoint.
4. **Void and credit** — cancel a `SENT` invoice. Needs slice 2.

## Dependencies

Slice 2 depends on `10-payments-adapter` existing with `CreateSession`. Slice 3 additionally depends on the
ingress being reachable from Stripe, which is infrastructure work outside this module and the reason slice 3
is not second.

## Order

1 → 2 → 4 → 3. Slice 4 precedes slice 3 despite being less valuable, because it needs nothing new from
infrastructure and keeps the team unblocked while the ingress is provisioned.

## Exit criteria

Slice 1: a `DRAFT` survives a restart. Slice 2: SCN-002 passes including its failure branch, and the 10 000-way
concurrency test shows zero duplicates. Slice 3: a replayed webhook produces one `PAID`, not two. Slice 4: a
voided invoice keeps its number.

## Risks and deferrals

Multi-currency totals are deferred to after slice 4; the rounding rule is unresolved and shipping it wrong is
harder to undo than shipping it late. Partial payments are out of scope entirely for this plan.
