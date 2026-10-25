# Evaluate documents with Jev

Jev is the default judge for cross-document semantics and the eight-rule language profile. The host author writes and revises drafts. No GPT model, OpenAI credential or automatic alternate-provider fallback is required. Assessment never grants qualification, acceptance or publication.

## Defaults and bounds

| Setting | Default |
|---|---|
| Judge | `typesafe-jev`, `https://api.typesafe.ai/v1/systemone`, `jev-1.14.0` |
| Credential | Server environment variable `JEV_API_KEY` |
| Reservation ceiling | USD 5 in a persistent SQLite ledger for pilot/language calls |
| Document review | One verdict request and one witness request per complete obligation packet; one attempt per stage, shared 60-second deadline |
| Context | Complete request at most 200,000 bytes; at most 127 source paragraphs and 128 questions per stage |
| Language assessment | At most 64 complete eligible sentences; 32 atomic rule questions per batch, full document context in every batch |
| Repair | Host-authored candidate; at most two rounds, 34 Jev calls and a shared 60-second default deadline (never more than 120 seconds) |

Pins identify repeatable configurations; they do not establish quality. Changing a pin or adapter invalidates the provider implementation binding and requires new qualification. On 2026-10-19 the authenticated catalog and pinned `jev-1.14.0` requests returned HTTP 200. Direct candidate/style/meaning evaluation and canary results remain advisory; the canary did not qualify the model. See direct verification for that dated run and qualification E2E for the subsequent preflight, resumption and input-discovery evidence.

Jev USD 1 per million input/output tokens is a conservative reservation assumption, **not a vendor price quotation**. Persistent reservations include failed and ambiguous calls; reopening the ledger cannot reset or raise its ceiling. Use the same ledger across the pilot and language commands. Candidate semantics, language and all repair descendants now share one persistent root-candidate account. Separate ledgers/candidates do not impose an account-wide cap; configure the provider account limit too.

## Review several documents together

The core builds each obligation packet from its source, affected consumers and their upstream authorities. For example, a payment timeout requirement, its API contract and its recovery flow are evaluated together. Packets include artifact IDs, exact revisions, full source text, relationships and required accepted baseline guarantees. The system obligation also reviews the complete configured inventory for missing relationships.

Jev first selects `pass`, `contradiction`, `missing`, `regression` or `unknown`. Its second request selects exact paragraph IDs indexed by code. Code maps those IDs to immutable artifact/revision/Unicode spans and runs the existing core verifier. Pass requires witnesses for every required current artifact and baseline pair. Contradictions require two distinct passages. Missing behavior requires source authority and the complete inspected scope. Regressions require old and current evidence. A selected `none`, confidence below 0.9, malformed response, one-sided finding, context limit or unavailable API cannot become PASS. The confidence threshold is a conservative routing policy, not a calibrated accuracy guarantee.

A large workspace is reviewed by complete obligation boundaries, preserving related documents together. The adapter does not silently truncate files, assume unseen relationships are consistent or synthesize a global pass from incomplete packets. Oversized obligation/system packets remain INCOMPLETE until the boundary is explicitly decomposed or supported limits are revised and evaluated. General cross-packet synthesis is not qualified.

An operator can configure a core workspace with the following provider, using the normal revision-bound configuration flow. Never place the credential itself in configuration:

```yaml
provider:
  type: typesafe-jev
  endpoint: https://api.typesafe.ai/v1/systemone
  model: jev-1.14.0
  api_key_env: JEV_API_KEY
  timeout_seconds: 60
  max_attempts: 2
  max_output_tokens: 4000
  max_cost_usd: 5
  input_per_million: 1
  output_per_million: 1
```

Use `architect-runtime sdd review-candidate WORKSPACE --change CHANGE_ID --live` for deterministic, semantic and language review of one exact candidate. Omit `--live` for local checks only. The underlying core `sdd review` command remains available for semantic-only operation. An agent cannot change accepted grants or publish a candidate by selecting this provider. Unqualified Jev evidence retains the same advisory/manual boundary as other providers. `openai-compatible` and `cascade` remain explicit operator choices for evaluated deployments; they are never selected automatically by the Jev path. The Python `repair_http` integration likewise requires explicit provider configuration and is outside the default path.

