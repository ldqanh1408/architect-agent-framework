# Changelog

## 2.0.0 — stabilization candidate (unpublished)

- Validate both patch move targets and malformed hook events.
- Export only versioned or explicit hash-bound inputs; keep paid descriptors and discovery metadata private.
- Install private descriptors with integrity checks and recover interrupted multi-pack updates.
- Synchronize lock/version/assets and provide independent public UI fixtures.
- Separate judge simulations from the production console.
- Add exact-artifact qualification, detached operator verification and partial-publication receipts.
- Release remains NOT_QUALIFIED pending applicable external evidence.

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Two version numbers appear in this repository and they mean different things:

- the **release version** (`VERSION`, git tags, `pyproject.toml`,
  `plugins/architect-agent-framework/.claude-plugin/plugin.json`) versions the repository as a whole;
- the **catalog version** (the `version:` field inside each `SKILL.md`) versions
  the skill packages, which evolved before this repository was published.

`scripts/check_versions.py` enforces both rules in CI.

🌐 **Language**: **[English](CHANGELOG.md)** | [Tiếng Việt](CHANGELOG.vi.md)

## [2.0.0] - 2026-10-24

### Added
- **Unified SDD Core v2.0 Engine & 16-Command Operational Control Plane**: Complete end-to-end architecture lifecycle across Claude Code, OpenAI Codex, and DeepSeek Harness (`dsh`) with 16 slash commands, 8 bundled skills, and 29 MCP tools.
- **Zero-Config Judge Discovery & Sharded Review (`resolve_provider_config`)**: Automatic `.env` / environment discovery (`SDD_JUDGE_API_KEY`, `JEV_API_KEY`, `JEV_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`) supporting both `typesafe-jev` and `openai-compatible` endpoints.
- **Native `sdd plan-waves` & UTF-8 `--out` Flag**: Deterministic topological wave lockfile generator (`--batch-size 4`) and BOM-free UTF-8 `--out` support across all CLI commands.
- **Interactive C4 Document Graph & Review Workbench (`:8767`)**: Dynamic system context IDs, automatic External Systems (`c2Externals`) discovery, `# H1` display titles, and hardware WebAuthn passkey sign-off.

### Fixed
- Fixed fenced code block byte-offset calculation and single-line paragraph handling in `_audit_prose_substance`.
- Fixed `prepare-check` depth witness stamping for concern-owning ledger artifacts (`CONCERN-INV`).
- Retired POSIX-only `runtime.sh` in favor of the cross-platform `architect_runtime.py --bootstrap` launcher.

## [1.0.0] - 2026-10-12

First public release of the framework as a Claude Code plugin. The framework is free and
MIT. All 297 skills ship as **skill slots**: each carries its contract and workspace template,
so the router, the multi-agent runtime and the gates know every skill. A slot's content is free
for four skills (`architect-skill-orchestrator`, `adr-authoring`, `agent-workflow-design`,
`arch-review-task`) and installed separately for the rest. The plugin runs from the
marketplace with nothing cloned: its launcher uses a Python that has the framework's packages,
or `uv` fetches the framework of the plugin's own version. The Python package is published as
`architect-agent-framework` on PyPI.

### Changed — one plugin

- The two Claude Code plugins (`plugins/claude-code`, `plugins/architect-runtime`)
  are now one, `plugins/architect-agent-framework`: ten slash commands, five
  skills (the four free catalog skills and `architect-runtime`), the `architect-runtime` MCP
  server and the sandbox hook. The marketplace
  lists that single plugin; the old `plugins/claude-code/plugin.json` was not a
  valid manifest location and failed `claude plugin validate`.
- `scripts/build_plugin_skills.py` keeps the plugin's own `architect-runtime`
  skill on rebuild, and `--check` now fails when a bundled skill differs from the
  catalog, not only when it is missing. The bundle was regenerated.
- README and INSTALL describe the MCP server that exists (`runtime mcp`, sixteen
  tools) instead of an `adapters.mcp_server` module. The old `plugins/codex`, `plugins/agy`
  and `plugins/hermes` stubs are removed.

### Removed

- Commercial-edition tooling and scratch files left the public tree.

The catalog's 294 `SKILL.md` bodies were rewritten by hand to v2.1.0, but the
tooling around them still described the previous generated shape. This release
reconciles the two: the tooling now matches the content, and the content is
protected from the tooling.

### Fixed

- **Regenerating no longer destroys the catalog.** `export-skills` defaulted to
  `--outdir exported_skills`, deleted each package, and rebuilt it from v2.0.0
  templates — one run replaced all 294 authored bodies with generic text. The
  generator now treats `SKILL.md` and `references/research-basis.md` as authored
  and carries them across regeneration, `--outdir` has no default, and writing
  into a populated directory requires `--force`. `--regenerate-skill-md` remains
  as an explicit opt-in for resetting a body.
- **Regenerating no longer deletes catalog-root files.** Generation swaps in a
  freshly built tree, which silently removed `exported_skills/agent.md`.
- **174 of 294 packages failed their own validator.** `check_skill_package.py`
  required a `Common Pitfalls` heading that the v2.1.0 rewrite replaced with
  `Required Distinctions` in 222 packages, so the validation step each `SKILL.md`
  documents exited 1. The gate now requires the *section*, accepting any heading
  the catalog uses for it.
- **CI was red on `main`.** Every package's `package.yml` and the release
  manifest carried stale hashes for `SKILL.md`; `release-check` failed on all 294.
  Manifests are regenerated and now verified.
