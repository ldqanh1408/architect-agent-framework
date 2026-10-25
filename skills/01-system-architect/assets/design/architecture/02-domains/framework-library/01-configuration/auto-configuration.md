---
primary_layer: content
---
# Auto-Configuration

[← Table of Contents]({{INDEX_PATH}}) · *Framework-Library / Configuration*

## Table of Contents

- [Summary](#summary)
- [1. Runtime Principle](#1-runtime-principle)
- [2. Contracts (Registration Surface)](#2-contracts-registration-surface)
- [3. Executable Boilerplate](#3-executable-boilerplate)
- [4. Guardrails and Defaults](#4-guardrails-and-defaults)
- [5. Related Diagrams](#5-related-diagrams)
- [6. Related Docs](#6-related-docs)

## Summary

{{AUTOCONFIG_SUMMARY}} — how the framework wires beans into the consumer application without requiring `@ComponentScan` or manual `@Bean` declarations, and under what conditions each bean is contributed.

## 1. Runtime Principle

Auto-configuration runs during application-context refresh. The framework's entry JAR ships:

1. A machine-discoverable index (`META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` for Spring Boot 3+, `META-INF/services/<SPI>` for plain JVM SPI, `package.json#exports` for Node).
2. A guarded `@Configuration` class per feature — the guard set decides whether the bean is contributed.
3. `@ConditionalOnMissingBean` on every public factory method so the consumer can override any default with a hand-written `@Bean`.

## 2. Contracts (Registration Surface)

| Consumer platform | Discovery mechanism | Example marker |
|---|---|---|
| Spring Boot 3+ | `AutoConfiguration.imports` | `com.example.starter.AutoConfig` |
| Plain JVM | `ServiceLoader` + `META-INF/services/<SPI>` | `com.example.spi.Provider` |
| Node.js | `package.json#exports` + side-effect free entry | `./index.js` |
| .NET | Source generator + `IServiceCollection` extension | `AddExampleFramework()` |

## 3. Executable Boilerplate

```java
package com.example.starter;

import org.springframework.boot.autoconfigure.AutoConfiguration;
import org.springframework.boot.autoconfigure.condition.ConditionalOnClass;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;

@AutoConfiguration
@ConditionalOnClass(name = "com.example.core.CoreEngine")
@ConditionalOnProperty(prefix = "example.starter", name = "enabled", matchIfMissing = true)
@EnableConfigurationProperties(ExampleProperties.class)
public class ExampleAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean
    public CoreEngine coreEngine(ExampleProperties props) {
        return new CoreEngine(props.getTimeoutMillis(), props.getMaxRetries());
    }

    @Bean
    @ConditionalOnMissingBean
    public FeatureCustomizer defaultCustomizer() {
        return FeatureCustomizer.NOOP;
    }
}
```

`src/main/resources/META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`:

```text
com.example.starter.ExampleAutoConfiguration
```

## 4. Guardrails and Defaults

| Guard | Default | Rationale |
|---|---|---|
| `example.starter.enabled` | `true` (`matchIfMissing = true`) | A starter that requires an opt-in property is a starter no one uses |
| `@ConditionalOnClass` | Framework-provided marker class only | Never trigger on consumer classes — creates load-order surprises |
| `@ConditionalOnMissingBean` | Applied to every public `@Bean` | Consumer override is a first-class feature, not a workaround |
| Startup log line | One INFO line naming the version | Silent activation makes support cases unfalsifiable |

## 5. Related Diagrams

- [Core Engine Class Diagram](../04-diagrams-specs/core-engine-class-diagram.md)

## 6. Related Docs

- [Conditional Matrix](conditional-matrix.md)
- [Configuration Contract](configuration-contract.md)
- [ADR – Auto-config discovery mechanism]({{ADR_LINK}})
