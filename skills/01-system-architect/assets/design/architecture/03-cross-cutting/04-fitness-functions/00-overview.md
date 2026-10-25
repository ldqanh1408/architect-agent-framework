---
primary_layer: content
---
# Fitness Functions — Quality Tree and Rule Catalog

[← Table of Contents]({{INDEX_PATH}}) · *Cross-Cutting › Fitness Functions*

## Table of Contents

- [Summary](#summary)
- [1. Purpose](#1-purpose)
- [2. Rule Catalogue](#2-rule-catalogue)
- [3. Executable Boilerplate](#3-executable-boilerplate)
- [4. CI Wiring](#4-ci-wiring)
- [5. Extending the Guardrail Set](#5-extending-the-guardrail-set)
- [6. Related Docs](#6-related-docs)

## Summary

This directory is the **catalog**, not the tests. `system-architect` owns the
rules; the target project owns the test files that materialize them in its
stack (ArchUnit for JVM, `import-linter` for Python,
`dependency-cruiser` for TS/JS). Neither writes into the other's tree, and
`sdd-agent` never runs architecture tests against target code.

One file per rule, `FIT-NNN-<slug>.md`, mirroring one-file-per-ADR. A single
shared catalog file would be the merge hotspot that co-locating diagrams was
introduced to remove.

## Quality Tree

Read top-down: a quality goal produces a scenario, and a scenario produces the
rule that would catch its violation. A `FIT-` rule with no quality attribute
behind it is a preference; a quality attribute with no rule is unenforced.

| Quality goal | Scenario | Fitness rule |
|---|---|---|
| {{QUALITY_GOAL}} | {{SCENARIO}} | {{FIT_ID}} |

## Rule File Schema

Every `FIT-NNN-<slug>.md` carries exactly one fenced YAML block:

```yaml
id: FIT-001                      # stable, never renumbered
quality_attribute: modifiability # must resolve into 01-global-strategy/01-requirements/quality-attributes.md
scope: layer-isolation           # layer-isolation | bounded-context-isolation | naming | dependency-direction | cycle
rule: forbid-dependency          # forbid-dependency | only-depend-on | require-naming | no-cycles
from: "**/_shared-kernel/**"
to: ["**/02-domains/_shared-adapters/**"]
severity: blocking               # advisory | blocking
source_adr: ADR-0001             # must resolve to an accepted ADR
submodules: []                   # [] means system-wide
```

Validated by `architect-runtime sdd check <workspace> --full`.


Architecture fitness tests are the **CI-enforced guardrails** that keep the boundaries this SSoT declares from silently eroding. They run on every commit like unit tests, but they assert *structure* (layer isolation, extension-point purity, dependency cycles) rather than behaviour. A red fitness test blocks merge — the same as a red unit test.

## 1. Purpose

An ADR that says *"the business layer must not depend on vendor SDK X"* is aspirational until a test proves it every commit. This page collects those tests in one catalogue, each rule linked to the ADR that motivated it, so that:

- A new architect can see every guardrail in one place.
- A relaxation of a rule requires an ADR (the rule was placed by an ADR; relaxation supersedes it).
- The `spec-critic` skill can compare the rule set here against the ADR set under `05-governance/decisions/` and flag orphan ADRs (decision but no enforcement) or orphan rules (enforcement but no decision).

## 2. Rule Catalogue

| Rule ID | Rule | Enforced by ADR | Failure sample |
|---|---|---|---|
| FIT-001 | Business layer must not import vendor SDK types | ADR-0002 | `com.example.subscription.OrderService` imports `com.stripe.Charge` |
| FIT-002 | No cyclic dependencies between bounded contexts | ADR-0001 | `backend` → `extension` → `backend` |
| FIT-003 | Filter classes end with `Filter` and extend `GenericFilterBean` | ADR-0004 | `TotpAuthenticationFilter extends Object` |
| FIT-004 | `internal.*` packages are not importable by consumer classes | ADR-0005 | Consumer `MyApp` imports `com.example.starter.internal.Wiring` |
| FIT-005 | Every `AuthenticationProvider` implementation is thread-safe (no mutable non-final fields) | ADR-0006 | `TotpAuthenticationProvider` has `private String lastNonce` |
| FIT-006 | No forbidden transitive on the runtime classpath | ADR-0007 | `commons-logging` reachable from `SubscriptionService` |
| FIT-007 | Public API surface only from packages listed in `public-api-surface.md` | ADR-0008 | `com.example.starter.experimental.NewApi` shipped without listing |

Add a new row whenever a new ADR ships an enforceable rule. Delete a row only when the motivating ADR is `SUPERSEDED` or `DEPRECATED`.

## 3. Executable Boilerplate

### JVM — ArchUnit

```java
package com.example.architecture;

import com.tngtech.archunit.junit.AnalyzeClasses;
import com.tngtech.archunit.junit.ArchTest;
import com.tngtech.archunit.lang.ArchRule;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.classes;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;
import static com.tngtech.archunit.library.dependencies.SlicesRuleDefinition.slices;

@AnalyzeClasses(packages = "com.example")
public class ArchitectureFitnessTest {

    // FIT-001 — Business layer independence
    @ArchTest
    public static final ArchRule businessLayerMustNotDependOnVendorSdk =
        noClasses().that().resideInAPackage("..subscription..")
            .should().dependOnClassesThat().resideInAnyPackage("com.stripe..", "com.paypal..");

    // FIT-002 — No cycles between bounded contexts
    @ArchTest
    public static final ArchRule noCyclesBetweenBoundedContexts =
        slices().matching("com.example.(*)..").should().beFreeOfCycles();

    // FIT-003 — Filter naming + base-class contract
    @ArchTest
    public static final ArchRule filterBeansMustExtendGenericFilterBean =
        classes().that().haveSimpleNameEndingWith("Filter")
            .and().resideInAPackage("..starter.security.filters..")
            .should().beAssignableTo(org.springframework.web.filter.GenericFilterBean.class);

    // FIT-004 — internal package containment
    @ArchTest
    public static final ArchRule internalPackagesAreNotImportedFromOutsideStarter =
        noClasses().that().resideOutsideOfPackage("com.example.starter..")
            .should().dependOnClassesThat().resideInAPackage("..starter.internal..");
}
```

### TypeScript — dependency-cruiser

```json
{
  "forbidden": [
    {
      "name": "no-vendor-sdk-in-business-layer",
      "comment": "FIT-001 — see ADR-0002",
      "severity": "error",
      "from": { "path": "^src/subscription" },
      "to":   { "path": "^node_modules/(stripe|@paypal)" }
    },
    {
      "name": "no-context-cycles",
      "comment": "FIT-002 — see ADR-0001",
      "severity": "error",
      "from": {},
      "to":   { "circular": true }
    }
  ]
}
```

### Python — import-linter

```ini
[importlinter]
root_package = example

[importlinter:contract:business-layer-independence]
name = FIT-001 business layer independence
type = forbidden
source_modules = example.subscription
forbidden_modules = stripe, paypalrestsdk

[importlinter:contract:no-cycles]
name = FIT-002 no context cycles
type = independence
modules = example.backend, example.extension, example.plugins
```

## 4. CI Wiring

- Fitness tests run in the same job as unit tests. No separate stage — separation invites "we'll fix the arch test later" behaviour.
- Failing fitness test → build red → merge blocked. No override, no `@Ignore`, no `@Disabled`; use ADR-driven suspension instead.
- Suite runtime target: under 30 seconds for the JVM catalogue, under 10 seconds for the TS/Python catalogues. Beyond that, tighten scoping — a slow fitness suite gets skipped in dev.

## 5. Extending the Guardrail Set

1. Author (or supersede) the ADR that motivates the rule.
2. Add a row to §2 with the ADR link.
3. Add the executable clause in §3 under the matching language.
4. Run once locally to confirm it fails on a hand-crafted violation and passes on the current codebase.

Do not add a fitness rule without a supporting ADR — the rule catalogue becomes a graveyard of intent-less assertions otherwise.

## 6. Related Docs

- [`05-governance/decisions/ADR-TEMPLATE.md`](../05-governance/decisions/ADR-TEMPLATE.md)
- [`05-governance/decisions/0002-adapter-pattern-for-payment.md`](../05-governance/decisions/0002-adapter-pattern-for-payment.md)
- [`workspace-skeleton-maximal.md Section 8`](../../../../../references/design/workspace-skeleton-maximal.md#8-fitness-functions-slot)
- [Transitive Exclusions](../../../architecture/02-domains/framework-library/05-classpath-dependencies/transitive-exclusions.md)
