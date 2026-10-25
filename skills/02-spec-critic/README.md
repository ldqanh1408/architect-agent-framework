# Spec Critic Skill

Red-teams the specification set before it becomes the Single Source of Truth — consistency, edge cases, failure modes, pre-mortem risks, ADR challenges (SDD Phase 1.5).

## Folder Directory Structure

- [SKILL.md](SKILL.md) - Deep guidelines, workflow, capabilities, and trigger rules.
- [agents/](agents/) - AI config stubs defining agent prompts.
- [assets/](assets/) - Design review template and pre-mortem checklist.
- [references/](references/) - Critic rules and shared reference set.
- [scripts/](scripts/) - Package and markdown link validators.

## Package Verification

To verify the integrity of the `spec-critic` skill package:
```bash
python scripts/check_skill_package.py spec-critic
```
