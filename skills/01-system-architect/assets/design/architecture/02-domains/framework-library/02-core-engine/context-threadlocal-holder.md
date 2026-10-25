---
primary_layer: content
---
# Security Context — Thread-Local Holder

[← Table of Contents]({{INDEX_PATH}}) · *Framework-Library / Core Engine*

## Table of Contents

- [Summary](#summary)
- [1. Runtime Principle](#1-runtime-principle)
- [2. Contracts](#2-contracts)
- [3. Executable Boilerplate](#3-executable-boilerplate)
- [4. Guardrails and Defaults](#4-guardrails-and-defaults)
- [5. Cross-Thread Propagation](#5-cross-thread-propagation)
- [6. Related Docs](#6-related-docs)

## Summary

The framework exposes an ambient `SecurityContext` for the duration of a request. Business code reads `SecurityContextHolder.getContext().getAuthentication()` without threading it through method signatures. This page specifies the holder, its strategy, and how it survives async boundaries.

## 1. Runtime Principle

The context is stored per-thread via `ThreadLocal`. The `AuthenticationFilter` sets it on request entry; a `finally` block in the filter clears it on exit. Async boundaries (`CompletableFuture`, Reactor, virtual threads) require an explicit *decorator* that captures the parent thread's context and re-applies it on the worker thread. Never assume `ThreadLocal` inheritance across executors.

## 2. Contracts

```java
package com.example.starter.security.context;

public interface SecurityContext {
    Authentication getAuthentication();
    void setAuthentication(Authentication authentication);
}

public interface SecurityContextHolderStrategy {
    void clearContext();
    SecurityContext getContext();
    void setContext(SecurityContext context);
    SecurityContext createEmptyContext();
}
```

## 3. Executable Boilerplate

```java
package com.example.starter.security.context;

public final class SecurityContextHolder {

    private static final ThreadLocal<SecurityContext> CONTEXT = new ThreadLocal<>();

    private SecurityContextHolder() {}

    public static SecurityContext getContext() {
        SecurityContext ctx = CONTEXT.get();
        if (ctx == null) {
            ctx = new SecurityContextImpl();
            CONTEXT.set(ctx);
        }
        return ctx;
    }

    public static void setContext(SecurityContext context) {
        CONTEXT.set(context);
    }

    public static void clearContext() {
        CONTEXT.remove();
    }
}
```

Task decorator for propagation to `@Async` methods:

```java
package com.example.starter.security.context;

import org.springframework.core.task.TaskDecorator;

public class SecurityContextTaskDecorator implements TaskDecorator {
    @Override
    public Runnable decorate(Runnable delegate) {
        SecurityContext parent = SecurityContextHolder.getContext();
        return () -> {
            SecurityContext previous = SecurityContextHolder.getContext();
            SecurityContextHolder.setContext(parent);
            try {
                delegate.run();
            } finally {
                SecurityContextHolder.setContext(previous);
            }
        };
    }
}
```

## 4. Guardrails and Defaults

| Guardrail | Default | Rationale |
|---|---|---|
| Clear on request exit | `finally { SecurityContextHolder.clearContext(); }` in `AuthenticationFilter` | Leaks between requests share auth state across users — a critical incident |
| Async propagation | Opt-in via `TaskDecorator` | Implicit inheritance would leak into unrelated executor tasks |
| Reactor context key | `SecurityContext.class` | Standardises access from `Mono.deferContextual` |
| Virtual thread scoping | Explicit scoped-value wrapper | Loom's inherited-thread-locals do not cover framework code by default |

## 5. Cross-Thread Propagation

| Boundary | Mechanism |
|---|---|
| `@Async` method | `SecurityContextTaskDecorator` on the `TaskExecutor` |
| Reactor pipeline | `Mono.deferContextual` reading `SecurityContext.class` key |
| Kotlin coroutine | `SecurityContextElement : CoroutineContext.Element` |
| Virtual thread | Scoped value carrier — `ScopedValue<SecurityContext>` |

## 6. Related Docs

- [Filter Chain (Chain of Responsibility)](filter-chain-responsibility.md)
- [Authentication Manager (Strategy)](authentication-manager-strategy.md)
