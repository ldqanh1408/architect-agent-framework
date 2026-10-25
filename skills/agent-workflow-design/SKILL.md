---
name: agent-workflow-design
description: "Design agent DAG interaction and subagent delegation workflows. Use when an authoritative objective/use case, task and decision boundaries, actors/owners, input-output contracts, tools/permissions, state/memory, data/security constraints, evaluation, failure/recovery and runtime authority must be converted into one bounded AI-agent workflow design. Produces explicit control, handoff and resume contracts without inventing autonomy or frameworks. Do not use for integrated autonomous-agent architecture, deterministic workflow implementation, prompt/tool/memory/model design alone, operating coding agents or generic task delegation."
license: MIT
compatibility: "Agent Skills clients; filesystem read/write access; accepted objective, actor, contract, tool, state, policy, evaluation and operations evidence when supplied"
allowed-tools: "read_file search_files write_file terminal"
version: 2.1.0
author: Architect Agent Framework
metadata:
  hermes:
    tags: [architecture-task, ai-tasks, agent-workflow, orchestration, handoffs]
---

# AI-Agent Workflow Design Contract

## Overview

`agent-workflow-design` defines one authority-bounded workflow in which deterministic, model-controlled, tool/service and human steps coordinate through typed state and handoffs. It does not invent agents, grant autonomy, select frameworks, implement runtime code or prove useful outcomes.

A DAG, role prompt, group chat, framework graph or successful run alone does not prove correct authority, durable state, safe effects, recoverability or quality.

## Fast Path

Take this route first. Leave it the moment a step cannot be answered from supplied authority.

1. **Check more than one decision loop is warranted.** If one agent with the right tools can do it, a second agent adds coordination cost and a new failure mode. Route to `agent-architect` for the loop itself.
2. **Assign each node a task class, not a persona.** What it decides and what it returns. Nodes named "researcher" and "critic" share tools and context and differ only in prompt, which is one agent wearing hats.
3. **Fix the contract on every edge.** Input, output schema, and what a downstream node does with a malformed one. Edges carrying free text make every node a parser of the last node's mood.
4. **Bound the graph.** Maximum depth, maximum fan-out, and whether cycles are permitted. An unbounded delegation graph is how one request becomes four hundred model calls.
5. **Decide who merges and who may not self-certify.** The node that produces a result must not be the node that approves it. Merge authority left implicit defaults to the last writer.
6. **Write the blueprint under the owned root**, classify every claim, and run postflight.

Leave the fast path for `## Workflow` when nodes run in parallel over shared state, when a child may spawn further children, when partial failure must be reconciled, or when a human sits inside the graph.

## Worked Example

**Intake.** "Our contract review assistant spawns a researcher, a summariser and a critic. It sometimes runs for twenty minutes, and last week the critic approved a summary that had invented a clause."

**What this skill produces** (excerpt from `multi-agent-workflow-blueprint.md`):

```markdown
## Workflow Graph

Node contract [NC-1]
  | node          | task class        | returns                          |
  |---------------|-------------------|----------------------------------|
  | clause-extract| extraction        | {clause_id, text, page, span}[]  |
  | risk-assess   | classification    | {clause_id, risk, rationale}[]   |
  | verify        | verification      | {clause_id, found_in_source:bool}|
  No "critic". A node whose only distinction is a prompt asking it to be
  sceptical shares the extractor's context and confirms its errors.

Edge contract [EC-1]
  clause-extract -> risk-assess: array above, schema-validated
  a clause_id absent from the source document is rejected AT THE EDGE
  This is the invented clause: it passed because the edge carried prose.

Graph bounds [GB-1]
  max_depth: 2      max_fan_out: 12 clauses per batch      cycles: forbidden
  budget: 60 model calls per document, hard stop
  The twenty-minute run was 340 calls, from a re-review loop with no bound.

Merge authority [MA-1]
  merge: deterministic assembler, not a model
  a clause enters the report only if verify.found_in_source is true
  why: the producing node must not certify its own output, and a model asked
       to approve its predecessor's work agrees with it most of the time.
```

