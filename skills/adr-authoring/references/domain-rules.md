# Task Rules: `adr-authoring`

## Focus

Maintainable documentation as code.

## Required Mechanisms

- **Audience:** document inputs, algorithm, outputs, owner, failure handling, and verification.
- **Source Authority:** document inputs, algorithm, outputs, owner, failure handling, and verification.
- **Document Structure:** document inputs, algorithm, outputs, owner, failure handling, and verification.
- **Freshness:** document inputs, algorithm, outputs, owner, failure handling, and verification.

## Adversarial Cases

- Reject or route **duplicated truth**; assert the expected diagnostic and forbidden output behavior.
- Reject or route **unverifiable example**; assert the expected diagnostic and forbidden output behavior.
- Reject or route **orphan document**; assert the expected diagnostic and forbidden output behavior.

## Evidence

- Preserve source map with path/ID, freshness, and reproducible check.
- Preserve link check with path/ID, freshness, and reproducible check.
- Preserve example execution with path/ID, freshness, and reproducible check.
