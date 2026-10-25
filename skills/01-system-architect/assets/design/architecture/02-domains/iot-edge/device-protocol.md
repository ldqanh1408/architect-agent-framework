---
primary_layer: content
---
# Device Protocol

[← Table of Contents]({{INDEX_PATH}}) · *IoT Edge Module*

## Table of Contents

{{TOC_LINKS}}

{{DEVICE_PROTOCOL_SUMMARY}}

## Protocol Sequence

```mermaid
sequenceDiagram
    participant Device as {{DEVICE}}
    participant Gateway as {{GATEWAY}}
    participant Cloud as {{CLOUD_SERVICE}}
    Device->>Gateway: {{DEVICE_MESSAGE}}
    Gateway->>Cloud: {{UPLINK_MESSAGE}}
    Cloud-->>Gateway: {{DOWNLINK_COMMAND}}
    Gateway-->>Device: {{DEVICE_COMMAND}}
```

## Message Contract

| Message | Direction | Payload | QoS/Retry | Security |
|---|---|---|---|---|
{{DEVICE_PROTOCOL_ROWS}}
## Assumptions and Open Questions

{{ASSUMPTIONS}}

## Self-Check

{{SELF_CHECK_NOTE}}

## Related Docs

{{RELATED_DOC_LINKS}}
