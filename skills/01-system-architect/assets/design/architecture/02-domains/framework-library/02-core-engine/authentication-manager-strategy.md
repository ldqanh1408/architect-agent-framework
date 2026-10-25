---
primary_layer: content
---
# Authentication Manager — Strategy

[← Table of Contents]({{INDEX_PATH}}) · *Framework-Library / Core Engine*

## Table of Contents

- [Summary](#summary)
- [1. Runtime Principle](#1-runtime-principle)
- [2. Contracts (Interfaces)](#2-contracts-interfaces)
- [3. Executable Boilerplate](#3-executable-boilerplate)
- [4. Guardrails and Defaults](#4-guardrails-and-defaults)
- [5. Provider Catalogue](#5-provider-catalogue)
- [6. Related Docs](#6-related-docs)

## Summary

Authentication is delegated to a set of `AuthenticationProvider` strategies. The `ProviderManager` walks the list, asks each strategy whether it `supports(...)` the incoming token type, and hands the token to the first match. There is no fallback across providers — a `supports()`-matched provider that fails throws instead of skipping to the next.

## 1. Runtime Principle

Strategy pattern. The `AuthenticationManager` is a stable seam; concrete providers are pluggable. A DB-backed `DaoAuthenticationProvider`, a JWT-backed `JwtAuthenticationProvider`, and an OAuth2 flow all coexist behind the same `AuthenticationManager.authenticate(...)` call. The strategy list is ordered but only for tie-breaking on `supports(...)` — providers should not overlap.

## 2. Contracts (Interfaces)

```java
package com.example.starter.security.auth;

public interface Authentication {
    String getPrincipal();
    Object getCredentials();
    boolean isAuthenticated();
    void setAuthenticated(boolean isAuthenticated);
}

public interface AuthenticationProvider {
    Authentication authenticate(Authentication authentication) throws AuthenticationException;
    boolean supports(Class<?> authenticationType);
}

public interface AuthenticationManager {
    Authentication authenticate(Authentication authentication) throws AuthenticationException;
}
```

## 3. Executable Boilerplate

```java
package com.example.starter.security.auth;

import java.util.List;

public class CustomProviderManager implements AuthenticationManager {

    private final List<AuthenticationProvider> providers;

    public CustomProviderManager(List<AuthenticationProvider> providers) {
        if (providers == null || providers.isEmpty()) {
            throw new IllegalArgumentException("At least one AuthenticationProvider is required.");
        }
        this.providers = List.copyOf(providers);
    }

    @Override
    public Authentication authenticate(Authentication authentication) throws AuthenticationException {
        Class<? extends Authentication> tokenType = authentication.getClass();
        for (AuthenticationProvider provider : providers) {
            if (provider.supports(tokenType)) {
                return provider.authenticate(authentication);
            }
        }
        throw new ProviderNotFoundException("No AuthenticationProvider supports " + tokenType.getName());
    }
}
```

## 4. Guardrails and Defaults

| Guardrail | Default | Rationale |
|---|---|---|
| `providers` list is immutable after construction | `List.copyOf` | Prevents live mutation while a request is being authenticated |
| Empty provider list at construction time | Rejected with `IllegalArgumentException` | Silent no-op auth is a critical incident, not a warning |
| Missing `supports()` match | Throws `ProviderNotFoundException` | Silent skip would let unsigned tokens pass |
| Provider that returns `null` | Wrapped as `AuthenticationServiceException` | A `null` `Authentication` is not a valid response |
| Credential erasure after success | `authentication.setCredentials(null)` on returned token | Prevents password logs downstream |

## 5. Provider Catalogue

| Provider | Token type accepted | Backing store |
|---|---|---|
| `DaoAuthenticationProvider` | `UsernamePasswordAuthenticationToken` | `UserDetailsService` (RDBMS) |
| `JwtAuthenticationProvider` | `BearerTokenAuthenticationToken` | `JwtDecoder` (JWKS) |
| `ApiKeyAuthenticationProvider` | `ApiKeyAuthenticationToken` | Encrypted API-key table |

## 6. Related Docs

- [Filter Chain (Chain of Responsibility)](filter-chain-responsibility.md)
- [Context ThreadLocal Holder](context-threadlocal-holder.md)
- [Custom Provider Integration](../03-extension-points/custom-provider-integration.md)
