# Requirement Clarifier Rules (Clarification Specification)

Authoritative rules for how `requirement-clarifier` conducts interviews and derives clarified requirements. SKILL.md and the agent prompt summarize these rules; this file is the detailed contract.

## 1. Derivation Rules

| Input (brief element) | Decision | Output element |
|---|---|---|
| Stated behavior ("users can X") | Rewrite in EARS with trigger + response | CLR-xxx row, MoSCoW class |
| Vague quality ("fast", "secure") | Demand a number in Round 5; refuse to record adjectives | CLR-xxx NFR with concrete metric |
| Unstated but necessary fact | Ask in the matching round; if user defers, propose a default | ASM-xxx (confirmed) or Open Question |
| Contradiction inside the brief | Surface both statements, ask user to pick | Interview-log row + corrected CLR |

## 2. Traceability Rules

- Every CLR-xxx records the interview round that resolved it (`Resolved In` column).
- CLR and ASM numbering is stable: never renumber; append only.
- `system-architect` maps every derived REQ-xxx back to a CLR-xxx (`REQ-001 ← CLR-003`); a REQ without a CLR source is a workflow-hook error once Phase 0 has run.

## 3. Classification Rules

| MoSCoW | Criteria |
|---|---|
| Must | Launch is meaningless without it, or legally required |
| Should | Important, but a manual workaround exists for launch |
| Could | Improves the experience; first candidate to cut |
| Won't | Explicitly out of scope this cycle — recorded so nobody re-adds it silently |

| Assumption status | Meaning |
|---|---|
| confirmed | User explicitly agreed (quote the round) |
| unconfirmed | Proposed by the clarifier, awaiting user decision — blocks the design workflow hook |

## 4. Boundary Rules

- This skill NEVER writes specifications — that is `system-architect`'s job on top of `clarified-requirements.md`.
- This skill NEVER decides an assumption on the user's behalf; a proposed default stays an Open Question until confirmed.
- When the user asks to change an already-specified requirement, run supplement mode (a delta interview) and hand the delta to `system-architect` instead of re-interviewing the whole brief.

## 5. EARS Reference

Accepted EARS patterns (pick the simplest that fits):

| Pattern | Form |
|---|---|
| Ubiquitous | The <system> shall <response>. |
| Event-driven | When <trigger>, the <system> shall <response>. |
| State-driven | While <state>, the <system> shall <response>. |
| Unwanted behavior | If <undesired condition>, then the <system> shall <response>. |
| Optional feature | Where <feature is included>, the <system> shall <response>. |

## 6. Output Quality Rules

- Follow the shared page structure in [template-standard.md](template-standard.md).
- No unresolved placeholders, no `TODO`; use `unspecified` plus an Open Question entry when facts are missing.
- Validate generated documents with `scripts/check_output_docs.py` before reporting completion.
