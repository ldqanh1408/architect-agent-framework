---
primary_layer: content
---
# ADR 0002 — Use Adapter Pattern for Third-Party Payment Gateway Integration

[← Table of Contents]({{INDEX_PATH}}) · *Architecture / Decisions*

## Table of Contents

- [Status](#status)
- [Context & Problem Statement](#context--problem-statement)
- [Options Considered](#options-considered)
- [Decision](#decision)
- [Consequences](#consequences)
- [Enforcement](#enforcement)
- [Related Docs](#related-docs)
- [Change Log](#change-log)

## Status

| Field | Value |
|---|---|
| Status | `ACCEPTED` |
| Decision date | `2026-07-14` |
| Decision owner | Lead Architect |
| Supersedes | — |
| Superseded by | — |
| Bounded contexts affected | `04-integration-adapters/`, `subscription-service` |

## Context & Problem Statement

The subscription-service must support two payment gateways (Stripe and PayPal) in Phase 2, and is likely to add a third (Adyen) in Phase 3. Each vendor SDK ships different method signatures, exception hierarchies, and response shapes. Wiring vendor SDK types directly into `SubscriptionService`:

- Couples business logic to the vendor's release cadence (SDK minor bumps break signatures).
- Makes unit-testing `SubscriptionService` impossible without a live network dependency.
- Leaks vendor-specific exceptions into service-level error handling, forcing a fan-out of `catch` clauses.

Deciding now (rather than deferring) is cheaper because Phase 2 has not yet begun and no code depends on either SDK.

## Options Considered

| # | Option | Cost / Effort | Risk | Reversibility |
|---|---|---|---|---|
| A | Call vendor SDK directly from `SubscriptionService` | Low upfront | High — SDK bumps ripple into business code | Low (rewrite required) |
| B | Adapter pattern — one `IPaymentGatewayAdapter` contract, one wrapper per vendor | Moderate upfront | Low — vendor changes contained in wrapper | High |
| C | Anti-corruption layer with domain translator + orchestration bus | High upfront | Low — over-engineered for two vendors | High |

**Why not Option A** — locks the codebase to vendor SDK types; a signature change in Stripe's JVM SDK v25 → v26 forced a rewrite of `SubscriptionService` in a prior project; not a repeatable pattern.

**Why not Option C** — a translator + bus is warranted for four or more vendors with divergent domain models. We have two vendors with near-identical domains; the extra layer would carry no information.

## Decision

> Chosen: **Option B — Adapter pattern with a single `IPaymentGatewayAdapter` contract and one Composition wrapper per vendor** (see [`architecture/02-domains/04-integration-adapters/01-adapters/composition-wrappers.md`]({{ADAPTER_LINK}})).

Reasons:

1. **Layer isolation.** `SubscriptionService` imports only `IPaymentGatewayAdapter`; vendor SDK types never appear in business packages.
2. **Testability.** A `FakePaymentGatewayAdapter` becomes trivial — no network mocking library required.
3. **Vendor-swap ergonomics.** Adding Adyen in Phase 3 is a new wrapper class plus one line in the DI container; no changes to `SubscriptionService`.
4. **Exception containment.** Vendor exceptions are translated into `ExternalGatewayTechnicalException` / `PaymentDeclinedException` inside the wrapper — service-level `catch` blocks stay flat.

## Consequences

| Consequence | Kind | Mitigation |
|---|---|---|
| Business layer never sees vendor types | positive | — |
| Extra classes (Adapter, Wrapper, Mapper, Translator) per vendor | negative | Accepted — the classes are small and mechanical |
| Vendor-specific *features* (Stripe Terminal, PayPal recurring billing UI) don't fit the shared contract | trade-off | Model as adapter capability flags: `IPaymentGatewayAdapter.supports(Feature.TERMINAL)` |
| Wrappers need version-compatibility tests against live vendor sandboxes | trade-off | Nightly CI job hits sandbox environments; failures page the on-call |

## Enforcement

- **Architecture-fitness test** — `businessLayerMustNotDependOnVendorSdk` in [Fitness Functions catalog](../../../03-cross-cutting/04-fitness-functions/00-overview.md). Fails the build if any class in `com.example.subscription..` imports `com.stripe..` or `com.paypal..`.
- **Code-review checklist item** — every new payment feature PR must show a new method on `IPaymentGatewayAdapter` *or* a new wrapper class; direct SDK imports are a blocker comment.
- **CI gate** — Sonatype dependency-check step lists Stripe/PayPal SDK versions and fails if the wrapper module is missing a matching adapter test.

## Related Docs

- [`architecture/02-domains/04-integration-adapters/01-adapters/composition-wrappers.md`]({{ADAPTER_LINK}})
- [Architecture Fitness Tests](../../../03-cross-cutting/04-fitness-functions/00-overview.md)
- [`REQ-021` — multi-gateway subscription support]({{REQUIREMENT_LINK}})

## Change Log

| Date | Change | Author |
|---|---|---|
| `2026-07-14` | Accepted | Lead Architect |
