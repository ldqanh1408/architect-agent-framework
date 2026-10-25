---
primary_layer: content
---
# Configuration Contract

[← Table of Contents]({{INDEX_PATH}}) · *Framework-Library Module*

## Table of Contents

{{TOC_LINKS}}

{{CONFIGURATION_SUMMARY}}

## Configuration Keys

| Key | Type | Default | Required | Purpose | Validation |
|---|---|---|---|---|---|
{{CONFIG_KEY_ROWS}}

Key names only — never document secret values. Mark sensitive keys with `sensitive: yes`.

## Configuration Sources and Precedence

| Priority | Source | Example |
|---|---|---|
{{CONFIG_SOURCE_ROWS}}

## Programmatic Configuration

{{PROGRAMMATIC_CONFIG_NOTES}}

```{{CODE_LANG}}
{{CONFIG_CODE_EXAMPLE}}
```

## Failure Behavior

| Misconfiguration | Detection point | Error message contract |
|---|---|---|
{{CONFIG_FAILURE_ROWS}}

## Assumptions and Open Questions

{{ASSUMPTIONS}}

## Self-Check

{{SELF_CHECK_NOTE}}

## Related Docs

- [Extension Points / SPI](extension-points-spi.md)
- [Public API Surface](public-api-surface.md)
{{RELATED_DOC_LINKS}}