**What it does not produce.** The agent runtime, the prompts, the document parser, or the risk taxonomy. Those are handoffs to `agent-architect`, `prompt-engineering`, and the legal domain.

## When to Use

Use when accepted AI-agent/runtime capabilities need a concrete workflow/control graph with explicit steps, transitions, contracts, effects, failures and human intervention.

Do not use for autonomous-agent architecture, deterministic implementation, prompt/tool/memory/model design alone, agent operation or generic delegation. Agent/workflow vocabulary alone is insufficient routing evidence.

## Ownership and Write Boundary

This task writes only `<output_root>/architecture/00-system-views/06-runtime/multi-agent-workflow-blueprint.md`. Agents, prompts, models, tools, services, memory, workflow engines, policies, deployments and runtime state remain read-only.

This task owns workflow topology, step/transition contracts, coordination, handoffs, state/checkpoints, effect/recovery and evaluation integration. `agent-architect` owns the integrated autonomous loop. Domain/tool/security/evaluation/platform owners define capabilities and implementation authority.

## Required Distinctions

- **Process** describes governed work; **workflow** defines executable progression; **plan** is intended sequence.
- **Orchestration** coordinates centrally; **choreography** uses participant events.

- Run is one workflow instance; step/node is bounded work; edge/transition controls eligibility and state movement.
- Event/message can trigger or carry facts; artifact is persisted output; context is selected decision input; state is authoritative run fact.
- Agent is an AI-controlled decision loop; role is responsibility/capability contract; persona is presentation/instruction framing.
- Model generates/decides under a prompt/config; runtime hosts execution; tool/service exposes capability/effect; human owns accountable judgment.

- Deterministic code applies owner-authored logic; model decision is probabilistic inference; tool action invokes external capability; human action exercises authority.
- Use deterministic validation/routing where rules are complete; do not delegate known arithmetic, policy or side-effect checks to model judgment silently.
- Single-agent workflow has one independent decision loop; multi-agent has multiple loops with explicit coordination contracts.

- Multi-agent must be justified by task decomposition, context isolation, authority/tool separation or evaluated quality—not organizational metaphor.
- Centralized/supervisor topology has one coordinator; decentralized/peer topology uses direct protocols; hierarchy adds bounded delegation layers.

- Router selects a path/owner under criteria; coordinator manages progression; planner proposes work; executor performs bounded work.
- Specialist supplies domain result; reviewer critiques under criteria; evaluator applies oracle; approver/decider exercises authority.

- Objective/task/decision/authority/owner remain distinct: task delegation never transfers undeclared decision or effect authority.
- Workflow input binds identity/schema/source/revision/trust/sensitivity; output binds schema/provenance/status/consumer/oracle.
- Step preconditions, permitted reads/writes/tools/effects, postconditions and failure states require stable identities.
- Message/handoff is a typed transfer; shared conversation text is not a reliable contract or authority boundary.
- Delegation transfers exact task, context, capabilities, authority, output schema, deadline/cancellation semantics and evidence requirements.

- Handoff differs from delegation: handoff transfers active responsibility/control; delegation can retain parent control and await result.


- Shared state differs from private agent scratch/context; each field needs owner, writer, conflict and freshness rules.
- Working state tracks current run facts; checkpoint is durable recovery boundary; memory is separately governed retained/retrieved information.

- State schema includes workflow/run/step/action/attempt/message/artifact/checkpoint/approval/delegation IDs and lifecycle states.

- Sequential execution respects dependencies; parallel/fan-out requires independence or conflict controls; fan-in needs aggregation/merge semantics.


- Aggregation can preserve, select, merge, vote, synthesize or escalate; strategy and authority must be supplied.

