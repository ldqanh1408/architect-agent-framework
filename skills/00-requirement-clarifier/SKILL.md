---
name: 00-requirement-clarifier
description: "SDD requirement clarification: Clarify raw briefs and incremental requirement deltas into sourced stable clauses, EARS behavior, MoSCoW priorities, assumptions and questions. Use when intent, scope, actors or acceptance criteria need clarification before architecture."
---

# Requirement Clarifier

## Required intake

Read [workflow-contract.yml](workflow-contract.yml) and [the domain method](references/clarification-method.md) **before every task**. The domain method is active guidance, not optional background. Read the complete authoritative brief and the relevant accepted baseline. Keep source facts, proposed assumptions and approved decisions distinct.

Use the current core lifecycle before writing:

- A `sdd-workspace.yml` marker selects [the core workflow](references/workflow-v2.md). A malformed marker is an error; never fall back to legacy.
- A workspace without that marker requires explicit initialization or migration. Do not run an old workflow.

Do not write `.sdd` records, approval records or engine/host ledgers yourself. Use the selected host service. Follow the granted ownership and scope; task completion is separate from review and human acceptance. Read required references even when only `SKILL.md` was loaded by the host.

## Work sequence

1. Inventory source clauses and current requirements with stable IDs, revisions and exact anchors.
2. Clarify the highest-impact uncertainty across business/value, actors/boundaries, features/MoSCoW and applicable quality/operation. Use the persona in the domain method: useful context before a small question group, no forced turn quota.
3. Normalize agreed behavior with the five EARS forms; preserve user meaning. Split independently testable obligations and maintain complete source coverage.
4. Record assumption reversal triggers and open-question owners. Do not invent metrics, defaults or confirmation.
5. For an existing spec, use supplement mode: new, modify, remove/deprecate or clarification-only delta with affected REQ/API/ENTITY/ADR IDs. Leave architecture edits to its owner.
6. Produce the clarified requirements/problem brief or delta using [the template](assets/clarified-requirements-template.md); adapt its lifecycle fields to the chosen host. Run actual checks and hand off unresolved issues and exact revisions.

Load [ambiguity taxonomy](references/ambiguity-taxonomy.yml) when categorizing uncertainties. Route architecture and diagrams to the architect, review to the critic.

## Workspace boundary

Use the active method and current output contract. Process old input only through the separate migration tool. Imported records grant no current approval.


Read [document-style.md](references/document-style.md) before writing or repairing English prose. Preserve protected facts and report incomplete style evidence.