- **`fail_closed: true` was decorative.** `package.yml` recorded a SHA-256 and
  byte count per file that nothing read. Both the per-package validator and the
  catalog gate now verify them.
- **`validate_catalog.py` reported a clean catalog while 174 packages were
  broken.** It checked neither headings nor manifest hashes; it now checks both.
- **Recovered a corrupted file.** `architect-skill-orchestrator/SKILL.md` had 20
  raw diff markers (`+`) pasted into it, which hid its `Verification Checklist`.
- **Pinned line endings.** With `core.autocrlf=true` and no `.gitattributes`,
  checkouts rewrote the files the manifests hash, so `release-check` failed on
  Windows while passing in CI.

### Changed

- **The Claude Code plugin is self-contained.** It shipped five slash commands,
  no skills, and commands that shelled out to `python -m architect_framework...`
  — which a marketplace user does not have. It now bundles an 11-skill spine
  (the orchestrator plus one lead domain architect per cluster, ~2K tokens of
  descriptions rather than the full catalog's ~62K), and every command works
  without the Python package, using it only as an optional accelerator.
- **Per-skill research provenance moved out of `SKILL.md`.** The
  `Open-Source Research Basis` section — 435 KB, roughly 109K tokens across the
  catalog — explains how a skill was designed and is never needed to run one. It
  now lives in `references/research-basis.md`, loaded on demand, with a pointer
  left behind. Content moved verbatim; nothing was summarised or dropped.
- **Shared governance rules are stated once** in `exported_skills/agent.md`
  (blocking frame, resume frame, and where content belongs) instead of being
  restated across packages.
- **The test suite is runnable again.** Seventeen tests each generated all 294
  packages from scratch. The catalog is now generated once per session and shared
  read-only or as a copy; only tests genuinely about generation still generate.

### Added

- `scripts/build_plugin_skills.py` — builds the plugin's bundled skill set from
  the catalog, with `--check` wired into CI so the bundle cannot go stale.
- `scripts/extract_research_basis.py` — the idempotent migration that moved the
  provenance sections.
- `tests/test_authored_content.py` — regression coverage for the authored half of
  the catalog: preservation across regeneration, the `--force` guard, manifest
  drift detection, and per-package section and hash checks.

## Before the public release (2026-08-01)

Early packaging. The skill catalog and the Python framework already
existed; this release adds everything needed to consume them from outside the
repository.

### Added

- **Installers** — `install.sh` (macOS, Linux, WSL, Git Bash) and `install.ps1`
  (Windows PowerShell). Both flatten the curated catalog on install, so the
  repository can keep its readable `domains/<NN_cluster>/<skill>` layout while
  agents receive the flat directory their runtimes expect. Supports selection by
  skill, by cluster, or `--all`; targets Claude Code, Codex CLI, opencode, and
  Cursor at either user or project scope; and `--dry-run`, `--force`, and
  `--uninstall` for a reversible install.
- **Release build** — `scripts/build_release.py` produces an install-ready flat
  tree, a machine-readable `index.json`, a browsable `INDEX.md`, one zip bundle
  per cluster plus a full bundle, and `SHA256SUMS.txt`. Per-cluster bundles exist
  so installing eleven security skills does not require downloading all 294.
- **Catalog gate** — `scripts/validate_catalog.py` checks every package in one
  pass for missing required files, unparsable or mismatched frontmatter,
  duplicate skill ids that would collide once flattened, and descriptions outside
  the range that triggers reliably. Reports all findings rather than stopping at
  the first.
- **Version gate** — `scripts/check_versions.py` verifies that `VERSION`,
  `pyproject.toml`, `plugins/claude-code/plugin.json`, and
  `.claude-plugin/marketplace.json` agree, and that the catalog version is
  uniform across all packages.
- **Continuous integration** — `.github/workflows/ci.yml` runs lint, the test
  suite on Python 3.10 through 3.13, the catalog and version gates, the release
  manifest integrity check, a bundle build with structural verification, and an
  installer smoke test on Linux, macOS, and Windows.
- **Release automation** — `.github/workflows/release.yml` publishes from a `v*`
  tag. It refuses to publish when the tag disagrees with `VERSION`, re-runs every
  gate, builds the bundles and Python distributions, extracts release notes from
  this changelog, and attaches the artifacts with checksums.
- **Claude Code marketplace manifest** — `.claude-plugin/marketplace.json`, so
  the plugin installs via `/plugin marketplace add`.
- **Release documentation** — `INSTALL.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`,
  and this changelog, each with a Vietnamese counterpart.
- **`VERSION`** as the single source of truth for the release version.

### Fixed

- A malformed fenced code block in `README.md` and `README.vi.md` caused the
  second Python SDK example to render as prose rather than as code.

### Notes

The catalog ships 294 skill packages: 110 domain skills across 10 architecture
clusters, 183 task skills across 20 task families, and 1 orchestrator. Each
package carries `SKILL.md`, a machine contract, references, scripts, assets,
evaluations, and agent manifests. Catalog integrity is pinned by
`exported_skills/release-manifest.yml`, with an SBOM
(`sbom.cdx.json`) and in-toto provenance (`provenance.intoto.jsonl`) alongside it.

[Unreleased]: https://github.com/ldqanh1408/Architect-Agent-Framework/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/ldqanh1408/Architect-Agent-Framework/releases/tag/v1.0.0
