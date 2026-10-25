# Orchestration Rules

- Score compact registry metadata only; do not ingest leaf skill bodies before selection.
- Enforce compatibility in both domain-to-family and task-to-cluster directions.
- Tied or low-confidence candidates block and require explicit selection.
- Select the smallest compatible leaf set that covers the requested decision: a direct authoritative leaf, one domain leaf, one task leaf, or one domain-plus-task pair. A pair is never the default.
- A load plan contains exactly the selected leaves' `SKILL.md` and `skill-contract.yml` — two files for a single leaf, four for a pair.
- Leaf contracts, not the orchestrator, own writes and completion.
