---
primary_layer: workflow
---
# CI/CD Pipeline

[← Table of Contents]({{INDEX_PATH}}) · *DevOps Infrastructure Module*

## Table of Contents

{{TOC_LINKS}}

{{CICD_PIPELINE_SUMMARY}}

## Pipeline Flow

```mermaid
flowchart LR
    Trigger["{{PIPELINE_TRIGGER}}"] --> Build["Build"]
    Build --> Test["Test"]
    Test --> Package["Package"]
    Package --> Deploy["Deploy"]
    Deploy --> Verify["Verify"]
```

## Job Catalog

| Stage | Job | Input | Output | Failure Action |
|---|---|---|---|---|
{{CICD_JOB_ROWS}}
## Assumptions and Open Questions

{{ASSUMPTIONS}}

## Self-Check

{{SELF_CHECK_NOTE}}

## Related Docs

{{RELATED_DOC_LINKS}}
