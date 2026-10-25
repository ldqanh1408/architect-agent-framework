---
primary_layer: content
---
# Conditional Matrix

[← Table of Contents]({{INDEX_PATH}}) · *Framework-Library / Configuration*

## Table of Contents

- [Summary](#summary)
- [1. Runtime Principle](#1-runtime-principle)
- [2. Truth Table](#2-truth-table)
- [3. Executable Boilerplate](#3-executable-boilerplate)
- [4. Guardrails and Defaults](#4-guardrails-and-defaults)
- [5. Related Docs](#5-related-docs)

## Summary

{{CONDITIONAL_MATRIX_SUMMARY}} — enumerates every activation guard on the framework's auto-configuration surface, the *state* each guard resolves to under representative consumer scenarios, and the resulting bean graph.

## 1. Runtime Principle

Auto-configuration guards form a boolean expression evaluated once per configuration class at context refresh. If the expression resolves `true`, the class is imported. If any single guard fails, the class and every `@Bean` it declares are skipped silently. The **matrix** documents the resolution table so consumers can predict activation without reading source.

## 2. Truth Table

| Scenario | `example.starter.enabled` | Marker class on classpath | Consumer bean present | Result |
|---|---|---|---|---|
| Default happy path | `true` | yes | no | ✅ Framework beans contributed |
| Consumer disabled | `false` | yes | no | ❌ Nothing contributed |
| Wrong runtime | `true` | no | no | ❌ Nothing contributed (silent) |
| Consumer overrides `CoreEngine` | `true` | yes | yes | ⚠️ Framework skips `CoreEngine`; other beans still contributed |
| Property missing entirely | `matchIfMissing = true` → treated as `true` | yes | no | ✅ Framework beans contributed |

## 3. Executable Boilerplate

Diagnostic listener that logs the resolved matrix at startup (drop into any `@AutoConfiguration` class):

```java
@Bean
ApplicationListener<ContextRefreshedEvent> exampleStarterDiagnostics(
        ConfigurableApplicationContext ctx,
        ExampleProperties props) {
    return event -> {
        var log = LoggerFactory.getLogger("com.example.starter.diagnostics");
        log.info("example-starter enabled={} coreEngine={} customizers={}",
            props.isEnabled(),
            ctx.getBeansOfType(CoreEngine.class).keySet(),
            ctx.getBeansOfType(FeatureCustomizer.class).keySet());
    };
}
```

## 4. Guardrails and Defaults

| Guard combination | Result | Recommendation |
|---|---|---|
| Two guards on the same property with opposite senses | Impossible to reason about | Split into two `@AutoConfiguration` classes |
| `@ConditionalOnClass` referencing a consumer-owned class | Load-order race | Only guard on framework-owned marker classes |
| Missing `@ConditionalOnMissingBean` on a public `@Bean` | Consumer cannot override | Always pair public factory methods with the missing-bean guard |

## 5. Related Docs

- [Auto-Configuration](auto-configuration.md)
- [Configuration Contract](configuration-contract.md)
