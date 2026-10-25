# Architecture Review Execution Contract — Open-Source Research Basis

Repositories inspected while designing this skill, the concepts adapted from each, and the ones deliberately rejected. Moved verbatim out of `SKILL.md` so it loads on demand rather than on every trigger.

These sources are references, not runtime authorities. Project evidence and `skill-contract.yml` remain authoritative for an execution.

## Sources Inspected

- `majiayu000/claude-skill-registry@ef926663574f5f7a0c19b0429b2540373279ed45`, `skills/data/architecture-review/SKILL.md`: requirements/constraints/bottleneck/risk/trade-off grounding; broad scalability/reliability/maintainability-only scope rejected.
- Same revision, `skills/data/architecture-design-review/SKILL.md`: review-area/finding/report vocabulary; monolith/microservice user/team cutoffs, technology/pattern choices, C4/ADR checklist, security products, RPO/RTO, severities/scores/effort estimates rejected.
- Same revision, `skills/data/architecture-review-and-approval/SKILL.md`: authority/validation boundary; design/stack selection, strong/eventual consistency, rollout/rollback and success-metric invention rejected.
- Same revision, `skills/data/running-design-reviews/SKILL.md`: review brief/feedback/dissent/follow-up boundary; UI/design-critique, Value→Ease→Delight, five questions, roles, timed agenda and due-date defaults rejected.
- Local review-architect owns portfolio/governance; this leaf executes one review.

These sources are boundary evidence, not authority for criteria, reviewers, scores, severities, decisions or remediation.
