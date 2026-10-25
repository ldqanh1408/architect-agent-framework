---
primary_layer: content
---
# Firmware Update Flow

[← Table of Contents]({{INDEX_PATH}}) · *IoT Edge Module*

## Table of Contents

{{TOC_LINKS}}

{{FIRMWARE_UPDATE_SUMMARY}}

## Update Lifecycle

```mermaid
stateDiagram-v2
    Idle --> Downloading: {{UPDATE_AVAILABLE}}
    Downloading --> Verifying: {{DOWNLOAD_COMPLETE}}
    Verifying --> Installing: {{SIGNATURE_VALID}}
    Installing --> Running: {{REBOOT_COMPLETE}}
    Verifying --> Rollback: {{SIGNATURE_INVALID}}
    Installing --> Rollback: {{INSTALL_FAILED}}
```

## Update Policy

| Stage | Requirement | Failure Handling | Security Control | Telemetry |
|---|---|---|---|---|
{{FIRMWARE_UPDATE_ROWS}}
## Assumptions and Open Questions

{{ASSUMPTIONS}}

## Self-Check

{{SELF_CHECK_NOTE}}

## Related Docs

{{RELATED_DOC_LINKS}}
