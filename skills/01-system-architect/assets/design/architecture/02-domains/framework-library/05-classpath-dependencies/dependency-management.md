---
primary_layer: content
---
# Dependency Management (BOM)

[← Table of Contents]({{INDEX_PATH}}) · *Framework-Library / Classpath & Dependencies*

## Table of Contents

- [Summary](#summary)
- [1. Pinned Direct Dependencies](#1-pinned-direct-dependencies)
- [2. BOM Layout](#2-bom-layout)
- [3. Executable Boilerplate](#3-executable-boilerplate)
- [4. Guardrails and Defaults](#4-guardrails-and-defaults)
- [5. Related Docs](#5-related-docs)

## Summary

The framework publishes a `-bom` (Bill of Materials) alongside the runtime JAR so consumers can align versions of every peer library (`jackson-databind`, `slf4j-api`, `spring-web`) without hand-picking. This page specifies the pinned set, the BOM structure, and the guardrails that keep the BOM honest.

## 1. Pinned Direct Dependencies

| Coordinate | Version | Scope | Rationale |
|---|---|---|---|
{{PINNED_DEPENDENCY_ROWS}}

## 2. BOM Layout

```text
com.example:example-starter-bom:${version}
├── com.example:example-starter               (runtime)
├── com.example:example-starter-core          (runtime)
├── com.example:example-starter-autoconfigure (runtime)
└── com.example:example-starter-test          (test)
```

## 3. Executable Boilerplate

Maven consumer:

```xml
<dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>com.example</groupId>
      <artifactId>example-starter-bom</artifactId>
      <version>${example-starter.version}</version>
      <type>pom</type>
      <scope>import</scope>
    </dependency>
  </dependencies>
</dependencyManagement>

<dependencies>
  <dependency>
    <groupId>com.example</groupId>
    <artifactId>example-starter</artifactId>
  </dependency>
</dependencies>
```

Gradle consumer:

```kotlin
dependencies {
    implementation(platform("com.example:example-starter-bom:${property("example-starter.version")}"))
    implementation("com.example:example-starter")
}
```

## 4. Guardrails and Defaults

| Guardrail | Default | Rationale |
|---|---|---|
| Every runtime coordinate has a pinned version in the BOM | Enforced by `check-bom.sh` in CI | Prevents accidental version drift between modules |
| Versions are only bumped via ADR | Enforced by review | Silent bumps have shipped incompatible transitives before |
| BOM never depends on non-published (SNAPSHOT) versions | Enforced by release job | SNAPSHOT in a released BOM is unreproducible |

## 5. Related Docs

- [Transitive Exclusions](transitive-exclusions.md)
- [Packaging & Distribution](packaging-distribution.md)
- [Versioning & Compatibility](versioning-compatibility.md)
