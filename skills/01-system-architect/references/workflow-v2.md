# Shared SDD workflow — contract v1, core 0.2

This is the workflow authority for v2 skills. `sdd_core/schema.py` owns executable
configuration and API schemas; `sdd_core/engine.py` owns acceptance. Skill files
describe author/reviewer behavior and load domain references as needed. They do
not own state transitions, evidence ledgers, numeric quality thresholds or gates.

## Framework host workflow

When this skill runs in Architect-Agent-Framework, use the host adapter. A human
initializes an empty workspace with `architect-runtime sdd host-init WORKSPACE
--workspace-id ID --reviewer HUMAN_ID`. The plugin hook reserves initialization,
reviewer enrollment, decisions, acceptance and recovery for the human channel.

Use `architect_sdd_check` and `architect_sdd_propose` for inspection and authoring.
Each proposal supplies the configured skill ID and the inspected live
`origin_snapshot`. To extend another skill's draft, supply its `change_id` as
`base_change` (CLI: `--base-change`). The combined candidate retains earlier
files, shares the same live origin and baseline, and checks each new operation
against the accepted grants. Expected file/config revisions come from the parent
candidate. Changed live bytes or baseline invalidate the chain; inspect and
rebuild it instead of overwriting edits. Authors configure only their own
obligations and external sources. Scope paths are literal directories or files.

Run `architect-runtime sdd review WORKSPACE --change CHANGE_ID` for a configured
independent judge and inspect regression. The human opens `architect-runtime
console serve WORKSPACE --enroll`, confirms a new key fingerprint at the terminal,
reviews the exact candidate, and signs any necessary semantic evidence and then
acceptance with a passkey. The initial advisory policy requires signed manual
review evidence for every obligation and the system boundary. Review packets
provide the exact source/consumer revisions and spans required for that evidence.
Raw standalone `decision record` or `accept` commands cannot bypass the host's
external signature verifier. No agent fabricates or signs human decisions.

Signed acceptance certifies and publishes the exact draft bytes through the host
journal. After interruption the human runs `architect-runtime sdd host-recover
WORKSPACE`: uncommitted acceptances are aborted without changing documents;
committed publications resume while preserving conflicting live edits. Aborted
operations require a fresh signature. `architect-runtime console verify WORKSPACE`
checks core signatures and the acceptance chain offline.

The remaining standalone examples apply to an independently operated SDD core
whose policy permits local decisions. In the framework host, use the commands
above for all authority and publication actions. Core migration is an explicit
human operation. A missing marker requires explicit initialization or migration.

## Contents

