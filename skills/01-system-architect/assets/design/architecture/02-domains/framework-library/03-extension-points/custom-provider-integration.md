---
primary_layer: content
---
# Custom Provider Integration

[← Table of Contents]({{INDEX_PATH}}) · *Framework-Library / Extension Points*

## Table of Contents

- [Summary](#summary)
- [1. Integration Contract](#1-integration-contract)
- [2. Executable Boilerplate](#2-executable-boilerplate)
- [3. Guardrails and Defaults](#3-guardrails-and-defaults)
- [4. Version-Compatibility Matrix](#4-version-compatibility-matrix)
- [5. Related Docs](#5-related-docs)

## Summary

Third parties integrate a new authentication mechanism by publishing a class that implements `AuthenticationProvider` and registering it through the DSL. This page specifies the contract the third party fulfils, the DSL hook they call, and the version-compatibility matrix they publish alongside their JAR.

## 1. Integration Contract

The third party ships:

- A concrete `AuthenticationProvider` whose `supports()` returns `true` for exactly one token type (see [Authentication Manager Strategy](../02-core-engine/authentication-manager-strategy.md)).
- A concrete `AbstractAuthenticationToken` subtype for that token type.
- An optional `SecurityConfigurer` that lets consumers wire the provider via the DSL.
- A `META-INF/example-starter/providers.json` manifest declaring the provider ID, supported token type, and target framework version.

## 2. Executable Boilerplate

Provider skeleton:

```java
package com.thirdparty.mfa;

public class TotpAuthenticationProvider implements AuthenticationProvider {

    private final TotpVerifier verifier;

    public TotpAuthenticationProvider(TotpVerifier verifier) {
        this.verifier = verifier;
    }

    @Override
    public Authentication authenticate(Authentication authentication) {
        TotpAuthenticationToken token = (TotpAuthenticationToken) authentication;
        if (!verifier.verify(token.getUserId(), token.getCode())) {
            throw new BadCredentialsException("Invalid TOTP code");
        }
        return TotpAuthenticationToken.authenticated(token.getUserId(), token.getAuthorities());
    }

    @Override
    public boolean supports(Class<?> authenticationType) {
        return TotpAuthenticationToken.class.isAssignableFrom(authenticationType);
    }
}
```

DSL wiring:

```java
public class TotpConfigurer extends AbstractHttpConfigurer<TotpConfigurer, HttpSecurity> {

    @Override
    public void configure(HttpSecurity http) {
        TotpVerifier verifier = http.getSharedObject(TotpVerifier.class);
        http.authenticationProvider(new TotpAuthenticationProvider(verifier));
        http.addFilterBefore(new TotpAuthenticationFilter(), AuthorizationFilter.class);
    }
}
```

Consumer usage:

```java
http.apply(new TotpConfigurer());
```

## 3. Guardrails and Defaults

| Guardrail | Default | Rationale |
|---|---|---|
| Provider ID is namespaced | `com.thirdparty.mfa.totp` | Prevents ID collisions across ecosystems |
| Provider claims exactly one token type | Enforced by `supports(...)` | Overlapping providers make behaviour order-dependent |
| Provider declares target framework version | `providers.json#frameworkVersion` | Consumer can fail fast on incompatible pairs |
| Provider is thread-safe | Enforced by architecture-fitness test | Providers are shared singletons |

## 4. Version-Compatibility Matrix

| Framework version | Supported provider manifest schema | Notes |
|---|---|---|
| `1.x` | `providers-v1.json` | Initial |
| `2.x` | `providers-v1.json`, `providers-v2.json` | v2 adds capability flags; v1 still accepted |
| `3.x+` | `providers-v2.json` | v1 dropped; migration guide required |

## 5. Related Docs

- [Authentication Manager (Strategy)](../02-core-engine/authentication-manager-strategy.md)
- [Fluid-DSL Configurer](security-configurer-dsl.md)
- [Versioning & Compatibility](../05-classpath-dependencies/versioning-compatibility.md)
