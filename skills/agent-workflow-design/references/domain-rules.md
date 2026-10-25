# Task Rules: `agent-workflow-design`

## Focus

Agentic and llm system behavior.

## Required Mechanisms

- **Task Contract:** document inputs, algorithm, outputs, owner, failure handling, and verification.
- **Tool Authority:** document inputs, algorithm, outputs, owner, failure handling, and verification.
- **Evaluation:** document inputs, algorithm, outputs, owner, failure handling, and verification.
- **Fallback:** document inputs, algorithm, outputs, owner, failure handling, and verification.

## Adversarial Cases

- Reject or route **self-evaluation**; assert the expected diagnostic and forbidden output behavior.
- Reject or route **unbounded context**; assert the expected diagnostic and forbidden output behavior.
- Reject or route **model-specific hidden assumption**; assert the expected diagnostic and forbidden output behavior.

## Evidence

- Preserve prompt/version hash with path/ID, freshness, and reproducible check.
- Preserve evaluation case with path/ID, freshness, and reproducible check.
- Preserve tool trace with path/ID, freshness, and reproducible check.
