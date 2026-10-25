# Architect Agent Framework plugin

Candidate: 1.0.0. Release status: hihi.

[English](README.md) · [Tiếng Việt](README.vi.md) · [Install Guide](INSTALL.md) · [Hướng dẫn cài đặt](INSTALL.vi.md) · [Contributing](CONTRIBUTING.md) · [Hướng dẫn đóng góp](CONTRIBUTING.vi.md) · [Changelog](CHANGELOG.md)

Use the plugin to prepare bounded architecture tasks in a current core workspace across **Claude Code (`claude`)**, **OpenAI Codex (`codex`)**, and **DeepSeek Harness (`dsh`)**. It packages four catalog skills, three foundation skills, and one runtime skill, alongside an embedded zero-install runtime engine (`architect_framework/`, `vendor/sdd-agent/`, and `contracts/`). Its local MCP server exposes proposals, scheduling, and observation.

Use the target host's local plugin procedure. Configure the launcher with this checkout's interpreter. The alpha package is not a published release.

The MCP and hook manifests require a Python 3.10+ command named `python` on the host's PATH, including native Windows. Set `ARCHITECT_PYTHON` to the prepared environment's interpreter. Otherwise the launcher probes its current interpreter and uses `uv`, when available, to provide missing dependencies in an isolated environment. Run any runtime action directly through `python scripts/architect_runtime.py --bootstrap <command>` from the plugin directory.

A missing marker requires explicit setup or migration. A malformed marker requires repair. Old approvals do not authorize current work.

## Quickstart and multi-harness installation

Install the bundled skills, shared templates, and 16 commands across Claude Code, OpenAI Codex, and DeepSeek Harness directly from this repository:

```bash
./install.sh --all --agent all        # macOS / Linux / WSL / Git Bash
.\install.ps1 -All -Agent all        # Windows PowerShell
```

Copy [.env.example](.env.example) to `.env` (or `~/.architect-framework/.env`) when configuring an optional live judge API key (`JEV_API_KEY`). See [INSTALL.md](INSTALL.md) and [INSTALL.vi.md](INSTALL.vi.md) for full setup details.

## Eight end-to-end architecture workflows (`UC-01` .. `UC-08`)

| Use Case | Command | Default Profile | Outcome |
|---|---|---|---|
| **UC-01: Raw Idea to Clarified SRS** | `/architect-clarify <idea or brief.md>` | `seed` · `solo-author` | Socratic interview (max 5 questions with defaults) producing `clarified-requirements.md` |
| **UC-02: Fast-Track MVP Specification** | `/architect-quickstart [source]` | `standard` · `solo-author` | Materializes 12–25 core pages, stamps witnesses, and passes `sdd check` |
| **UC-03: Full Enterprise Maximal Spec** | `/architect-design --profile maximal --sources <...> --out <dir>` | `maximal` · `solo-author` | Autonomous 6-phase execution (Intake, Materialize, Waves, Prepare-Check, Gate, Review) |
| **UC-04: Brownfield Code & Test Audit** | `/architect-audit <code/test> --against <SRS>` | `standard` / `maximal` | Reconciles implementation against specs and records `CNF-*` conflicts |
| **UC-05: Point Solution (Single ADR/API)** | `/architect-route` & `/architect-execute --standalone` | `standalone` | Routes to Domain × Task skill pair and writes a standalone artifact |
| **UC-06: Spec Critique & Gate Check** | `/architect-check --full` & `/architect-review [--live]` | Current workspace | Runs anti-stub/depth gates (`DTG-01..10`), `02-spec-critic`, and sharded judge |
| **UC-07: Living Spec Change Request** | `/architect-change <change description>` | Incremental | Computes graph impact radius and verifies `DTG-07` non-regression |
| **UC-08: C4 Console, Skills & Sign-Off** | `/architect-console`, `/architect-skills`, `/architect-approve` | Workbench (`:8767`) | Interactive C4 map (`< 20ms` reader), 297 skill slot manager, and WebAuthn Passkey sign-off |

Read the complete 16-command manual and multi-harness guide in [docs/QUICKSTART-USE-CASES.md](docs/QUICKSTART-USE-CASES.md).