- [Intake and authority](#intake-and-authority)
- [Draft, candidate and baseline](#draft-candidate-and-baseline)
- [Structural and semantic review](#structural-and-semantic-review)
- [Candidate language review](#candidate-language-review)
- [Human decision and acceptance](#human-decision-and-acceptance)
- [Export, generated documents and freshness](#export-generated-documents-and-freshness)
- [Evaluation and recurring regression](#evaluation-and-recurring-regression)
- [Result contract and migration](#result-contract-and-migration)

## Intake and authority

Install the package in the same Python environment used by the skills:

```sh
python -m pip install /path/to/sdd-agent
python -m sdd_core doctor /path/to/spec-workspace
```

The target is a **spec workspace**, not an entire application checkout. All text
files within it are inventoried, including untracked files. Source code, binary
attachments and generated tool caches belong outside this directory. `.sdd` and
`.git` are engine state and version control, excluded from spec inventory.

Read this workflow, the skill's `workflow-contract.yml`, and the workspace's
`sdd-workspace.yml`. Read authoritative source artifacts and accepted guarantees
before authoring. The engine task record supplies the frozen read set, current
revisions and write scope:

```sh
python -m sdd_core task start WORKSPACE --skill SKILL_ID --capability author
```

Use `--capability review` for a critic. The configured grant is authoritative;
an installed skill cannot grant itself a capability. Local CLI reviewer names
are trusted local assertions, not authenticated human identities. The host must
restrict who can execute decision commands if stronger access control is needed.

## Draft, candidate and baseline

Editor/Git changes are drafts. Capture a candidate by scanning the whole tree:

```sh
python -m sdd_core reconcile WORKSPACE
python -m sdd_core check WORKSPACE --change CHANGE_ID --full
```

The returned `change_id` and `snapshot_digest` name immutable bytes. Subsequent
edits make that candidate stale for acceptance. A proposal instead creates
isolated candidate bytes without overwriting an editor's files:

```sh
python -m sdd_core changes propose WORKSPACE --file operations.json \
  --skill SKILL_ID --expect-snapshot DIGEST --operation-id OP_UNIQUE
python -m sdd_core changes inspect WORKSPACE --id OP_UNIQUE
```

An operation array supports create, update, rename, delete, deprecate, restore,
split, merge and revision-bound configure. Configuration changes cannot grant a skill new approval powers. Updates/deletes/renames require `expected_revision`; split/merge
require explicit source/replacement identities and revision mappings. Stable
clause IDs survive reordering; removed identities become tombstones after
acceptance. Restore explicitly names an earlier snapshot and rechecks today's
consumers. Rename changes paths, never IDs. Fix path-based links in the same
candidate or leave the candidate blocked with a dangling-link diagnostic.

Example update:

```json
[{"action":"update","artifact_id":"API-PAYMENT",
  "expected_revision":"CURRENT_FILE_DIGEST","content":"COMPLETE_NEW_TEXT"}]
```

Configuration uses a `configure` operation with `expected_config` (SHA256 of
canonical config) and `set`. Humans may change policy/provider/grants. An author
with `configure` permission may update only its own obligations/external sources
and must have `sdd-workspace.yml` in its write scope. Ownership changes require a
human `transfer_owner` decision. Expected config changes are reviewed against
the previous accepted authority; a candidate cannot grant itself approval rights.

## Structural and semantic review

`check` parses identities/anchors, types, links, scope and relationships; it
does not judge prose by language, keywords, number of words or interview turns.
Typed predicates compare canonical facts such as enum, timeout, unit, transitions
and retention. Historical diffs protect accepted expectations even if all current
documents are edited to agree with one another.

```sh
python -m sdd_core review WORKSPACE --change CHANGE_ID
python -m sdd_core regression WORKSPACE --change CHANGE_ID --full
```

The judge runs through a separately configured API. It receives frozen source
and consumer text, prior guarantees, graph, obligation inventory and explicit
rubrics. It cannot execute tools or write files. Findings need exact revision and
Unicode spans; missing behavior cites its authority plus inspected scope. An
invalid quote, incomplete coverage, context overflow, refusal, budget exhaustion
or HTTP failure leaves review incomplete. Per-obligation decomposition includes
its cross-document boundary; the system packet reviews missing edges. Oversized
system boundaries remain incomplete until explicitly decomposed or resized.

Review reuse requires the same packet digest, engine/rubric/provider/policy and
observations. `--force` records a new evaluation; a newer incomplete result does
not silently fall back to an older pass. Rejected rounds are capped by policy;
then revise the candidate or request human adjudication. Retry and candidate
cost reservations are bounded and durable. Configured token prices are operator
inputs; conservative reservations do not claim exact provider billing.

## Candidate language review

Use `architect_candidate_review` with the captured `change_id`. Its default runs local checks only. Set `live: true` when the configured provider and shared candidate budget permit paid review. The core runs deterministic, semantic and all-document language checks. Use `architect_language_review` to refresh language evidence separately. The CLI equivalents are `architect-runtime sdd review-candidate WORKSPACE --change CHANGE_ID --live` and `sdd language-review` through the same launcher.

Read each artifact's local findings, rule evidence, unknown rules, numerator/denominator and meaning status. Unknown rules stay in the denominator. Missing glossary authority cannot be invented. The default judge is Jev; no GPT credential or automatic model fallback is required. Jev selects outcomes and exact indexed source passages; the host author writes repairs.

For a targeted change, call `architect_language_repair` with `change_id`, `artifact_id`, complete repaired `text`, the accepted author `skill`, and the current live `expected_snapshot`. The service checks protected facts and grants, creates an isolated child candidate and reserves one of at most two repair attempts per document lineage. Replaying the same operation is idempotent; a new child does not reset rounds or the shared cost ceiling. Run candidate review on its returned change ID. Broader paraphrases need independent review rather than a relaxed fact guard.

The console displays current language jobs beside candidate diffs and findings. The signing packet binds that exact job; refreshed review evidence invalidates an old challenge. Model-assessed coverage remains advisory until its profile, glossary and model are independently qualified. Human signatures, acceptance and publication remain separate. Exceeding supported context or losing API access leaves explicit INCOMPLETE evidence; do not omit documents to make the result pass.

## Human decision and acceptance

The host presents the exact snapshot, diff, findings, evidence and before/after
guarantees to the human. Only record decisions that the human actually gave.
Never invent an actor's approval or use a synthetic fixture identity in real work.
The engine binds each decision to its reviewed baseline acceptance as well as
the snapshot: later return to identical bytes cannot revive an old approval.

```sh
python -m sdd_core decision record WORKSPACE --change CHANGE_ID --file decision.json
python -m sdd_core regression WORKSPACE --change CHANGE_ID --full
python -m sdd_core accept WORKSPACE --change CHANGE_ID \
  --expect-snapshot DIGEST --operation-id ACC_UNIQUE
```

Decision payloads contain `kind`, `actor`, `reason`, nonempty `scope` and exact
`snapshot_digest`. Supported kinds: accept, change_obligation, manual_review,
false_positive, waiver, confirm_source and transfer_owner. Manual reviews cite
current source/consumer spans. A false-positive disposition binds finding IDs and
packet digest. Waivers require enabled policy and expiry, retain accepted risk,
and never erase the original finding. Manual review cannot hide a known blocker.

`shadow`/`advisory` need human semantic evidence; `enforce` allows validated judge
coverage, still with human acceptance by default. Changing/deleting accepted
obligations or policy requires a scoped before/after decision. Removed ownership
routes to configured fallback/reviewers and stays incomplete until resolved.

Acceptance publishes one pointer to an immutable certificate and snapshot under
a local POSIX or Windows process lock. A prepared record is not a published baseline. To
resume after interruption:

```sh
python -m sdd_core recover WORKSPACE
python -m sdd_core status WORKSPACE
```

Retry the same committed operation ID to retrieve the result. An aborted
operation requires a new ID. Recovery preserves live user edits.

## Export, generated documents and freshness

```sh
python -m sdd_core export WORKSPACE --candidate --change CHANGE_ID --to NEW_DRAFT_DIR
python -m sdd_core export WORKSPACE --to NEW_ACCEPTED_DIR
python -m sdd_core derive WORKSPACE --artifact PROJECTION_ID --skill SKILL_ID
python -m sdd_core freshness WORKSPACE --due
python -m sdd_core observe WORKSPACE --source REGISTERED_SOURCE_ID
```

Export always writes a new directory. Candidate export is labeled DRAFT.
Official export revalidates the accepted baseline with current evidence and
expiry; it names accepted bytes, not subsequent working-tree edits. Proposals
remain separate from the original tree even after acceptance. Export then adopt
the new tree explicitly; there is no silent multi-file overwrite. Official export carries the immutable acceptance chain, decisions and evidence; its baseline pointer is written last. Draft exports do not carry acceptance.

Generated outputs bind source revisions, recipe graph/contracts and output hash. Editing the output or
its source makes it stale; regeneration is one-way. Supported built-in recipes
are dependency-mermaid and obligation-index; unsupported generators stay
incomplete. Registry hash edits are not semantic renewal.

External sources are registered with owner, pinned version and freshness age.
Fetch produces an observation; human confirmation binds the observation and
digest. Fetch failure is UNKNOWN. Overdue is REVIEW_DUE, not confirmed drift.
Later different bytes revoke older confirmation, including an A→B→A sequence.
Due state is calculated from the clock even if scheduled jobs miss a run.

## Evaluation and recurring regression

```sh
python -m sdd_core eval WORKSPACE --corpus tests/evals/core-corpus.json --to evaluation.json
python -m sdd_core eval WORKSPACE --corpus APPROVED_CORPUS --live --operation-id EVAL_UNIQUE --to live-evaluation.json
python -m sdd_core report WORKSPACE
architect-runtime sdd regression WORKSPACE --full --out regression-report.json
```

Without `--live` or recorded responses, evaluation is explicitly not-run. The
12-case seed has proposed labels; it cannot qualify a provider. Enforce with a
configured provider requires a current live evaluation bound to that provider's
configuration: at least 30 clean and 30 defective held-out examples, labels
approved by two human adjudicators, precision/critical recall at least 0.95 and
zero abstention/invalid evidence. These are pilot defaults; reported confidence
intervals and sample size remain visible. Qualification expires after 30 days.
Review age follows `policy.max_review_age_seconds` (default 30 days).

Per-change and pre-accept checks always reconcile all candidate files. Nightly
core CI runs full offline invariants and E2E; the reusable workspace CI consumes
a trusted restored `.sdd` acceptance history and gates readiness. Weekly external
observation can be explicitly enabled by the host scheduler, followed by human
source confirmation; it does not call a model or renew evidence automatically.
The workflows become active only when committed to the host GitHub repository.
Reports keep confirmed blockers, repaired drafts, accepted closure, risk waivers
and owner fallback visible. A repaired draft alone does not close accepted debt.

## Result contract and migration

PASS means the requested check's scope passed; deterministic PASS alone is not
acceptance. FAIL means a confirmed blocking violation. ERROR, INCOMPLETE and
STALE cannot be accepted. SKIPPED/N/A are never substitutes for missing required
coverage. CLI JSON reports `scope: spec-only`; it does not certify implementation.
Exit codes: 0 success in the requested mode, 1 failure, 2 invocation/schema/I/O
error, 3 incomplete/stale/unavailable evidence.

```sh
architect-migrate OLD --workspace-id ID --reviewer HUMAN_ID --owner 01-system-architect
architect-migrate OLD --destination NEW --workspace-id ID --reviewer HUMAN_ID --owner 01-system-architect
architect-migrate OLD --destination NEW --resume --workspace-id ID --reviewer HUMAN_ID --owner 01-system-architect
```

Migration preserves the original, reports ambiguities/unsupported files, creates
stable initial IDs and imports unverified drafts. Legacy PASS is not a v2
certificate. Resume verifies all copied bytes and the original plan; any newer
target/source edit is preserved and reported as a conflict. Old workflow writers, signatures and pending runs are not imported or executed.
The migration reader is a separate offline tool; the runtime has no fallback authority.