- Reviewer/evaluator must not be circularly asked to validate its own unsupported output as the only oracle.
- Terminal outcomes include complete, partial, unable, blocked, rejected, cancelled, expired, unsafe and failed under supplied vocabulary.

- Transition guard uses explicit state/evidence/authority; model confidence is not a universal branch threshold.
- Loop continuation/termination needs owner-defined progress, completion, inability, safety, resource and escalation semantics.

- Retry repeats an eligible attempt; backoff controls timing; neither is safe without error classification and effect reconciliation.

- Timeout limits waiting/execution under authority; timeout does not prove cancellation or absence of side effect.

- Idempotency prevents/reconciles duplicate effects for an identity; deterministic text generation alone is not idempotent outcome.

- Partial effect requires receipt/observation/reconciliation before retry, compensation or resume.
- Compensation is a new authorized effect, not generic rollback; irreversible actions need escalation/containment.
- Checkpoint validity binds workflow/state/prompt/model/tool/policy/source revisions and completed effect receipts.
- Resume restores from validated checkpoint, reconciles external effects and invalidates stale pending decisions.


- Human-in-loop can review, approve, steer, supply evidence, take over or revoke; identity/scope/timing/expiry must be explicit.

- Fail-open/fail-closed/degrade/hold behavior requires authority per failure and effect class.
- Tool contract binds eligibility, typed inputs/outputs/errors, data/effect scope, reversibility, idempotency, cancellation and evidence.
- Tool call success/exit code proves adapter behavior only; business effect and postcondition need observation.


- Permissions bind actor/workflow/run/tool/action/resource/tenant/environment/data/effect and time; least privilege is capability-specific.


- Data classification, residency, purpose, minimization, retention/deletion and cross-agent disclosure follow security/privacy authority.

- Prompt, model, tool, policy, state schema and runtime configuration have independent versions and compatibility.



- Workflow design differs from prompt authoring, model selection, tool implementation, memory/RAG design and deployment.
- Workflow trace binds trigger, selected inputs/context, decisions, messages, tools, state transitions, effects, errors and terminal outcome.

- Evaluation claim binds task population/dataset, oracle/evaluator, metrics, baseline, coverage and uncertainty.
- Quality, correctness, groundedness, safety, cost and latency are separate dimensions; one aggregate score cannot hide failures without authority.





- Fallback can be deterministic path, alternate capability/model, human, partial output, hold or fail; trigger/authority/equivalence need definition.


- Evidence states include proposed, accepted, configured, implemented, deployed, invoked, running, awaiting, delegated, blocked, interrupted, resumed, completed, partial, failed, cancelled, evaluated, observed, stale and retired.
- **Completion** means workflow-design evidence gates passed—not implementation deployed or objective achieved.

## Workflow Evidence Tuple

Bind claims to stable design/objective/use-case/workflow/run/step/transition/actor/agent/role/model/prompt/tool/service/human/message/artifact/context/state/memory/checkpoint/action/attempt/effect/approval/delegation/handoff/evaluation/deployment IDs; exact contract/schema/config/policy/source revisions; proposed/accepted/implemented/deployed/invoked/evaluated/stale states; authority, provenance, data class, permissions, concurrency, failure/recovery and invalidation trigger.

Keep design, implementation, configuration, deployment, invocation, effect, evaluation and outcome separate.

## Required Intake

Require objective/use case and terminal outcomes; current/target behavior; task/decision/authority owners; actors/agents/humans; typed inputs/outputs/artifacts/messages; tools/services/effects/permissions; state/context/memory/checkpoints; topology/coordination needs; concurrency/asynchrony; retries/timeouts/cancellation/idempotency/compensation/escalation; data/security/privacy; prompt/model/runtime revisions; evaluation claims/oracles; deployment/operations owners and output conventions.

Block rather than infer need for AI/multi-agent, roles/topology, decomposition, routing/aggregation, shared context/state, permissions, tools, autonomy, retries/timers/limits, human gates, failure/recovery, frameworks/models/prompts, evaluation metrics/thresholds or production outcome.