## Run the transport pilot

Set `JEV_API_KEY` through a secret manager or secure shell credential flow. Keep its value out of command arguments, source, reports and workflow inputs. The three included synthetic examples test the interface, not semantic quality or independently labeled holdout performance.

```bash
.venv/bin/python -m architect_framework.evaluation_pilot \
  --corpus contracts/evaluation-pilot.json \
  --ledger /path/to/private/pilot-budget.sqlite \
  --report /path/to/private/jev-pilot.json
```

The pilot has at most 30 cases, one attempt per case and stops on the first error. A successful transport cohort reports PASS with `qualified: false`; expected-route mismatches are separate. Missing credentials or failed requests report INCOMPLETE and exit 3. The report omits source bodies and credentials. This pilot remains a small route smoke test; grounded multi-document review uses the core command above.

## Assess and revise language

Offline assessment runs the three local heuristics:

```bash
.venv/bin/python -m architect_framework.style_review \
  --input /path/to/draft.md --report /path/to/private/style.json
```

Add `--live --ledger /path/to/private/pilot-budget.sqlite` for Jev assessment. Every eligible sentence is assessed against all eight rules, with exact source/profile/glossary digests and prebound sentence spans. Every batch sees the complete original document, including protected content as context. Unknown rules remain in the denominator; a model PASS cannot override local failure or invent dictionary authority. `--glossary` supplies lowercase terms with `part_of_speech` and `source`; partial authority remains incomplete. No official ASD dictionary is bundled. `model_assessed_coverage` is advisory, not ASD certification or a qualified 80% claim.

With `--repair`, the report requests a host-author revision. Supply that unpublished draft via `--candidate /path/to/revised.md` to check it. The source and draft files remain unchanged. Programmatic hosts can call `repair_jev` with their existing author callback; Jev checks style and six atomic meaning-preservation questions in separate calls. It does not generate replacement prose. Protected ordered facts, actors, quantities, normative force, identifiers, literals and quotations must pass the local guard first. Uncertain meaning keeps the original text. Broad paraphrases remain subject to independent review. Results stay unpublished and require human review.

## Qualification and recorded exceptions

Real qualification requires independently reviewed labels, source-family-separated calibration and holdout sets, confidence bounds, served-model binding and expiry/revocation. Mock transport choices and model confidence cannot satisfy those requirements. The current companion validation report binds software checks to their actual source; the imported assurance index remains historical. Release quality remains NOT_QUALIFIED until the outstanding evidence is supplied. Existing owner-authorized human verification exceptions remain recorded; runtime signatures, trust, acceptance and publication requirements still apply.

