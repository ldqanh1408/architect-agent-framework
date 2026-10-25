# Task Rules: `arch-review-task`

## Focus

Enforceable architecture governance.

## Required Mechanisms

- **Policy Owner:** document inputs, algorithm, outputs, owner, failure handling, and verification.
- **Rule:** document inputs, algorithm, outputs, owner, failure handling, and verification.
- **Exception Route:** document inputs, algorithm, outputs, owner, failure handling, and verification.
- **Gate:** document inputs, algorithm, outputs, owner, failure handling, and verification.

## Adversarial Cases

- Reject or route **advisory-only standard**; assert the expected diagnostic and forbidden output behavior.
- Reject or route **self-approval**; assert the expected diagnostic and forbidden output behavior.
- Reject or route **permanent exception**; assert the expected diagnostic and forbidden output behavior.

## Evidence

- Preserve policy source with path/ID, freshness, and reproducible check.
- Preserve red-capable test with path/ID, freshness, and reproducible check.
- Preserve exception ledger with path/ID, freshness, and reproducible check.
