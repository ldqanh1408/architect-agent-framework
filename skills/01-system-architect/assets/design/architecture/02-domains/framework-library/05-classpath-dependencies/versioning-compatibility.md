---
primary_layer: content
---
# Versioning & Compatibility

[← Table of Contents]({{INDEX_PATH}}) · *Framework-Library / Classpath & Dependencies*

## Table of Contents

- [Summary](#summary)
- [1. Semver Policy](#1-semver-policy)
- [2. Deprecation Window](#2-deprecation-window)
- [3. Consumer Runtime Matrix](#3-consumer-runtime-matrix)
- [4. Executable Boilerplate](#4-executable-boilerplate)
- [5. Guardrails and Defaults](#5-guardrails-and-defaults)
- [6. Related Docs](#6-related-docs)

{{VERSIONING_SUMMARY}}

## 1. Semver Policy

| Change | Version bump | Requires ADR |
|---|---|---|
| Add a new public type / method | MINOR | No |
| Add a new SPI | MINOR | Yes |
| Change signature of a public type | MAJOR | Yes |
| Remove a `@Deprecated` type | MAJOR | Yes |
| Fix a bug without changing signatures | PATCH | No |
| Change a pinned transitive major version | MAJOR | Yes |

## 2. Deprecation Window

- `@Deprecated(since=X)` remains present for at least the following MINOR versions of the same MAJOR train.
- Removal happens no earlier than the next MAJOR bump.
- Migration guide file `migration-<X>-to-<Y>.md` accompanies every removal.

## 3. Consumer Runtime Matrix

| Framework version | Java baseline | Spring Boot | Notes |
|---|---|---|---|
{{RUNTIME_MATRIX_ROWS}}

## 4. Executable Boilerplate

Compile-time deprecation warning driven by `@Deprecated`:

```java
package com.example.starter;

/**
 * @deprecated since 2.1 — use {@link NewApi} instead.
 * Scheduled for removal in 3.0 (see migration-2.x-to-3.0.md).
 */
@Deprecated(since = "2.1", forRemoval = true)
public class OldApi { … }
```

Runtime detection using `japicmp-maven-plugin`:

```xml
<plugin>
  <groupId>com.github.siom79.japicmp</groupId>
  <artifactId>japicmp-maven-plugin</artifactId>
  <version>0.19.2</version>
  <configuration>
    <parameter>
      <accessModifier>public</accessModifier>
      <onlyModified>true</onlyModified>
      <breakBuildOnBinaryIncompatibleModifications>true</breakBuildOnBinaryIncompatibleModifications>
    </parameter>
  </configuration>
</plugin>
```

## 5. Guardrails and Defaults

| Guardrail | Default | Rationale |
|---|---|---|
| Every release runs `japicmp` against the last release | Enforced by CI | Semver violations must fail the pipeline, not be caught in review |
| Deprecation must include `since` **and** `forRemoval` | Enforced by architecture-fitness test | Consumers need the removal date, not just the notice |
| Migration guide required before MAJOR bump | Enforced by release checklist | Rewrites without guidance produce migration abandonment |

## 6. Related Docs

- [Public API Surface](../03-extension-points/public-api-surface.md)
- [Dependency Management (BOM)](dependency-management.md)
- [Packaging & Distribution](packaging-distribution.md)
