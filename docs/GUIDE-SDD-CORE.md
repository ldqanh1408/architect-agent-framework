# SDD core: install, author, review and accept

Use this guide for a spec workspace with `sdd-workspace.yml`. A missing marker requires explicit setup or migration. A malformed marker requires repair. Use the current task guide for scheduling and review.

## Install and initialize

Install this alpha checkout into an active Python 3.10+ environment:

```bash
python -m pip install ".[sdd,console]"
architect-runtime sdd host-init ./my-spec --workspace-id my-project --reviewer owner
```

Run initialization in the person's terminal. Use a new empty spec directory, separate from the application code and binary assets. Existing workspaces require an explicit migration dry run and a new destination; opening them does not migrate them.

Load the delivered plugin from the release directory:

```bash
claude --plugin-dir ./repo/plugins/architect-agent-framework
```

The plugin carries the free catalog and the three SDD foundation skills. The runtime command is supplied by its launcher. In Claude Code, commands carry the plugin namespace, for example `/architect-agent-framework:architect-run ./my-spec`.

## Authoring and checks

1. Give the agent the authoritative brief and confirmed answers. `00-requirement-clarifier` preserves source clauses, EARS behavior, assumptions and open questions.
2. `01-system-architect` plans the smallest sufficient document set, canonical fact owners, shared contracts and failure/recovery behavior. Its method and conditional references remain required.
3. The agent inspects `architect_sdd_check` and proposes isolated candidate bytes through `architect_sdd_propose`. The expected live snapshot and granted skill scope are required. A later author extends the earlier `change_id` with `base_change`.
4. Full deterministic checks and historical regression inspect the candidate. `02-spec-critic` reviews exact revisions read-only. A configured independent judge is advisory until its model/prompt/corpus/policy qualification permits otherwise. Missing access, evidence or coverage is INCOMPLETE.
5. The person receives the candidate diff, findings and review packets. Changed source bytes, baseline or policy invalidate stale evidence; an old PASS is not carried forward automatically.

`/architect-check` and `/architect-status` inspect core work without creating proposals. The sample-view consistency CLI is an example of rules, not a full audit of the person's workspace.

## Document shape and external skills

Declare artifacts, owners, typed dependencies and obligations in `sdd-workspace.yml`. Source-backed package templates suggest conditional document shapes; they do not grant write authority. Preview explicit selections with `scripts/scaffold_skill_workspace.py`, then submit scoped core proposals. Preserve authored paths and contents. Old tree, phase and seam ledgers require migration and do not certify current readiness.

Install a package whose frontmatter name matches a catalog slot:

```bash
architect-runtime skills install /path/to/skill-pack.zip
architect-runtime skills doctor
architect-runtime skills offer backend-service-architect
```

Packages persist under `~/.architect-framework/exported_skills/`. The installer fills known catalog slots. For a differently named third-party skill, keep its package outside the spec workspace and bind the slot in the user-level `~/.architect-framework/skill-bindings.yml`:

```yaml
schema_version: "2026.10"
bindings:
  backend-service-architect:
    path: /path/to/external-skills/spring-boot-expert
```

Use an absolute path to the external package. Do not place host skill packages or binding files in the core spec workspace: its files must be registered artifacts or declared attachments. The package at that path must contain `SKILL.md`. A content-only binding uses the slot's existing contract. A compatible `workspace-template.yml` can declare output shape; a custom contract governs only from a trusted source. Neither installation nor a binding grants authority to accept or write another owner's documents. A new output type requires explicit contract/template/check support; arbitrary skills do not register new document semantics automatically.

## Human review and publication

In the person's interactive terminal, start first-time enrollment:

```bash
architect-runtime console serve ./my-spec --enroll
```

Open the printed `localhost` URL. Register the passkey, then confirm the displayed key fingerprint in the terminal. Read the exact candidate and sign required semantic review evidence and acceptance. An agent cannot confirm the key, sign a decision or accept a candidate.

The host verifies reviewer trust, snapshot, baseline and policy; core acceptance uses compare-and-swap, then the host publishes the certified bytes. After an interrupted publication, the person runs:

```bash
architect-runtime sdd host-recover ./my-spec
architect-runtime console verify ./my-spec
```

Recovery preserves conflicting live edits and reports them. A software-authenticator fixture does not certify a physical device or a live target host.

## Regression and qualification

CRUD checks inspect old and new consumers, obligations and accepted guarantees. Source observation, expiry, policy/model/prompt changes and unknown sources retain separate freshness states. Deterministic PASS means the requested predicates passed; semantic completeness and implementation/deployment behavior require their own evidence.

Before publishing the plugin, its owner exports hash-only paid-content coverage from the original corpus:

```bash
python scripts/check_public_tree.py --source /path/to/private-source --write-fingerprints release/paid-fingerprints.json
python scripts/build_public_tree.py --out dist/public-tree
python scripts/check_public_tree.py --tree dist/public-tree --require-paid-corpus --report dist/public-scan.json
# Build wheel/sdist/bundles from dist/public-tree, then qualify the actual archives:
python scripts/check_release_artifacts.py dist/python/* dist/bundles/*.zip --require-paid-corpus --report dist/artifact-scan.json
```

Keep only the exported hashes in the public repository. Missing original coverage returns INCOMPLETE for release qualification. A regular structural scan remains useful but does not certify original paid-content leak coverage. Native Windows, live hosts, physical passkeys, independent judge labels and publication accounts require separate qualification.
