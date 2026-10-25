# `adr-authoring` — Architecture Decision Record (ADR) Authoring

Production package for the `adr-authoring` technical-task skill in **17. Documentation Tasks** (`17_documentation`). `SKILL.md` defines behavior; `skill-contract.yml` is the machine authority; references disclose detailed contracts; scripts provide fail-closed package and generated-output checks.

## Execution

1. Read `SKILL.md`, `skill-contract.yml`, and `_shared/references/prompt-contract.md` completely.
2. Supply the required intake and an owned `output_root`.
3. Run the workflow and retain source/validator evidence.
4. Run `python <catalog>/_shared/scripts/check_skill_package.py .` and `python <catalog>/_shared/scripts/check_output_docs.py <output_root>`.

Shared references and validators live once at the catalog's `_shared/` rather than in every package, so this package is valid inside its catalog, not on its own.

A package-presence check is not behavioral proof. Completion requires the contract's fresh validator evidence over the final artifact state.