The 2026-10-20 search covered nine relevant local roots and six source ZIPs. The supplied `.architect/reviewers.yml` is a registry containing one reviewer public key; it contains no signed case labels. The discovered evaluation seeds contain 12 semantic cases and two language cases with provisional labels. No independently signed 600-case holdout or authoritative local ASD rule/dictionary mapping was found in that search scope. The project profile remains **UNVERIFIED/advisory**. The [official ASD guidance](https://asd-ste100.org/STEsoftware.html) states that ASD and STEMG do not certify software, including AI tools. An ASD software certificate is therefore not a release requirement; evidence for this project's mapping and measured behavior is still required. This repository does not redistribute the full standard or dictionary.

Technical references checked on 2026-10-16: [TypeSafe state](https://docs.typesafe.ai/concepts/state), [Choice and parallel questions](https://docs.typesafe.ai/primitives/choice), [parallel-question cookbook](https://docs.typesafe.ai/cookbooks/parallel_questions), [preparsed source selection](https://docs.typesafe.ai/cookbooks/pre_parsed_value_extraction_cookbook). These document the typed interface; the packet boundaries and evidence verifier are AAF policy, not vendor quality guarantees.


## Integrated candidate workflow

The local MCP tools are `architect_candidate_review`, `architect_language_review` and `architect_language_repair`. A caller selects an explicit change ID. Live spending requires `live: true`; remote HTTP MCP exposes none of these spending or repair tools. The workbench shows the configured Jev pin, shared reservation ceiling, explicit local/live buttons, per-document revisions, all-rule denominator, unknowns and protected-meaning status. A new job is included in the signing packet binding, so a previously prepared packet cannot silently approve different evidence.

The author writes the draft through its existing host. Use `architect-runtime sdd language-repair WORKSPACE --change CHANGE_ID --artifact ARTIFACT_ID --draft /private/draft.md --skill OWNER_SKILL --expect-snapshot ORIGIN_DIGEST`. The grant and exact source revision must match. Repairs create isolated child candidates, preserve protected facts and consume at most two persistent rounds per root candidate/artifact. Ambiguous attempts retain their reservation. Review the returned child before asking for a human decision. No review or repair accepts or publishes documents.

Candidate language scope is bounded to 32 complete registered documents, 50,000 UTF-8 bytes per document and 64 eligible sentences per document. All related candidate documents accompany each language batch. A candidate language session permits at most 64 calls; the combined semantic stage permits 128 calls and the entire combined operation has a 120-second upper deadline. Full context that exceeds an envelope remains INCOMPLETE; it is never truncated into PASS. Missing credentials, exhausted reservations and oversized scope provide a concrete next action.

## Separate style and meaning evaluation

`architect_framework.language_evaluation` measures the eight style rules and six meaning-preservation checks separately. A version 1 `language-evaluation` corpus names `profile_id`, unique cases, source groups, base cases, families, language and calibration/held_out splits. Style cases supply Markdown, source-backed glossary records and one complete expected rule map per eligible sentence. Meaning cases supply original/candidate text and all six expected check labels. Labels never enter model requests. The existing label-manifest console stages and signs this complete corpus; unverified approval strings grant nothing.

```bash
python -m architect_framework.language_evaluation WORKSPACE \
  --corpus tests/core_engine/evals/language-corpus.json \
  --operation-id LANG-EVAL-OWNER-CHOSEN-ID \
  --report /private/language-evaluation.json
```

Add `--live` only for a real run. The included corpus has provisional synthetic labels and cannot qualify a model. Each invocation has at most 128 calls and 120 seconds; use the same operation ID to resume without resetting its persistent budget. Reports retain abstentions, per-rule confusion/disagreement, Wilson intervals and source-group bootstrap uncertainty. Separate style and meaning qualification requires live execution, two verified independent human labels per held-out case, at least 600 distinct base cases, 30 source groups, 12 families, separated calibration groups, critical examples and conservative per-rule confidence bounds. This is project-profile qualification only: no report certifies ASD compliance, configures a model, accepts documents or qualifies the release. The independent official rule/dictionary mapping remains HUMAN-03.

## Recurring evaluation and drift

```bash
python -m architect_framework.evaluation_monitor WORKSPACE \
  --corpus tests/core_engine/evals/core-corpus.json \
  --report /private/monitor.json
```

The offline health inspection makes no API calls. `--live` requests a bounded Jev canary; `--force` explicitly creates another run. Otherwise the monitor reuses completed results until they are due. An interrupted operational attempt retries with the same operation ID, even across a due-window boundary, preserving its cumulative budget. Identical completed frozen case sets support paired outcome/cost/latency reports. A partial interrupted cohort cannot produce a paired comparison and revokes existing qualification. Changed provider/implementation, expired or revoked qualification, or a failed canary also revokes the old qualification to advisory/manual. The monitor never installs a replacement qualification or edits an accepted policy. Revocations and language/evaluation provenance survive workspace export.

The scheduled GitHub workflow is delivered but disabled by default. The operator must enable `JEV_SCHEDULED_EVAL_ENABLED`, the `model-evaluation` environment, its secret and an account spending limit. Each ephemeral CI canary has its own USD 5 reservation ceiling; that is not a daily account limit. Its public seed is provisional, not a signed independent holdout. No scheduled live run has been executed here. Owner setup and real execution are skipped under HUMAN-04/05.