## Blocking Conditions

Block when objective/terminal authority is absent; deterministic workflow would suffice but AI choice is unexplained; step/decision/effect owners are unclear; handoffs lack schemas/provenance; tools have unknown side effects; shared state has conflicting writers; repeated/partial effects cannot reconcile; stop/cancel/resume/escalation is undefined; prompt is sole security control; evaluator is circular; or success is claimed from DAG validity, agent count, framework compile, tool exit, consensus, deployment or sampled trace alone.

Return stable IDs, blocked steps/transitions/actors/contracts/effects/claims, missing authority/evidence, safe deterministic/single-agent/human/hold alternative, owner and exact resume condition.

## Minimum-Sufficient Design

Compare no automation, deterministic workflow, model-assisted step, constrained tool-calling assistant, single agent, supervisor with deterministic workers, bounded multi-agent fan-out/fan-in, peer handoff and human-led handling. Use least autonomous topology satisfying accepted requirements. Do not default to ReAct/planner-reviewer, multiple agents, LangGraph/CrewAI/AutoGen, shared memory, parallelism, voting, model confidence, retries, timers, limits or tools.

## Workflow

1. **Frame workflow decision.** Record objective/use case, consumer/actors, current/target behavior, terminal outcomes, non-goals and write boundary. Done when workflow—not integrated agent architecture/implementation—is required.
2. **Resolve authorities.** Identify product/domain, task/decision, tool/effect, data/security, evaluation, human-approval and runtime owners. Done when topology cannot create authority.
3. **Freeze inputs.** Inventory exact accepted agents/prompts/models/tools/services/state/memory/policies/evaluations and revisions. Done when design is reproducible.
4. **Classify mechanism.** Compare deterministic, model-assisted, single-agent and multi-agent needs by who selects actions. Done when labels cannot force autonomy.
5. **Define terminal outcomes.** Specify complete/partial/unable/blocked/rejected/cancelled/expired/unsafe/failed semantics and oracles. Done when fluent text cannot end run.
6. **Decompose bounded work.** Map tasks/decisions/dependencies/owners without inventing product scope. Done when each step has one purpose/authority.
7. **Define actors/roles.** Bind agent/human/service responsibilities, capabilities, permitted decisions and non-responsibilities. Done when personas cannot grant access.
8. **Design control topology.** Choose sequence/branch/loop/fan-out/fan-in/router/coordinator/handoff only from requirements. Done when minimum topology is justified.
9. **Specify step contracts.** Define preconditions, inputs, reads/writes, action/tool/effect, output/error, postcondition and oracle. Done when every node is executable in principle.
10. **Specify transitions.** Bind guards/events/evidence/authority/state updates and default/unknown handling. Done when model confidence cannot silently route.
11. **Define state/context.** Specify run IDs, canonical/shared/private fields, writers, freshness, conflicts, retention and context selection. Done when conversation is not state by default.
12. **Define messages/artifacts.** Specify schemas, provenance, trust, sensitivity, consumer, acknowledgement and compatibility. Done when prose handoff cannot reconstruct missing facts.
13. **Define delegation/handoffs.** Bind task/context/capabilities/authority/output/failure/cancellation/merge semantics. Done when parent authority is not inherited.
14. **Define concurrency/asynchrony.** Specify dependencies, parallel eligibility, isolation, deduplication, race/conflict and fan-in behavior. Done when parallelism cannot duplicate effects.
15. **Integrate tool/effect authority.** Bind eligibility, permission, approval, effect receipt, reconciliation and postcondition per action. Done when tool call is not outcome proof.
16. **Design failures/recovery.** Classify errors and define retry/hold/fallback/compensation/escalation under sourced policies. Done when counts/timers are not invented.
17. **Design checkpoint/resume.** Bind durable state, effect receipts, validity/invalidation and reconciliation. Done when restart cannot repeat effects.
18. **Design human intervention.** Specify review/approval/steer/takeover/revoke identities, scope, expiry and unavailable behavior. Done when human gate is operational.
19. **Apply data/security boundaries.** Map classifications, permissions, secrets, sandboxing, untrusted content, retention and disclosure. Done when prompts are not controls.
20. **Integrate evaluation/observability.** Define traces, task populations, oracles, dimensions, baseline, coverage, cost/latency and outcome handoff. Done when self-evaluation cannot certify.
21. **Compare topology alternatives.** Expose deterministic/single/multi-agent cost, latency, quality, context, authority and failure trade-offs. Done when complexity is not auto-selected.
22. **Adversarially verify.** Test stale context, prompt injection, wrong route, disagreement, duplicate/partial effect, timeout without cancellation, checkpoint drift and unavailable approver. Done when each yields evidence or blocker.
23. **Issue typed handoffs.** Route agent-architecture, prompt/tool/state/security/evaluation and runtime-implementation gaps with resume conditions. Done when designer cannot implement or deploy.
24. **Publish owned artifact.** Write only resolved run-root workflow/evidence record. Done when output is minimum sufficient.
25. **Close or resume safely.** Validate topology/steps/transitions/contracts/state/authority/effects/recovery/security/evaluation/freshness. Done when completion means design passed—not outcome.

