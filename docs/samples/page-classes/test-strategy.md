---
page_class: test_strategy
---

# Invoice sending — test strategy

## Risk

A reused invoice number reaching a client. It is a legal defect the customer cannot correct afterwards, and
it only appears under concurrency plus a failing external call — the combination unit tests miss.

## Levels

Unit tests cover the state machine. An **integration** test against a real PostgreSQL covers allocation under
concurrency, because the guarantee lives in the row lock and a mocked database cannot exercise it. One
contract test covers every documented error code of `API-invoice-send`. No end-to-end test covers this risk:
e2e is too slow to run 10 000 concurrent sends.

## Data and environment

A seeded tenant with `next_invoice_seq = 1`, PostgreSQL 16 in a container, and a Stripe stub that can be told
to delay, fail, or rate-limit on command. The stub is the only way to reach the SCN-002 failure branch
deterministically.

## Pass criteria

Zero duplicate numbers across 10 000 concurrent sends; allocation p99 under 25 ms; every error code in the
API contract reached at least once by the contract test.

## Reading failures

A duplicate number is never flaky — it is always a real defect. A p99 breach on a loaded CI machine may be:
re-run once on an idle runner before filing. A contract test failing on an *unreachable* code usually means
the code was removed from the service but left in the documentation.
