# Security Policy

🌐 **Language**: **[English](SECURITY.md)** | [Tiếng Việt](SECURITY.vi.md)

## Supported versions

| Version | Supported |
| --- | --- |
| 1.0.x | Yes |
| < 1.0 | No — pre-release, upgrade to 1.0.x |

Security fixes land on the latest minor release. Older minors are not backported
while the project is at 1.x.

## Reporting a vulnerability

Report privately, not through a public issue.

1. Preferred: open a
   [private security advisory](https://github.com/ldqanh1408/Architect-Agent-Framework/security/advisories/new)
   on this repository.
2. If that is unavailable to you, contact the maintainer through their GitHub
   profile and ask for a private channel before sharing details.

Please include:

- what the issue is and where in the repository it lives;
- the steps or input needed to reproduce it;
- what an attacker gains — this is what determines severity;
- the version or commit you tested;
- any proof-of-concept, clearly marked as such.

**Response targets.** Acknowledgement within 5 business days, an initial
assessment within 10, and a fix or a documented reason for not fixing within 90
for confirmed issues. This is a volunteer-maintained project; if a deadline
slips, you will be told rather than left waiting.

**Disclosure.** Please give 90 days from acknowledgement before disclosing
publicly, or less by mutual agreement once a fix is released. Reporters are
credited in the advisory and the changelog unless they ask not to be.

## What this project's threat model actually is

This matters more here than in a typical library, because most of the repository
is not executable code — it is instructions that an AI agent reads and acts on.

### Skill content is untrusted input to a trusted process

A skill package is prose that an agent loads into its own context and follows. A
skill that instructs an agent to exfiltrate files, weaken a security control, or
run an unexpected command is a real vulnerability even though it contains no
code. **Report malicious or manipulative skill content as a security issue**, not
as a documentation bug.

The catalog is written to a fixed discipline that limits this class of problem:
every skill declares an owned output subtree, is required to treat everything
outside it as read-only, and must classify claims by evidence rather than assert
them. A skill that quietly widens its own write scope, invents authority it was
not given, or reaches outside its subtree is a defect worth reporting.

### Installation writes to your agent's configuration

`install.sh` and `install.ps1` copy directories into `~/.claude/skills` and
equivalents. Anything that lets those scripts write outside the resolved
destination — a crafted skill id, a path-traversal directory name, a symlink in
the catalog — is a vulnerability. Use `--dry-run` to inspect the plan first.

Both scripts write a `.architect-agent-framework` marker into each installed
package and refuse to `--uninstall` a directory that lacks one, specifically so
that an uninstall cannot be turned into a delete of unrelated files.

### The validators are a supply-chain control, not a formality

`exported_skills/release-manifest.yml` pins a SHA-256 for every file in the
catalog, and `sbom.cdx.json` and `provenance.intoto.jsonl` record what the
release contains and how it was produced. Any way to make
`release-check` pass against content that does not match the manifest defeats the
point of publishing hashes at all, and is a security issue.

Verify a downloaded bundle before extracting it:

```bash
sha256sum -c SHA256SUMS.txt --ignore-missing
```

### Out of scope

- Architectural advice you disagree with, or a skill producing a design you
  consider wrong. That is a correctness issue — please open a normal issue.
- Vulnerabilities in a system that an agent designed while using these skills.
  The skills produce documents; they do not build or operate systems.
- Anything requiring an attacker who already controls your machine or your
  agent's configuration directory.
- Denial of service from installing all 297 skills at once. That is documented
  behaviour with a documented remedy: install fewer skills.

## Hardening notes for operators

- Install only the clusters you need. Every installed skill's description enters
  the model's context, and a smaller surface is both safer and more reliable.
- Pin to a tag rather than tracking `main`, and verify checksums on download.
- Run agents with a workspace scope that matches the work. Skills declare their
  own write boundaries, but an agent sandbox is the control that enforces them.
- Review `SKILL.md` before installing a skill from any fork of this repository.
  Forks are not covered by this policy.
