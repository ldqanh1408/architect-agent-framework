# Conditional Architecture Rules (R11–R18)

These rules do not apply to every system. Each one activates only when the system
exhibits the shape it names — read the section, and only that section, when the
trigger matches. Applying a rule to a system that does not have its shape adds
noise to the specification and buries the rules that do apply.

`SKILL.md` carries the router; the detail lives here so a project with none of
these shapes never pays for them.

## Contents

| Rule | Activates when | Section |
|---|---|---|
| R11 | data flows in both directions and must be reconciled | [§1](#r11--two-way-state-synchronisation) |
| R12 | one backend is both an API client and a user-facing server | [§2](#r12--user-session-vs-service-credential-separation) |
| R13 | an external system pushes events in via webhook | [§3](#r13--webhook-receiver-and-event-ingestion) |
| R14 | the system shells out to an external agent or CLI to edit user data | [§4](#r14--sandboxed-cli--agent-runners) |
| R15 | the deployment unit is configured by file or environment | [§5](#r15--configuration-surface) |
| R16 | the system holds money, stock, or any balance that must reconcile | [§6](#r16--ledger-and-balance-integrity) |
| R17 | the client must keep working while disconnected | [§7](#r17--offline-capable-clients) |
| R18 | a third-party API is on the critical path of a user-visible flow | [§8](#r18--third-party-api-dependence) |

---

## R11 — Two-way state synchronisation

**Activates when** the same logical record can be edited on two sides and both
edits must survive.

Reconciliation is where these systems fail, and they fail quietly: the losing
edit disappears without an error anyone sees. So the architecture must state:

- **Loop trigger and cadence** — webhook, cron, interval, or user action, and
  what happens when two triggers overlap.
- **Diff granularity** — whole-record, field-level, block-level hash, or LCS.
  This choice determines which conflicts are even detectable; a whole-record diff
  cannot see that two people edited different paragraphs.
- **Conflict detection** — diverged timestamps, version vector, dirty flag,
  content hash. Name the signal, not "detect conflicts".
- **Resolution modes offered to the user** — take remote, keep local, merge,
  or refuse to auto-merge. Refusing is a legitimate answer and is often the
  right one; what is not legitimate is silently picking a winner.
- **Preservation guarantees** — what must survive a sync that the diff does not
  model. Inline comments and annotations attached to remote content are the
  usual casualty.

## R12 — User session vs service credential separation

**Activates when** the same process authenticates end users *and* authenticates
itself to an upstream service.

The two credential types have different lifetimes, different blast radii and
different revocation stories, and merging them means revoking a fired employee's
access also breaks the integration. Specify separately:

- **User sessions** — cookie attributes (`HttpOnly`, `SameSite`, `Secure`,
  `Path`), where session state lives, TTL, and the rotation trigger.
- **Service credentials** — where the secret comes from, its rotation schedule,
  and which components may read it.
- **Session record storage** — the raw session identifier must never be stored
  as-is, so that a leaked store does not hand over live sessions.
- **Revocation path** — the exact sequence that makes an active session stop
  working, and the observable upper bound on how long that takes.

On the storage transform, record *which* transform you chose and why, as an ADR —
do not let the skill pick it for you. The choice depends on the identifier's
entropy: a high-entropy random session token and a user-chosen password have
different threat models and want different primitives. Stating the property you
need ("a leaked store must not yield usable sessions", "verification must not add
measurable latency to every request") makes the ADR reviewable; naming an
algorithm without the property makes it dogma.

## R13 — Webhook receiver and event ingestion

**Activates when** an external system pushes events to an endpoint you expose.

- **Signature verification** — the algorithm, the signed payload, and a
  constant-time comparison. A short-circuiting comparison leaks the signature a
  byte at a time.
- **Replay defence** — timestamp tolerance window and nonce or event-id
  deduplication, since a valid signature stays valid forever without one.
- **Acknowledge-then-process** — the response SLA the sender expects, the durable
  log the event lands in before any processing, and the out-of-band worker that
  drains it. Processing inline means the sender's retry policy becomes your
  load-shedding policy.
- **Failure surface** — what the sender sees on 4xx vs 5xx, and what your retry
  and dead-letter behaviour is.
- **Push channel to the UI** — SSE, WebSocket or polling, and the freshness the
  user experiences.

## R14 — Sandboxed CLI / agent runners

**Activates when** the system invokes an external CLI or AI agent that can modify
user-visible data.

- **Sandbox layout** — the working directory, and the guarantee that the runner
  sees copies rather than the live tree.
- **Process controls** — timeout, environment and locale, resource limits, and
  the exit-code map to application outcomes.
- **Review gate** — how a human sees the diff and accepts or rejects it before
  anything reaches the real workspace. A runner that writes directly is not this
  pattern and should be documented as the different, riskier thing it is.

## R15 — Configuration surface

**Activates when** the deployment unit reads configuration from files or the
environment.

Every property that changes behaviour is part of the contract: key, type,
default, whether it is required, which environments it applies to, and what
happens when it is absent or malformed. Include dev-server proxies, local data
paths, file-watcher roots and framework overrides — these are the settings that
make a working checkout fail on a colleague's machine.

Secrets appear as key and source only. Never a sample value that looks real; a
plausible-looking placeholder account number will be copied into production by
somebody.

## R16 — Ledger and balance integrity

**Activates when** the system tracks money, stock levels, points, or any quantity
that must reconcile against an external truth.

- **Source of truth** — which table or service holds the authoritative balance,
  and whether balances are stored or derived from an append-only ledger.
- **Mutation path** — every operation that can change the balance, and the
  isolation level or lock that keeps two of them from interleaving. "Two cashiers
  sell the last unit simultaneously" must have a stated outcome.
- **Reconciliation** — the periodic check that recomputes the balance from the
  ledger, its cadence, and what happens on mismatch.
- **Correction** — how a wrong balance gets fixed. Direct mutation loses the
  audit trail; a compensating entry preserves it.

## R17 — Offline-capable clients

**Activates when** the client must keep functioning without a network.

- **Local durability** — the storage mechanism and what survives a tab close, a
  browser crash, and a device restart. These are three different guarantees.
- **Queue semantics** — ordering, retry, and the client-generated identifier that
  makes replay idempotent server-side.
- **Server-side idempotency** — the header or key, how long the server remembers
  it, and what a duplicate returns.
- **Re-entry conflicts** — what happens when queued work is no longer valid on
  arrival: stock sold out, price changed, record deleted. Every offline system
  meets this case and most specifications skip it.
- **User-visible state** — how the operator knows they are offline, how many
  items are pending, and what failed to sync.

## R18 — Third-party API dependence

**Activates when** an external API sits on the critical path of something a user
waits for.

- **Exact contract, verified** — endpoint, method, auth, request and response
  shape, taken from the provider's current documentation rather than from
  memory. Plausible-looking invented endpoints are the most expensive error in
  this whole document set: they survive review, reach the test suite, and fail
  first in integration. Cite the documentation URL next to the contract.
- **Failure modes** — timeout, rate limit, malformed response, provider outage,
  and what the user sees in each.
- **Fallback** — the safe path when the integration is down. A timeout after a
  possible payment remains UNKNOWN until provider evidence reconciles it. Specify
  payment identity, duplicate prevention, and the customer status. A manual action
  cannot declare a charge successful without evidence or authorize a blind retry.
- **Cost and quota** — per-call cost or rate ceiling if either constrains design.
