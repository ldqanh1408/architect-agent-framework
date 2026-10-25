---
primary_layer: content
---
# Transitive Exclusions

[← Table of Contents]({{INDEX_PATH}}) · *Framework-Library / Classpath & Dependencies*

## Table of Contents

- [Summary](#summary)
- [1. Forbidden Transitives](#1-forbidden-transitives)
- [2. Exclusion Rules by Coordinate](#2-exclusion-rules-by-coordinate)
- [3. Executable Boilerplate](#3-executable-boilerplate)
- [4. Detection in CI](#4-detection-in-ci)
- [5. Related Docs](#5-related-docs)

## Summary

Some transitive dependencies must never reach the consumer's classpath — either because the framework replaces them with a slim substitute, because they conflict with the runtime, or because their licence is incompatible with the framework's redistribution promise. This page enumerates each one and the exclusion mechanism that keeps it out.

## 1. Forbidden Transitives

| Coordinate | Pulled in by | Reason | Replacement |
|---|---|---|---|
{{FORBIDDEN_TRANSITIVE_ROWS}}

## 2. Exclusion Rules by Coordinate

| Direct dependency | Exclude | Notes |
|---|---|---|
{{EXCLUSION_RULE_ROWS}}

## 3. Executable Boilerplate

Maven — exclude a transitive on a single dependency:

```xml
<dependency>
  <groupId>com.example</groupId>
  <artifactId>example-starter</artifactId>
  <exclusions>
    <exclusion>
      <groupId>commons-logging</groupId>
      <artifactId>commons-logging</artifactId>
    </exclusion>
  </exclusions>
</dependency>
```

Gradle — global substitution rule:

```kotlin
configurations.all {
    resolutionStrategy.dependencySubstitution {
        substitute(module("commons-logging:commons-logging"))
            .using(module("org.slf4j:jcl-over-slf4j:2.0.13"))
            .because("Framework routes commons-logging through SLF4J bridge")
    }
}
```

## 4. Detection in CI

- Nightly job runs `mvn dependency:tree -Dincludes=commons-logging` against a canary consumer; a non-empty tree fails the build.
- Architecture-fitness test `noForbiddenPackagesOnClasspath` reads this page's forbidden list and asserts against `Class.forName(...)` reachability at test-time.

## 5. Related Docs

- [Dependency Management (BOM)](dependency-management.md)
- [Packaging & Distribution](packaging-distribution.md)
- [Architecture Fitness Tests](../../../../architecture/03-cross-cutting/04-fitness-functions/00-overview.md)
