# Requirement Clarifier Skill

Interviews the user in structured rounds to remove ambiguity from raw briefs before any specification is written (SDD Phase 0).

## Folder Directory Structure

- [SKILL.md](SKILL.md) - Deep guidelines, workflow, capabilities, and trigger rules.
- [agents/](agents/) - AI config stubs defining agent prompts.
- [assets/](assets/) - Clarified-requirements template and interview question bank.
- [references/](references/) - Clarification rules and shared reference set.
- [scripts/](scripts/) - Package and markdown link validators.

## Package Verification

To verify the integrity of the `requirement-clarifier` skill package:
```bash
python scripts/check_skill_package.py requirement-clarifier
```