## Workbench and human decisions

Open the printed localhost link. `/runs` shows Overview, Runs, Gate inbox, Documents, and Settings. `/` shows exact candidate changes and document decisions.

A dispatch signature permits one task attempt. Document acceptance remains separate. Reading starts no work. A scheduling pause stops new dispatch. Running host workers can continue. Cancellation fences late results.

The person starts `architect-runtime console serve <workspace> --enroll` in their own terminal. Register a configured reviewer and confirm the fingerprint there. Copied keys need explicit trust on each machine.

The agent cannot enroll keys, sign decisions, or accept documents. MCP exposes no human approval tool. Required gates stay pending without a trusted key.

## Review and installed skills

Configure an exact model, scope, deadline, attempts, and reservation budget. Inspection does not invoke it. Screening cannot certify grounded correctness. A label signature does not qualify a model automatically.

Use `architect-runtime skills offer <skill-id>` to inspect a slot. Use `architect-runtime skills install <package.zip>` to install compatible content. Accepted grants control writes.

Read the bundled [runtime skill](skills/architect-runtime/SKILL.md) and [command catalog](commands/architect.md). The writing checker is partial and does not certify ASD-STE100.

Current core paths replace the retired runtime. Release qualification remains incomplete where independent human evidence is absent. Local tests use synthetic workers and virtual keys. Live hosts, physical devices, native OS runs, real models, and user studies require separate evidence.

## Current workbench preview

These pictures use the [public payments example](https://github.com/ldqanh1408/Architect-Agent-Framework/blob/main/examples/core-payments/README.md).
They show pending synthetic tasks, not accepted documents. These previews are synthetic workbench examples. The evidence index records the verified source and artifact revision.

Open the local workbench overview to inspect pending task counts and incomplete readiness.

Use `/runs` for dependencies, write scope, and partial observation.

Review task scope in the dispatch gate. Document acceptance remains a separate decision.

## Packaged surfaces

| Surface | Count |
|---|---:|
| Commands | 16 |
| Skills | 8 |
| MCP tools | 29 |

MCP tools expose core planning, candidates and observation. Human signatures stay in the trusted review surface.

## Documentation, issue reporting, and community contributions

| Resource | English | Tiếng Việt / Template |
|---|---|---|
| Documentation Index | [docs/README.md](docs/README.md) | [docs/QUICKSTART-USE-CASES.md](docs/QUICKSTART-USE-CASES.md) |
| Core & E2E Guides | [GUIDE-SDD-CORE.md](docs/GUIDE-SDD-CORE.md) · [GUIDE-CORE-RUNS.md](docs/GUIDE-CORE-RUNS.md) | [GUIDE-E2E-PIPELINE.md](docs/GUIDE-E2E-PIPELINE.md) · [CONCEPTS.md](docs/CONCEPTS.md) |
| CLI, Gates & Support | [REFERENCE-CLI.md](docs/REFERENCE-CLI.md) · [REFERENCE-GATES.md](docs/REFERENCE-GATES.md) | [SUPPORT-MATRIX.md](docs/SUPPORT-MATRIX.md) · [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |
| Contribution Guide | [CONTRIBUTING.md](CONTRIBUTING.md) · [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) | [CONTRIBUTING.vi.md](CONTRIBUTING.vi.md) |
| Code of Conduct & Security | [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) · [SECURITY.md](SECURITY.md) | [CODE_OF_CONDUCT.vi.md](CODE_OF_CONDUCT.vi.md) · [SECURITY.vi.md](SECURITY.vi.md) |
| Changelog, Privacy & License | [CHANGELOG.md](CHANGELOG.md) · [PRIVACY.md](PRIVACY.md) · [LICENSE](LICENSE) | [CHANGELOG.vi.md](CHANGELOG.vi.md) · [NOTICE](NOTICE) |
| Report a Bug / Request Feature | [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md) | [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md) |
| Propose Skill / Adapter / PR | [Skill Proposal](.github/ISSUE_TEMPLATE/skill_proposal.md) · [Adapter Proposal](.github/ISSUE_TEMPLATE/adapter_proposal.md) | [Pull Request Template](.github/PULL_REQUEST_TEMPLATE.md) |
