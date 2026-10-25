# Interview Question Bank

Question groups for the structured interview, in fixed round order. Pick only groups the brief does not already answer; scale depth to the complexity tier (small: 1 round, standard: 2-3, large: up to 5).

## Round Order

1. Actors & Personas
2. Scope In / Out
3. Happy Paths
4. Edge Cases & Failure Behavior
5. NFRs (numbers required)
6. Constraints

## 1. Actors & Personas

- Who uses the system? List every human role and every external system.
- Which actor triggers the most valuable flow? Which actor can cause the most damage?
- Are there admin/back-office roles with different permissions?

## 2. Scope In / Out

- What is explicitly OUT of scope for the first delivery?
- Is this replacing an existing tool, or is it new? If replacing: what must stay identical?
- Single tenant or multi-tenant? Single language/currency/timezone or several?

## 3. Happy Paths

- Walk me through the single most important flow, step by step, from the actor's point of view.
- What does "done" look like for that flow? What does the actor see/receive?
- What data must exist before that flow can run?

## 4. Edge Cases & Failure Behavior

- What should happen when the input is invalid / duplicated / too large?
- What should the user see when a dependency (payment, email, third-party API) is down?
- Is partial completion acceptable, or must the flow be all-or-nothing?

## 5. NFRs — Numbers Required

- How many users/requests at peak? (RPS or concurrent users)
- Acceptable response time for the main flow? (demand p95 in ms, not "fast")
- Required uptime? (99.x%) Data-loss tolerance? (RPO/RTO)
- Expected data volume after 1 year? Retention rules? Compliance regimes (PII, PCI, HIPAA)?

## 6. Constraints

- Hard deadline or budget cap?
- Mandated technology (existing stack, cloud provider, license policy)?
- Team profile of whoever implements this (language expertise, size)?

## Project-Type Extensions

For project-specific rounds, mirror the archetype and bounded-context set in `01-system-architect/references/design/workspace-skeleton-maximal.md` (Section 12 Bounded-Context Catalogue: `frontend`, `backend-service`, `ai-system`, `data-platform`, `identity-access`, `integration-adapter`, `infra-platform`, `observability`). Ask the module's overview questions only when the project type matches.

## Questioning Rules

- One question group per message; never dump all groups at once.
- Every "don't know" becomes an Open Question with a proposed default.
- Close each round by reading back what was decided and asking for a yes/no confirmation.
