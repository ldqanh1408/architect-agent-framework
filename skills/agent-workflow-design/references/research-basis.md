# AI-Agent Workflow Design Contract — Open-Source Research Basis

Repositories inspected while designing this skill, the concepts adapted from each, and the ones deliberately rejected. Moved verbatim out of `SKILL.md` so it loads on demand rather than on every trigger.

These sources are references, not runtime authorities. Project evidence and `skill-contract.yml` remain authoritative for an execution.

## Sources Inspected

- `majiayu000/claude-skill-registry@ef926663574f5f7a0c19b0429b2540373279ed45`, `skills/design/agentic-workflow-design/SKILL.md`: loop/plan/multi-agent/handoff/tool/state/error vocabulary; C# patterns, max iterations/turns, role prompts and implementation defaults rejected.
- Same revision, `skills/design/agent-workflow-patterns/SKILL.md`: workflow/loop/tool/monitoring vocabulary; Vercel/OpenAI defaults, fixed iteration/token/time/confidence limits and templates rejected.
- Same revision, `skills/data/multi-agent-patterns/SKILL.md`: context isolation, supervisor/peer/hierarchical, coordination/failure vocabulary; token multipliers, benchmark claims, voting/debate/TTL/retry prescriptions rejected.
- Same revision, `skills/data/langgraph-multi-agent/SKILL.md`: supervisor/swarm/agent-as-tool/state/handoff vocabulary; LangGraph/LangChain/OpenAI packages, models, in-memory stores and code defaults rejected.
- Local agent-architect owns integrated autonomous-loop architecture; architect-skill-orchestrator owns metadata-only skill routing, not runtime workflow.

These sources are boundary evidence, not authority for topology, agents, frameworks, tools, permissions, timers, limits or outcomes.