## Typed Outputs and Handoffs

- `agent_workflow_scope`: design/objective/use-case/actors/terminal outcomes/owners/source IDs and exclusions.
- `agent_workflow_graph_contract`: workflow/run/state/step/transition/dependency/guard/actor/input/output/error/effect/oracle record.
- `agent_handoff_state_contract`: delegation/handoff/message/artifact/context/state/checkpoint/provenance/permission/concurrency/resume semantics.
- `agent_workflow_failure_evaluation_contract`: error/retry/fallback/cancel/compensation/escalation/human/evaluation/trace/coverage semantics.
- `agent_architecture_authority_handoff`: missing autonomy/goal/agent/topology/tool/effect/state/oversight architecture authority.
- `agent_component_policy_handoff`: missing prompt/model/tool/memory/data/security/permission/evaluation contract.
- `agent_runtime_implementation_handoff`: missing framework/engine/queue/persistence/deployment/operations/telemetry implementation authority.

Every payload includes stable ID, producer, consumer/owner, workflow/step/state/tool/effect/evaluation/source/authority revisions, assumptions, unknowns, stale behavior and acceptance oracle.

## Resume Semantics

A blocker records design/workflow/step/transition/actor/agent/tool/message/state/checkpoint/effect/approval/handoff/evaluation/runtime/output IDs, missing authorities, conflicts, requests, owners and resume point. On resume compare objective/task/contract/prompt/model/tool/policy/state/evaluation/runtime revisions; preserve accepted topology/history, invalidate stale transitions/checkpoints and never convert design into deployment/outcome.

## Open-Source Research Basis

Recorded in `references/research-basis.md`: the repositories inspected for this skill, the concepts adapted from each, and the ones deliberately rejected. Load it when auditing provenance or revising the skill's boundaries; it is not required to execute the skill.

## Verification Checklist

- [ ] Trigger requests one bounded AI-agent workflow design
- [ ] Product/task/tool/security/evaluation/human/runtime owners resolve
- [ ] Design/configuration/deployment/invocation/effect/evaluation/outcome states remain distinct
- [ ] Topology/step/transition/handoff/state/effect/recovery semantics are explicit
- [ ] Concurrency/security/human/evaluation/freshness limitations are bounded
- [ ] Agents, frameworks, retries, timers, autonomy, tools and thresholds remain sourced
- [ ] Typed architecture, component-policy and runtime handoffs resolve gaps
- [ ] Completion means design passed—not deployment or objective achievement
- [ ] Resume invalidates stale checkpoints and reconciles effects
- [ ] Only artifacts under the resolved agent-workflow-design run root are writable
