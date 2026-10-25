---
primary_layer: content
---
# Configuration Contract

[← Table of Contents]({{INDEX_PATH}}) · *Framework-Library / Configuration*

## Table of Contents

- [Summary](#summary)
- [1. Configuration Keys](#1-configuration-keys)
- [2. Configuration Sources and Precedence](#2-configuration-sources-and-precedence)
- [3. Programmatic Configuration](#3-programmatic-configuration)
- [4. Failure Behavior](#4-failure-behavior)
- [5. Assumptions and Open Questions](#5-assumptions-and-open-questions)
- [6. Self-Check](#6-self-check)
- [7. Related Docs](#7-related-docs)

{{CONFIGURATION_SUMMARY}}

## 1. Configuration Keys

| Key | Type | Default | Required | Purpose | Validation |
|---|---|---|---|---|---|
{{CONFIG_KEY_ROWS}}

Key names only — never document secret values. Mark sensitive keys with `sensitive: yes`.

## 2. Configuration Sources and Precedence

| Priority | Source | Example |
|---|---|---|
{{CONFIG_SOURCE_ROWS}}

## 3. Programmatic Configuration

{{PROGRAMMATIC_CONFIG_NOTES}}

```{{CODE_LANG}}
{{CONFIG_CODE_EXAMPLE}}
```

## 4. Failure Behavior

| Misconfiguration | Detection point | Error message contract |
|---|---|---|
{{CONFIG_FAILURE_ROWS}}

## 5. Assumptions and Open Questions

{{ASSUMPTIONS}}

## 6. Self-Check

{{SELF_CHECK_NOTE}}

## 7. Related Docs

- [Auto-Configuration](auto-configuration.md)
- [Conditional Matrix](conditional-matrix.md)
- [Fluid-DSL Configurer](../03-extension-points/security-configurer-dsl.md)
{{RELATED_DOC_LINKS}}
