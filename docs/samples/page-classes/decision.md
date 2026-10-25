---
page_class: decision
---

# Invoice sequence allocation — assessment

## Criteria and weights

Correctness under partition **0.5** — REQ-002 is a legal obligation, so a wrong number costs more than a slow
one. Latency at p99 **0.3**. Operational surface **0.2**, counting components that can fail independently.

## Candidates

Tenant row lock; per-tenant database sequence; Redis counter with a Lua allocation script. A fourth option,
UUID-based numbering, was ruled out before scoring: it cannot produce a gapless sequence at all.

## Scores

| Candidate | Correctness (0.5) | p99 (0.3) | Ops (0.2) | Total |
|---|---|---|---|---|
| Row lock | 5 | 3 | 5 | **4.4** |
| DB sequence | 4 | 4 | 5 | 4.2 |
| Redis counter | 2 | 5 | 2 | 2.9 |

Correctness scores come from a partition-injection run; p99 from 10 000 concurrent allocations on the staging
database; ops from counting independently failing components.

## Losing case

The Redis counter is genuinely faster — 8 ms at p99 against 16 ms — and if the sequence were a display
convenience rather than a legal record, it would win. The DB sequence loses only on gap behaviour under
rollback, which is a narrower defect than it first appears.

## Consumed by

ADR-0007.
